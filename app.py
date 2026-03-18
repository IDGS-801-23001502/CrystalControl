from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from flask_migrate import Migrate
from modules import users_bp, suppliers_bp, raw_materials_bp, purchases_bp, recipes_bp, production_bp, products_bp, analytics_bp, sales_bp
from models import db, mongo
import locale

try:
    locale.setlocale(locale.LC_TIME, 'es_MX.UTF-8')
except:
    locale.setlocale(locale.LC_TIME, 'es_ES')

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
db.init_app(app)
mongo.init_app(app)
csrf = CSRFProtect()
migrate = Migrate(app, db)
app.register_blueprint(users_bp, url_prefix='/users')
app.register_blueprint(suppliers_bp, url_prefix='/suppliers')
app.register_blueprint(raw_materials_bp, url_prefix='/inventory')
app.register_blueprint(purchases_bp, url_prefix='/purchases')
app.register_blueprint(recipes_bp, url_prefix='/recipes')
app.register_blueprint(production_bp, url_prefix='/production')
app.register_blueprint(products_bp, url_prefix='/products')
app.register_blueprint(analytics_bp, url_prefix='/analytics')
app.register_blueprint(sales_bp, url_prefix='/sales')

if __name__ == '__main__':
	csrf.init_app(app)
	with app.app_context():
		db.create_all()
	app.run()