from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_pymongo import PyMongo

db = SQLAlchemy()
mongo = PyMongo()