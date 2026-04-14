from wtforms import form
import os
from flask import Blueprint, render_template, jsonify, redirect, url_for, flash, request, current_app
from models import db, Recipe, ProductionOrder, ProductionOrderInput, Raw_Material, User, ProductionLot, ProductionLotQuality, InventoryMovementMP, InventoryMovementPT, Producto, Raw_Material_Supplier, ProductoPresentacionPrecio, PackagingRecord, ProductionStepTracking,ProductionCycle,ProductionCycleInput
from forms import FormProductionOrder, FormQualityCheck, FormCloseProductionOrder, FormInventoryAdjustment, FormPackaging
from utils.decorators import roles_accepted
from flask_security import current_user
from datetime import datetime, timedelta
from utils.functions import generar_gs1_128, formatear_cadena_gs1_128, process_packaging


module='production'

production_bp = Blueprint(
    module, 
    __name__,
    template_folder='templates',
    static_folder='static'
    )

@production_bp.route('/')
@roles_accepted('Administrador', 'Produccion')
def production():
    orders = ProductionOrder.query.order_by(ProductionOrder.scheduled_date.desc()).all()
    return render_template('production/orders.html', orders=orders)

@production_bp.route('/start_order/<int:id>')
@roles_accepted('Administrador', 'Produccion')
def start_order(id):
    order = ProductionOrder.query.get_or_404(id)
    if order.status == 2:
        order.status = 3
        order.start_date = datetime.now()
        db.session.commit()
        flash(f"Orden {order.folio} ahora está en proceso.", "info")
    return redirect(url_for('production.production'))

@production_bp.route('/add_order', methods=['GET', 'POST'])
@roles_accepted('Administrador', 'Produccion')
def add_order():
    form = FormProductionOrder()
    form.recipe_id.choices = [(r.id, r.final_name) for r in Recipe.query.filter_by(status=1).all()]
    
    if request.method == 'GET':
        form.operator_id.data = current_user.id
        form.scheduled_date.data = datetime.now()

    if form.validate_on_submit():
        try:
            recipe = Recipe.query.get_or_404(form.recipe_id.data)
            num_lotes = int(form.requested_quantity.data)
            qty_total = num_lotes * float(recipe.produced_quantity or 1)
            factor = num_lotes

            # ── Validación completa ────────────────────────────────────────────
            insumos_a_registrar = []
            errores_stock = []

            for detail in recipe.details:
                cantidad_necesaria = float(detail.required_quantity) * factor

                material = Raw_Material.query.with_for_update().get(detail.material_id)

                if not material:
                    errores_stock.append(f"Material ID {detail.material_id} no encontrado.")
                    continue

                stock_disponible = float(material.available_stock or 0)

                if stock_disponible < cantidad_necesaria:
                    faltante = round(cantidad_necesaria - stock_disponible, 2)
                    errores_stock.append(
                        f"{material.name}: necesitas {round(cantidad_necesaria, 2)} "
                        f"{material.nombre_unidad} — "
                        f"disponible: {stock_disponible} — "
                        f"falta: {faltante}"
                    )
                    continue

                rel_proveedor = Raw_Material_Supplier.query.filter_by(
                    id_material=material.id
                ).order_by(Raw_Material_Supplier.price.asc()).first()

                precio_u = float(rel_proveedor.price) if rel_proveedor else 0.0

                insumos_a_registrar.append({
                    'id':           material.id,
                    'name':         material.name,
                    'qty':          cantidad_necesaria,
                    'cost':         round(precio_u * cantidad_necesaria, 2),
                    'precio_u':     precio_u,
                    'material_obj': material
                })

            if errores_stock:
                for error in errores_stock:
                    flash(error, "warning")
                return render_template('production/add.html', form=form)

            # ── Cálculo piezas estimadas ───────────────────────────────────────
            piezas_estimadas = []
            if recipe.product_id:
                producto = Producto.query.get(recipe.product_id)
                if producto and producto.precios:
                    multiplicador = {1: 1000, 2: 1000, 3: 1}.get(recipe.unit_med, 1)
                    cantidad_base_total = qty_total * multiplicador

                    for presentacion in producto.precios:
                        unit_size = float(presentacion.unit_size or 0)
                        if unit_size > 0:
                            piezas_estimadas.append({
                                'presentacion': presentacion.presentation,
                                'piezas': int(cantidad_base_total // unit_size)
                            })

            # ── Creación de la orden ───────────────────────────────────────────
            new_order = ProductionOrder(
                folio=f"OP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                recipe_id=recipe.id,
                requested_quantity=num_lotes,
                unit_med=recipe.unit_med or 1,
                operator_id=form.operator_id.data,
                scheduled_date=form.scheduled_date.data,
                status=2
            )
            db.session.add(new_order)
            db.session.flush()  # Necesitamos new_order.id antes de crear ciclos

            # ── Crear un ciclo por cada lote solicitado ────────────────────────
            qty_por_ciclo = float(recipe.produced_quantity or 1)

            for num_ciclo in range(1, num_lotes + 1):
                ciclo = ProductionCycle(
                    order_id=new_order.id,
                    cycle_number=num_ciclo,
                    quantity_to_produce=qty_por_ciclo,
                    operator_id=form.operator_id.data,
                    scheduled_start_date=form.scheduled_date.data,
                    status=1  # Programado
                )
                db.session.add(ciclo)
                db.session.flush()  # Necesitamos ciclo.id antes de crear insumos y pasos

                # Insumos proporcionales a 1 lote (qty_total / num_lotes)
                for insumo in insumos_a_registrar:
                    qty_ciclo = round(insumo['qty'] / num_lotes, 4)
                    db.session.add(ProductionCycleInput(
                        cycle_id=ciclo.id,
                        material_id=insumo['id'],
                        estimated_quantity=qty_ciclo,
                        actual_used_quantity=0.00,
                        moment_unit_cost=insumo['precio_u']
                    ))

                # Pasos de la receta → seguimiento individual por ciclo
                for paso in recipe.steps:
                    db.session.add(ProductionStepTracking(
                        cycle_id=ciclo.id,
                        recipe_step_id=paso.id,
                        execution_order=paso.step_order,
                        step_name_snapshot=paso.stage_name,
                        description=paso.description,
                        status=1,  # Pendiente
                        requires_verification=(paso.process_type == 7)  # Control de Calidad
                    ))

            # ── Reservar available_stock (una sola vez sobre el total) ─────────
            for insumo in insumos_a_registrar:
                material = insumo['material_obj']
                material.available_stock = float(material.available_stock or 0) - insumo['qty']

                db.session.add(InventoryMovementMP(
                    material_id=insumo['id'],
                    movement_type=2,
                    reason=2,
                    quantity=insumo['qty'],
                    resulting_stock=material.available_stock,
                    pending_quantity=insumo['qty'],
                    status=2,
                    user_id=current_user.id
                ))

            db.session.commit()

            resumen_piezas = ""
            if piezas_estimadas:
                detalle = ", ".join(
                    f"{p['piezas']} uds de {p['presentacion']}"
                    for p in piezas_estimadas
                )
                resumen_piezas = f" | Estimado: {detalle}"

            flash(
                f"Orden {new_order.folio} generada — "
                f"{num_lotes} lote(s) × {recipe.produced_quantity} "
                f"= {qty_total} totales"
                f"{resumen_piezas}. Stock reservado.",
                "success"
            )
            return redirect(url_for('production.production'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error al generar la orden: {type(e).__name__} - {str(e)}", "danger")

    return render_template('production/add.html', form=form)

@production_bp.route('/close_order/<int:id>', methods=['GET', 'POST'])
@roles_accepted('Administrador', 'Produccion')
def close_order(id):
    order = ProductionOrder.query.get_or_404(id)

    # ... (Validaciones de estados y ciclos incompletos se mantienen igual) ...

    form = FormCloseProductionOrder()
    recipe = order.recipe
    num_lotes = int(order.requested_quantity or 1)
    qty_teorica_total = num_lotes * float(recipe.produced_quantity or 1)

    if request.method == 'GET':
        porcentaje_merma = float(recipe.estimated_waste or 0) / 100
        qty_esperada = round(qty_teorica_total * (1 - porcentaje_merma), 2)
        merma_esperada = round(qty_teorica_total - qty_esperada, 2)
        form.produced_qty.data = qty_esperada
        form.real_waste.data = merma_esperada
        dias_vida = int(getattr(recipe, 'days_of_life', 365) or 365)
        form.expiry_date.data = (datetime.now() + timedelta(days=dias_vida)).date()

    if form.validate_on_submit():
        try:
            qty_real = float(form.produced_qty.data)
            merma_real = round(qty_teorica_total - qty_real, 2)

            if qty_real <= 0:
                flash("La cantidad producida debe ser mayor a cero.", "warning")
                return render_template('production/close.html', order=order, form=form, total_input=qty_teorica_total)

            # 1. Actualizar Orden
            order.real_waste = merma_real
            order.end_date = datetime.now()
            order.status = 4

            # 2. Descontar Stock de Materia Prima (Esto se queda, ya se consumió)
            for insumo in order.inputs:
                material = Raw_Material.query.with_for_update().get(insumo.material_id)
                material.real_stock = float(material.real_stock or 0) - float(insumo.used_quantity)
                
                # Actualizar movimiento a completado
                mov_pendiente = InventoryMovementMP.query.filter_by(
                    material_id = insumo.material_id,
                    status = 2,
                    pending_quantity = insumo.used_quantity
                ).order_by(InventoryMovementMP.timestamp.desc()).first()

                if mov_pendiente:
                    mov_pendiente.status = 1 
                    mov_pendiente.resulting_stock = material.real_stock
                    mov_pendiente.pending_quantity = 0

            # 3. Costo unitario
            total_costo_insumos = sum(float(i.moment_cost or 0) for i in order.inputs)
            costo_u = round(total_costo_insumos / qty_real, 4) if qty_real > 0 else 0

            # 4. Crear Lote en Cuarentena (A granel)
            new_lot = ProductionLot(
                lot_code = f"LOT-{order.folio}-{datetime.now().strftime('%y%m%d%H%M')}",
                product_id = recipe.product_id,
                product_name = recipe.final_name,
                order_folio_ref = order.folio,
                produced_quantity = qty_real,
                current_stock = qty_real, # Stock a granel disponible para envasar
                unit_med = str(order.unit_med),
                unit_cost = costo_u,
                expiry_date = form.expiry_date.data,
                warehouse_location = form.location.data,
                status = 2 # Cuarentena (Laboratorio)
            )
            db.session.add(new_lot)
            db.session.commit()

            flash(f"Orden {order.folio} cerrada. Lote enviado a laboratorio.", "success")
            return redirect(url_for('production.quality_pending'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error al cerrar la orden: {str(e)}", "danger")

    return render_template('production/close.html', order=order, form=form, total_input=qty_teorica_total)

@production_bp.route('/quality_check/<int:lot_id>', methods=['GET', 'POST'])
@roles_accepted('Administrador', 'Produccion')
def quality_check(lot_id):
    lot = ProductionLot.query.get_or_404(lot_id)
    form = FormQualityCheck()

    if form.validate_on_submit():
        try:
            is_approved = int(form.is_approved.data) == 1
            
            # Guardamos el PH y Aspecto
            check = ProductionLotQuality(
                lot_id=lot.id,
                parameter="Calidad Fisicoquímica",
                obtained_value=f"pH: {form.ph_level.data} | Asp: {form.appearance.data} | Dens: {form.density.data}",
                is_approved=is_approved
            )
            db.session.add(check)

            # Obtenemos el producto y su primera presentación (o la específica del lote)
            # Nota: Si tu lote tiene un 'presentation_id', úsalo aquí. 
            # Si no, tomamos la primera disponible.
            prod = Producto.query.get_or_404(lot.product_id)
            presentacion = prod.precios[0] if prod.precios else None

            if not presentacion:
                raise Exception("El producto no tiene presentaciones configuradas para asignar stock.")

            if is_approved:
                lot.status = 5  # Pendiente de envasado
                flash(f"Lote {lot.lot_code} aprobado.", "success")

            else:
                lot.status = 4 # Rechazado
                # En rechazo no sumamos stock, pero registramos el evento
                db.session.add(InventoryMovementPT(
                    product_id=prod.id,
                    type=2,               # Salida/Merma
                    reason=1,             # Rechazo Calidad
                    quantity=lot.produced_quantity,
                    resulting_stock=presentacion.stock,
                    status=2,
                    user_id=current_user.id
                ))
                flash(f"Lote {lot.lot_code} rechazado por calidad.", "warning")

            db.session.commit()
            return redirect(url_for('production.quality_pending'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error técnico: {str(e)}", "danger")

    return render_template('production/quality_form.html', lot=lot, form=form)

@production_bp.route('/quality_pending')
@roles_accepted('Administrador', 'Produccion')
def quality_pending():
    # Filtramos lotes que están en status 2 (Cuarentena)
    from models import ProductionLot
    lots = ProductionLot.query.filter_by(status=2).all()
    return render_template('production/quality_list.html', lots=lots)
@production_bp.route('/inventory_pt_adjustment', methods=['GET', 'POST'])
@roles_accepted('Administrador')
def inventory_pt_adjustment():
    form = FormInventoryAdjustment()

    # CAMBIO: Traemos las presentaciones, no los productos base
    presentaciones = ProductoPresentacionPrecio.query.join(Producto).filter(Producto.status == 'Activo').all()
    
    # El choice ahora debe ser sobre el ID de la presentación
    form.product_id.choices = [
        (p.id, f"{p.producto.name} - {p.presentation} (Actual: {p.stock or 0})") 
        for p in presentaciones
    ]

    if form.validate_on_submit():
        try:
            # CAMBIO: Buscamos en la tabla de presentaciones
            presentacion = ProductoPresentacionPrecio.query.get_or_404(form.product_id.data)
            tipo = form.type.data
            cantidad = float(form.quantity.data)
            
            # Lógica de Stock aplicada a la presentación
            stock_actual = presentacion.stock or 0
            if tipo == 1: # Entrada
                presentacion.stock = stock_actual + cantidad
            else: # Salida
                presentacion.stock = stock_actual - cantidad

            # Registro del movimiento
            nuevo_mov = InventoryMovementPT(
                product_id=presentacion.id_producto, # ID del producto padre
                # OJO: Si tu tabla InventoryMovementPT no tiene 'presentation_id', 
                # te sugiero agregarla en el futuro para saber exactamente qué se ajustó.
                type=tipo,
                reason=form.reason.data,
                quantity=cantidad,
                resulting_stock=presentacion.stock, # Stock de la presentación
                user_id=current_user.id,
                status=1,
                timestamp=datetime.now()
            )
            
            db.session.add(nuevo_mov)
            db.session.commit()
            
            flash("Inventario de presentación actualizado correctamente", "success")
            return redirect(url_for('production.inventory_pt'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")

    return render_template('production/inventory_pt_adjustment.html', form=form)

@production_bp.route('/inventory_pt')
@roles_accepted('Administrador', 'Produccion')
def inventory_pt():
    # Traemos productos y cargamos sus presentaciones (precios) de una vez (eager loading)
    productos = Producto.query.all()
    movimientos = InventoryMovementPT.query.order_by(InventoryMovementPT.timestamp.desc()).limit(50).all()
    
    return render_template('production/inventory_pt.html', 
                           productos=productos, 
                           movimientos=movimientos)

@production_bp.route('/history/<int:product_id>')
@roles_accepted('Administrador', 'Produccion')
def inventory_pt_history(product_id):
    producto = Producto.query.get_or_404(product_id)
    movimientos = InventoryMovementPT.query.filter_by(product_id=product_id).order_by(InventoryMovementPT.timestamp.desc()).all()
    
    return render_template('production/inventory_pt_history.html',
                           producto=producto, 
                           movimientos=movimientos)

@production_bp.route('/order_details/<int:id>')
@roles_accepted('Administrador', 'Produccion', 'Almacenista')
def order_details(id):
    order = ProductionOrder.query.get_or_404(id)
    recipe = order.recipe

    # ═══════════════════════════════════════════
    # CANTIDAD REAL A PRODUCIR
    # requested_quantity = lotes (Integer)
    # qty_total = lotes × cantidad base de receta
    # ═══════════════════════════════════════════
    num_lotes = int(order.requested_quantity or 1)
    qty_total = num_lotes * float(recipe.produced_quantity or 1)
    factor    = num_lotes

    # ═══════════════════════════════════════════
    # COSTO TOTAL DE INSUMOS
    # ═══════════════════════════════════════════
    total_cost_insumos = sum(float(i.moment_cost or 0) for i in order.inputs)

    # ═══════════════════════════════════════════
    # INSUMOS CON DETALLE (para mostrar en tabla)
    # ═══════════════════════════════════════════
    insumos_detalle = []
    for insumo in order.inputs:
        insumos_detalle.append({
            'nombre':       insumo.material_name,
            'cantidad':     float(insumo.used_quantity),
            'unidad':       insumo.material.nombre_unidad if insumo.material else '',
            'costo_total':  float(insumo.moment_cost or 0),
            # Costo unitario por kg/L de ese insumo
            'costo_unit':   round(float(insumo.moment_cost or 0) / float(insumo.used_quantity), 4)
                            if float(insumo.used_quantity) > 0 else 0
        })

    # ═══════════════════════════════════════════
    # PIEZAS ESTIMADAS (mismo cálculo que add_order)
    # ═══════════════════════════════════════════
    piezas_estimadas = []
    if recipe.product_id:
        producto = Producto.query.get(recipe.product_id)
        if producto and producto.precios:
            multiplicador       = {1: 1000, 2: 1000, 3: 1}.get(recipe.unit_med, 1)
            cantidad_base_total = qty_total * multiplicador

            for presentacion in producto.precios:
                unit_size = float(presentacion.unit_size or 0)
                if unit_size > 0:
                    piezas_estimadas.append({
                        'presentacion': presentacion.presentation,
                        'piezas':       int(cantidad_base_total // unit_size),
                        'unit_size':    unit_size
                    })

    # ═══════════════════════════════════════════
    # LOTE GENERADO (si ya se cerró la orden)
    # ═══════════════════════════════════════════
    lote = ProductionLot.query.filter_by(order_folio_ref=order.folio).first()

    return render_template('production/details.html',
                           order=order,
                           lote=lote,
                           total_cost=total_cost_insumos,
                           # Nuevos
                           num_lotes=num_lotes,
                           qty_total=qty_total,
                           insumos_detalle=insumos_detalle,
                           piezas_estimadas=piezas_estimadas)

@production_bp.route('/lots_pt')
@roles_accepted('Administrador', 'Produccion', 'Almacenista')
def lots_pt():
    # Obtenemos el término de búsqueda si existe
    search = request.args.get('search', '')
    
    query = ProductionLot.query
    
    if search:
        query = query.filter(
            (ProductionLot.lot_code.contains(search)) | 
            (ProductionLot.product_name.contains(search)) |
            (ProductionLot.order_folio_ref.contains(search))
        )
    
    # Ordenar por fecha de creación (ID descendente suele ser lo más rápido)
    lots = query.order_by(ProductionLot.id.desc()).all()
    
    return render_template('production/lots_pt.html', lots=lots, search=search, now=datetime.now())

@production_bp.route('/recipe_info/<int:recipe_id>')
@roles_accepted('Administrador', 'Produccion')
def recipe_info(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    
    # Insumos con stock actual
    insumos = []
    for detail in recipe.details:
        material = detail.material
        insumos.append({
            'nombre':      material.name,
            'cantidad':    float(detail.required_quantity),
            'unidad':      material.nombre_unidad,
            'stock_disp':  float(material.available_stock or 0),
            'stock_real':  float(material.real_stock or 0),
        })

    # Presentaciones del producto
    presentaciones = []
    if recipe.product_id and recipe.product:
        for p in recipe.product.precios:
            presentaciones.append({
                'nombre':    p.presentation,
                'unit_size': float(p.unit_size or 0),
                'unit_type': p.unit_type,
            })

    unidades = {1: 'kg', 2: 'L', 3: 'pzas'}

    return jsonify({
        'nombre':           recipe.final_name,
        'instrucciones':    recipe.general_instructions or '',
        'cantidad_base':    float(recipe.produced_quantity or 0),
        'unidad':           unidades.get(recipe.unit_med, ''),
        'merma_estimada':   float(recipe.estimated_waste or 0),
        'tiempo_estimado':  recipe.estimated_time or 0,
        'producto_nombre':  recipe.product.name if recipe.product else '—',
        'insumos':          insumos,
        'presentaciones':   presentaciones,
    })

@production_bp.route('/lot_barcode/<int:lot_id>')
@roles_accepted('Administrador', 'Produccion', 'Almacenista')
def lot_barcode(lot_id):
    
    
    lot = ProductionLot.query.get_or_404(lot_id)
    
    # Necesitamos product_id y presentation_id — usamos 1 como presentación base
    # si no tienes presentacion_id en el lote, puedes ajustar este valor
    barcode_img = generar_gs1_128(
        producto_id=lot.product_id,
        presentacion_id=1,          # ajusta si tienes el dato en el lote
        lote_nombre=lot.lot_code
    )
    cadena_gs1 = formatear_cadena_gs1_128(lot.product_id, 1, lot.lot_code)
    
    return jsonify({
        'imagen_base64': barcode_img,
        'codigo_gs1': cadena_gs1,
        'lot_code': lot.lot_code,
        'product_name': lot.product_name
    })

#Empaquetado
@production_bp.route('/lots_pending')
@roles_accepted('Administrador', 'Produccion')
def lots_list():
    """Lotes aprobados en QC esperando ser embasados (status 5 y 6)."""
    lotes = ProductionLot.query.filter(
        ProductionLot.status.in_([5, 6])
    ).order_by(ProductionLot.manufacture_date.desc()).all()

    return render_template('production/lots_list.html', lotes=lotes)


@production_bp.route('/lots_package/<int:lot_id>', methods=['GET', 'POST'])
@roles_accepted('Administrador', 'Produccion')
def package_lot(lot_id):
    """Detalle del lote + acción de embasado por presentación."""
    lote = ProductionLot.query.get_or_404(lot_id)

    if lote.status not in [5, 6]:
        flash("Este lote no está disponible para embasado.", "warning")
        return redirect(url_for('production.lots_list'))

    presentaciones = ProductoPresentacionPrecio.query.filter_by(
        id_producto=lote.product_id
    ).all()

    form = FormPackaging()
    form.id_presentacion.choices = [
        (p.id, f"{p.presentation} — {p.unit_size} {'ml' if p.unit_type == 1 else 'g'}")
        for p in presentaciones
    ]

    # Precálculo por presentación: max unidades posibles considerando
    # tanto el contenido del lote como el stock de MP de empaque
    calculos = {}
    for p in presentaciones:
        contenido_por_unidad = float(p.unit_size) / 1000
        max_units = int(float(lote.current_stock) / contenido_por_unidad) if contenido_por_unidad > 0 else 0

        mp_details = []
        for pm in p.packaging_materials:
            disponible = float(pm.material.available_stock)
            requerido_max = float(pm.quantity_per_unit) * max_units
            alcanza = disponible >= requerido_max

            if not alcanza and float(pm.quantity_per_unit) > 0:
                max_units = min(max_units, int(disponible / float(pm.quantity_per_unit)))

            mp_details.append({
                'nombre':        pm.material.name,
                'disponible':    disponible,
                'requerido_max': float(pm.quantity_per_unit) * max_units,
                'alcanza':       alcanza
            })

        calculos[p.id] = {
            'max_units':           max_units,
            'contenido_por_unidad': contenido_por_unidad,
            'mp_details':          mp_details,
            'mp_suficiente':       all(d['alcanza'] for d in mp_details)
        }

    historial = PackagingRecord.query.filter_by(lot_id=lot_id).order_by(
        PackagingRecord.timestamp.desc()
    ).all()

    if form.validate_on_submit():
        ok, resultado = process_packaging(
            lot_id=lot_id,
            id_presentacion=form.id_presentacion.data,
            units_to_package=form.units_to_package.data,
            operator_id=current_user.id
        )
        if ok:
            flash(
                f"Embasado exitoso: {resultado['units_packaged']} unidades. "
                f"Stock PT actualizado: {resultado['stock_pt_nuevo']}",
                "success"
            )
            return redirect(url_for('production.package_lot', lot_id=lot_id))
        else:
            flash(f"Error: {resultado}", "danger")

    return render_template(
        'production/package_lot.html',
        lote=lote,
        form=form,
        presentaciones=presentaciones,
        calculos=calculos,
        historial=historial
    )


@production_bp.route('/api/calcular-embasado')
@roles_accepted('Administrador', 'Produccion')
def api_calcular_embasado():
    """Validación AJAX en tiempo real para el formulario de embasado."""
    lot_id = request.args.get('lot_id', type=int)
    id_pres = request.args.get('id_presentacion', type=int)
    units   = request.args.get('units', type=int, default=0)

    lote = ProductionLot.query.get(lot_id)
    pres = ProductoPresentacionPrecio.query.get(id_pres)

    if not lote or not pres:
        return jsonify({'ok': False, 'error': 'Lote o presentación no encontrada'})

    contenido_por_unidad  = float(pres.unit_size) / 1000
    contenido_necesario   = contenido_por_unidad * units

    errores  = []
    mp_check = []

    if contenido_necesario > float(lote.current_stock):
        errores.append(
            f"Contenido insuficiente. Necesario: {contenido_necesario:.2f}, "
            f"Disponible: {lote.current_stock}"
        )

    for pm in pres.packaging_materials:
        requerido  = float(pm.quantity_per_unit) * units
        disponible = float(pm.material.available_stock)
        alcanza    = disponible >= requerido

        if not alcanza:
            errores.append(
                f"Stock insuficiente de '{pm.material.name}': "
                f"necesario {requerido:.2f}, disponible {disponible:.2f}"
            )

        mp_check.append({
            'material':   pm.material.name,
            'requerido':  requerido,
            'disponible': disponible,
            'ok':         alcanza
        })

    return jsonify({
        'ok':                   len(errores) == 0,
        'errores':              errores,
        'contenido_necesario':  contenido_necesario,
        'contenido_disponible': float(lote.current_stock),
        'mp_check':             mp_check
    })

@production_bp.route('/cycle_step_update/<int:step_id>', methods=['POST'])
@roles_accepted('Administrador', 'Produccion')
def cycle_step_update(step_id):
    """Actualiza el estado de un paso de seguimiento de ciclo."""
    step = ProductionStepTracking.query.get_or_404(step_id)
    new_status = request.form.get('status', type=int)
    notes = request.form.get('notes', '')

    if new_status not in [1, 2, 3, 4]:
        return jsonify({'ok': False, 'error': 'Estado inválido'})

    step.status = new_status
    step.notes = notes

    if new_status == 2 and not step.start_date:
        step.start_date = datetime.now()
        step.operator_id = current_user.id
    elif new_status == 3:
        step.end_date = datetime.now()

    # Si todos los pasos del ciclo están completados → ciclo terminado
    ciclo = ProductionCycle.query.get(step.cycle_id)
    todos = ProductionStepTracking.query.filter_by(cycle_id=ciclo.id).all()
    if all(s.status == 3 for s in todos):
        ciclo.status = 4  # Terminado
        ciclo.actual_end_date = datetime.now()

    db.session.commit()
    return jsonify({'ok': True, 'cycle_status': ciclo.status})


@production_bp.route('/cycle_update/<int:cycle_id>', methods=['POST'])
@roles_accepted('Administrador', 'Produccion')
def cycle_update(cycle_id):
    """Avanza el estado general de un ciclo."""
    ciclo = ProductionCycle.query.get_or_404(cycle_id)
    new_status = request.form.get('status', type=int)

    if new_status == 2 and ciclo.status == 1:  # Programado → En Pesaje
        ciclo.status = 2
        ciclo.actual_start_date = datetime.now()
    elif new_status == 3 and ciclo.status == 2:  # En Pesaje → Mezclado
        ciclo.status = 3

    db.session.commit()
    return redirect(url_for('production.order_details', id=ciclo.order_id))

from sqlalchemy import func

@production_bp.route('/bulk_inventory_status')
@roles_accepted('Administrador', 'Produccion')
def bulk_inventory_status():
    bulk_stocks = db.session.query(
        ProductionLot.product_id,
        ProductionLot.product_name,
        ProductionLot.unit_med,
        func.sum(ProductionLot.current_stock).label('total_bulk')
    ).filter(ProductionLot.status.in_([5, 6]))\
     .group_by(ProductionLot.product_id, ProductionLot.product_name, ProductionLot.unit_med)\
     .all()

    results = []
    for item in bulk_stocks:
        recipe = Recipe.query.filter_by(product_id=item.product_id, status=1).first()
        
        # --- SOLUCIÓN: Conversión explícita ---
        # Convertimos a float para evitar el TypeError en el HTML
        total_bulk = float(item.total_bulk or 0)
        threshold = float(recipe.produced_quantity) if recipe else 0.0
        
        is_low = total_bulk < threshold if threshold > 0 else False

        results.append({
            'product_id': item.product_id,
            'product_name': item.product_name,
            'unit_med': item.unit_med,
            'total_bulk': total_bulk,
            'threshold': threshold,
            'is_low': is_low
        })

    return render_template('production/bulk_status.html', results=results)

from sqlalchemy import func

@production_bp.route('/production_reports')
@roles_accepted('Administrador', 'Produccion')
def production_reports():
    """Genera un reporte de productos más producidos cruzando Ciclos -> Orden -> Receta -> Producto."""
    
    # Realizamos el triple join para llegar al nombre del producto
    # Usamos quantity_to_produce que es el campo real en ProductionCycle
    report_data = db.session.query(
        Producto.name.label('product_name'),
        func.sum(ProductionCycle.quantity_to_produce).label('total_produced'),
        func.count(ProductionCycle.id).label('times_produced')
    ).join(ProductionOrder, ProductionCycle.order_id == ProductionOrder.id) \
     .join(Recipe, ProductionOrder.recipe_id == Recipe.id) \
     .join(Producto, Recipe.product_id == Producto.id) \
     .filter(ProductionCycle.status == 4) \
     .group_by(Producto.name) \
     .order_by(func.sum(ProductionCycle.quantity_to_produce).desc()) \
     .all()

    # Calculamos el total global para los porcentajes
    total_global = sum(float(item.total_produced or 0) for item in report_data)

    results = []
    for item in report_data:
        total_item = float(item.total_produced or 0)
        participation = (total_item / total_global * 100) if total_global > 0 else 0
        
        results.append({
            'name': item.product_name,
            'total': total_item,
            'count': item.times_produced,
            'pct': round(participation, 1)
        })

    return render_template('production/reports_production.html', results=results, total_global=total_global)