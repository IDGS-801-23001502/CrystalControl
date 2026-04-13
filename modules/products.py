import os
from flask import Blueprint, render_template, jsonify, redirect, url_for, flash, request, current_app
from models import db, Producto, ProductoPresentacionPrecio, PackagingMaterial, Raw_Material, PackagingMaterial 
from forms import FormProduct, FormPackagingMaterial
from utils.decorators import roles_accepted
from werkzeug.utils import secure_filename
from utils.functions import generar_gs1_128

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
    all_products = Producto.query.all()
    return render_template('products/catalog.html', all_products=all_products)

@products_bp.route('/add_product', methods=['GET', 'POST'])
@roles_accepted('Administrador')
def add_product():
    form = FormProduct()

    if form.validate_on_submit():
        try:
            #Creamos la instancia de la tabla principal
            new_product = Producto(
                name=form.name.data,
                category=form.category.data,
                stock=form.stock.data,
                status='Activo'
            )

            #Guardamos primero el producto para generar el ID
            db.session.add(new_product)
            db.session.flush() # Flush envía a la base de datos sin cerrar la transacción

            #Generación automatica del código de barras
            id_str = str(new_product.id).zfill(3)
            codigo_generado = f"C750{id_str}"

            new_product.barcode = codigo_generado

            #Creamos la instancia de la tabla de precios vinculada al ID del producto
            new_pricing = ProductoPresentacionPrecio(
                id_producto=new_product.id,
                price_men=form.price_men.data,
                price_may=form.price_may.data,
                presentation=form.presentation.data,
                cant_may = form.cant_may.data,
                unit_size=form.unit_size.data,
                unit_type=form.unit_type.data
            )

            #Manejo de la Imagen
            if form.picture.data:
                file = form.picture.data
                filename = secure_filename(file.filename)
                upload_path = os.path.join(current_app.root_path, 'static/img/products')
                
                if not os.path.exists(upload_path):
                    os.makedirs(upload_path)
                
                file.save(os.path.join(upload_path, filename))
                new_pricing.picture = filename
            
            db.session.add(new_pricing)
            db.session.commit()
            
            flash("Producto y precios registrados exitosamente", "success")
            return redirect(url_for('products.products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error al registrar: {str(e)}", "danger")
            
    return render_template('products/add.html', form=form)

@products_bp.route('/edit_product/<int:id>', methods=['GET', 'POST'])
@roles_accepted('Administrador')
def edit_product(id):
    producto = Producto.query.get_or_404(id)
    precios_existentes = ProductoPresentacionPrecio.query.filter_by(id_producto=id).first()
    precios = ProductoPresentacionPrecio.query.filter_by(id_producto=id).all()
    
    # Inicializamos con el objeto producto para cargar name, category, etc.
    form = FormProduct(obj=producto)

    if request.method == 'GET':
        form.status.data = producto.status
        if precios_existentes:
            form.price_men.data = precios_existentes.price_men
            form.price_may.data = precios_existentes.price_may
            form.presentation.data = precios_existentes.presentation
            form.cant_may.data = precios_existentes.cant_may
            form.unit_size.data = precios_existentes.unit_size
            form.unit_type.data = precios_existentes.unit_type

    if form.validate_on_submit():
        try:
            # Actualizar Producto
            producto.status = form.status.data
            producto.name = form.name.data
            producto.category = form.category.data
            producto.stock = form.stock.data

            # Definir objeto de precios a actualizar
            if precios_existentes:
                target_precios = precios_existentes
            else:
                target_precios = ProductoPresentacionPrecio(id_producto=id)
                db.session.add(target_precios)

            # Actualizar campos de precios
            target_precios.price_men = form.price_men.data
            target_precios.price_may = form.price_may.data
            target_precios.presentation = form.presentation.data
            target_precios.cant_may = form.cant_may.data
            target_precios.unit_size = form.unit_size.data
            target_precios.unit_type = form.unit_type.data
            
            # Lógica de imagen (Guardar en target_precios)
            if form.picture.data:
                file = form.picture.data
                if file and file.filename != '':
                    filename = secure_filename(file.filename)
                    upload_path = os.path.join(current_app.root_path, 'static/img/products')
                    os.makedirs(upload_path, exist_ok=True)
                    file.save(os.path.join(upload_path, filename))
                    target_precios.picture = filename

            db.session.commit()
            flash("Cambios guardados correctamente", "success")
            return redirect(url_for('products.products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar: {str(e)}", "danger")

    return render_template('products/edit.html', form=form, producto=producto, precios=precios)

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