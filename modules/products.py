from wtforms import form
import os
from flask import Blueprint, render_template, jsonify, redirect, url_for, flash, request, current_app
from models import db, Producto 
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
    all_products = Producto.query.all()
    return render_template('/products/catalog.html', all_products=all_products)

@products_bp.route('/add_product', methods=['GET', 'POST'])
@roles_accepted('Administrador')
def add_product():
    #Para archivos se usa request.form Y request.files
    form = FormProduct(request.form)
    if request.method == 'POST':        
        #Actualizar el formulario con los archivos recibidos
        form.picture.data = request.files.get('picture')
        
        if form.validate():
            try:
                new_product = Producto()
                
                #Copiamos los datos básicos (excepto la foto)
                #Excluimos 'picture' porque el tipo de dato no coincide (File vs String)
                form.populate_obj(new_product)
                
                #Manejo de la Imagen
                if form.picture.data:
                    file = form.picture.data
                    #Limpiamos el nombre del archivo para evitar ataques
                    filename = secure_filename(file.filename)
                    
                    #Definimos la ruta donde se guardará)
                    upload_path = os.path.join(current_app.root_path, 'static/img/products')
                        
                    #Guardamos el archivo físico en el servidor
                    file.save(os.path.join(upload_path, filename))
                    
                    #Guardamos SOLO el nombre del archivo en la base de datos
                    new_product.picture = filename
                
                #Guardar en DB
                db.session.add(new_product)
                db.session.commit()
                
                flash("Producto agregado exitosamente", "success")
                return redirect(url_for('products'))
                
            except Exception as e:
                db.session.rollback()
                flash(f"Error al registrar producto: {str(e)}", "danger")
            
    return render_template('/products/add.html', form=form)

@products_bp.route('/edit_product/<int:id>', methods=['GET', 'POST'])
@roles_accepted('Administrador')
def edit_product(id):
    #Buscamos el producto o lanzamos 404 si no existe
    producto = Producto.query.get_or_404(id)
    
    #Cargamos el form con los datos del objeto
    if request.method == 'GET':
        form = FormProduct(obj=producto)
    else:
        # Si es POST, recibimos los datos y los archivos
        form = FormProduct(request.form)
        form.picture.data = request.files.get('picture')

    if form.validate_on_submit():
        try:
            #Guardamos el nombre de la foto actual por si no se sube una nueva
            old_picture = producto.picture
            
            #Copiamos los datos del form al objeto (esto sobreescribirá campos simples)
            form.populate_obj(producto)
            
            #Lógica para la nueva imagen
            if form.picture.data:
                file = form.picture.data
                filename = secure_filename(file.filename)
                
                #Definir ruta y guardar físicamente
                upload_path = os.path.join(current_app.root_path, 'static/img/products')
                if not os.path.exists(upload_path):
                    os.makedirs(upload_path)
                
                file.save(os.path.join(upload_path, filename))
                
                # Actualizamos el nombre en la base de datos
                producto.picture = filename
            else:
                #Si no subió foto nueva, mantenemos la anterior
                producto.picture = old_picture

            db.session.commit()
            flash("Producto actualizado exitosamente", "success")
            return redirect(url_for('products.list_products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar: {str(e)}", "danger")

    return render_template('products/edit.html', form=form, producto=producto)

@products_bp.route('/delete_product/<int:id>', methods=['GET', 'POST'])
@roles_accepted('Administrador')
def delete_product(id):
    producto = Producto.query.get_or_404(id)

    form = FormProduct(obj=producto) 

    if request.method == 'POST':
        try:
            #Desactivar producto a través de su status
            producto.status = 'Inactivo' 
            db.session.commit()
            
            flash(f"Producto {producto.name} ha sido desactivado.", "warning")
            return redirect(url_for('products.list_products'))
        
        except Exception as e:
            db.session.rollback()
            flash(f"Error al desactivar: {str(e)}", "danger")
            
    return render_template('products/delete.html', form=form, producto=producto)