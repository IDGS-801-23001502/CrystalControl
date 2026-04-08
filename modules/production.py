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
            qty_requested = float(form.requested_quantity.data)
            
            # ─────────────────────────────────────────────
            # FACTOR: cuántos "lotes base" se van a producir
            # Ej: receta base = 10kg, qty_requested = 30kg → factor = 3
            # ─────────────────────────────────────────────
            factor = qty_requested / float(recipe.produced_quantity or 1)

            # ═══════════════════════════════════════════════════════
            # 1. VALIDACIÓN DE STOCK Y PREPARACIÓN DE INSUMOS
            # ═══════════════════════════════════════════════════════
            insumos_a_registrar = []
            errores_stock = []  # Recolectamos TODOS los errores antes de retornar

            for detail in recipe.details:
                cantidad_necesaria = float(detail.required_quantity) * factor
                material = detail.material

                # ✅ CORREGIDO: Usamos available_stock del modelo directamente
                # (más confiable que buscar el último movimiento)
                stock_disponible = float(material.available_stock or 0)

                if stock_disponible < cantidad_necesaria:
                    faltante = round(cantidad_necesaria - stock_disponible, 2)
                    errores_stock.append(
                        f"❌ {material.name}: necesitas {cantidad_necesaria} {material.nombre_unidad}, "
                        f"disponible: {stock_disponible}, falta: {faltante}"
                    )
                    continue  # Seguimos revisando los demás para mostrar todos los errores

                # Costo de referencia del proveedor
                costo_prov = db.session.query(Raw_Material_Supplier.price).filter_by(
                    id_material=detail.material_id
                ).order_by(Raw_Material_Supplier.price.asc()).first()  # El más barato como referencia
                precio_u = float(costo_prov[0]) if costo_prov else 0.0

                insumos_a_registrar.append({
                    'id': detail.material_id,
                    'name': material.name,
                    'qty': cantidad_necesaria,
                    'cost': precio_u * cantidad_necesaria,
                    'material_obj': material  # Guardamos referencia para actualizar stock
                })

            # Si hay errores de stock, mostramos TODOS y detenemos
            if errores_stock:
                for error in errores_stock:
                    flash(error, "warning")
                return render_template('production/add.html', form=form)

            # ═══════════════════════════════════════════════════════
            # 2. CÁLCULO DE PIEZAS ESTIMADAS POR PRESENTACIÓN
            # Requiere el campo unit_size en ProductoPresentacionPrecio
            # ═══════════════════════════════════════════════════════
            piezas_estimadas = []

            if recipe.product_id:
                producto = Producto.query.get(recipe.product_id)
                if producto and producto.precios:
                    # qty_requested está en la unidad base de la receta (ej: litros o kg)
                    # Convertimos a ml o g según corresponda para comparar con unit_size
                    # unit_med: 1=Kilos→gramos, 2=Litros→ml, 3=Piezas
                    
                    factor_conversion = {1: 1000, 2: 1000, 3: 1}  # kg→g, L→ml, piezas→piezas
                    multiplicador = factor_conversion.get(recipe.unit_med, 1)
                    cantidad_base_total = qty_requested * multiplicador  # Ej: 10L → 10,000 ml

                    for presentacion in producto.precios:
                        unit_size = float(presentacion.unit_size or 0)
                        if unit_size > 0:
                            piezas = int(cantidad_base_total // unit_size)
                            piezas_estimadas.append({
                                'presentacion': presentacion.presentation,
                                'piezas': piezas,
                                'unit_size': unit_size
                            })

            # ═══════════════════════════════════════════════════════
            # 3. CREACIÓN DE LA ORDEN
            # ═══════════════════════════════════════════════════════
            new_order = ProductionOrder(
                folio=f"OP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                recipe_id=recipe.id,
                requested_quantity=qty_requested,
                unit_med=recipe.unit_med or 1,
                operator_id=form.operator_id.data,
                scheduled_date=form.scheduled_date.data,
                status=2  # Pendiente
            )
            db.session.add(new_order)
            db.session.flush()  # Necesario para obtener new_order.id

            # ═══════════════════════════════════════════════════════
            # 4. REGISTRO DE INSUMOS + DESCUENTO DE STOCK DISPONIBLE
            # El stock REAL se descuenta al CERRAR la orden (consumo real)
            # El stock DISPONIBLE se descuenta AHORA (reserva)
            # ═══════════════════════════════════════════════════════
            for insumo in insumos_a_registrar:
                # Snapshot del insumo en la orden
                nuevo_detalle = ProductionOrderInput(
                    order_id=new_order.id,
                    material_id=insumo['id'],
                    material_name=insumo['name'],
                    used_quantity=insumo['qty'],
                    moment_cost=insumo['cost']
                )
                db.session.add(nuevo_detalle)

                # ✅ NUEVO: Reservar stock disponible (no el real todavía)
                material = insumo['material_obj']
                material.available_stock = float(material.available_stock or 0) - insumo['qty']

                # ✅ NUEVO: Registrar movimiento MP de reserva para trazabilidad
                db.session.add(InventoryMovementMP(
                    material_id=insumo['id'],
                    movement_type=2,        # Salida
                    reason=2,               # Consumo/Reserva producción
                    quantity=insumo['qty'],
                    # El resulting_stock aquí refleja el disponible actualizado
                    resulting_stock=material.available_stock,
                    pending_quantity=0,
                    status=2,               # 2: Pendiente (se confirma al cerrar)
                    user_id=current_user.id
                ))

            db.session.commit()

            # ─────────────────────────────────────────────
            # Mensaje con resumen de la orden
            # ─────────────────────────────────────────────
            resumen_piezas = ""
            if piezas_estimadas:
                detalle = ", ".join(
                    [f"{p['piezas']} uds de {p['presentacion']}" for p in piezas_estimadas]
                )
                resumen_piezas = f" | Producción estimada: {detalle}"

            flash(
                f"✅ Orden {new_order.folio} generada. "
                f"Factor: x{round(factor, 2)}{resumen_piezas}. "
                f"Stock disponible reservado.",
                "success"
            )
            return redirect(url_for('production.production'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error al generar la orden: {str(e)}", "danger")

    return render_template('production/add.html', form=form)

@production_bp.route('/close_order/<int:id>', methods=['GET', 'POST'])
@roles_accepted('Administrador', 'Produccion')
def close_order(id):
    order = ProductionOrder.query.get_or_404(id)

    # Guardamos en guardas para evitar cerrar una orden que no está en proceso
    if order.status not in [2, 3]:
        flash("Esta orden no puede cerrarse en su estado actual.", "warning")
        return redirect(url_for('production.production'))

    form = FormCloseProductionOrder()

    # ─────────────────────────────────────────────────────────
    # Masa total de entrada = suma de todos los insumos
    # ─────────────────────────────────────────────────────────
    total_input_qty = sum(float(i.used_quantity) for i in order.inputs)

    # ═══════════════════════════════════════════════════════
    # GET: Pre-llenado automático del formulario
    # ═══════════════════════════════════════════════════════
    if request.method == 'GET':
        recipe = order.recipe

        # 1. Merma estimada desde la receta
        porcentaje_merma = float(recipe.estimated_waste or 0) / 100
        qty_esperada     = round(total_input_qty * (1 - porcentaje_merma), 2)
        merma_esperada   = round(total_input_qty - qty_esperada, 2)

        form.produced_qty.data = qty_esperada
        form.real_waste.data   = merma_esperada

        # 2. Fecha de caducidad desde días_de_vida de la receta
        #    Si el campo no existe en tu modelo aún, usa 365 como fallback
        dias_vida = int(getattr(recipe, 'days_of_life', 365) or 365)
        form.expiry_date.data = datetime.now() + timedelta(days=dias_vida)

    # ═══════════════════════════════════════════════════════
    # POST: Procesamiento del cierre
    # ═══════════════════════════════════════════════════════
    if form.validate_on_submit():
        try:
            qty_real = float(form.produced_qty.data)

            if qty_real <= 0:
                flash("La cantidad producida debe ser mayor a cero.", "warning")
                return render_template('production/close.html',
                                       order=order, form=form,
                                       total_input=total_input_qty)

            # Merma recalculada en servidor (no confiamos solo en el form)
            merma_real = round(total_input_qty - qty_real, 2)

            # ───────────────────────────────────────────────
            # 1. Cerrar la Orden de Producción
            # ───────────────────────────────────────────────
            order.real_waste = merma_real
            order.end_date   = datetime.now()
            order.status     = 4  # Completada

            # ───────────────────────────────────────────────
            # 2. Confirmar salidas de MP (ya reservadas en add_order)
            #    Cambiamos status de movimientos pendientes a Aplicado
            #    y descontamos el real_stock
            # ───────────────────────────────────────────────
            for insumo in order.inputs:
                material = insumo.material

                # Actualizar real_stock (el available ya se descontó al crear la orden)
                material.real_stock = float(material.real_stock or 0) - float(insumo.used_quantity)

                # Buscar el movimiento pendiente que se creó en add_order y confirmarlo
                mov_pendiente = InventoryMovementMP.query.filter_by(
                    material_id=insumo.material_id,
                    status=2  # Pendiente
                ).order_by(InventoryMovementMP.timestamp.desc()).first()

                if mov_pendiente:
                    # Confirmamos el movimiento existente en lugar de crear uno duplicado
                    mov_pendiente.status = 1          # Aplicado
                    mov_pendiente.resulting_stock = material.real_stock
                else:
                    # Fallback: si no existe el movimiento pendiente, lo creamos ahora
                    db.session.add(InventoryMovementMP(
                        material_id=insumo.material_id,
                        movement_type=2,              # Salida
                        reason=2,                     # Consumo producción
                        quantity=insumo.used_quantity,
                        resulting_stock=material.real_stock,
                        pending_quantity=0,
                        status=1,                     # Aplicado directamente
                        user_id=current_user.id
                    ))

            # ───────────────────────────────────────────────
            # 3. Costo unitario de producción
            # ───────────────────────────────────────────────
            total_costo = sum(float(i.moment_cost or 0) for i in order.inputs)
            costo_u     = round(total_costo / qty_real, 4) if qty_real > 0 else 0

            # ───────────────────────────────────────────────
            # 4. Crear el Lote en CUARENTENA
            #    ✅ status=2 (Cuarentena), NO tocamos stock de PT todavía
            #    El stock real se acredita cuando quality_check apruebe el lote
            # ───────────────────────────────────────────────
            new_lot = ProductionLot(
                lot_code          = f"LOT-{order.folio}-{datetime.now().strftime('%y%m%d%H%M')}",
                product_id        = order.recipe.product_id,
                product_name      = order.recipe.final_name,
                order_folio_ref   = order.folio,
                produced_quantity = qty_real,
                current_stock     = qty_real,
                unit_med          = str(order.unit_med),
                unit_cost         = costo_u,
                expiry_date       = form.expiry_date.data,
                warehouse_location= form.location.data,
                status            = 2  # Cuarentena → espera quality_check
            )
            db.session.add(new_lot)

            db.session.commit()

            flash(
                f"✅ Orden {order.folio} cerrada. "
                f"Producido: {qty_real} | Merma real: {merma_real} | "
                f"Costo unitario: ${costo_u:.4f} | "
                f"Lote {new_lot.lot_code} en cuarentena, pendiente de control de calidad.",
                "success"
            )
            return redirect(url_for('production.quality_pending'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error al cerrar la orden: {str(e)}", "danger")

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

                # ✅ AQUÍ sí entra el stock real a PT
                prod = Producto.query.get_or_404(lot.product_id)
                prod.stock = (prod.stock or 0) + float(lot.produced_quantity)

                db.session.add(InventoryMovementPT(
                    product_id=prod.id,
                    type=1,               # Entrada
                    reason=4,             # Producción
                    quantity=lot.produced_quantity,
                    resulting_stock=prod.stock,
                    user_id=current_user.id
                ))
                flash(f"Lote {lot.lot_code} aprobado. Stock actualizado.", "success")

            else:
                lot.status = 4  # Retirado

                # Registrar movimiento de merma/rechazo para trazabilidad
                prod = Producto.query.get_or_404(lot.product_id)
                db.session.add(InventoryMovementPT(
                    product_id=prod.id,
                    type=2,               # Salida
                    reason=1,             # Merma/Rechazo
                    quantity=lot.produced_quantity,
                    resulting_stock=prod.stock,  # Stock no cambia porque nunca entró
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
    
    # Calculamos el costo total acumulado de los insumos (si tienes el campo moment_cost)
    total_cost_insumos = sum([float(insumo.moment_cost or 0) for insumo in order.inputs])
    
    # Buscamos si ya existe un lote generado para esta orden
    lote = ProductionLot.query.filter_by(order_folio_ref=order.folio).first()
    
    return render_template('production/details.html', 
                           order=order, 
                           lote=lote, 
                           total_cost=total_cost_insumos)

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