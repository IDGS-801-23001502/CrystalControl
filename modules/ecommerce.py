from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, Sales, SaleDetail, SalePayment, Producto, ProductoPresentacionPrecio
from forms import AddToCartForm, CheckoutForm, PaymentForm
import uuid

modulo = 'e-commerce'

ecommerce_bp = Blueprint(
    modulo, 
    __name__,
    template_folder='templates',
    static_folder='static'
    )

@ecommerce_bp.route("catalog")
def catalog():
    # 1. Obtener todas las categorías únicas para el sidebar
    categorias_unicas = db.session.query(Producto.category).distinct().all()
    lista_categorias = [c[0] for c in categorias_unicas if c[0]]

    # 2. Obtener parámetros de filtro de la URL
    search_query = request.args.get('q', '')
    cat_seleccionadas = request.args.getlist('cat') # Recibe los checkboxes marcados

    # 3. Construir la consulta principal
    query = Producto.query.filter_by(status='Activo')

    if search_query:
        query = query.filter(Producto.name.ilike(f'%{search_query}%'))

    if cat_seleccionadas:
        query = query.filter(Producto.category.in_(cat_seleccionadas))

    productos = query.all()

    return render_template("ecommerce/catalog.html", 
                           productos=productos, 
                           categorias=lista_categorias, # Enviamos las categorías reales
                           search_query=search_query,
                           cat_seleccionadas=cat_seleccionadas)

# Debe ser exactamente así, sin <id> ni nada extra
@ecommerce_bp.route("/producto_details") 
def product_detail():
    producto_id = request.args.get("id")
    if not producto_id:
        return "Falta el ID del producto", 400

    producto = Producto.query.get_or_404(producto_id)
    
    # 1. Preparamos el formulario
    form = AddToCartForm(id_product=producto.id)
    
    # 2. Llenamos las opciones del SelectField con las presentaciones del modelo
    # Formato: (id_de_la_presentacion, "Nombre (Precio)")
    form.id_presentacion_precio.choices = [
        (p.id, f"{p.presentation} - ${p.price_men}") for p in producto.precios
    ]
    
    return render_template("ecommerce/details_product.html", 
                           producto=producto, 
                           form=form)


@ecommerce_bp.route("/pedidos")
def pedidos():
    user_id = session.get('user_id')
    mis_ventas = Sales.query.filter_by(id_user=user_id).order_by(Sales.sale_date.desc()).all()
    return render_template("ecommerce/pedidos.html", mis_ventas=mis_ventas)

@ecommerce_bp.route("/favoritos")
def favoritos():
    return render_template("ecommerce/favoritos.html")

@ecommerce_bp.route("/configuracion")
def configuracion():
    return render_template("ecommerce/configuracion.html")



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
                'precio': float(pres_precio.price_men), # Usamos el de la tabla relacional
                'presentacion': pres_precio.presentation
            }
        
        session.modified = True
        flash(f"Se añadió {producto.name} ({pres_precio.presentation}) al carrito.")
        
    return redirect(url_for('e-commerce.catalog'))




@ecommerce_bp.route("/carrito")
def carrito():
    cart = session.get('cart', {})
    total_bruto = sum(item['precio'] * item['cantidad'] for item in cart.values())
    
    # Formulario para la dirección de envío (Checkout)
    form_checkout = CheckoutForm()
    
    return render_template("ecommerce/carrito.html", 
                           cart=cart, 
                           total=total_bruto, 
                           form=form_checkout)



@ecommerce_bp.route("/carrito/confirmar", methods=['POST'])
def confirmar_compra():
    form = CheckoutForm()
    cart = session.get('cart', {})
    
    if not cart:
        flash("El carrito está vacío")
        return redirect(url_for('e-commerce.catalog'))

    if form.validate_on_submit():
        # 1. Calcular totales para el modelo Sales
        total_venta = sum(item['precio'] * item['cantidad'] for item in cart.values())
        
        # 2. Crear la Venta (Status 2: Esperando Pago / Apartada)
        nueva_venta = Sales(
            folio=str(uuid.uuid4())[:8].upper(),
            id_user=session.get('user_id'),
            shipping_address=form.shipping_address.data,
            gross_total=total_venta,
            status=2 # Aparecerá en el historial como 'Esperando pago'
        )
        db.session.add(nueva_venta)
        db.session.flush() # Para obtener el id_venta

        # 3. Crear los detalles (SaleDetail)
        for item in cart.values():
            detalle = SaleDetail(
                id_sale=nueva_venta.id,
                id_product=item['id'],
                lot=item['cantidad'],
                unit_price_moment=item['precio']
            )
            db.session.add(detalle)
        
        # 4. Vaciar carrito y guardar cambios
        db.session.commit()
        session.pop('cart', None)
        
        flash("Pedido apartado. Procede al pago para enviarlo.")
        return redirect(url_for('e-commerce.pasarela_pago', id_venta=nueva_venta.id))
    print("ERRORES DEL FORMULARIO:", form.errors)
    flash("Error de seguridad (CSRF). Inténtalo de nuevo.")
    return redirect(url_for('e-commerce.carrito'))



@ecommerce_bp.route("/carrito/remove/<int:id>")
def remove_from_cart(id):
    cart = session.get('cart', {})
    if str(id) in cart:
        cart.pop(str(id))
        session.modified = True
        flash("Producto eliminado del carrito.")
    return redirect(url_for('e-commerce.carrito'))



@ecommerce_bp.route("/pasarela_pago", methods=['GET', 'POST'])
def pasarela_pago():
    id_venta = request.args.get('id_venta')
    venta = Sales.query.get_or_404(id_venta)
    form = PaymentForm(id_sale=id_venta, paid_amount=venta.gross_total)

    if form.validate_on_submit():
        # 1. Registrar el Pago
        pago = SalePayment(
            id_sale=id_venta,
            payment_method=form.payment_method.data,
            paid_amount=form.paid_amount.data,
            payment_reference=form.reference.data
        )
        db.session.add(pago)

        # 2. Actualizar Estatus de la Venta: De Pagada (3) a En camino (4)
        # Según tu regla: "una vez que se marca pagada ahora si se cambia a en camino"
        venta.status = 4 
        
        db.session.commit()
        flash("¡Pago exitoso! Tu pedido está en camino.")
        return redirect(url_for('e-commerce.pedidos'))
    return render_template("ecommerce/pasarela_pago.html", form=form, venta=venta)

@ecommerce_bp.route("/ayuda")
def ayuda():
    return render_template("ecommerce/ayuda.html")