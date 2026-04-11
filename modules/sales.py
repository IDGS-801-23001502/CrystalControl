from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from models import db, Producto, ProductoPresentacionPrecio, ProductionLot, CashBox, CashRegisters, User, Role, SalePayment, Sales, SaleDetail,Producto
from decimal import Decimal
from utils.decorators import roles_accepted
from utils.functions import parse_gs1_128, sale_out
from sqlalchemy import func, extract, case
from flask_security import current_user
from datetime import datetime, timedelta, date
import uuid

module = 'sales'

sales_bp = Blueprint(
    module,
    __name__,
    template_folder='templates',
    static_folder='static'
)

@sales_bp.route("/")
@roles_accepted('Administrador','Gerente')
def sales():
    sales = Sales.query.order_by(Sales.sale_date.desc()).all()
    return render_template("sales/list.html", sales=sales)

@sales_bp.route("/view/<int:id>")
@roles_accepted('Administrador', 'Vendedor', 'Almacenista')
def view_detail(id):
    sale = Sales.query.get_or_404(id)
    
    # 1. Obtener detalles del producto
    details = db.session.query(
        SaleDetail, 
        Producto.name.label('product_name'),
        Producto.barcode.label('product_sku')
    ).join(Producto, SaleDetail.id_product == Producto.id).filter(SaleDetail.id_sale == id).all()

    # 2. Obtener el nombre del vendedor (si existe)
    vendedor_nombre = "TIENDA ONLINE"
    if sale.id_user and sale.id_user != 0:
        vendedor = User.query.get(sale.id_user)
        if vendedor:
            vendedor_nombre = vendedor.nombre # O el campo donde guardes el nombre

    payments = SalePayment.query.filter_by(id_sale=id).order_by(SalePayment.payment_date.desc()).all()

    return render_template(
        "sales/view_detail.html", 
        sale=sale, 
        details=details, 
        payments=payments,
        vendedor_nombre=vendedor_nombre # Pasamos la variable procesada
    )

@sales_bp.route("/")
@roles_accepted('Administrador','Gerente')
def utility():
    return render_template("sales/utility_report.html")


@sales_bp.route('/cajas')
@roles_accepted('Administrador', 'Gerente')
def list_cash_boxes():
    # El outerjoin es la clave para que no se filtren las cajas sin cajero
    cajas_data = db.session.query(CashBox, User).outerjoin(
        User, CashBox.id_user_cashier == User.id
    ).all()
    return render_template('sales/cash_boxes_list.html', cajas_data=cajas_data)

@sales_bp.route('/cajas/nuevo', methods=['GET', 'POST'])
@roles_accepted('Administrador', 'Gerente')
def create_cash_box():
    if request.method == 'POST':
        name = request.form.get('name')
        id_user = request.form.get('id_user_cashier')
        
        nueva_caja = CashBox(
            name=name,
            id_user_cashier=id_user if id_user else None,
            status=1
        )
        db.session.add(nueva_caja)
        db.session.commit()
        return redirect(url_for('sales.list_cash_boxes'))

    # Filtrar usuarios que tienen el rol de 'Vendedor'
    vendedores = User.query.join(Role, User.id_perfil == Role.id).filter(Role.name == 'Vendedor').all()
    return render_template('sales/cash_box_form.html', vendedores=vendedores)

@sales_bp.route('/cajas/abrir', methods=['GET', 'POST'])
@roles_accepted('Vendedor', 'Administrador','Gerente')
def open_cash_register():
    if request.method == 'POST':
        id_caja = request.form.get('id_caja')
        monto_inicial = request.form.get('open_amount')

        # 1. Validar que la caja no esté ya abierta
        corte_activo = CashRegisters.query.filter_by(id_cash_box=id_caja, status=1).first()
        if corte_activo:
            flash('Esta caja ya tiene un corte activo.', 'warning')
            return redirect(url_for('sales.open_cash_register'))

        # 2. Crear el nuevo registro de corte
        nuevo_corte = CashRegisters(
            id_cash_box=id_caja,
            open_amount=monto_inicial,
            status=1  # 1 = Abierta
            # open_date se llena solo por el server_default
        )
        
        try:
            db.session.add(nuevo_corte)
            db.session.commit()
            flash(f'Caja abierta con éxito. ¡Buen turno!', 'success')
            return redirect(url_for('sales.view_pos')) # Dirigir al punto de venta
        except Exception as e:
            db.session.rollback()
            flash('Error al abrir la caja.', 'danger')

    # Para el GET: Solo mostrar cajas activas y que NO tengan un corte abierto
    # Esto limpia la interfaz para el usuario
    subquery = db.session.query(CashRegisters.id_cash_box).filter(CashRegisters.status == 1).subquery()
    cajas_disponibles = CashBox.query.filter(
        CashBox.status == 1, 
        ~CashBox.id.in_(subquery)
    ).all()

    return render_template('sales/open_register_form.html', cajas=cajas_disponibles)

@sales_bp.route('/pos/cerrar-corte', methods=['GET', 'POST'])
@roles_accepted('Vendedor', 'Administrador')
def close_cash_register():
    # 1. Buscamos la caja que el usuario tiene asignada
    caja = CashBox.query.filter_by(id_user_cashier=current_user.id, status=1).first()
    
    if not caja:
        flash("No tienes una caja asignada para realizar el cierre.", "danger")
        return redirect(url_for('panel'))

    # 2. Buscamos el corte que esté actualmente abierto (status=1) para esa caja
    corte = CashRegisters.query.filter_by(id_cash_box=caja.id, status=1).first()

    if not corte:
        flash("No hay un corte activo para esta caja.", "warning")
        return redirect(url_for('sales.view_pos'))

    # 3. Cálculo de montos por método de pago (usando el ID del corte encontrado)
    pagos_por_metodo = db.session.query(
        SalePayment.payment_method,
        func.sum(SalePayment.paid_amount).label('total')
    ).join(Sales, Sales.id == SalePayment.id_sale)\
     .filter(Sales.id_break == corte.id)\
     .group_by(SalePayment.payment_method).all()

    totales = {p.payment_method: p.total for p in pagos_por_metodo}
    
    # El monto esperado es: Fondo Inicial + Suma de todos los pagos registrados
    monto_ventas = sum(totales.values())
    monto_esperado = corte.open_amount + monto_ventas

    if request.method == 'POST':
        try:
            monto_real = Decimal(request.form.get('real_close_amount', 0))
            
            corte.close_date = db.func.now()
            corte.expected_close_amount = monto_esperado
            corte.real_close_amount = monto_real
            corte.difference = monto_real - monto_esperado
            corte.status = 2  # Cambiamos a 'Cerrada'
            
            db.session.commit()
            flash(f"Corte #{corte.id} cerrado. Diferencia: ${corte.difference}", "success")
            return redirect(url_for('panel'))
            
        except Exception as e:
            db.session.rollback()
            flash("Error al procesar el cierre de caja.", "danger")
            print(f"Error: {e}")

    return render_template('sales/close_register_form.html', 
                           corte=corte, 
                           caja=caja,
                           totales=totales, 
                           monto_esperado=monto_esperado)

@sales_bp.route('/pos')
@roles_accepted('Administrador','Vendedor')
def view_pos():
    # 1. Buscar la caja asignada a este usuario
    caja = CashBox.query.filter_by(id_user_cashier=current_user.id, status=1).first()

    if not caja:
        flash("No tienes una caja asignada o tu caja está inactiva.", "danger")
        return redirect(url_for('panel')) # O a tu dashboard

    # 2. Verificar si hay un corte (sesión) abierto para esa caja
    corte_activo = CashRegisters.query.filter_by(id_cash_box=caja.id, status=1).first()

    if not corte_activo:
        # Si la caja está asignada pero no abierta, mandarlo a abrir caja
        flash("Debes realizar la apertura de caja antes de vender.", "warning")
        return redirect(url_for('sales.open_cash_register'))

    # 3. Datos para el POS
    return render_template('/sales/pos.html', 
                           caja=caja, 
                           vendedor=current_user, 
                           corte=corte_activo)

@sales_bp.route('/pos/procesar-venta', methods=['POST'])
@roles_accepted('Vendedor')
def procesar_venta_pos():
    data = request.get_json()
    items = data.get('items', [])
    metodo_pago_nombre = data.get('metodo_pago') # Recibimos 'Efectivo', 'Tarjeta', etc.
    
    if not items:
        return jsonify({"success": False, "message": "Carrito vacío"}), 400

    # 1. Obtener el corte activo del usuario
    caja = CashBox.query.filter_by(id_user_cashier=current_user.id, status=1).first()
    corte = CashRegisters.query.filter_by(id_cash_box=caja.id, status=1).first()

    if not corte:
        return jsonify({"success": False, "message": "No hay un corte de caja abierto"}), 400

    try:
        # 2. Crear la Cabecera de la Venta
        nueva_venta = Sales(
            folio=str(uuid.uuid4())[:8].upper(), # Generamos un folio rápido
            id_user=current_user.id,
            id_break=corte.id,
            status=3, # 3 = Pagada
            gross_total=Decimal(str(data.get('total', 0)))
        )
        db.session.add(nueva_venta)
        db.session.flush() # Para obtener el id_venta

        # 3. Registrar Detalles y actualizar Stock
        for item in items:
            # Buscamos la presentación para validar precio y utilidad
            pres = ProductoPresentacionPrecio.query.get(item['id_presentacion'])
            if not pres: continue

            detalle = SaleDetail(
                id_sale=nueva_venta.id,
                id_product=item['id_producto'],
                lot=item['cantidad'],
                unit_price_moment=pres.price_men,
                moment_utility=pres.price_men - (pres.price_men * Decimal('0.7')) # Ejemplo 30% utilidad
            )
            # Actualizar stock global del producto
            prod = Producto.query.get(item['id_producto'])
            prod.stock -= item['cantidad']
            
            db.session.add(detalle)

        # 4. Registrar el Pago
        # Mapeo de nombres a IDs de tu modelo
        map_metodos = {'Efectivo': 1, 'Tarjeta': 5, 'Transferencia': 4}
        pago = SalePayment(
            id_sale=nueva_venta.id,
            payment_method=map_metodos.get(metodo_pago_nombre, 1),
            paid_amount=nueva_venta.gross_total
        )
        db.session.add(pago)
        db.session.commit()
        sale_out(nueva_venta.id,status=1)
        return jsonify({"success": True, "folio": nueva_venta.folio})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@sales_bp.route('/api/pos/procesar_codigo/<string:barcode>')
@roles_accepted('Vendedor')
def procesar_codigo_pos(barcode_raw):
    try:
        # 1. Parsing GS1-128 (01 = GTIN, 10 = Lote)
        # Ejemplo: 010000001000000210LOT-V102
        if not barcode_raw.startswith('01'):
            return jsonify({"success": False, "message": "Código no reconocido"}), 400
        
        data = parse_gs1_128(barcode_raw)
        # Extraemos IDs (7 dígitos para producto, 7 para presentación)
        id_prod = data['producto_id']
        id_pres = data['presentacion_id']
        lote_codigo = data['lote']

        # 2. Consulta a Modelos
        # Buscamos el producto y su presentación específica
        resultado = db.session.query(
            Producto.name,
            ProductoPresentacionPrecio.presentation,
            ProductoPresentacionPrecio.price_men,
            ProductoPresentacionPrecio.price_may,
            ProductoPresentacionPrecio.id_presentacion_precio
        ).join(ProductoPresentacionPrecio, Producto.id == ProductoPresentacionPrecio.id_producto)\
         .filter(Producto.id == id_prod, ProductoPresentacionPrecio.id == id_pres)\
         .first()

        if not resultado:
            return jsonify({"success": False, "message": "Producto o presentación no existen"}), 404

        # 3. Validar existencia del Lote en Producción (Opcional pero recomendado)
        lote_info = ProductionLot.query.filter_by(lot_code=lote_codigo).first()
        
        return jsonify({
            "success": True,
            "item": {
                "id_producto": id_prod,
                "id_presentacion": resultado.id_presentacion_precio,
                "nombre": f"{resultado.name} ({resultado.presentation})",
                "precio_men": float(resultado.price_men),
                "precio_may": float(resultado.price_may),
                "lote": lote_codigo,
                "stock_lote": float(lote_info.current_stock) if lote_info else 0
            }
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    
@sales_bp.route('/reports')
@roles_accepted('Administrador', 'Gerente')
def reports():
    # ── Parámetros del filtro ─────────────────────────────────────────────────
    periodo   = request.args.get('periodo', 'mes')      # dia | semana | mes | anio
    fecha_str = request.args.get('fecha', date.today().isoformat())  # YYYY-MM-DD

    try:
        fecha_ref = date.fromisoformat(fecha_str)
    except ValueError:
        fecha_ref = date.today()

    # ── Rango según período ───────────────────────────────────────────────────
    if periodo == 'dia':
        fecha_ini = fecha_ref
        fecha_fin = fecha_ref
        label_fmt = 'Día %d/%m/%Y'
    elif periodo == 'semana':
        # Lunes de la semana que contiene fecha_ref
        fecha_ini = fecha_ref - timedelta(days=fecha_ref.weekday())
        fecha_fin = fecha_ini + timedelta(days=6)
        label_fmt = 'Semana %d/%m'
    elif periodo == 'anio':
        fecha_ini = date(fecha_ref.year, 1, 1)
        fecha_fin = date(fecha_ref.year, 12, 31)
        label_fmt = 'Año %Y'
    else:  # mes (default)
        fecha_ini = date(fecha_ref.year, fecha_ref.month, 1)
        # último día del mes
        if fecha_ref.month == 12:
            fecha_fin = date(fecha_ref.year, 12, 31)
        else:
            fecha_fin = date(fecha_ref.year, fecha_ref.month + 1, 1) - timedelta(days=1)
        label_fmt = 'Mes %m/%Y'

    dt_ini = datetime.combine(fecha_ini, datetime.min.time())
    dt_fin = datetime.combine(fecha_fin, datetime.max.time())

    # ── KPIs resumen ─────────────────────────────────────────────────────────
    ventas_periodo = Sales.query.filter(
        Sales.sale_date.between(dt_ini, dt_fin),
        Sales.status.notin_([6])          # excluir canceladas
    ).all()

    total_ingresos  = sum(float(v.gross_total or 0) for v in ventas_periodo)
    total_utilidad  = sum(float(v.profit_total or 0) for v in ventas_periodo)
    num_ventas      = len(ventas_periodo)
    ticket_promedio = (total_ingresos / num_ventas) if num_ventas else 0

    # ── Serie temporal (ventas agrupadas por día) ─────────────────────────────
    serie_raw = db.session.query(
        func.date(Sales.sale_date).label('dia'),
        func.sum(Sales.gross_total).label('ingresos'),
        func.sum(Sales.profit_total).label('utilidad'),
        func.count(Sales.id).label('num_ventas')
    ).filter(
        Sales.sale_date.between(dt_ini, dt_fin),
        Sales.status.notin_([6])
    ).group_by(func.date(Sales.sale_date))\
     .order_by(func.date(Sales.sale_date)).all()

    serie_labels   = [str(r.dia) for r in serie_raw]
    serie_ingresos = [float(r.ingresos or 0) for r in serie_raw]
    serie_utilidad = [float(r.utilidad or 0) for r in serie_raw]

    # ── Utilidad por producto (top 10) ────────────────────────────────────────
    utilidad_prod_raw = db.session.query(
        Producto.name.label('producto'),
        func.sum(SaleDetail.moment_utility * SaleDetail.lot).label('utilidad_total'),
        func.sum(SaleDetail.lot).label('unidades'),
        func.sum(SaleDetail.unit_price_moment * SaleDetail.lot).label('ingreso_total')
    ).join(SaleDetail, Producto.id == SaleDetail.id_product)\
     .join(Sales, Sales.id == SaleDetail.id_sale)\
     .filter(
        Sales.sale_date.between(dt_ini, dt_fin),
        Sales.status.notin_([6])
     ).group_by(Producto.id, Producto.name)\
      .order_by(func.sum(SaleDetail.moment_utility * SaleDetail.lot).desc())\
      .limit(10).all()

    utilidad_productos = [{
        'producto':      r.producto,
        'utilidad':      float(r.utilidad_total or 0),
        'unidades':      int(r.unidades or 0),
        'ingreso':       float(r.ingreso_total or 0),
        'margen':        round(
                            float(r.utilidad_total or 0) /
                            float(r.ingreso_total or 1) * 100, 1
                         )
    } for r in utilidad_prod_raw]

    # ── Tabla detallada de ventas ─────────────────────────────────────────────
    ventas_tabla = db.session.query(Sales, User).outerjoin(
        User, Sales.id_user == User.id
    ).filter(
        Sales.sale_date.between(dt_ini, dt_fin),
        Sales.status.notin_([6])
    ).order_by(Sales.sale_date.desc()).all()

    return render_template(
        'sales/utility_report.html',
        # Filtros activos
        periodo=periodo,
        fecha_ref=fecha_ref.isoformat(),
        fecha_ini=fecha_ini,
        fecha_fin=fecha_fin,
        # KPIs
        total_ingresos=total_ingresos,
        total_utilidad=total_utilidad,
        num_ventas=num_ventas,
        ticket_promedio=ticket_promedio,
        # Gráficas
        serie_labels=serie_labels,
        serie_ingresos=serie_ingresos,
        serie_utilidad=serie_utilidad,
        # Utilidad por producto
        utilidad_productos=utilidad_productos,
        # Tabla
        ventas_tabla=ventas_tabla,
        now=datetime.now()
    )
