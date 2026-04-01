from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from models import db, Raw_Material, Raw_Material_Supplier, Supplier
from forms import FormRaw_Materials, FormRaw_Materials_Supplier
from utils.decorators import roles_accepted

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


@raw_materials_bp.route('/add_raw_materials', methods=['GET','POST'])
@roles_accepted('Administrador','Compras')
def add_raw_materials():
    formRaw = FormRaw_Materials(request.form)

    if request.method == 'POST':
        if formRaw.validate():
            try:
                new_raw_material = Raw_Material()
                formRaw.populate_obj(new_raw_material)
                
                if not new_raw_material.id:
                    new_raw_material.id = None
                
                db.session.add(new_raw_material)
                db.session.commit()
                flash("Materia prima registrada exitosamente", "success")
                return redirect(url_for('raw_materials.index'))             
            except Exception as e:
                db.session.rollback()
                flash(f"Error al registrar: {str(e)}", "danger")

    return render_template('raw_materials/add.html', formRaw=formRaw)


@raw_materials_bp.route('/edit_raw_material/<int:id>', methods=['GET','POST'])
@roles_accepted('Administrador','Compras')
def edit_raw_material(id):
    raw_material = Raw_Material.query.get_or_404(id)
    
    if request.method == 'GET':
        formRaw = FormRaw_Materials(obj=raw_material)
    else:
        formRaw = FormRaw_Materials(request.form)
        if formRaw.validate():
            try:
                formRaw.populate_obj(raw_material)
                db.session.commit()
                flash("Materia prima actualizada correctamente", "success")
                return redirect(url_for('raw_materials.index'))
            
            except Exception as e:
                db.session.rollback()
                flash(f"Error al actualizar: {str(e)}", "danger")

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