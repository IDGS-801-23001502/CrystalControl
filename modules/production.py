from wtforms import form
import os
from flask import Blueprint, render_template, jsonify, redirect, url_for, flash, request, current_app
from models import db, Recipe, ProductionOrder, ProductionOrderInput, Raw_Material, User, ProductionLot, ProductionLotQuality, InventoryMovementMP, InventoryMovementPT, Producto, Sales, SaleDetail
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
    if order.status == 2: # De Pendiente a En Proceso
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
            # Factor: Cantidad Solicitada / Cantidad Base de la Receta
            factor = qty_requested / float(recipe.produced_quantity or 1)

            # 1. VALIDACIÓN Y PREPARACIÓN DE INSUMOS
            insumos_a_registrar = []
            for detail in recipe.details:
                cantidad_necesaria = float(detail.required_quantity) * factor
                
                # Obtener stock actual
                ultimo_mov = InventoryMovementMP.query.filter_by(material_id=detail.material_id)\
                             .order_by(InventoryMovementMP.timestamp.desc()).first()
                stock_actual = float(ultimo_mov.resulting_stock) if ultimo_mov else 0.0

                if stock_actual < cantidad_necesaria:
                    flash(f"Stock insuficiente para {detail.material.name}. Falta: {cantidad_necesaria - stock_actual}", "warning")
                    return render_template('production/add.html', form=form)
                
                # Obtener costo del proveedor para Trazabilidad
                costo_prov = db.session.query(Raw_Material_Supplier.price).filter_by(
                    id_material=detail.material_id).first()
                precio_u = float(costo_prov[0]) if costo_prov else 0.0

                insumos_a_registrar.append({
                    'id': detail.material_id,
                    'name': detail.material.name,
                    'qty': cantidad_necesaria,
                    'cost': precio_u * cantidad_necesaria
                })

            # 2. CREACIÓN DE LA ORDEN
            new_order = ProductionOrder(
                folio=f"OP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                recipe_id=recipe.id,
                requested_quantity=qty_requested,
                unit_med=recipe.unit_med or 1,
                operator_id=form.operator_id.data,
                scheduled_date=form.scheduled_date.data,
                status=2
            )
            db.session.add(new_order)
            db.session.flush()

            # 3. REGISTRO DE DETALLE DE INSUMOS (Snapshot de costo y cantidad)
            for insumo in insumos_a_registrar:
                nuevo_detalle = ProductionOrderInput(
                    order_id=new_order.id,
                    material_id=insumo['id'],
                    material_name=insumo['name'],
                    used_quantity=insumo['qty'],
                    moment_cost=insumo['cost'] # Se guarda el costo calculado
                )
                db.session.add(nuevo_detalle)

            db.session.commit()
            flash(f"Orden {new_order.folio} generada con insumos calculados.", "success")
            return redirect(url_for('production.production'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")

    return render_template('production/add.html', form=form)

@production_bp.route('/close_order/<int:id>', methods=['GET', 'POST'])
@roles_accepted('Administrador', 'Produccion')
def close_order(id):
    order = ProductionOrder.query.get_or_404(id)
    form = FormCloseProductionOrder()

    # Calculamos la masa total de entrada (suma de todos los insumos registrados)
    total_input_qty = sum([float(insumo.used_quantity) for insumo in order.inputs])

    if request.method == 'GET':
        # --- LÓGICA DE CÁLCULO BASADA EN RECETA ---
        # Obtenemos el porcentaje de merma de la receta (asumiendo que el campo se llama 'waste' o 'merma')
        # Si tu campo en el modelo Recipe se llama distinto, cámbialo aquí:
        porcentaje_merma = float(getattr(order.recipe, 'waste', 0)) / 100 
        
        # Cantidad Real Esperada = Entrada * (1 - % merma)
        qty_real_esperada = total_input_qty * (1 - porcentaje_merma)
        merma_esperada = total_input_qty - qty_real_esperada

        form.produced_qty.data = round(qty_real_esperada, 2)
        form.real_waste.data = round(merma_esperada, 2)
        
        # --- FECHA DE CADUCIDAD ---
        dias_vida = getattr(order.recipe, 'days_of_life', 200) 
        fecha = datetime.now() + timedelta(days=dias_vida)
        # IMPORTANTE: format_date para que el input HTML5 lo reconozca
        form.expiry_date.data = fecha
        
    if form.validate_on_submit():
        try:
            qty_real = float(form.produced_qty.data)
            merma_calculada = total_input_qty - qty_real # Recalculamos en el server por seguridad
            
            # 1. Actualizar Orden
            order.real_waste = merma_calculada
            order.end_date = datetime.now()
            order.status = 4
            
            # 2. Salidas de Inventario MP
            for insumo in order.inputs:
                ult_mov = InventoryMovementMP.query.filter_by(material_id=insumo.material_id)\
                          .order_by(InventoryMovementMP.timestamp.desc()).first()
                stock_p = float(ult_mov.resulting_stock) if ult_mov else 0.0
                
                db.session.add(InventoryMovementMP(
                    material_id=insumo.material_id,
                    type=2,
                    reason=2,
                    quantity=insumo.used_quantity,
                    resulting_stock=stock_p - float(insumo.used_quantity),
                    user_id=current_user.id
                ))

            # 3. Costo Unitario
            total_cost_production = sum([float(i.moment_cost or 0) for i in order.inputs])
            costo_u = total_cost_production / qty_real if qty_real > 0 else 0

            # 4. Crear Lote
            new_lot = ProductionLot(
                lot_code=f"LOT-{order.folio}-{datetime.now().strftime('%y%m%d')}",
                product_id=order.recipe.product_id,
                product_name=order.recipe.final_name,
                order_folio_ref=order.folio,
                produced_quantity=qty_real,
                current_stock=qty_real,
                unit_med=str(order.unit_med),
                unit_cost=costo_u,
                expiry_date=form.expiry_date.data,
                warehouse_location=form.location.data,
                status=2 
            )
            db.session.add(new_lot)

            # 5. Entrada PT
            prod = Producto.query.get(order.recipe.product_id)
            prod.stock = (prod.stock or 0) + qty_real
            
            db.session.add(InventoryMovementPT(
                product_id=prod.id,
                type=1,
                reason=4,
                quantity=qty_real,
                resulting_stock=prod.stock,
                user_id=current_user.id
            ))

            db.session.commit()
            flash(f"Producción cerrada. Merma: {merma_calculada}", "success")
            return redirect(url_for('production.production'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")

    return render_template('production/close.html', order=order, form=form, total_input=total_input_qty)

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
                lot.status = 1 
                flash(f"Lote {lot.lot_code} aprobado", "success")
            else:
                lot.status = 4 
                producto = Producto.query.get(lot.product_id)
                producto.stock -= lot.produced_quantity
                flash(f"Lote {lot.lot_code} rechazado y stock ajustado", "warning")

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

"""
@production_bp.route('/sale_movement', methods=['POST'])
@roles_accepted('Administrador', 'Vendedor')
def sale_movement():
    #Se recibe el ID de la venta creada
    sale_id = request.form.get('sale_id')
    venta = Sales.query.get_or_404(sale_id)
    
    try:
        #Obtener productos asociados a esa venta
        detalles = SaleDetail.query.filter_by(id_sale=venta.id).all()
        
        if not detalles:
            flash("La venta no tiene productos registrados", "warning")
            return redirect(url_for('production.inventory_pt'))

        for item in detalles:
            producto = Producto.query.get(item.id_product)
            
            if producto:
                cantidad_venta = item.lot
                
                #Actualizar el stock
                nuevo_stock = (producto.stock or 0) - cantidad_venta
                producto.stock = nuevo_stock

                #Registrar el movimiento
                nuevo_movimiento = InventoryMovementPT(
                    product_id=producto.id,
                    type=2,
                    reason=2,
                    quantity=cantidad_venta,
                    resulting_stock=nuevo_stock,
                    user_id=current_user.id,
                    timestamp=datetime.now()
                )
                
                db.session.add(nuevo_movimiento)

        db.session.commit()
        flash(f"Movimientos de inventario generados para la venta Folio: {venta.folio}", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error al procesar el movimiento: {str(e)}", "danger")

    return render_template('ecommerce/catalog.html')"""

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
    
    return render_template('production/lots_pt.html', lots=lots, search=search)