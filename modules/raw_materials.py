from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from models import db, Raw_Material, Raw_Material_Supplier, Supplier, InventoryMovementMP as RawMaterialMovement
from forms import FormRaw_Materials, FormRaw_Materials_Supplier, FormBulkInventoryMovement
from utils.decorators import roles_accepted
from flask_security import current_user
from decimal import Decimal
from datetime import datetime
from utils.functions import register_log_auto

module = 'raw_materials'

raw_materials_bp = Blueprint(
    module, 
    __name__,
    template_folder='templates',
    static_folder='static'
)

@raw_materials_bp.route('/')
@roles_accepted('Administrador','Compras')
def index():
    raw_materials = Raw_Material.query.all()
    return render_template('/raw_materials/list.html', raw_materials=raw_materials)


@raw_materials_bp.route('/add_raw_materials', methods=['GET', 'POST'])
@roles_accepted('Administrador', 'Compras')
def add_raw_materials():
    # Instanciamos el formulario con los datos del request si es POST
    formRaw = FormRaw_Materials(request.form)

    if request.method == 'POST' and formRaw.validate():
        try:
            # Creamos la instancia del modelo
            new_raw_material = Raw_Material()
            
            # populate_obj transfiere automáticamente los datos del form al modelo
            # incluyendo el entero de unidad_medida y los Decimal de los stocks
            formRaw.populate_obj(new_raw_material)
            
            # Forzamos que el ID sea manejado por la DB si viene vacío del HiddenField
            if not formRaw.id.data:
                new_raw_material.id = None

            db.session.add(new_raw_material)
            db.session.commit()
            
            flash("Materia prima registrada exitosamente", "success")
            return redirect(url_for('raw_materials.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error al registrar en la base de datos: {str(e)}", "danger")

    return render_template('raw_materials/add.html', formRaw=formRaw)


@raw_materials_bp.route('/edit_raw_material/<int:id>', methods=['GET', 'POST'])
@roles_accepted('Administrador', 'Compras')
def edit_raw_material(id):
    # Obtenemos el objeto existente o lanzamos 404
    raw_material = Raw_Material.query.get_or_404(id)
    
    if request.method == 'GET':
        # Al cargar por GET, pasamos el objeto para que el form se llene solo
        formRaw = FormRaw_Materials(obj=raw_material)
    else:
        # Al procesar el POST, validamos los nuevos datos
        formRaw = FormRaw_Materials(request.form)
        if formRaw.validate():
            try:
                # Actualizamos los campos del objeto existente con los del form
                formRaw.populate_obj(raw_material)
                
                db.session.commit()
                flash("Materia prima actualizada correctamente", "success")
                return redirect(url_for('raw_materials.index'))
            
            except Exception as e:
                db.session.rollback()
                flash(f"Error al actualizar los cambios: {str(e)}", "danger")

    return render_template('raw_materials/edit.html', formRaw=formRaw, raw_material=raw_material)



@raw_materials_bp.route('/delete_raw_material/<int:id>', methods=['GET', 'POST'])
@roles_accepted('Administrador','Compras')
def delete_raw_material(id):
    raw_material = Raw_Material.query.get_or_404(id)
    
    formRaw = FormRaw_Materials(obj=raw_material)

    if request.method == 'POST':
        try:
            if raw_material.estatus == 'Activo':
                raw_material.estatus = 'Inactivo'
                mensaje = f"Materia prima {raw_material.name} desactivada."
                categoria = "warning"
            else:
                raw_material.estatus = 'Activo'
                mensaje = f"Materia prima {raw_material.name} activada correctamente."
                categoria = "success"

            db.session.commit()
            flash(mensaje, categoria)
            return redirect(url_for('raw_materials.index'))
        
        except Exception as e:
            db.session.rollback()
            flash(f"Error al cambiar estatus: {str(e)}", "danger")
            
    return render_template('raw_materials/delete.html', formRaw=formRaw, raw_material=raw_material)


@raw_materials_bp.route('/suppliers_material/<int:id>', methods=['GET', 'POST'])
@roles_accepted('Administrador', 'Compras')
def suppliers_material(id):
    raw_material = Raw_Material.query.get_or_404(id)
    
    form = FormRaw_Materials_Supplier(request.form)
    
    proveedores = Supplier.query.all() 
    form.id_supplier.choices = [(p.id, p.name) for p in proveedores]
    
    if request.method == 'GET':
        form.id_material.data = id

    if request.method == 'POST' and form.validate():
        try:
            new_association = Raw_Material_Supplier(
                id_material = id, 
                id_supplier = form.id_supplier.data,
                price = form.price.data,
                lot = form.lot.data,
                unidad_medida = form.unidad_medida.data
            )
            
            db.session.add(new_association)
            db.session.commit()
            flash(f"Proveedor asignado correctamente a {raw_material.name}", "success")
            
            return redirect(url_for('raw_materials.suppliers_material', id=id))

        except Exception as e:
            db.session.rollback()
            flash(f"Error al asociar proveedor: El proveedor ya podría estar asignado.", "danger")
    current_suppliers = Raw_Material_Supplier.query.filter_by(id_material=id).all()

    return render_template(
        'raw_materials/material_suppliers.html', 
        form=form, 
        raw_material=raw_material,
        current_suppliers=current_suppliers
    )

@raw_materials_bp.route('/inventory')
@roles_accepted('Administrador', 'Almacenista', 'Compras', 'Produccion') 
def inventory_status():
    # Solo traemos las activas para el control de inventario actual
    raw_materials = Raw_Material.query.filter_by(estatus='Activo').all()
    return render_template('inventory/material_list.html', raw_materials=raw_materials)


@raw_materials_bp.route('/add_bulk_movement', methods=['GET', 'POST'])
@roles_accepted('Administrador', 'Compras', 'Produccion', 'Almacenista')
def add_bulk_movement():
    form = FormBulkInventoryMovement(request.form)
    materials_list = Raw_Material.query.filter_by(estatus='Activo').all()
    material_choices = [(m.id, m.name) for m in materials_list]

    # Carga inicial de opciones
    for entry in form.movements:
        entry.material_id.choices = material_choices

    if request.method == 'POST' and form.validate():
        try:
            movimientos_a_procesar = []
            materiales_seleccionados = set()
            
            # --- FASE 1: VALIDACIÓN ---
            for entry in form.movements.data:
                mid = entry['material_id']
                
                # Validación de duplicados
                if mid in materiales_seleccionados:
                    flash("No puedes seleccionar la misma materia prima más de una vez en el mismo ajuste.", "danger")
                    db.session.rollback()
                    for e in form.movements: e.material_id.choices = material_choices
                    return render_template('inventory/material_movement.html', form=form)
                
                materiales_seleccionados.add(mid)
                material = Raw_Material.query.get(mid)
                qty = Decimal(str(entry['quantity']))
                m_type = entry['movement_type']

                # Validación de topes (stock_max)
                if m_type == 1: # Entrada
                    if (material.available_stock + qty) > material.stock_max:
                        espacio = material.stock_max - material.available_stock
                        flash(f"Límite excedido en {material.name}: Máximo {material.stock_max}. Disponible: {espacio}.", "danger")
                        db.session.rollback()
                        for e in form.movements: e.material_id.choices = material_choices
                        return render_template('inventory/material_movement.html', form=form)
                
                elif m_type == 2: # Salida
                    if qty > material.available_stock:
                        flash(f"No hay suficiente stock de '{material.name}'. "
              f"Intentaste retirar {qty}, pero solo hay {material.available_stock} disponible.", "danger")
                        db.session.rollback()
                        for e in form.movements: e.material_id.choices = material_choices
                        return render_template('inventory/material_movement.html', form=form)
                
                movimientos_a_procesar.append((material, qty, m_type, entry))

            # --- FASE 2: APLICACIÓN ---
            for material, qty, m_type, entry_data in movimientos_a_procesar:
                new_move = RawMaterialMovement(
                    material_id=material.id,
                    movement_type=m_type,
                    reason=entry_data['reason'],
                    quantity=qty,
                    status=1,
                    user_id=current_user.id,
                    pending_quantity=0
                )
                
                if m_type == 1:
                    material.real_stock += qty
                    material.available_stock += qty
                else:
                    material.real_stock -= qty
                    material.available_stock -= qty
                
                db.session.add(new_move)

                register_log_auto(
                    accion="Actualización", 
                    modulo="Inventario Materia Prima", 
                    obj_puro_nuevo=material 
                )

            db.session.commit()
            flash("Ajustes aplicados correctamente.", "success")
            return redirect(url_for('raw_materials.inventory_status'))

        except Exception as e:
            db.session.rollback()
            for e_form in form.movements: e_form.material_id.choices = material_choices
            flash(f"Error de sistema: {str(e)}", "danger")

    return render_template('inventory/material_movement.html', form=form)


#FUNCION QUE USARA NOE PARA APARTAR MATERIA PRIMA

def registrar_apartado_material(material_id, cantidad):
    
    # 1. Obtener la materia prima
    material = Raw_Material.query.get(material_id)
    if not material:
        return False, f"ID {material_id} no encontrado.", None

    try:
        cantidad_dec = Decimal(str(cantidad))

        # 2. Validación de disponibilidad 
        if cantidad_dec > material.available_stock:
            return False, f"Stock insuficiente para {material.name} (Disponible: {material.available_stock})", None

        # 3. Crear el registro de movimiento
        nuevo_movimiento = RawMaterialMovement(
            material_id=material.id,
            movement_type=2, # Salida
            reason=2,        # Consumo
            quantity=cantidad_dec,
            pending_quantity=cantidad_dec, # Se mantiene para rastrear el consumo real después
            status=2,       #Pendiente/Apartado
            user_id=current_user.id
        )

        # 4. Actualizar Stock Disponible solo se resta del disponible para "bloquear"esa cantidad
        material.available_stock -= cantidad_dec

        db.session.add(nuevo_movimiento)
        
        db.session.flush() 
        
        return True, "Apartado preparado.", nuevo_movimiento

    except Exception as e:
        return False, f"Error en {material.name}: {str(e)}", None
    


    #RUTA MUY GENERAL PARA SALIDA POR CONSUMO
@raw_materials_bp.route('/confirm_consumption', methods=['POST'])
@roles_accepted('Administrador', 'Produccion', 'Almacenista')
def confirm_consumption():
    # Quiero pensar que en el formulario vendrán los IDs de los movimientos que estaban en estatus 2 (Apartados)
    movement_ids = request.form.getlist('movement_ids[]')
    
    if not movement_ids:
        flash("No se seleccionaron materiales para consumir.", "warning")
        return redirect(url_for('raw_materials.pending_requests')) # O vista de pendientes

    try:
        for m_id in movement_ids:
            # 1. Buscar el movimiento de apartado
            movement = RawMaterialMovement.query.get(m_id)
            
            # 2. Solo procesar si existe y está como 'Apartado' (Status 2)
            if not movement or movement.status != 2:
                continue

            # 3. CAPTURAR la cantidad que realmente se consumió 
            # (Por si pidieron 10kg pero solo usaron 8kg hoy)
            consumed_qty = Decimal(request.form.get(f'consume_qty_{m_id}', '0'))
            
            if consumed_qty <= 0:
                continue

            # 4. ACTUALIZACIÓN CRÍTICA: Restar del STOCK REAL
            # El disponible ya se restó cuando se hizo el apartado.
            material = movement.material
            material.real_stock -= consumed_qty
            
            # 5. Actualizar el movimiento
            # Si consumió todo lo apartado:
            if consumed_qty >= movement.pending_quantity:
                movement.status = 1  # Completado
                movement.pending_quantity = 0
            else:
                # Si fue un consumo parcial de lo apartado:
                movement.pending_quantity -= consumed_qty
                # El status se queda en 2 porque aún "debe" material el almacén
            
            # 6. Registrar la fecha real de salida
            movement.timestamp = datetime.utcnow()

        db.session.commit()
        flash("Consumo de materia prima registrado en Stock Real.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error al procesar consumo: {str(e)}", "danger")

    return redirect(url_for('raw_materials.inventory_status'))