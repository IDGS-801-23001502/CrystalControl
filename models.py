from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin
from flask_pymongo import PyMongo
from sqlalchemy.dialects.mysql import TINYINT
from datetime import datetime, timedelta
 
mongo= PyMongo()
db = SQLAlchemy()

# Tabla intermedia Perfil_Modulo (Muchos a Muchos)
perfil_modulo = db.Table('Perfil_Modulo',
    db.Column('id_perfil', db.Integer, db.ForeignKey('Perfiles.id_perfil'), primary_key=True),
    db.Column('id_modulo', db.Integer, db.ForeignKey('Modulos.id_modulo'), primary_key=True),
    db.Column('permiso_escritura', db.Integer, default=1)
)

class Role(db.Model, RoleMixin):
    __tablename__ = 'Perfiles'
    id = db.Column('id_perfil', db.Integer, primary_key=True)
    name = db.Column('nombre_perfil', db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    
    modulos = db.relationship('Modulo', secondary=perfil_modulo, backref='perfiles')

class Modulo(db.Model):
    __tablename__ = 'Modulos'
    id = db.Column('id_modulo', db.Integer, primary_key=True)
    name = db.Column('nombre_modulo', db.String(50), nullable=False)

class User(db.Model, UserMixin):
    __tablename__ = 'Usuarios'
    id = db.Column('id_usuario', db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(50),nullable=False)
    password = db.Column('password_hash', db.String(255), nullable=False)
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False)
    estatus = db.Column(db.Enum('Activo', 'Inactivo'), default='Activo')
    
    # Llave foránea al perfil
    id_perfil = db.Column(db.Integer, db.ForeignKey('Perfiles.id_perfil'))
    cliente_perfil = db.relationship('Cliente', backref='usuario', uselist=False)
    roles = db.relationship('Role', 
                           primaryjoin="User.id_perfil == Role.id",
                           viewonly=True,
                           uselist=True)
    @property
    def is_client(self):
        if not self.roles:
            return False
        return any(role.name.strip() == 'Cliente' for role in self.roles)
    
    @property
    def perfil(self):
        if self.roles and len(self.roles) > 0:
            return self.roles[0]
        return None
    
    @property
    def active(self):
        return self.estatus == 'Activo'

    def nivel_acceso(self, nombre_modulo):
        """Retorna el nivel de privilegio (1-4) para un módulo específico."""
        if not self.perfil:
            return 0
        
        # Buscamos en la relación ya cargada de módulos del perfil
        # Esto es más rápido que hacer un query manual cada vez
        for modulo in self.perfil.modulos:
            if modulo.name == nombre_modulo:
                # Necesitamos obtener el valor de la tabla intermedia
                permiso = db.session.query(perfil_modulo.c.permiso_escritura).filter(
                    perfil_modulo.c.id_perfil == self.id_perfil,
                    perfil_modulo.c.id_modulo == modulo.id
                ).scalar()
                return permiso or 1
        return 0

class Cliente(db.Model):
    __tablename__ = 'Clientes'
    id = db.Column('id_cliente', db.Integer, primary_key=True)
    # Llave foránea que apunta al Usuario
    id_usuario = db.Column(db.Integer, db.ForeignKey('Usuarios.id_usuario'), nullable=False)
    
    # Datos específicos del negocio
    direccion_envio = db.Column(db.Text)
    telefono = db.Column(db.String(20))
    
##MATERIAS PRIMAS###
class Raw_Material(db.Model):
    __tablename__='MateriaPrima'
    id= db.Column('id_materia', db.Integer,primary_key=True)
    name = db.Column('nombre',db.String(100))
    stock_min= db.Column('stock_min',db.Numeric(10,2), default='0.00')
    stock_max= db.Column('stock_max',db.Numeric(10,2))    
    unidad_medida = db.Column('unidad_medida', db.Integer, nullable=False)
    real_stock = db.Column('stock_real', db.Numeric(10,2), default='0.00')
    available_stock = db.Column('stock_disponible', db.Numeric(10,2), default='0.00') 
    @property
    def nombre_unidad(self):
        unidades = {1: 'Kilos', 2: 'Litros', 3: 'Galones', 4: 'Pieza'}
        return unidades.get(self.unidad_medida, 'Desconocido')
    
    estatus = db.Column(db.Enum('Activo', 'Inactivo'), default='Activo')
    suppliers = db.relationship('Raw_Material_Supplier', backref='materia_asociada', cascade="all, delete-orphan")

class Raw_Material_Supplier(db.Model):
    __tablename__ = 'materia_prima_proveedor'
    id_material = db.Column('id_materia', db.Integer, 
                            db.ForeignKey('MateriaPrima.id_materia'), 
                            primary_key=True, nullable=False)
    
    id_supplier = db.Column('id_proveedor', db.Integer, 
                            db.ForeignKey('Proveedores.id_proveedor'), 
                            primary_key=True, nullable=False)
    price = db.Column('precio_referencia', db.Numeric(10, 2), nullable=False)
    lot = db.Column('cantidad', db.Numeric(10, 2), nullable=False)
    # (1: Kilos, 2: Litros, etc.)
    unidad_medida = db.Column('unidad_medida', db.Integer, nullable=False)
    @property
    def nombre_unidad(self):
        unidades = {1: 'Kilos', 2: 'Litros', 3: 'Galones', 4: 'Pieza'}
        return unidades.get(self.unidad_medida, 'Desconocido')

##PROVEEDORES##
class Supplier(db.Model):
    __tablename__ = 'Proveedores'
    
    id = db.Column('id_proveedor', db.Integer, primary_key=True)
    unique_code = db.Column('num_unico_prov', db.String(20), unique=True, nullable=False)
    name = db.Column('nombre', db.String(100), nullable=False)
    address = db.Column('domicilio', db.Text)
    phone = db.Column('telefono', db.String(20))
    email = db.Column('correo', db.String(100))
    status = db.Column('estatus', db.Enum('Activo', 'Inactivo'), default='Activo')

    materials = db.relationship('Raw_Material_Supplier', backref='proveedor_asociado', cascade="all, delete-orphan")

##RECETAS##
 
class Recipe(db.Model):
    __tablename__ = 'recetas'

    id = db.Column('id_receta', db.Integer, primary_key=True)
    unique_code = db.Column('num_unico_receta', db.String(20), unique=True, nullable=False)
    final_name = db.Column('nombre_final', db.String(100), nullable=False)
    general_instructions = db.Column('instrucciones_generales', db.Text)
    estimated_time = db.Column('tiempo_total_estimado_min', db.Integer)
    expected_utility = db.Column('utilidad_esperada_porcent', db.Numeric(5, 2))
    estimated_waste = db.Column('merma_estimada_porcent', db.Numeric(5, 2))
    produced_quantity = db.Column('cantidad_producida', db.Integer)
    unit_med = db.Column('unidad_medida', TINYINT) # 1-Kilos 2-Litros 3-Piezas
    product_id = db.Column('id_producto', db.Integer, db.ForeignKey('productos.id_producto'))
    status = db.Column('estatus', db.Integer, default=1)
    version = db.Column('receta_version_anterior', db.Integer)
    details = db.relationship('RecipeDetail', backref='recipe')
    steps = db.relationship('RecipeStep', backref='recipe')
    product = db.relationship('Producto', backref='recipe')

    @property
    def nombre_unidad_lote(self):
        unidades = {1: 'Kilos', 2: 'Litros', 3: 'Galones', 4: 'Pieza'}
        return unidades.get(self.unit_med, 'Desconocido')


class RecipeDetail(db.Model):
    __tablename__ = 'receta_detalle'
    
    id = db.Column('id_receta_detalle', db.Integer, primary_key=True)
    recipe_id = db.Column('id_receta', db.Integer, db.ForeignKey('recetas.id_receta'), nullable=False)
    material_id = db.Column('id_materia', db.Integer, db.ForeignKey('MateriaPrima.id_materia'), nullable=False)
    required_quantity =  db.Column('cantidad_necesaria', db.Numeric(10, 2), nullable=False)
    # unit_med = db.Column(db.Integer) 

    material = db.relationship('Raw_Material', backref='recipe_details')

class RecipeStep(db.Model):
    __tablename__ = 'pasosreceta'
   
    id = db.Column('id_paso', db.Integer, primary_key=True)
    recipe_id = db.Column('id_receta', db.Integer, db.ForeignKey('recetas.id_receta'), nullable=False)
    step_order = db.Column('orden_paso', db.Integer, nullable=False)
    stage_name = db.Column('nombre_etapa', db.String(50), nullable=False)
    description = db.Column('descripcion_especifica', db.Text)
    estimated_time = db.Column('tiempo_estimado_paso', db.Integer, nullable=False)
    process_type = db.Column('tipo_proceso', db.Integer, nullable=False)

    @property
    def nombre_proceso(self):
        procesos = {1: 'Mezclado', 2: 'Envasado', 3: 'Reposo'}
        return procesos.get(self.process_type, 'Otro')

##PRODUCTOS##
class Producto(db.Model):
    __tablename__ = 'productos'

    id = db.Column('id_producto', db.Integer, primary_key=True, autoincrement=True)
    barcode = db.Column('codigo_barras', db.String(20))
    name = db.Column('nombre', db.String(100), nullable=False)
    category = db.Column('categoria', db.String(50), nullable=False)
    stock = db.Column('stock_disponible', db.Integer, default=0)
    picture = db.Column('foto', db.String(255), nullable=True) 
    status = db.Column('estatus', db.Enum('Activo', 'Inactivo'), default='Activo')
    #stock_real = db.Column('stock_real', db.Integer)

    precios = db.relationship('ProductoPresentacionPrecio', backref='producto', lazy=True)

class ProductoPresentacionPrecio(db.Model):
    __tablename__ = 'producto_presentación_precio'

    id = db.Column('id_presentacion_precio', db.Integer, primary_key=True)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), nullable=False)
    price_men = db.Column('precio_menudeo', db.Numeric(10, 2), nullable=False)
    price_may = db.Column('precio_mayoreo', db.Numeric(10, 2), nullable=False)
    presentation = db.Column('presentacion', db.String(50), nullable=False)
    cant_may = db.Column('cantidad_mayoreo', db.Integer, nullable = False)
    unit_size = db.Column('tamano_unidad', db.Numeric(10), nullable=True)
    unit_type = db.Column('tipo_unidad_base', db.Integer, default=1)
    picture = db.Column('img', db.String(50), nullable = True)

# Modelos de Compras
class Purchase(db.Model):
    __tablename__ = 'Compras'
    
    id = db.Column('id_compra', db.Integer, primary_key=True, autoincrement=True)
    folio = db.Column('folio_compra', db.String(20), unique=True)
    requester_id = db.Column('id_usuario_solicita', db.Integer, db.ForeignKey('Usuarios.id_usuario'), nullable=False)
    request_date = db.Column('fecha_solicitud', db.DateTime, default=datetime.utcnow)
    generate_date = db.Column('fecha_generada', db.DateTime)
    # 1: Solicitud, 2: En Análisis, 3: Comparativa, 4: Orden Generada, 5: En Tránsito, 6: Recibido, 7: Cancelado/Rechazada, 8: Entrega Incompleta
    status = db.Column('status_general', db.Integer, default=1)
    admin_notes = db.Column('observaciones_admin', db.Text)

    # Relaciones
    details = db.relationship('PurchaseDetail', backref='purchase', lazy=True, cascade="all, delete-orphan")
    # Asumo que tu clase de usuarios se llama 'User'
    requester = db.relationship('User', backref='purchase_requests')

    def __repr__(self):
        return f'<Purchase {self.folio} - Status {self.status}>'

class PurchaseDetail(db.Model):
    __tablename__ = 'Detalle_Compras'
    id = db.Column('id_detalle_compra', db.Integer, primary_key=True, autoincrement=True)
    purchase_id = db.Column('id_compra', db.Integer, db.ForeignKey('Compras.id_compra', ondelete='CASCADE'), nullable=False)
    material_id = db.Column('id_materia', db.Integer, db.ForeignKey('MateriaPrima.id_materia'), nullable=False)
    supplier_id = db.Column('id_proveedor_seleccionado', db.Integer, db.ForeignKey('Proveedores.id_proveedor'), nullable=True)
    # Campo de Unidad de Medida (1: Kilos, 2: Litros, 3: Galones, 4: Piezas)
    demand_quantity = db.Column('cantidad_solicitada', db.Numeric(10,2), nullable=False)
    approved_quantity = db.Column('cantidad_aprobada', db.Numeric(10, 2), default=0.0)
    unit_price = db.Column('precio_unitario_final', db.Numeric(10, 2), default=0.0)
    delivery_days = db.Column('dias_entrega', db.Integer)
    # 1: Pendiente, 2: Aprobado, 3: Rechazado, 4: Recibido, 5:Revibido con retraso
    status = db.Column('status_item', db.Integer, default=1)

    material = db.relationship('Raw_Material', backref='purchase_details')
    supplier = db.relationship('Supplier', backref='purchase_details')

    def __repr__(self):
        return f'<PurchaseDetail ID:{self.id} Material:{self.material_id}>'
##VENTAS##

class Sales(db.Model):
    __tablename__ = 'Ventas'
    
    id = db.Column('id_venta', db.Integer, primary_key=True, autoincrement=True, nullable=False)
    folio = db.Column('folio', db.String(20), unique=True)
    id_user = db.Column('id_usuario', db.Integer, db.ForeignKey('Usuarios.id_usuario'))
    sale_date = db.Column('fecha_venta', db.DateTime, server_default=db.func.now())
    estimated_delivery_date = db.Column('fecha_entrega_estimada', db.String(5))
    gross_total = db.Column('total_bruto', db.Numeric(10, 2))
    profit_total = db.Column('total_utilidad', db.Numeric(10, 2))
    shipping_address = db.Column('direccion_envio', db.String(50))
    id_client_sold = db.Column('id_cliente_vendido', db.Integer, db.ForeignKey('Clientes.id_cliente'))
    id_break = db.Column('id_corte', db.Integer, db.ForeignKey('cortes_cajas.id_corte'))
    tracking = db.Column('rastreo', db.String(50))

    status = db.Column('status', db.Integer) 

    @property
    def value_status(self):
        values = {1: 'Solicitada', 2: 'Esperando pago', 3: 'Pagada', 4: 'En camino', 5:'Entregada', 6:'Cancelada'}
        return values.get(self.status)

class SaleDetail(db.Model):
    __tablename__ = 'detalle_venta'
    id = db.Column('id_detalle_venta', db.Integer, primary_key=True, nullable=False)
    id_sale = db.Column('id_venta', db.Integer, db.ForeignKey('Ventas.id_venta'), primary_key=True)
    id_product = db.Column('id_producto', db.Integer, db.ForeignKey('productos.id_producto'), primary_key=True)
    lot = db.Column('cantidad', db.Integer)
    unit_price_moment = db.Column('precio_unitario_momento', db.Numeric(10,2))
    moment_utility = db.Column('utilidad_momento', db.Numeric(10,2))

class SalePayment(db.Model):
    __tablename__ = 'ventas_pagos'
    
    id = db.Column('id_pago', db.Integer, primary_key=True, autoincrement=True, nullable=False)
    id_sale = db.Column('id_venta', db.Integer, db.ForeignKey('Ventas.id_venta'), nullable=False)
    payment_method = db.Column('metodo_pago', db.Integer, nullable=False)
    paid_amount = db.Column('monto_pagado', db.Numeric(10, 2), nullable=False)
    payment_reference = db.Column('referencia_pago', db.String(100), nullable=True)
    payment_date = db.Column('fecha_pago', db.DateTime, server_default=db.func.now())

    @property
    def methods(self):
        values = {1: 'Efectivo', 2: 'Tarjeta Debito', 3: 'Tarjeta Credito', 4: 'Transferencia', 5:'Clip/Terminal', 6:'Credito tienda'}
        return values.get(self.payment_method)
    
class CashRegisters(db.Model):
    __tablename__ = 'cortes_cajas'
    
    id = db.Column('id_corte', db.Integer, primary_key=True, autoincrement=True, nullable=False)
    id_cash_box = db.Column('id_caja', db.Integer, db.ForeignKey('Cajas.id_caja'), nullable=False)
    
    open_date = db.Column('fecha_apertura', db.DateTime, server_default=db.func.now())
    close_date = db.Column('fecha_cierre', db.DateTime, nullable=True)

    open_amount = db.Column('monto_apertura', db.Numeric(10, 2), nullable=False)
    expected_close_amount = db.Column('monto_cierre_esperado', db.Numeric(10, 2), nullable=True)
    real_close_amount = db.Column('monto_cierre_real', db.Numeric(10, 2), nullable=True)
    difference = db.Column('diferencia', db.Numeric(10, 2), nullable=True)
    
    status = db.Column('estatus', db.Integer, default=1)

    @property
    def value_status(self):
        values = {1: 'Abierta', 2: 'Cerrada'}
        return values.get(self.status)

class CashBox(db.Model):
    __tablename__ = 'Cajas'
    
    id = db.Column('id_caja', db.Integer, primary_key=True, autoincrement=True, nullable=False)
    name = db.Column('nombre_caja', db.String(50))
    id_user_cashier = db.Column('id_usuario_cajero', db.Integer, db.ForeignKey('Usuarios.id_usuario'))
    status = db.Column('status', db.Integer, default=1) 

    @property
    def value_status(self):
        values = {1: 'Activa', 2: 'Inactiva'}
        return values.get(self.status)    


### EVENTO PARA LAS VENTAS A CANCELAR POR ANTIGUEDAD ###

def verificar_cancelaciones():
    limite = datetime.now() - timedelta(days=3)
    # Buscamos ventas que:
    # 1. Tengan fecha anterior al límite
    # 2. No estén ya canceladas (6) ni entregadas (5)
    ventas_a_cancelar = Sales.query.filter(
        Sales.sale_date < limite,
        Sales.status.notin_([3, 4, 5, 6])
    ).update({Sales.status: 6}, synchronize_session=False)
    
    db.session.commit()
    print(f"Se cancelaron {ventas_a_cancelar} ventas por antigüedad.")


## MOVIMIENTOS INVENTARIO MATERIA PRIMA ##

class ProductionOrder(db.Model):
    __tablename__ = 'ordenesproduccion'

    id = db.Column('id_orden_produccion', db.Integer, primary_key=True)
    folio = db.Column('folio_orden', db.String(20), unique=True, nullable=False)
    recipe_id = db.Column('id_receta_ref', db.Integer, db.ForeignKey('recetas.id_receta'), nullable=False)
    requested_quantity = db.Column('cantidad_solicitada', db.Integer, nullable=False)
    unit_med = db.Column('unidad_medida', db.Integer, nullable=False) # 1: kg, 2: lt, 3: pieza
    operator_id = db.Column('id_operador', db.Integer, db.ForeignKey('Usuarios.id_usuario'), nullable=False)
    real_waste = db.Column('merma_real', db.Numeric(10, 2), default=0.00)
    
    scheduled_date = db.Column('fecha_programada', db.DateTime)
    start_date = db.Column('fecha_inicio', db.DateTime)
    end_date = db.Column('fecha_cierre', db.DateTime)
    
    # 1: Esperando Validacion, 2: Pendiente, 3: En Proceso, 4: Completado, 5: Cancelado
    status = db.Column('status', db.Integer, default=2)

    # Relaciones
    recipe = db.relationship('Recipe', backref='production_orders')
    operator = db.relationship('User', backref='orders_assigned')
    inputs = db.relationship('ProductionOrderInput', backref='order', cascade="all, delete-orphan")

class ProductionOrderInput(db.Model):
    __tablename__ = 'ordenesproduccion_insumos'

    id = db.Column('id_op_insumo', db.Integer, primary_key=True)
    order_id = db.Column('id_orden_produccion', db.Integer, db.ForeignKey('ordenesproduccion.id_orden_produccion', ondelete='CASCADE'))
    material_id = db.Column('id_materia_prima', db.Integer, db.ForeignKey('MateriaPrima.id_materia'))
    material_name = db.Column('nombre_materia', db.String(100)) # Snapshot del nombre
    supplier_lot = db.Column('lote_proveedor', db.String(50)) # Para Trazabilidad RDF 6.3
    used_quantity = db.Column('cantidad_utilizada', db.Numeric(10, 2))
    moment_cost = db.Column('costo_insumo_momento', db.Numeric(10, 2))

    material = db.relationship('Raw_Material', backref='production_inputs')

class ProductionLot(db.Model):
    __tablename__ = 'lotesproduccion'

    id = db.Column('id_lote', db.Integer, primary_key=True)
    lot_code = db.Column('codigo_lote', db.String(50), unique=True, nullable=False)
    product_id = db.Column('id_producto', db.Integer, db.ForeignKey('productos.id_producto'), nullable=False)
    product_name = db.Column('nombre_producto', db.String(100))
    order_folio_ref = db.Column('folio_orden_ref', db.String(20))
    produced_quantity = db.Column('cantidad_producida', db.Numeric(10, 2))
    unit_med = db.Column('unidad_medida', db.String(20))
    unit_cost = db.Column('costo_unitario_produccion', db.Numeric(10, 2))
    
    manufacture_date = db.Column('fecha_fabricacion', db.DateTime, default=datetime.utcnow)
    expiry_date = db.Column('fecha_caducidad_estimada', db.DateTime)
    warehouse_location = db.Column('ubicacion_almacen', db.String(50))
    current_stock = db.Column('stock_actual', db.Numeric(10, 2))
    
    # 1: Disponible, 2: Cuarentena, 3: Agotado, 4: Retirado
    status = db.Column('status', db.Integer, default=2)

    product = db.relationship('Producto', backref='production_lots')
    quality_controls = db.relationship('ProductionLotQuality', backref='lot', cascade="all, delete-orphan")

class ProductionLotQuality(db.Model):
    __tablename__ = 'lotesproduccion_calidad'

    id = db.Column('id_control', db.Integer, primary_key=True)
    lot_id = db.Column('id_lote', db.Integer, db.ForeignKey('lotesproduccion.id_lote', ondelete='CASCADE'))
    parameter = db.Column('parametro', db.String(50))
    obtained_value = db.Column('valor_obtenido', db.String(50))
    is_approved = db.Column('aprobado', db.Boolean, default=False)

class InventoryMovementMP(db.Model):
    __tablename__ = 'movimientosinventariomp'
    id = db.Column('id_movimiento_mp', db.Integer, primary_key=True, autoincrement=True)
    material_id = db.Column('id_materia', db.Integer, db.ForeignKey('MateriaPrima.id_materia'), nullable=False)
    # 1: Entrada, 2: Salida
    movement_type = db.Column('tipo_movimiento', db.Integer, nullable=False)
    # 1: Merma, 2: Consumo, 3: Ajuste, 4: Abasto
    reason = db.Column('motivo', db.Integer, nullable=False)
    quantity = db.Column('cantidad', db.Numeric(10, 2), nullable=False)
    resulting_stock = db.Column('stock_resultante', db.Numeric(10, 2), nullable=True) 
    pending_quantity = db.Column('cantidad_pendiente', db.Numeric(10, 2), default=0.00)
    # 1: Aplicado, 2: Pendiente
    status = db.Column('status_movimiento', db.Integer, default=1)
    expiration_date = db.Column('fecha_caducidad', db.Date, nullable=True)
    user_id = db.Column('id_usuario', db.Integer, db.ForeignKey('Usuarios.id_usuario'), nullable=False)
    timestamp = db.Column('timestamp', db.DateTime, default=datetime.utcnow)

    # Relaciones
    material = db.relationship('Raw_Material', backref='inventory_movements')
    user = db.relationship('User', backref='inventory_actions')

    def __repr__(self):
        return f'<RawMaterialMovement ID:{self.id} Material:{self.material_id}>'

class InventoryMovementPT(db.Model):
    __tablename__ = 'movimientosinventariopt'

    id = db.Column('id_movimiento_pt', db.Integer, primary_key=True)
    product_id = db.Column('id_producto', db.Integer, db.ForeignKey('productos.id_producto'), nullable=False)
    type = db.Column('tipo_movimiento', db.Integer, nullable=False) # 1: Entrada, 2: Salida
    reason = db.Column('motivo', db.Integer, nullable=False) # 1: Merma, 2: Venta, 3: Ajuste, 4: Produccion
    quantity = db.Column('cantidad', db.Numeric(10, 2), nullable=False)
    resulting_stock = db.Column('stock_resultante', db.Numeric(10, 2), nullable=False)
    user_id = db.Column('id_usuario', db.Integer, db.ForeignKey('Usuarios.id_usuario'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column('status', db.Integer, nullable=False)
    products = db.relationship('Producto', backref='product_movements')
    user = db.relationship('User', backref='user_inventory_actions')
