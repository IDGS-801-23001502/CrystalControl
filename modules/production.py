from wtforms import form
import os
from flask import Blueprint, render_template, jsonify, redirect, url_for, flash, request, current_app
from models import db, Recipe, ProductionOrder, ProductionOrderInput, Raw_Material, User, ProductionLot, ProductionLotQuality, InventoryMovementMP, InventoryMovementPT, Producto, Sales, SaleDetail
from forms import FormProductionOrder, FormQualityCheck, FormCloseProductionOrder, FormInventoryAdjustment
from utils.decorators import roles_accepted
from flask_security import current_user
from datetime import datetime


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
    return redirect(url_for('production.index'))

@production_bp.route('/add_order', methods=['GET', 'POST'])
@roles_accepted('Administrador', 'Produccion')
def add_order():
    form = FormProductionOrder()
    
    # Llenamos los SelectField dinámicamente
    form.recipe_id.choices = [(r.id, r.final_name) for r in Recipe.query.filter_by(status=1).all()]
    form.operator_id.choices = [(u.id, u.nombre) for u in User.query.all()]

    if form.validate_on_submit(): # Aquí ya se usan los datos validados del form
        try:
            recipe = Recipe.query.get_or_404(form.recipe_id.data)
            qty_requested = float(form.requested_quantity.data)
            
            factor = qty_requested / float(recipe.produced_quantity)

            # Validación de inventario
            faltantes = []
            insumos_calculados = []
            for detail in recipe.details:
                cantidad_necesaria = float(detail.required_quantity) * factor
                material = Raw_Material.query.get(detail.material_id)
                if float(material.stock_min) < cantidad_necesaria:
                     faltantes.append(f"{material.name}")
                
                insumos_calculados.append({
                    'material_id': material.id,
                    'nombre': material.name,
                    'cantidad': cantidad_necesaria
                })

            if faltantes:
                flash(f"Insumos insuficientes: {', '.join(faltantes)}", "danger")
                return render_template('production/add.html', form=form)

            new_order = ProductionOrder(
                folio=f"OP-{datetime.now().strftime('%Y%m%d%H%M')}",
                recipe_id=recipe.id,
                requested_quantity=qty_requested,
                unit_med=form.unit_med.data,
                operator_id=form.operator_id.data,
                scheduled_date=form.scheduled_date.data,
                status=2 
            )
            db.session.add(new_order)
            db.session.flush()

            for insumo in insumos_calculados:
                db.session.add(ProductionOrderInput(
                    order_id=new_order.id,
                    material_id=insumo['material_id'],
                    material_name=insumo['nombre'],
                    used_quantity=insumo['cantidad']
                ))

            db.session.commit()
            flash(f"Orden {new_order.folio} creada", "success")
            return redirect(url_for('production.index'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")

    return render_template('production/add.html', form=form)

@production_bp.route('/close_order/<int:id>', methods=['GET', 'POST'])
@roles_accepted('Administrador', 'Produccion')
def close_order(id):
    order = ProductionOrder.query.get_or_404(id)
    form = FormCloseProductionOrder()
    
    if order.status not in [2, 3]:
        flash("Estado no válido para cerrar.", "warning")
        return redirect(url_for('production.index'))

    if form.validate_on_submit():
        try:
            # A. Actualizar orden
            order.real_waste = form.real_waste.data
            order.end_date = datetime.now()
            order.status = 4 
            
            # B. Crear Lote
            new_lot = ProductionLot(
                lot_code = f"LOT-{order.folio}-{datetime.now().strftime('%y%m%d')}",
                product_id = order.recipe.product_id,
                product_name = order.recipe.final_name,
                order_folio_ref = order.folio,
                produced_quantity = form.produced_qty.data,
                current_stock = form.produced_qty.data,
                unit_med = str(order.unit_med),
                expiry_date = form.expiry_date.data,
                warehouse_location = form.location.data,
                status = 2
            )
            db.session.add(new_lot)

            # C. Movimientos MP
            for insumo in order.inputs:
                material = Raw_Material.query.get(insumo.material_id)
                material.stock_min = float(material.stock_min) - float(insumo.used_quantity)
                db.session.add(InventoryMovementMP(
                    material_id=material.id, type=2, reason=2,
                    quantity=insumo.used_quantity, resulting_stock=material.stock_min,
                    user_id=order.operator_id
                ))

            # D. Entrada PT
            producto_final = Producto.query.get(order.recipe.product_id)
            producto_final.stock = (producto_final.stock or 0) + int(form.produced_qty.data)
            db.session.add(InventoryMovementPT(
                product_id=producto_final.id, type=1, reason=4,
                quantity=form.produced_qty.data, resulting_stock=producto_final.stock,
                user_id=order.operator_id
            ))

            db.session.commit()
            flash(f"Lote {new_lot.lot_code} generado en cuarentena", "success")
            return redirect(url_for('production.index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al cerrar: {str(e)}", "danger")

    return render_template('production/close.html', order=order, form=form)

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

    return render_template('ecommerce/catalog.html')