from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_pymongo import PyMongo
from flask_security import UserMixin, RoleMixin

db = SQLAlchemy()
mongo = PyMongo()

##TABLA PERFILES##
class Perfil(db.Model, RoleMixin):
    __tablename__ = 'Perfiles'
    id = db.Column('id_perfil', db.Integer, primary_key=True)
    name = db.Column('nombre_perfil', db.String(50), unique=True, nullable=False)

##TABLA MODULOS##
class Modulo(db.Model):
    __tablename__ = 'Modulos'
    id = db.Column('id_modulo', db.Integer, primary_key=True)
    name = db.Column('nombre_modulo', db.String(50), nullable=False)

## Tabla intermedia: Perfil_Modulo ##
perfil_modulo = db.Table('Perfil_Modulo',
    db.Column('id_perfil', db.Integer, db.ForeignKey('Perfiles.id_perfil'), primary_key=True),
    db.Column('id_modulo', db.Integer, db.ForeignKey('Modulos.id_modulo'), primary_key=True),
    db.Column('permiso_escritura', db.Integer, default=1)
)

##TABLA USUARIOS ##
class User(db.Model, UserMixin):
    __tablename__ = 'Usuarios'
    id = db.Column('id_usuario', db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column('password_hash', db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    active = db.Column('estatus', db.Boolean) 
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False)

    id_perfil = db.Column(db.Integer, db.ForeignKey('Perfiles.id_perfil'))
    roles = db.relationship('Role', secondary=None,
                           backref=db.backref('users', lazy='dynamic'))