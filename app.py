from flask import Flask, render_template, redirect, url_for
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from flask_migrate import Migrate
from modules import users_bp, ecommerce_bp ,login_bp,suppliers_bp, raw_materials_bp, purchases_bp, recipes_bp, production_bp, products_bp, analytics_bp, sales_bp
from models import db, User,Role, mongo
from flask_security import SQLAlchemyUserDatastore, Security, current_user
import locale

try:
    locale.setlocale(locale.LC_TIME, 'es_MX.UTF-8')
except:
    locale.setlocale(locale.LC_TIME, 'es_ES')

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
db.init_app(app)
mongo.init_app(app)
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)
csrf = CSRFProtect()
migrate = Migrate(app, db)

# Registro de Blueprints
app.register_blueprint(users_bp, url_prefix='/panel/users')
app.register_blueprint(suppliers_bp, url_prefix='/panel/suppliers')
app.register_blueprint(raw_materials_bp, url_prefix='/panel/inventory')
app.register_blueprint(purchases_bp, url_prefix='/panel/purchases')
app.register_blueprint(recipes_bp, url_prefix='/panel/recipes')
app.register_blueprint(production_bp, url_prefix='/panel/production')
app.register_blueprint(products_bp, url_prefix='/panel/products')
app.register_blueprint(analytics_bp, url_prefix='/panel/analytics')
app.register_blueprint(sales_bp, url_prefix='/panel/sales')
app.register_blueprint(login_bp, url_prefix='/login')
app.register_blueprint(ecommerce_bp, url_prefix="/")

@app.context_processor
def inject_functions():
    return dict(hasattr=hasattr)

@app.route("/")
def home():
     return render_template("/ecommerce/index.html")

@app.route("/panel/dashboard")
def panel():
    if not current_user.is_authenticated:
        return redirect(url_for('login.login_employees'))
    if hasattr(current_user, 'id_cliente'):
        return redirect(url_for('cliente_dashboard'))
    return render_template("index.html")

if __name__ == '__main__':
	csrf.init_app(app)
	app.run()