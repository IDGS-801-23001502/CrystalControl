from flask import Blueprint, render_template, jsonify, redirect, url_for, flash, request
from models import db, Supplier 
from forms import FormSupplier, EditFormSupplier
from flask_wtf.csrf import CSRFProtect 
from utils.decorators import roles_accepted
from flask_security import current_user
from utils.functions import register_log_auto

module='suppliers'
#level_access =  current_user.nivel_acceso(module)

suppliers_bp = Blueprint(
    module, 
    __name__,
    template_folder='templates',
    static_folder='static')

@suppliers_bp.route('/')
@roles_accepted('Administrador','Compras', 'Almacenista')
def index():
    all_suppliers = Supplier.query.all()
    return render_template('/suppliers/list.html', all_suppliers=all_suppliers)


@suppliers_bp.route('/add_supplier', methods=['GET', 'POST'])
@roles_accepted('Administrador','Compras')
def add_supplier():
    form = FormSupplier(request.form)
    
    if request.method == 'POST':
        if form.validate():
            try:
                new_supplier = Supplier()
                form.populate_obj(new_supplier)
                if not new_supplier.id: 
                 new_supplier.id = None
                
                db.session.add(new_supplier)

                db.session.flush()

                # LOG DE CREACIÓN
                register_log_auto(
                    accion="Creación",
                    modulo="Proveedores",
                    obj_puro_nuevo=new_supplier
                )

                db.session.commit()                 
                return redirect(url_for('suppliers.index'))
                
            except Exception as e:
                db.session.rollback()
                flash(f"Error al registrar: {str(e)}", "danger")
            
    return render_template('suppliers/add.html', form=form)



@suppliers_bp.route('/edit_supplier/<int:id>', methods=['GET', 'POST'])
@roles_accepted('Administrador','Compras')
def edit_supplier(id):
    supplier = Supplier.query.get_or_404(id)

    # Guardamos una copia del estado original para el log de comparación
    import copy
    supplier_original = copy.copy(supplier)

    if request.method == 'GET':
        form = EditFormSupplier(obj=supplier)
    else:
        form = EditFormSupplier(request.form)
        form.status.data = supplier.status

        if form.validate():
            try:
                form.populate_obj(supplier)

                # LOG DE ACTUALIZACIÓN
                register_log_auto(
                    accion="Actualización",
                    modulo="Proveedores",
                    obj_puro_original=supplier_original,
                    obj_puro_nuevo=supplier
                )

                db.session.commit()
                flash("Proveedor actualizado", "success")
                return redirect(url_for('suppliers.index'))
            
            except Exception as e:
                db.session.rollback()
                flash(f"Error: {e}", "danger")

    return render_template('suppliers/edit.html', form=form, supplier=supplier)


@suppliers_bp.route('/delete_supplier/<int:id>', methods=['GET', 'POST'])
@roles_accepted('Administrador','Compras')
def delete_supplier(id):
    supplier = Supplier.query.get_or_404(id)

    form = EditFormSupplier(obj=supplier) 

    if request.method == 'POST':
        try:
            # Determinamos la acción para el log antes de cambiar el dato
            accion_estatus = "Desactivación" if supplier.status == 'Activo' else "Activación"
            
            if supplier.status == 'Activo':
                supplier.status = 'Inactivo'
                mensaje = f"Proveedor {supplier.name} desactivado."
                categoria = "warning"
            else:
                supplier.status = 'Activo'
                mensaje = f"Proveedor {supplier.name} activado correctamente."
                categoria = "success"


            # LOG DE CAMBIO DE ESTATUS
            register_log_auto(
                accion=accion_estatus,
                modulo="Proveedores",
                obj_puro_nuevo=supplier
            )

            db.session.commit()
            flash(mensaje, categoria)
            return redirect(url_for('suppliers.index'))
        
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")
            
    return render_template('suppliers/delete.html', form=form, supplier=supplier)