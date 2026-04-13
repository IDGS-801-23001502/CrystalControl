import os
class Config(object):
    SECRET_KEY = os.urandom(24)
    SESSION_COOKIE_SECURE = False
    
    # --- Configuración MongoDB (PyMongo) ---
    # Definimos el nombre de la base de datos por defecto
    MONGO_DBNAME = "crystalcontrol"
    
    # --- Flask-Security Config ---
    SECURITY_PASSWORD_SALT = "una_cadena_fija_y_larga"
    SECURITY_JOIN_USER_ROLES = False
    
    SECURITY_USER_IDENTITY_ATTRIBUTES = [
        {"username": {"mapper": "username"}},
        {"email": {"mapper": "email"}},
    ]
    
    SECURITY_LOGIN_URL = "/panel/login/employees"
    SECURITY_POST_LOGIN_VIEW = "/panel/dashboard"
    SECURITY_POST_LOGOUT_VIEW = "/panel/login/employees"
    SECURITY_LOGIN_USER_TEMPLATE = "login/login_employees.html"
    
    SECURITY_PASSWORD_HASH = "bcrypt"
    SECURITY_REGISTERABLE = False
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_RECOVERABLE = False
    
    SECURITY_MSG_ANONYMOUS_USER = ("Por favor inicia sesión para continuar.", "error")
    SECURITY_MSG_UNAUTHORIZED = ("Acceso denegado: No tienes los permisos necesarios.", "error")
    
    SECURITY_URL_PREFIX = "/panel"

class DevelopmentConfig(Config):
    DEBUG = True
    # --- Configuración MySQL (SQLAlchemy) ---
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://crystalcontrol:robloxianos@10.147.17.29:3306/crystalcontrol"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Configuración PyMongo ---
    MONGO_URI = "mongodb://crystalcontrol:robloxianos@10.147.17.28:27017/crystalcontrol?authSource=admin"