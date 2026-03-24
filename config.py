import os

class Config(object):
    SECRET_KEY = os.urandom(24)
    SESSION_COOKIE_SECURE = False
    MONGO_DBNAME = "crystalcontrol"
    # --- Flask-Security Config ---
    SECURITY_PASSWORD_SALT = "tu_salt_super_secreto"
    SECURITY_USER_IDENTITY_ATTRIBUTES = "username"
    SECURITY_LOGIN_USER_TEMPLATE = "/login/login.html"
    SECURITY_PASSWORD_HASH = "bcrypt"
    SECURITY_REGISTERABLE = False
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_RECOVERABLE = False

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