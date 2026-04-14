from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_security import current_user, login_required
from models import db, Sales, SaleDetail, SalePayment, Producto, ProductoPresentacionPrecio, Cliente, Address, FavoriteProduct,verificar_cancelaciones
from forms import AddToCartForm, AddressForm, FormEditProfile, FormChangePassword
import uuid
from utils.functions import sale_out, register_log_auto, object_to_dict
from utils.decorators import only_client
from flask_security import verify_password, hash_password

modulo = 'e-commerce'
ecommerce_bp = Blueprint(
    modulo,
    __name__,
    template_folder='templates',
    static_folder='static'
)

@ecommerce_bp.route('/')
def index():
    productos = Producto.query.filter_by(status='Activo').all()
    categorias_db = db.session.query(Producto.category).distinct().all()
    categorias = [c[0] for c in categorias_db]
    return render_template('ecommerce/index.html', productos=productos, categorias=categorias)

@ecommerce_bp.route("/catalog")
def catalog():
    categorias_unicas = db.session.query(Producto.category).distinct().all()
    lista_categorias = [c[0] for c in categorias_unicas if c[0]]
    search_query = request.args.get('q', '')
    cat_seleccionadas = request.args.getlist('cat')
    cat_index = request.args.get('category')
    if cat_index and cat_index not in cat_seleccionadas:
        cat_seleccionadas.append(cat_index)

    query = Producto.query.filter_by(status='Activo')
    if search_query:
        query = query.filter(Producto.name.ilike(f'%{search_query}%'))
    if cat_seleccionadas:
        query = query.filter(Producto.category.in_(cat_seleccionadas))
    productos = query.all()
    fav_ids = []
    if current_user.is_authenticated:
        cliente = Cliente.query.filter_by(id_usuario=current_user.id).first()
        if cliente:
            fav_ids = [f.id_product for f in FavoriteProduct.query.filter_by(id_client=cliente.id).all()]
            
    return render_template("ecommerce/catalog.html",
                           productos=productos,
                           categorias=lista_categorias,
                           search_query=search_query,
                           cat_seleccionadas=cat_seleccionadas,
                           fav_ids=fav_ids)


@ecommerce_bp.route("/producto_details")
def product_detail():
    producto_id = request.args.get("id")
    if not producto_id:
        return "Falta el ID del producto", 400
    producto = Producto.query.get_or_404(producto_id)
    form = AddToCartForm(id_product=producto.id)
    form.id_presentacion_precio.choices = [
        (p.id, f"{p.presentation} - ${p.price_men}") for p in producto.precios
    ]
    is_favorite = False
    if current_user.is_authenticated:
        cliente = Cliente.query.filter_by(id_usuario=current_user.id).first()
        if cliente:
            exists = FavoriteProduct.query.filter_by(id_client=cliente.id, id_product=producto.id).first()
            is_favorite = True if exists else False

    form = AddToCartForm(id_product=producto.id)
    form.id_presentacion_precio.choices = [
        (p.id, f"{p.presentation} - ${p.price_men}") for p in producto.precios
    ]
    return render_template("ecommerce/details_product.html", 
                           producto=producto, 
                           form=form,
                           is_favorite=is_favorite)

@ecommerce_bp.route("/carrito/add", methods=['POST'])
@only_client
def add_to_cart():
    producto_id = request.form.get('id_product')
    producto = Producto.query.get_or_404(producto_id)
    form = AddToCartForm()
    form.id_presentacion_precio.choices = [(p.id, p.presentation) for p in producto.precios]
    
    if form.validate_on_submit():
        id_pres = form.id_presentacion_precio.data
        cantidad = form.quantity.data
        
        # BUSCAMOS EL STOCK EN LA PRESENTACIÓN ESPECÍFICA
        pres_precio = ProductoPresentacionPrecio.query.get(id_pres)
        if not pres_precio:
            flash("La presentación seleccionada no es válida.", "danger")
            return redirect(url_for('e-commerce.product_detail', id=producto.id))

        if 'cart' not in session:
            session['cart'] = {}
        
        print(session['cart']) 

        cart = session['cart']
        cart_key = f"{producto.id}_{id_pres}"
        cantidad_en_carrito = cart[cart_key]['cantidad'] if cart_key in cart else 0
        
        # VALIDACIÓN: Usamos pres_precio.stock en lugar de producto.stock
        stock_disponible = pres_precio.stock if pres_precio.stock is not None else 0
        
        if (cantidad_en_carrito + cantidad) > stock_disponible:
            flash(f"No puedes agregar más. Ya tienes {cantidad_en_carrito} en el carrito y el stock de {pres_precio.presentation} es {stock_disponible}.", "danger")
            return redirect(url_for('e-commerce.product_detail', id=producto.id))
        
        if cart_key in cart:
            cart[cart_key]['cantidad'] += cantidad
        else:
            cart[cart_key] = {
                'id_producto': producto.id,
                'id_presentacion': id_pres,
                'nombre': producto.name,
                'cantidad': cantidad,
                'precio': float(pres_precio.price_men),
                'presentacion': pres_precio.presentation,
                'imagen': pres_precio.picture or 'default.png'
            }
        
        session.modified = True
        flash(f"✓ {producto.name} ({pres_precio.presentation}) agregado al carrito.", "success")
        
    for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error en {field}: {error}", "danger")
    return redirect(url_for('e-commerce.catalog'))

@ecommerce_bp.route("/carrito")
@only_client
def carrito():
    cart = session.get('cart', {})
    subtotal = sum(item['precio'] * item['cantidad'] for item in cart.values())
    iva = subtotal * 0.16
    total = subtotal + iva
    return render_template("ecommerce/carrito.html", cart=cart, subtotal=subtotal, iva=iva, total=total)

@ecommerce_bp.route("/carrito/remove/<path:cart_key>")
@only_client
def remove_from_cart(cart_key):
    cart = session.get('cart', {})
    if cart_key in cart:
        nombre = cart[cart_key].get('nombre', 'Producto')
        cart.pop(cart_key)
        session.modified = True
        flash(f"Se eliminó {nombre} del carrito.", "info")
    return redirect(url_for('e-commerce.carrito'))

@ecommerce_bp.route("/carrito/update", methods=['POST'])
@only_client
def update_cart():
    cart_key = request.form.get('cart_key')
    try:
        nueva_cantidad = int(request.form.get('cantidad', 1))
    except ValueError:
        nueva_cantidad = 1
        
    cart = session.get('cart', {})

    if cart_key in cart:
        # OBTENEMOS EL ID DE LA PRESENTACIÓN DESDE LA SESIÓN
        id_pres = cart[cart_key].get('id_presentacion')
        pres_precio = ProductoPresentacionPrecio.query.get(id_pres)

        # VALIDACIÓN: Revisamos el stock de la presentación
        if pres_precio:
            stock_disponible = pres_precio.stock if pres_precio.stock is not None else 0
            if nueva_cantidad > stock_disponible:
                flash(f'¡Stock insuficiente para {pres_precio.presentation}! Solo hay {stock_disponible} disponibles.', 'danger')
                return redirect(url_for('e-commerce.carrito'))

        if nueva_cantidad > 0:
            cart[cart_key]['cantidad'] = nueva_cantidad
        else:
            cart.pop(cart_key)
            
        session.modified = True
        
    return redirect(url_for('e-commerce.carrito'))


@ecommerce_bp.route("/checkout/direccion", methods=['GET', 'POST'])
@only_client
@login_required
def checkout_direccion():
    cart = session.get('cart', {})
    if not cart:
        flash("El carrito está vacío.", "warning")
        return redirect(url_for('e-commerce.catalog'))
    cliente = Cliente.query.filter_by(id_usuario=current_user.id).first()
    mis_direcciones = []
    if cliente:
        mis_direcciones = Address.query.filter_by(id_client=cliente.id).all()
    form_nueva = AddressForm()
    if request.method == 'POST':
        accion = request.form.get('accion')
        if accion == 'usar_existente':
            id_dir = request.form.get('id_direccion')
            if not id_dir:
                flash("Selecciona una dirección.", "danger")
                return redirect(url_for('e-commerce.checkout_direccion'))
            
            dir_obj = Address.query.get(id_dir)
            if not dir_obj or dir_obj.id_client != cliente.id:
                flash("Dirección no válida.", "danger")
                return redirect(url_for('e-commerce.checkout_direccion'))
            
            session['checkout_id_direccion'] = dir_obj.id
            session['checkout_direccion_texto'] = dir_obj.address
            return redirect(url_for('e-commerce.checkout_pago'))
        elif accion == 'nueva_direccion':
            if form_nueva.validate_on_submit():
                if not cliente:
                    cliente = Cliente(id_usuario=current_user.id, telefono=form_nueva.telefono.data or '')
                    db.session.add(cliente)
                    db.session.flush() 
                nueva_dir = Address(address=form_nueva.direccion.data, id_client=cliente.id)
                db.session.add(nueva_dir)
                db.session.commit()
                session['checkout_id_direccion'] = nueva_dir.id
                session['checkout_direccion_texto'] = nueva_dir.address
                flash("Dirección registrada correctamente.", "success")
                return redirect(url_for('e-commerce.checkout_pago'))
            else:
                flash("Revisa los datos del formulario.", "danger")
    subtotal = sum(item['precio'] * item['cantidad'] for item in cart.values())
    iva = subtotal * 0.16
    total = subtotal + iva
    return render_template("ecommerce/checkout_direccion.html", 
                           cart=cart, 
                           subtotal=subtotal,
                           iva=iva, total=total, mis_direcciones=mis_direcciones, form_nueva=form_nueva)

@ecommerce_bp.route("/checkout/pago", methods=['GET', 'POST'])
@only_client
@login_required
def checkout_pago():
    cart = session.get('cart', {})
    id_direccion = session.get('checkout_id_direccion')
    direccion_texto = session.get('checkout_direccion_texto')
    if not cart or not direccion_texto:
        flash("Faltan datos para completar la compra.", "warning")
        return redirect(url_for('e-commerce.checkout_direccion'))
    subtotal = sum(item['precio'] * item['cantidad'] for item in cart.values())
    iva = subtotal * 0.16
    total = subtotal + iva
    if request.method == 'POST':
        card_number = request.form.get('card_number', '').replace(' ', '')
        cliente = Cliente.query.filter_by(id_usuario=current_user.id).first()
        nueva_venta = Sales(
            folio=str(uuid.uuid4())[:8].upper(),
            id_user=current_user.id,
            id_client_sold=cliente.id if cliente else None,
            id_address=id_direccion,
            shipping_address_text=direccion_texto,
            gross_total=total,
            status=3 
        )
        db.session.add(nueva_venta)
        db.session.flush()
        register_log_auto('Creación', 'Ventas', obj_puro_nuevo=nueva_venta)
        for item in cart.values():
            detalle = SaleDetail(
                id_sale=nueva_venta.id,
                id_product=item['id_producto'],
                id_presentation=item['id_presentacion'],
                lot=item['cantidad'],
                unit_price_moment=item['precio'],
                moment_utility=0 
            )
            db.session.add(detalle)
        ultimos_4 = card_number[-4:] if len(card_number) >= 4 else 'N/A'
        pago = SalePayment(
            id_sale=nueva_venta.id,
            payment_method=3,
            paid_amount=total,
            payment_reference=f"**** {ultimos_4}"
        )
        db.session.add(pago)
        db.session.flush()
        register_log_auto('Creación', 'Pagos', obj_puro_nuevo=pago)
        db.session.commit()
        success_almacen, mensaje_almacen = sale_out(nueva_venta.id)
        if not success_almacen:
            print(f"ALERTA INVENTARIO: {mensaje_almacen}")

        session.pop('cart', None)
        session.pop('checkout_id_direccion', None)
        session.pop('checkout_direccion_texto', None)
        flash(f"✓ ¡Compra exitosa! Pedido #{nueva_venta.folio} confirmado.", "success")
        return redirect(url_for('e-commerce.pedidos'))
    return render_template("ecommerce/checkout_pago.html", cart=cart, 
                           subtotal=subtotal,
                           iva=iva, total=total, direccion=direccion_texto)

@ecommerce_bp.route("/pedidos/<int:id_venta>/pagar", methods=['GET', 'POST'])
@only_client
@login_required
def pagar_venta(id_venta):
    venta = Sales.query.filter_by(id=id_venta, id_user=current_user.id).first_or_404()
    if venta.status not in [1, 2]:
        flash("Este pedido ya no puede pagarse.", "warning")
        return redirect(url_for('e-commerce.pedidos'))
    if request.method == 'POST':
        card_number = request.form.get('card_number', '').replace(' ', '')
        ultimos_4 = card_number[-4:] if len(card_number) >= 4 else 'N/A'
        pago = SalePayment(
            id_sale=venta.id,
            payment_method=3,
            paid_amount=venta.gross_total,
            payment_reference=f"**** {ultimos_4}"
        )
        db.session.add(pago)
        venta.status = 3 
        db.session.commit()
        success_almacen, mensaje_almacen = sale_out(venta.id)
        if success_almacen:
            flash(f"✓ ¡Pago exitoso y stock actualizado!", "success")
        else:
            flash(f"Pago exitoso, pero hubo un detalle con el stock: {mensaje_almacen}", "info")
        return redirect(url_for('e-commerce.pedidos'))
    return render_template("ecommerce/pagar_venta.html", venta=venta)

@ecommerce_bp.route("/pedidos")
@only_client
@login_required
def pedidos():
    try:
        verificar_cancelaciones()
    except Exception:
        pass
    mis_ventas = Sales.query.filter_by(id_user=current_user.id).order_by(Sales.sale_date.desc()).all()
    filtro = request.args.get('filtro', 'todos')
    return render_template("ecommerce/pedidos.html",
                           mis_ventas=mis_ventas,
                           filtro=filtro)

@ecommerce_bp.route("/favoritos/toggle/<int:id_producto>", methods=['POST'])
@only_client
@login_required
def toggle_favorito(id_producto):
    cliente = Cliente.query.filter_by(id_usuario=current_user.id).first()
    if not cliente:
        flash("Perfil de cliente no encontrado.", "danger")
        return redirect(url_for('e-commerce.catalog'))
    fav = FavoriteProduct.query.filter_by(id_client=cliente.id, id_product=id_producto).first()

    if fav:
        db.session.delete(fav)
        flash("Eliminado de favoritos.", "info")
    else:
        nuevo_fav = FavoriteProduct(id_product=id_producto, id_client=cliente.id)
        db.session.add(nuevo_fav)
        flash("¡Agregado a tus favoritos!", "success")
    
    db.session.commit()
    return redirect(request.referrer or url_for('e-commerce.catalog'))

@ecommerce_bp.route("/favoritos")
@only_client
@login_required
def favoritos():
    cliente = Cliente.query.filter_by(id_usuario=current_user.id).first()
    mis_favs = FavoriteProduct.query.filter_by(id_client=cliente.id).all()
    return render_template("ecommerce/favoritos.html", favoritos=mis_favs)

@ecommerce_bp.route("/configuracion", methods=['GET', 'POST'])
@only_client
@login_required
def configuracion():
    cliente = Cliente.query.filter_by(id_usuario=current_user.id).first()
    if not cliente:
        cliente = Cliente(id_usuario=current_user.id)
        db.session.add(cliente)
        db.session.commit()

    form_perfil = FormEditProfile(obj=current_user)
    form_password = FormChangePassword()
    form_direccion = AddressForm()

    if request.method == 'GET':
        form_perfil.email.data = current_user.username
        form_perfil.telefono.data = cliente.telefono

    accion = request.form.get('accion')

    if request.method == 'POST':

        if accion == 'update_profile' and form_perfil.validate_on_submit():
            user_original = object_to_dict(current_user) 
            estado_anterior = object_to_dict(current_user)
            current_user.username = form_perfil.email.data 
            cliente.telefono = form_perfil.telefono.data
            register_log_auto('Actualización', 'Perfil', 
                      obj_puro_original=estado_anterior, 
                      obj_puro_nuevo=current_user)
            
            db.session.commit()

        elif accion == 'change_password' and form_password.validate_on_submit():
            if verify_password(form_password.old_password.data, current_user.password):
                user_original = object_to_dict(current_user)
                current_user.password = hash_password(form_password.new_password.data)
                
                register_log_auto('Actualización', 'Seguridad/Password', 
                                obj_puro_original=user_original, 
                                obj_puro_nuevo=current_user)
                
                db.session.commit()

        elif accion == 'add_address' and form_direccion.validate_on_submit():
            nueva_dir = Address(address=form_direccion.direccion.data, id_client=cliente.id)
            db.session.add(nueva_dir)
            db.session.flush()
            register_log_auto('Creación', 'Direcciones', obj_puro_nuevo=nueva_dir)
            db.session.commit()
            flash("✓ Dirección agregada.", "success")
            return redirect(url_for('e-commerce.configuracion'))

    mis_direcciones = Address.query.filter_by(id_client=cliente.id).all()

    return render_template("ecommerce/configuracion.html",
                           form_perfil=form_perfil,
                           form_password=form_password,
                           form_direccion=form_direccion,
                           mis_direcciones=mis_direcciones)

@ecommerce_bp.route("/configuracion/direccion/eliminar/<int:id_dir>", methods=['POST'])
@only_client
@login_required
def eliminar_direccion(id_dir):
    cliente = Cliente.query.filter_by(id_usuario=current_user.id).first()
    direccion = Address.query.get_or_404(id_dir)
    dir_eliminada = object_to_dict(direccion)

    if dir_eliminada.id_client == cliente.id:
        db.session.delete(direccion)
        register_log_auto('Eliminación', 'Direcciones', obj_puro_original=direccion)
        db.session.commit()
        flash("Dirección eliminada.", "info")
    
    return redirect(url_for('e-commerce.configuracion'))

@ecommerce_bp.route("/configuracion/desactivar", methods=['POST'])
@only_client
@login_required
def desactivar_cuenta():
    current_user.estatus = 'Inactivo'
    db.session.commit()
    
    from flask_security import logout_user
    logout_user()
    
    flash("Tu cuenta ha sido desactivada correctamente. Lamentamos verte partir.", "info")
    return redirect(url_for('e-commerce.catalog'))

@ecommerce_bp.route("/ayuda")
def ayuda():
    return render_template("ecommerce/ayuda.html")