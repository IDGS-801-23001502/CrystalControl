from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin

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
    password = db.Column('password_hash', db.String(255), nullable=False)
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False)
    estatus = db.Column(db.Enum('Activo', 'Inactivo'), default='Activo')
    
    # Llave foránea al perfil
    id_perfil = db.Column(db.Integer, db.ForeignKey('Perfiles.id_perfil'))
    roles = db.relationship('Role', 
                           primaryjoin="User.id_perfil == Role.id",
                           viewonly=True, 
                           uselist=True)
    @property
    def perfil(self):
        if self.roles and len(self.roles) > 0:
            return self.roles[0]
        return None
    
    @property
    def active(self):
        return self.estatus == 'Activo'

    def tiene_escritura(self, nombre_modulo):
        if not self.id_perfil: return 0
        modulo = Modulo.query.filter_by(name=nombre_modulo).first()
        if not modulo: return 0
        
        permiso = db.session.query(perfil_modulo).filter_by(
            id_perfil=self.id_perfil,
            id_modulo=modulo.id
        ).first()
        return permiso.permiso_escritura if permiso else 0

class Cliente(db.Model, UserMixin):
    __tablename__ = 'Clientes'
    id = db.Column('id_cliente', db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column('password_hash', db.String(255), nullable=False)
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False)
    estatus = db.Column(db.Enum('Activo', 'Inactivo'), default='Activo')

    # Los clientes no tienen roles, pero Flask-Security lo busca
    roles = [] 

    @property
    def active(self):
        return self.estatus == 'Activo'