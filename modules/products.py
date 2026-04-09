import os
from flask import Blueprint, render_template, jsonify, redirect, url_for, flash, request, current_app
from models import db, Producto, ProductoPresentacionPrecio 
from forms import FormProduct
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
    precios = ProductoPresentacionPrecio.query.filter_by(id_producto=id).first()
    
    if request.method == 'POST':
        form = FormProduct(request.form)
    else:
        form = FormProduct(obj=producto)
        form.status.data = producto.status
        if precios:
            form.price_men.data = precios.price_men
            form.price_may.data = precios.price_may
            form.presentation.data = precios.presentation
            form.cant_may.data = precios.cant_may
            form.unit_size.data = precios.unit_size
            form.unit_type.data = precios.unit_type

    if form.validate_on_submit():
        try:
            # Actualizar datos de la tabla Producto
            producto.status = form.status.data
            producto.name = form.name.data
            producto.category = form.category.data

            #Actualizar datos de la tabla Precios
            if precios:
                precios.price_men = form.price_men.data
                precios.price_may = form.price_may.data
                precios.presentation = form.presentation.data
                precios.cant_may = form.cant_may.data
                precios.unit_size = form.unit_size.data
                precios.unit_type = form.unit_type.data

                # Lógica de imagen (se activa solo si hay un archivo nuevo)
            if form.picture.data:
                file = form.picture.data
                if file and file.filename != '':
                    filename = secure_filename(file.filename)
                    upload_path = os.path.join(current_app.root_path, 'static/img/products')
                    os.makedirs(upload_path, exist_ok=True)
                    file.save(os.path.join(upload_path, filename))
                    precios.picture = filename

            else:
                nuevos_precios = ProductoPresentacionPrecio(
                    id_producto=id,
                    price_men=form.price_men.data,
                    price_may=form.price_may.data,
                    presentation=form.presentation.data,
                    cant_may=form.cant_may.data,
                    unit_size=form.unit_size.data,
                    unit_type=form.unit_type.data
                )
                db.session.add(nuevos_precios)
            
            db.session.commit()
            flash("Cambios guardados correctamente", "success")
            return redirect(url_for('products.products'))
            
        except Exception as e:
            db.session.rollback()
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