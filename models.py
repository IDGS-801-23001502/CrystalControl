from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin
from flask_pymongo import PyMongo
from sqlalchemy.dialects.mysql import TINYINT
 
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
    unidad_medida = db.Column('unidad_medida',db.String(20))
    
    estatus = db.Column(db.Enum('Activo', 'Inactivo'), default='Activo')



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

