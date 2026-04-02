from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin
from flask_pymongo import PyMongo
from sqlalchemy.dialects.mysql import TINYINT
from datetime import datetime

 
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
    product_id = db.Column('id_producto', db.Integer, db.ForeignKey('productos.id_producto'))
    status = db.Column('estatus', db.Integer, default=1)
    
class RecipeDetail(db.Model):
    __tablename__ = 'receta_detalle'
    
    id = db.Column('id_receta_detalle', db.Integer, primary_key=True)
    recipe_id = db.Column('id_receta', db.Integer, db.ForeignKey('recetas.id_receta'), nullable=False)
    material_id = db.Column('id_materia', db.Integer, db.ForeignKey('MateriaPrima.id_materia'), nullable=False)
    required_quantity =  db.Column('cantidad_necesaria', db.Numeric(10, 2), nullable=False)
    unit_med = db.Column('unidad_medida', TINYINT) #1-Kilos 2-Litros 3-Piezas 

class RecipeStep(db.Model):
    __tablename__ = 'pasosreceta'
   
    id = db.Column('id_paso', db.Integer, primary_key=True)
    recipe_id = db.Column('id_receta', db.Integer, db.ForeignKey('recetas.id_receta'), nullable=False)
    step_order = db.Column('orden_paso', db.Integer, nullable=False)
    stage_name = db.Column('nombre_etapa', db.String(50), nullable=False)
    description = db.Column('descripcion_especifica', db.Text)
    estimated_time = db.Column('tiempo_estimado_paso', db.Integer, nullable=False)
    process_type = db.Column('tipo_proceso', db.Integer, nullable=False)

##PRODUCTOS##

class Producto(db.Model):
    __tablename__ = 'productos'

    id = db.Column('id_producto', db.Integer, primary_key=True, autoincrement=True)
    barcode = db.Column('codigo_barras', db.Integer)
    name = db.Column('nombre', db.String(100), nullable=False)
    stock = db.Column('stock_disponible', db.Integer, default=0)
    picture = db.Column('foto', db.String(255), nullable=True) # Campo solicitado para la imagen
    status = db.Column('estatus', db.Enum('Activo', 'Inactivo'), default='Activo')

    precios = db.relationship('ProductoPresentacionPrecio', backref='producto', lazy=True)

class ProductoPresentacionPrecio(db.Model):
    __tablename__ = 'producto_presentación_precio'

    id = db.Column('id_presentacion_precio', db.Integer, primary_key=True)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), nullable=False)
    price_men = db.Column('precio_menudeo', db.Numeric(10, 2), nullable=False)
    price_may = db.Column('precio_mayoreo', db.Numeric(10, 2), nullable=False)
    presentation = db.Column('presentacion', db.String(50), nullable=False)

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
    
    id = db.Column('id_ventas', db.Integer, primary_key=True)
    folio = db.Column('folio', db.String(20), unique=True, nullable=False)
    id_user = db.Column('id_usuario', db.Integer, db.ForeignKey('Usuarios.id_usuario'), nullable=False)
    sale_date = db.Column('fecha_venta', db.DateTime, server_default=db.func.now())
    gross_total = db.Column('total_bruto', db.Numeric(10,2))
    profit_total = db.Column('total_utilidad', db.Numeric(10,2))
    payment_method = db.Column('metodo_pago', db.String(50))
    id_client_sold = db.Column('id_cliente_vendido', db.Integer, db.ForeignKey('Clientes.id_cliente'), nullable=False)

class SaleDetail(db.Model):
    __tablename__ = 'detalle_venta'
    
    id = db.Column('id_detalle_venta', db.Integer, primary_key=True)
    id_sale = db.Column('id_venta', db.Integer, db.ForeignKey('Ventas.id_ventas'), nullable=False)
    id_product = db.Column('id_producto', db.Integer, db.ForeignKey('productos.id_producto'), nullable=False)
    lot = db.Column('cantidad', db.Integer)
    unit_price_moment = db.Column('precio_unitario_momento', db.Numeric(10,2))
    moment_utility = db.Column('utilidad_momento', db.Numeric(10,2))


