from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column,String, Integer

db = SQLAlchemy()
'''
engine = create_engine("mongodb:///?Server=10.147.17.28&Port=27017&Database=crystalcontrol&User=crystalcontrol&Password=robloxianos") 
mongo = declarative_base()

# --- MODELOS EN MONGODB (Usando el Bind) ---
class ModeloMongo(mongo):
    __bind_key__ = 'mongo_engine'  # <--- IMPORTANTE: Debe coincidir con Config.py
    __tablename__ = "model"
    
    id = db.Column("_id", db.String, primary_key=True) # Mapeo del ID de Mongo
    dato_ejemplo = db.Column(db.String)
'''