import os

class Config(object):
    SECRET_KEY = os.urandom(24)
    SESSION_COOKIE_SECURE = False
    MONGO_DBNAME = "crystalcontrol"
    # --- Flask-Security Config ---
    SECURITY_PASSWORD_SALT = "una_cadena_fija_y_larga"
    SECURITY_JOIN_USER_ROLES = False
    # Permitir ambos campos para identificar (Staff usa username, Clientes usa email)
    SECURITY_USER_IDENTITY_ATTRIBUTES = [
        {"username": {"mapper": "username"}},
        {"email": {"mapper": "email"}},
    ]
    # URL de login por defecto (la del Staff del panel)
    SECURITY_LOGIN_URL = "/panel/login/employees"
    # A dónde mandar al usuario después de entrar/salir exitosamente
    SECURITY_POST_LOGIN_VIEW = "/panel/dashboard"
    SECURITY_POST_LOGOUT_VIEW = "/panel/login/employees"
    
    # Templates (puedes dejar uno base, pero los manejaremos desde los Blueprints)
    SECURITY_LOGIN_USER_TEMPLATE = "login/login_employees.html"
    
    SECURITY_PASSWORD_HASH = "bcrypt"
    SECURITY_REGISTERABLE = False
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_RECOVERABLE = False
    
    # Mensajes personalizados para CrystalControl
    SECURITY_MSG_ANONYMOUS_USER = ("Por favor inicia sesión para continuar.", "error")
    SECURITY_MSG_UNAUTHORIZED = ("Acceso denegado: No tienes los permisos necesarios.", "error")
    
    # --- Configuración Extra de Sesión ---
    # Esto evita que si un cliente se loguea, pueda saltar al panel de staff
    SECURITY_URL_PREFIX = "/panel"

class DevelopmentConfig(Config):
    DEBUG = True
    # Configuración para MySQL (SQLAlchemy)
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://crystalcontrol:robloxianos@10.147.17.28:3306/crystalcontrol"
    # Binds para bases de datos adicionales (MongoDB vía Conector)
    '''
    SQLALCHEMY_BINDS = {
        "mongo_engine": "mongodb:///?Server=10.147.17.28&Port=27017&Database=crystalcontrol&User=crystalcontrol&Password=robloxianos"
    }'''
    SQLALCHEMY_TRACK_MODIFICATIONS = False