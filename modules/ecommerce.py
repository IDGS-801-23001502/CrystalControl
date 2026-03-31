from flask import Blueprint, render_template, jsonify, request

modulo = 'e-commerce'

ecommerce_bp = Blueprint(
    modulo, 
    __name__,
    template_folder='templates',
    static_folder='static'
    )

@ecommerce_bp.route("catalog")
def catalog():
    return render_template("ecommerce/catalog.html")

@ecommerce_bp.route("producto_details")
def product_detail():
    id = request.args.get("id")
    return render_template("ecommerce/details_product.html")

@ecommerce_bp.route("/pedidos")
def pedidos():
    return render_template("ecommerce/pedidos.html")

@ecommerce_bp.route("/favoritos")
def favoritos():
    return render_template("ecommerce/favoritos.html")

@ecommerce_bp.route("/configuracion")
def configuracion():
    return render_template("ecommerce/configuracion.html")

@ecommerce_bp.route("/carrito")
def carrito():
    return render_template("ecommerce/carrito.html")

@ecommerce_bp.route("/pasarela_pago")
def pasarela_pago():
    return render_template("ecommerce/pasarela_pago.html")

@ecommerce_bp.route("/ayuda")
def ayuda():
    return render_template("ecommerce/ayuda.html")