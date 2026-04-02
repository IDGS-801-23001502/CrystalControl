from wtforms import form
import os
from flask import Blueprint, render_template, jsonify, redirect, url_for, flash, request, current_app
from models import db, Producto, ProductoPresentacionPrecio 
from forms import FormProduct
from flask_wtf.csrf import CSRFProtect 
from utils.decorators import roles_accepted
from flask_security import current_user
from werkzeug.utils import secure_filename

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
    # podremos acceder a los datos de la otra tabla en el HTML.
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
                barcode=form.barcode.data,
                stock=form.stock.data,
                status='Activo'
            )

            #Manejo de la Imagen
            if form.picture.data:
                file = form.picture.data
                filename = secure_filename(file.filename)
                upload_path = os.path.join(current_app.root_path, 'static/img/products')
                
                if not os.path.exists(upload_path):
                    os.makedirs(upload_path)
                
                file.save(os.path.join(upload_path, filename))
                new_product.picture = filename

            #Guardamos primero el producto para generar el ID
            db.session.add(new_product)
            db.session.flush() # Flush envía a la base de datos sin cerrar la transacción

            #Creamos la instancia de la tabla de precios vinculada al ID del producto
            new_pricing = ProductoPresentacionPrecio(
                id_producto=new_product.id,
                price_men=form.price_men.data,
                price_may=form.price_may.data,
                presentation=form.presentation.data
            )
            
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
    # Obtenemos el primer registro de precios asociado
    precios = ProductoPresentacionPrecio.query.filter_by(id_producto=id).first()
    
    if request.method == 'GET':
        form = FormProduct(obj=producto)
        form.status.data = producto.status
        # Llenamos manualmente los campos que pertenecen a la otra tabla
        if precios:
            form.price_men.data = precios.price_men
            form.price_may.data = precios.price_may
            form.presentation.data = precios.presentation
    else:
        form = FormProduct()

    if form.validate_on_submit():
        try:
            # Actualizar datos tabla Producto
            producto.status = form.status.data
            producto.name = form.name.data
            producto.barcode = form.barcode.data
            producto.stock = form.stock.data
            
            # Lógica de imagen
            if form.picture.data:
                file = form.picture.data
                filename = secure_filename(file.filename)
                upload_path = os.path.join(current_app.root_path, 'static/img/products')
                file.save(os.path.join(upload_path, filename))
                producto.picture = filename

            # Actualizar datos tabla Precios
            if precios:
                precios.price_men = form.price_men.data
                precios.price_may = form.price_may.data
                precios.presentation = form.presentation.data
            
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