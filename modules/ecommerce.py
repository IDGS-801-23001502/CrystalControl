from flask import Blueprint, render_template, request
from models import Producto, db

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
    print(f"Buscando producto con ID: {producto_id}")
    
    if not producto_id:
        return "Falta el ID del producto", 400

    producto = Producto.query.get_or_404(producto_id)
    
    return render_template("ecommerce/details_product.html", producto=producto)

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