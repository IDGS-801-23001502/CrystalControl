from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_security import current_user, login_required
from models import db, Sales, SaleDetail, SalePayment, Producto, ProductoPresentacionPrecio, Cliente, Address, verificar_cancelaciones
from forms import AddToCartForm, AddressForm
import uuid

modulo = 'e-commerce'

ecommerce_bp = Blueprint(
    modulo,
    __name__,
    template_folder='templates',
    static_folder='static'
)

@ecommerce_bp.route("/catalog")
def catalog():
    categorias_unicas = db.session.query(Producto.category).distinct().all()
    lista_categorias = [c[0] for c in categorias_unicas if c[0]]
    search_query = request.args.get('q', '')
    cat_seleccionadas = request.args.getlist('cat')
    query = Producto.query.filter_by(status='Activo')
    if search_query:
        query = query.filter(Producto.name.ilike(f'%{search_query}%'))
    if cat_seleccionadas:
        query = query.filter(Producto.category.in_(cat_seleccionadas))
    productos = query.all()
    return render_template("ecommerce/catalog.html",
                           productos=productos,
                           categorias=lista_categorias,
                           search_query=search_query,
                           cat_seleccionadas=cat_seleccionadas)


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
    return render_template("ecommerce/details_product.html", producto=producto, form=form)


@ecommerce_bp.route("/carrito/add", methods=['POST'])
def add_to_cart():
    producto_id = request.form.get('id_product')
    producto = Producto.query.get_or_404(producto_id)
    form = AddToCartForm()
    form.id_presentacion_precio.choices = [(p.id, p.presentation) for p in producto.precios]
    if form.validate_on_submit():
        id_pres = form.id_presentacion_precio.data
        cantidad = form.quantity.data
        pres_precio = ProductoPresentacionPrecio.query.get(id_pres)
        if 'cart' not in session:
            session['cart'] = {}
        cart = session['cart']
        cart_key = f"{producto.id}_{id_pres}"
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
                'imagen': producto.picture or 'default.png'
            }
        session.modified = True
        flash(f"✓ {producto.name} agregado al carrito.", "success")
    return redirect(url_for('e-commerce.catalog'))



@ecommerce_bp.route("/carrito")
def carrito():
    cart = session.get('cart', {})
    subtotal = sum(item['precio'] * item['cantidad'] for item in cart.values())
    iva = subtotal * 0.16
    total = subtotal + iva
    return render_template("ecommerce/carrito.html", cart=cart, subtotal=subtotal, iva=iva, total=total)



@ecommerce_bp.route("/carrito/remove/<path:cart_key>")
def remove_from_cart(cart_key):
    cart = session.get('cart', {})
    if cart_key in cart:
        nombre = cart[cart_key].get('nombre', 'Producto')
        cart.pop(cart_key)
        session.modified = True
        flash(f"Se eliminó {nombre} del carrito.", "info")
    return redirect(url_for('e-commerce.carrito'))



@ecommerce_bp.route("/carrito/update", methods=['POST'])
def update_cart():
    cart_key = request.form.get('cart_key')
    nueva_cantidad = int(request.form.get('cantidad', 1))
    cart = session.get('cart', {})
    if cart_key in cart:
        if nueva_cantidad > 0:
            cart[cart_key]['cantidad'] = nueva_cantidad
        else:
            cart.pop(cart_key)
        session.modified = True
    return redirect(url_for('e-commerce.carrito'))


@ecommerce_bp.route("/checkout/direccion", methods=['GET', 'POST'])
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
            if not dir_obj:
                flash("Dirección no válida.", "danger")
                return redirect(url_for('e-commerce.checkout_direccion'))
            session['checkout_direccion'] = dir_obj.address
            session.modified = True
            return redirect(url_for('e-commerce.checkout_pago'))

        elif accion == 'nueva_direccion':
            if form_nueva.validate_on_submit():
                if not cliente:
                    nueva_dir = Address(address=form_nueva.direccion.data, id_client=None)
                    db.session.add(nueva_dir)
                    db.session.flush()
                    cliente = Cliente(
                        id_usuario=current_user.id,
                        direccion_envio=nueva_dir.id,
                        telefono=form_nueva.telefono.data or ''
                    )
                    db.session.add(cliente)
                    db.session.flush()
                    nueva_dir.id_client = cliente.id
                    db.session.commit()
                else:
                    nueva_dir = Address(address=form_nueva.direccion.data, id_client=cliente.id)
                    db.session.add(nueva_dir)
                    db.session.commit()
                session['checkout_direccion'] = form_nueva.direccion.data
                session.modified = True
                flash("Dirección registrada correctamente.", "success")
                return redirect(url_for('e-commerce.checkout_pago'))
            else:
                flash("Por favor completa el formulario correctamente.", "danger")

    subtotal = sum(item['precio'] * item['cantidad'] for item in cart.values())
    iva = subtotal * 0.16
    total = subtotal + iva

    return render_template("ecommerce/checkout_direccion.html",
                           cart=cart, subtotal=subtotal, iva=iva, total=total,
                           mis_direcciones=mis_direcciones, form_nueva=form_nueva)


@ecommerce_bp.route("/checkout/pago", methods=['GET', 'POST'])
@login_required
def checkout_pago():
    cart = session.get('cart', {})
    direccion = session.get('checkout_direccion')

    if not cart:
        flash("El carrito está vacío.", "warning")
        return redirect(url_for('e-commerce.catalog'))
    if not direccion:
        flash("Necesitas ingresar una dirección de envío.", "warning")
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
            shipping_address=direccion[:50],
            gross_total=total,
            id_client_sold=cliente.id if cliente else None,
            status=3  # Pagada
        )
        db.session.add(nueva_venta)
        db.session.flush()

        for item in cart.values():
            detalle = SaleDetail(
                id_sale=nueva_venta.id,
                id_product=item['id_producto'],
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
        db.session.commit()

        session.pop('cart', None)
        session.pop('checkout_direccion', None)
        session.modified = True

        flash(f"✓ ¡Pago exitoso! Pedido #{nueva_venta.folio} confirmado.", "success")
        return redirect(url_for('e-commerce.pedidos'))

    return render_template("ecommerce/checkout_pago.html",
                           cart=cart, subtotal=subtotal, iva=iva, total=total, direccion=direccion)


@ecommerce_bp.route("/pedidos/<int:id_venta>/pagar", methods=['GET', 'POST'])
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
        venta.status = 3  # Pagada
        db.session.commit()
        flash(f"✓ ¡Pago exitoso! Pedido #{venta.folio} pagado.", "success")
        return redirect(url_for('e-commerce.pedidos'))

    return render_template("ecommerce/pagar_venta.html", venta=venta)


@ecommerce_bp.route("/pedidos")
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


@ecommerce_bp.route("/favoritos")
def favoritos():
    return render_template("ecommerce/favoritos.html")

@ecommerce_bp.route("/configuracion")
def configuracion():
    return render_template("ecommerce/configuracion.html")

@ecommerce_bp.route("/ayuda")
def ayuda():
    return render_template("ecommerce/ayuda.html")
