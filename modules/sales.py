from flask import Blueprint, render_template, jsonify, request
from models import db, Producto, ProductoPresentacionPrecio
from decimal import Decimal

module = 'sales'

sales_bp = Blueprint(
    module,
    __name__,
    template_folder='templates',
    static_folder='static'
)


@sales_bp.route('/pos')
def view_pos():
    return render_template('/sales/pos.html')

@sales_bp.route('/calculate_pos', methods=['POST'])
def calculate_pos():
    """
    Hagan de cuenta que se recibe una lista de los productos seleccionados y devuelve los cálculos
    se supone que esto es lo esperado:
    {
        "items": [
            {"barcode": "123456", "id_presentacion": 1, "cantidad": 2},
            {"barcode": "789012", "id_presentacion": 3, "cantidad": 1}
        ]
    }
    """
    data = request.get_json()
    if not data or 'items' not in data:
        return jsonify({"error": "No se enviaron productos"}), 400

    results = []
    grand_total = Decimal('0.00')

    for item in data['items']:
        barcode = item.get('barcode')
        id_presentacion = item.get('id_presentacion')
        cantidad = int(item.get('cantidad', 1))

        # Aquiiiiii se busca el producto por código de barras
        producto = Producto.query.filter_by(barcode=barcode, status='Activo').first()
        
        if not producto:
            continue # se retorna un error si un código no existe

        # 2. Aqui busca la presentación específica para obtener el precio
        # Si no mandan id_presentacion, intentamos agarrar la primera disponible
        query_presentacion = ProductoPresentacionPrecio.query.filter_by(id_producto=producto.id)
        
        if id_presentacion:
            presentacion = query_presentacion.filter_by(id=id_presentacion).first()
        else:
            presentacion = query_presentacion.first()

        if not presentacion:
            continue

        # 3. Realizar Cálculos
        # se usa precio menudeo por defecto, aun no se como manejaran lo de mayoreo o soy de ventas y asi
        precio_unitario = presentacion.price_men
        subtotal_item = precio_unitario * cantidad

        # 4. Acumular al Graaaaan Total
        grand_total += subtotal_item

        # 5. Estructurar respuesta del renglón (como un ticket)
        results.append({
            "id_producto": producto.id,
            "nombre": producto.name,
            "presentacion": presentacion.presentation,
            "cantidad": cantidad,
            "precio_unitario": float(precio_unitario),
            "subtotal": float(subtotal_item)
        })

    return jsonify({
        "detalle_calculado": results,
        "total_a_pagar": float(grand_total),
        "conteo_productos": len(results)
    }), 200