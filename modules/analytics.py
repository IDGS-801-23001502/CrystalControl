from flask import Blueprint, render_template, request
from models import db, Sales, Purchase, Raw_Material, ProductionOrder, Recipe, User, ProductionLot, Producto, SaleDetail, PurchaseDetail, Raw_Material_Supplier
from sqlalchemy import func
from datetime import datetime, date, timedelta
import calendar
from utils.decorators import roles_accepted

analytics_bp = Blueprint('analytics', __name__, template_folder='templates')

@analytics_bp.route('/')
@roles_accepted('Administrador', 'Gerente')
def main():
    # 1. Gestión de Fechas (Default: Mes Actual)
    today = date.today()
    # Primer día del mes
    default_start = today.replace(day=1)
    # Último día del mes
    last_day = calendar.monthrange(today.year, today.month)[1]
    default_end = today.replace(day=last_day)

    # Obtener fechas del request o usar defaults
    start_str = request.args.get('start_date')
    end_str = request.args.get('end_date')
    active_tab = request.args.get('tab', 'ventas') # Ventas por default

    start_date = datetime.strptime(start_str, '%Y-%m-%d').date() if start_str else default_start
    end_date = datetime.strptime(end_str, '%Y-%m-%d').date() if end_str else default_end

    # Diccionario para enviar datos al template
    data = {}

    # 2. Lógica por Pestañas (Solo estructura por ahora)
    if active_tab == 'ventas':
        # 1. Gráfica de Tendencia (Ventas diarias en el rango)
        # Filtramos por Sales.sale_date.between(start_date, end_date)
        ventas_tendencia = db.session.query(
            func.date(Sales.sale_date).label('fecha'),
            func.sum(Sales.gross_total).label('total')
        ).filter(
            Sales.sale_date.between(start_date, end_date),
            Sales.status.notin_([6]) # Excluimos canceladas
        ).group_by('fecha').order_by('fecha').all()

        # 2. Top Productos más vendidos (Cantidad)
        # Relacionamos SaleDetail con Producto
        top_productos = db.session.query(
            Producto.name,
            func.sum(SaleDetail.lot).label('cantidad_vendida'),
            func.sum(SaleDetail.lot * SaleDetail.unit_price_moment).label('ingreso_total')
        ).join(SaleDetail, Producto.id == SaleDetail.id_product)\
        .join(Sales, Sales.id == SaleDetail.id_sale)\
        .filter(Sales.sale_date.between(start_date, end_date))\
        .group_by(Producto.id)\
        .order_by(db.desc('cantidad_vendida'))\
        .limit(5).all()

        data['ventas_tendencia'] = ventas_tendencia
        data['top_productos'] = top_productos
        
        # 3. Kpis rápidos del periodo
        data['total_periodo'] = sum(v.total for v in ventas_tendencia)
        data['ticket_promedio'] = data['total_periodo'] / len(data['ventas_periodo']) if data.get('ventas_periodo') else 0
    elif active_tab == 'clientes':
        # 1. Ranking de Clientes (Pareto: Quién deja más dinero)
        pareto_clientes = db.session.query(
            User.username,
            func.sum(Sales.gross_total).label('total_comprado'),
            func.count(Sales.id).label('numero_pedidos')
        ).join(Sales, User.id == Sales.id_user)\
        .filter(Sales.sale_date.between(start_date, end_date),
                Sales.status.notin_([6]))\
        .group_by(User.id)\
        .order_by(db.desc('total_comprado'))\
        .limit(10).all()

        # 2. Promedio de compra por cliente (Ticket Medio por Cliente)
        # Calculamos el total global entre clientes únicos en el periodo
        stats_clientes = db.session.query(
            func.count(func.distinct(Sales.id_user)).label('clientes_activos'),
            func.avg(Sales.gross_total).label('promedio_venta')
        ).filter(Sales.sale_date.between(start_date, end_date)).first()

        data['pareto'] = pareto_clientes
        data['stats'] = stats_clientes
        data['top_comprador'] = pareto_clientes[0] if pareto_clientes else None

    elif active_tab == 'compras':
        # 1. Gasto total por categoría de Materia Prima
        # Relacionamos Compra -> Detalle -> Materia Prima
        gasto_por_categoria = db.session.query(
            Raw_Material.name,
            func.sum(PurchaseDetail.approved_quantity * PurchaseDetail.unit_price).label('total_gasto')
        ).join(PurchaseDetail, Raw_Material.id == PurchaseDetail.material_id)\
        .join(Purchase, Purchase.id == PurchaseDetail.purchase_id)\
        .filter(Purchase.status == 6, # Solo compras RECIBIDAS
                Purchase.generate_date.between(start_date, end_date))\
        .group_by(Raw_Material.id)\
        .order_by(db.desc('total_gasto'))\
        .limit(5).all()

        # 2. Estado de Órdenes de Compra (Embudo)
        # 1: Solicitud, 4: Orden Generada, 6: Recibido, 7: Cancelado
        status_compras = db.session.query(
            Purchase.status,
            func.count(Purchase.id).label('cantidad')
        ).filter(Purchase.request_date.between(start_date, end_date))\
        .group_by(Purchase.status).all()

        # 3. Materiales Críticos (Stock Real < Stock Min) - Sin filtro de fecha (es actual)
        materiales_bajo_minimo = Raw_Material.query.filter(
            Raw_Material.real_stock <= Raw_Material.stock_min,
            Raw_Material.estatus == 'Activo'
        ).all()

        data['gasto_categoria'] = gasto_por_categoria
        data['status_compras'] = {s.status: s.cantidad for s in status_compras}
        data['materiales_criticos'] = materiales_bajo_minimo
        data['total_invertido'] = sum(g.total_gasto for g in gasto_por_categoria)

    elif active_tab == 'produccion':
        # 1. Órdenes por Estado (Para gráfica de pastel o embudo)
        # Estados comunes: 1: Pendiente, 2: En Proceso, 3: Calidad, 4: Terminado
        status_counts = db.session.query(
            ProductionOrder.status, 
            func.count(ProductionOrder.id).label('total')
        ).filter(ProductionOrder.start_date.between(start_date, end_date))\
        .group_by(ProductionOrder.status).all()

        # 2. Eficiencia de Mermas por Receta
        # Comparamos lo que se esperaba perder vs lo que realmente se perdió
        mermas_analisis = db.session.query(
            Recipe.final_name,
            func.avg(Recipe.estimated_waste).label('esperado'),
            func.avg(ProductionOrder.real_waste).label('real')
        ).join(ProductionOrder, Recipe.id == ProductionOrder.recipe_id)\
        .filter(ProductionOrder.status == 4, 
                ProductionOrder.end_date.between(start_date, end_date))\
        .group_by(Recipe.id).all()

        # 3. Procesos Activos (Órdenes que NO están terminadas ni canceladas)
        procesos_activos = ProductionOrder.query.filter(
            ProductionOrder.status.in_([1, 2, 3]) 
        ).order_by(ProductionOrder.start_date.desc()).all()

        data['status_counts'] = {s.status: s.total for s in status_counts}
        data['mermas'] = mermas_analisis
        data['procesos_activos'] = procesos_activos
        data['total_ordenes'] = sum(s.total for s in status_counts)

    elif active_tab == 'inventarios':
        # 1. Valor total de Materia Prima (Existencia Real * Precio de compra)
        valor_mp = db.session.query(
            func.sum(Raw_Material.real_stock * Raw_Material_Supplier.price)
        ).join(Raw_Material_Supplier, Raw_Material.id == Raw_Material_Supplier.id_material).scalar() or 0

        # 2. Valor total de Producto Terminado (Existencia en Lotes * Costo de Receta)
        # Asumiendo que ProductionLot representa el stock de PT aprobado
        valor_pt = db.session.query(
            func.sum(ProductionLot.quantity * Recipe.production_cost)
        ).join(ProductionOrder, ProductionLot.id_order == ProductionOrder.id)\
        .join(Recipe, ProductionOrder.id_recipe == Recipe.id)\
        .filter(ProductionLot.status == 1).scalar() or 0 # 1 = En Stock

        # 3. Datos para gráfica de comparación (Categorías más valiosas)
        top_stock_mp = Raw_Material.query.order_by(Raw_Material.real_stock.desc()).limit(5).all()
        top_stock_pt = db.session.query(
            Recipe.final_name, 
            func.sum(ProductionLot.quantity).label('total')
        ).join(ProductionOrder).join(ProductionLot)\
        .filter(ProductionLot.status == 1).group_by(Recipe.id).limit(5).all()

        data['valor_mp'] = valor_mp
        data['valor_pt'] = valor_pt
        data['top_mp'] = top_stock_mp
        data['top_pt'] = top_stock_pt

    return render_template('analytics/main.html', 
                           active_tab=active_tab,
                           start_date=start_date,
                           end_date=end_date,
                           data=data)