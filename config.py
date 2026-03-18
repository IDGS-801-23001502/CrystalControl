import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or "ClaveSecreta"
    SESSION_COOKIE_SECURE = False
    # Configuraciones generales de MongoDB si fuera necesario
    MONGO_DBNAME = "examen_db" 

class DevelopmentConfig(Config):
    DEBUG = True
    # Configuración para MySQL (SQLAlchemy)
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://crystalcontrol:robloxianos@10.147.17.28:3306/crystalcontrol"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración para MongoDB
    MONGO_URI = "mongodb://crystalcontrol:robloxianos@10.147.17.28:27017/crystalcontrol?authSource=admin"