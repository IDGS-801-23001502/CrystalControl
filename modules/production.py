from wtforms import form
import os
from flask import Blueprint, render_template, jsonify, redirect, url_for, flash, request, current_app
from models import db, Recipe, ProductionOrder, ProductionOrderInput, Raw_Material, User, ProductionLot, ProductionLotQuality, InventoryMovementMP, InventoryMovementPT, Producto, Raw_Material_Supplier
from forms import FormProductionOrder, FormQualityCheck, FormCloseProductionOrder, FormInventoryAdjustment
from utils.decorators import roles_accepted
from flask_security import current_user
from datetime import datetime, timedelta


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

            #Validacion completa
            insumos_a_registrar = []
            errores_stock = []

            for detail in recipe.details:
                cantidad_necesaria = float(detail.required_quantity) * factor

                # Leemos el material con lock
                material = Raw_Material.query.with_for_update().get(detail.material_id)

                if not material:
                    errores_stock.append(f"Material ID {detail.material_id} no encontrado.")
                    continue

                #Usamos available_stock (ya descuenta reservas de otras órdenes)
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

                # Precio del proveedor más barato asociado a este material
                rel_proveedor = Raw_Material_Supplier.query.filter_by(
                    id_material=material.id
                ).order_by(Raw_Material_Supplier.price.asc()).first()

                precio_u = float(rel_proveedor.price) if rel_proveedor else 0.0

                insumos_a_registrar.append({
                    'id':           material.id,
                    'name':         material.name,
                    'qty':          cantidad_necesaria,
                    'cost':         round(precio_u * cantidad_necesaria, 2),
                    'material_obj': material
                })

            # Si hay Cualquier error, abortamos sin tocar la BD
            if errores_stock:
                for error in errores_stock:
                    flash(error, "warning")
                return render_template('production/add.html', form=form)

            #Calculo piezas estimadas
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

            #Creación de la orden
            new_order = ProductionOrder(
                folio = f"OP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                recipe_id = recipe.id,
                requested_quantity = num_lotes,
                unit_med = recipe.unit_med or 1,
                operator_id = form.operator_id.data,
                scheduled_date = form.scheduled_date.data,
                status = 2
                )
            
            db.session.add(new_order)
            db.session.flush()

            for insumo in insumos_a_registrar:
                material = insumo['material_obj']

                db.session.add(ProductionOrderInput(
                    order_id = new_order.id,
                    material_id = insumo['id'],
                    material_name = insumo['name'],
                    used_quantity = insumo['qty'],
                    moment_cost = insumo['cost']
                ))

                #Descontar available_stock (reserva)
                #real_stock NO se toca hasta close_order
                material.available_stock = float(material.available_stock or 0) - insumo['qty']

                db.session.add(InventoryMovementMP(
                    material_id = insumo['id'],
                    movement_type = 2,    
                    reason = 2,    
                    quantity = insumo['qty'],
                    resulting_stock  = material.available_stock,
                    pending_quantity = insumo['qty'], 
                    status = 2,             
                    user_id = current_user.id
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

    if order.status not in [2, 3]:
        flash("Esta orden no puede cerrarse en su estado actual.", "warning")
        return redirect(url_for('production.production'))

    form = FormCloseProductionOrder()
    total_input_qty = sum(float(i.used_quantity) for i in order.inputs)

    if request.method == 'GET':
        recipe = order.recipe
        porcentaje_merma = float(recipe.estimated_waste or 0) / 100
        qty_esperada = round(total_input_qty * (1 - porcentaje_merma), 2)
        merma_esperada = round(total_input_qty - qty_esperada, 2)

        form.produced_qty.data = qty_esperada
        form.real_waste.data = merma_esperada

        dias_vida = int(getattr(recipe, 'days_of_life', 365) or 365)
        form.expiry_date.data = (datetime.now() + timedelta(days=dias_vida)).date()

    if form.validate_on_submit():
        try:
            qty_real = float(form.produced_qty.data)
            merma_real = round(total_input_qty - qty_real, 2)

            if qty_real <= 0:
                flash("La cantidad producida debe ser mayor a cero.", "warning")
                return render_template('production/close.html',
                                       order=order, form=form,
                                       total_input=total_input_qty)

            #Cerrar la orden
            order.real_waste = merma_real
            order.end_date = datetime.now()
            order.status = 4

            for insumo in order.inputs:
                material = Raw_Material.query.with_for_update().get(insumo.material_id)

                #Descontar real_stock
                material.real_stock = float(material.real_stock or 0) - float(insumo.used_quantity)

                #Buscar el movimiento pendiente de este insumo en esta orden
                #Usando pending_quantity que guardamos en add_order
                mov_pendiente = InventoryMovementMP.query.filter_by(
                    material_id = insumo.material_id,
                    status = 2,
                    pending_quantity = insumo.used_quantity
                ).order_by(InventoryMovementMP.timestamp.desc()).first()

                if mov_pendiente:
                    mov_pendiente.status = 1 
                    mov_pendiente.resulting_stock = material.real_stock
                    mov_pendiente.pending_quantity = 0
                else:
                    db.session.add(InventoryMovementMP(
                        material_id = insumo.material_id,
                        movement_type = 2,
                        reason = 2,
                        quantity = insumo.used_quantity,
                        resulting_stock = material.real_stock,
                        pending_quantity = 0,
                        status = 1,
                        user_id = current_user.id
                    ))

            # 3. Costo unitario
            total_costo = sum(float(i.moment_cost or 0) for i in order.inputs)
            costo_u = round(total_costo / qty_real, 4) if qty_real > 0 else 0

            #Crear lote en cuarentena
            #Stock de PT NO se toca — lo hace quality_check al aprobar
            new_lot = ProductionLot(
                lot_code = f"LOT-{order.folio}-{datetime.now().strftime('%y%m%d%H%M')}",
                product_id = order.recipe.product_id,
                product_name = order.recipe.final_name,
                order_folio_ref = order.folio,
                produced_quantity = qty_real,
                current_stock = qty_real,
                unit_med = str(order.unit_med),
                unit_cost = costo_u,
                expiry_date = form.expiry_date.data,
                warehouse_location = form.location.data,
                status = 2
            )
            db.session.add(new_lot)
            db.session.commit()

            flash(
                f"Orden {order.folio} cerrada. "
                f"Producido: {qty_real} | Merma: {merma_real} | "
                f"Costo unitario: ${costo_u:.4f} | "
                f"Lote {new_lot.lot_code} en cuarentena.",
                "success"
            )
            return redirect(url_for('production.quality_pending'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error al cerrar la orden: {type(e).__name__} - {str(e)}", "danger")
    else:
        if request.method == 'POST':
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Campo {getattr(form, field).label.text}: {error}", "warning")

    return render_template('production/close.html',
                           order=order,
                           form=form,
                           total_input=total_input_qty)

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
                obtained_value=f"pH: {form.ph_level.data} | Asp: {form.appearance.data}",
                is_approved=is_approved
            )
            db.session.add(check)

            if is_approved:
                lot.status = 1  # Disponible

                #AQUÍ sí entra el stock real a PT
                prod = Producto.query.get_or_404(lot.product_id)
                prod.stock = (prod.stock or 0) + float(lot.produced_quantity)

                db.session.add(InventoryMovementPT(
                    product_id=prod.id,
                    type=1,               # Entrada
                    reason=2,             # Producción
                    quantity=lot.produced_quantity,
                    resulting_stock=prod.stock,
                    user_id=current_user.id
                ))
                flash(f"Lote {lot.lot_code} aprobado. Stock actualizado.", "success")

            else:
                lot.status = 4

                # Registrar movimiento de merma/rechazo para trazabilidad
                prod = Producto.query.get_or_404(lot.product_id)
                db.session.add(InventoryMovementPT(
                    product_id=prod.id,
                    type=2,              
                    reason=1,            
                    quantity=lot.produced_quantity,
                    resulting_stock=prod.stock,
                    user_id=current_user.id
                ))
                flash(f"Lote {lot.lot_code} rechazado. Sin impacto en stock.", "warning")

            db.session.commit()
            return redirect(url_for('production.quality_pending'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")

    return render_template('production/quality_form.html', lot=lot, form=form)

@production_bp.route('/quality_pending')
@roles_accepted('Administrador', 'Produccion')
def quality_pending():
    # Filtramos lotes que están en status 2 (Cuarentena)
    from models import ProductionLot
    lots = ProductionLot.query.filter_by(status=2).all()
    return render_template('production/quality_list.html', lots=lots)

@production_bp.route('/inventory_pt')
@roles_accepted('Administrador', 'Produccion')
def inventory_pt():
    # Obtenemos todos los productos y sus lotes activos
    productos = Producto.query.all()
    # Movimientos recientes de producto terminado
    movimientos = InventoryMovementPT.query.order_by(InventoryMovementPT.timestamp.desc()).all()
    return render_template('production/inventory_pt.html', productos=productos, movimientos=movimientos)

@production_bp.route('/inventory_pt_adjustment', methods=['GET', 'POST'])
@roles_accepted('Administrador')
def inventory_pt_adjustment():
    form = FormInventoryAdjustment()

    productos = Producto.query.filter_by(status='Activo').all()
    form.product_id.choices = [(p.id, f"{p.name} (Actual: {p.stock})") for p in productos]

    if form.validate_on_submit():
        try:
            producto = Producto.query.get_or_404(form.product_id.data)
            tipo = form.type.data
            cantidad = float(form.quantity.data)
            
            # Lógica de Stock
            if tipo == 1: # Entrada
                producto.stock = (producto.stock or 0) + cantidad
            else: # Salida
                producto.stock = (producto.stock or 0) - cantidad

            # Registro en el modelo de movimientos
            nuevo_mov = InventoryMovementPT(
                product_id=producto.id,
                type=tipo,
                reason=form.reason.data,
                quantity=cantidad,
                resulting_stock=producto.stock,
                user_id=current_user.id,
                timestamp=datetime.now()
            )
            
            db.session.add(nuevo_mov)
            db.session.commit()
            
            flash("Inventario actualizado correctamente", "success")
            return redirect(url_for('production.inventory_pt'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")

    return render_template('production/inventory_pt_adjustment.html', form=form, productos=productos)

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