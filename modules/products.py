import os
from flask import Blueprint, render_template, jsonify, redirect, url_for, flash, request, current_app
from models import db, Producto, ProductoPresentacionPrecio, PackagingMaterial, Raw_Material, PackagingMaterial 
from forms import FormProduct, FormPackagingMaterial
from utils.decorators import roles_accepted
from werkzeug.utils import secure_filename
from utils.functions import generar_gs1_128
from sqlalchemy.orm import joinedload

module='products'

products_bp = Blueprint(
    module, 
    __name__,
    template_folder='templates',
    static_folder='static'
    )

@products_bp.route('/')
@roles_accepted('Administrador')
def products():
    # Consultamos los productos.
    all_products = Producto.query.options(joinedload(Producto.precios)).all()
    return render_template('products/catalog.html', all_products=all_products)

@products_bp.route('/add_product', methods=['GET', 'POST'])
@roles_accepted('Administrador')
def add_product():
    form = FormProduct()

    if form.validate_on_submit():
        try:
            # 1. Crear producto base
            new_product = Producto(
                name=form.name.data,
                category=form.category.data,
                status='Activo'
            )
            db.session.add(new_product)
            db.session.flush() 

            # Generar código de barras base
            id_str = str(new_product.id).zfill(3)
            new_product.barcode = f"C750{id_str}"

            # 2. Iterar sobre las presentaciones enviadas
            for p_form in form.presentaciones:
                new_pricing = ProductoPresentacionPrecio(
                    id_producto=new_product.id,
                    presentation=p_form.presentation.data,
                    price_men=p_form.price_men.data,
                    price_may=p_form.price_may.data,
                    cant_may=p_form.cant_may.data,
                    stock=p_form.stock.data,
                    unit_size=p_form.unit_size.data,
                    unit_type=p_form.unit_type.data
                )

                if p_form.picture.data:
                    file = p_form.picture.data
                    filename = secure_filename(file.filename)
                    upload_path = os.path.join(current_app.root_path, 'static/img/products')
                    os.makedirs(upload_path, exist_ok=True)
                    file.save(os.path.join(upload_path, filename))
                    new_pricing.picture = filename
                
                db.session.add(new_pricing)

            db.session.commit()
            flash("Producto y presentaciones registradas", "success")
            return redirect(url_for('products.products'))

        except Exception as e:
            db.session.rollback()
            # Log de error detallado en consola
            print(f"DEBUG: Error de Base de Datos: {str(e)}")
            flash(f"Error de base de datos: {str(e)}", "danger")

    # --- BLOQUE DE DEPURACIÓN DE VALIDACIÓN ---
    if request.method == 'POST' and not form.validate_on_submit():
        print(f"DEBUG: Errores de validación: {form.errors}")
        for fieldName, errorMessages in form.errors.items():
            for err in errorMessages:
                # Si el error es en una presentación específica, aparecerá como diccionario
                flash(f"Error en campo {fieldName}: {err}", "warning")
    # ------------------------------------------

    return render_template('products/add.html', form=form)

@products_bp.route('/edit_product/<int:id>', methods=['GET', 'POST'])
@roles_accepted('Administrador')
def edit_product(id):
    producto = Producto.query.get_or_404(id)
    form = FormProduct(obj=producto)

    if request.method == 'GET':
        while len(form.presentaciones) > 0:
            form.presentaciones.pop_entry()
            
        for pres in producto.precios:
            form.presentaciones.append_entry({
                'presentation': pres.presentation,
                'price_men': pres.price_men,
                'price_may': pres.price_may,
                'cant_may': pres.cant_may,
                'stock': pres.stock,
                'unit_size': pres.unit_size,
                'unit_type': pres.unit_type
            })

    if form.validate_on_submit():
        try:
            # 1. Actualizar datos básicos
            producto.name = form.name.data
            producto.category = form.category.data
            producto.status = form.status.data

            # 2. Sincronizar Presentaciones sin romper FKs
            presentaciones_actuales = producto.precios # Lista de objetos BD
            nuevas_presentaciones_data = form.presentaciones.data # Lista de diccionarios del form

            # Iteramos sobre los datos enviados por el formulario
            for i, data_f in enumerate(nuevas_presentaciones_data):
                if i < len(presentaciones_actuales):
                    # ACTUALIZAR existente (mantiene el ID, no rompe packaging_materials)
                    p_db = presentaciones_actuales[i]
                    p_db.presentation = data_f['presentation']
                    p_db.price_men = data_f['price_men']
                    p_db.price_may = data_f['price_may']
                    p_db.cant_may = data_f['cant_may']
                    p_db.stock = data_f['stock']
                    p_db.unit_size = data_f['unit_size']
                    p_db.unit_type = data_f['unit_type']
                    
                    # Imagen: solo si subió una nueva
                    foto_nueva = form.presentaciones[i].picture.data
                    if foto_nueva:
                        filename = secure_filename(foto_nueva.filename)
                        upload_path = os.path.join(current_app.root_path, 'static/img/products')
                        foto_nueva.save(os.path.join(upload_path, filename))
                        p_db.picture = filename
                else:
                    # CREAR nueva si el usuario añadió filas en el JS
                    nueva_p = ProductoPresentacionPrecio(
                        id_producto=producto.id,
                        presentation=data_f['presentation'],
                        price_men=data_f['price_men'],
                        price_may=data_f['price_may'],
                        cant_may=data_f['cant_may'],
                        stock=data_f['stock'],
                        unit_size=data_f['unit_size'],
                        unit_type=data_f['unit_type']
                    )
                    
                    foto_nueva = form.presentaciones[i].picture.data
                    if foto_nueva:
                        filename = secure_filename(foto_nueva.filename)
                        upload_path = os.path.join(current_app.root_path, 'static/img/products')
                        foto_nueva.save(os.path.join(upload_path, filename))
                        nueva_p.picture = filename
                        
                    db.session.add(nueva_p)

            # 3. Eliminar las que sobran (si el usuario borró filas en el JS)
            if len(presentaciones_actuales) > len(nuevas_presentaciones_data):
                for p_extra in presentaciones_actuales[len(nuevas_presentaciones_data):]:
                    # CUIDADO: Esto solo funcionará si p_extra no tiene materiales asociados
                    # o si configuraste la relación con cascade="all, delete-orphan"
                    db.session.delete(p_extra)

            db.session.commit()
            flash("Producto actualizado correctamente", "success")
            return redirect(url_for('products.products'))

        except Exception as e:
            db.session.rollback()
            print(f"DEBUG Error: {str(e)}")
            flash(f"Error al actualizar: {str(e)}", "danger")

    return render_template('products/edit.html', form=form, producto=producto)

@products_bp.route('/delete_product/<int:id>', methods=['GET','POST'])
@roles_accepted('Administrador')
def delete_product(id):
    producto = Producto.query.get_or_404(id)
    form = FormProduct()

    if request.method == 'POST':
        try:
            producto.status = 'Inactivo' 
            db.session.commit()
            flash(f"Producto {producto.name} desactivado.", "warning")
            return redirect(url_for('products.products'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('products.products'))

    return render_template('products/delete.html', producto=producto, form=form)

from flask import jsonify, request

@products_bp.route('/search-suggestions')
def search_suggestions():
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])

    # Buscamos coincidencias
    productos = Producto.query.filter(Producto.name.ilike(f'%{query}%')).limit(5).all()
    
    results = []
    for p in productos:
        results.append({
            'nombre': p.name,
            'tipo': 'Producto',
            'url': url_for('e-commerce.catalog', q=p.name) 
        })
        
    return jsonify(results)

@products_bp.route('/generar_etiqueta/<int:prod_id>/<int:pres_id>/<string:lote>')
@roles_accepted('Administrador')
def ver_etiqueta(prod_id, pres_id, lote):
    img_b64 = generar_gs1_128(prod_id, pres_id, lote)
    return render_template('products/barcode_view.html', 
                           barcode_img=img_b64,
                           lote=lote)

# ─── PACKAGING MATERIALS (botellas/etiquetas por presentación) ───────────────

@products_bp.route('/presentacion/<int:pres_id>/packaging', methods=['GET', 'POST'])
@roles_accepted('Administrador')
def manage_packaging_materials(pres_id):
    """
    Lista y agrega los materiales de empaque asociados a una presentación.
    """
    presentacion = ProductoPresentacionPrecio.query.get_or_404(pres_id)
    materiales_mp = Raw_Material.query.filter_by(estatus='Activo').all()

    form = FormPackagingMaterial()
    form.id_material.choices = [
        (m.id, f"{m.name} ({m.nombre_unidad})") for m in materiales_mp
    ]
    
    # En GET, inicializamos el campo oculto
    if request.method == 'GET':
        form.id_presentacion.data = pres_id

    # CAMBIO: Usar validate_on_submit() para validar POST y CSRF al mismo tiempo
    if form.validate_on_submit():
        try:
            # Evitar duplicados: si ya existe esa combinación, actualizar cantidad
            existing = PackagingMaterial.query.filter_by(
                id_presentacion=pres_id,
                id_material=form.id_material.data
            ).first()

            if existing:
                existing.quantity_per_unit = form.quantity_per_unit.data
                flash("Cantidad actualizada.", "info")
            else:
                nuevo = PackagingMaterial(
                    id_presentacion=pres_id,
                    id_material=form.id_material.data,
                    quantity_per_unit=form.quantity_per_unit.data
                )
                db.session.add(nuevo)
                flash("Material de empaque agregado.", "success")

            db.session.commit()
            return redirect(url_for('products.manage_packaging_materials', pres_id=pres_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")

    # Si la validación falla (ej. CSRF inválido), los errores estarán en form.errors
    # y se mostrarán en el HTML gracias a los bloques de error que ya tienes.

    packaging_actuales = PackagingMaterial.query.filter_by(
        id_presentacion=pres_id
    ).all()

    return render_template(
        'products/packaging_materials.html',
        presentacion=presentacion,
        form=form,
        packaging_actuales=packaging_actuales
    )


@products_bp.route('/presentacion/<int:pres_id>/packaging/delete/<int:pm_id>', methods=['POST'])
@roles_accepted('Administrador')
def delete_packaging_material(pres_id, pm_id):    
    # Nota: Flask-WTF protege automáticamente las rutas POST si CSRF está habilitado globalmente.
    # Como en el HTML enviamos el <input type="hidden" name="csrf_token"...>, 
    # Flask validará que sea correcto antes de entrar aquí.
    
    pm = PackagingMaterial.query.get_or_404(pm_id)
    try:
        db.session.delete(pm)
        db.session.commit()
        flash("Material eliminado.", "warning")
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "danger")
        
    return redirect(url_for('products.manage_packaging_materials', pres_id=pres_id))