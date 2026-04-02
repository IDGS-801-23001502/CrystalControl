from flask import Flask, render_template, redirect, url_for, request, g
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from utils.decorators import exclude_roles, roles_accepted
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

@app.before_request
def load_user_permissions():
    if not current_user.is_authenticated:
        g.level = 0
        return
    blueprint_actual = request.blueprint
    modulos_ignorados = ['login', 'ecommerce']
    
    if blueprint_actual and blueprint_actual not in modulos_ignorados:
        g.level = current_user.nivel_acceso(blueprint_actual)
    else:
        g.level = 0

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route("/")
@exclude_roles('Compras','Almacenista','Vendedor','Produccion','Gerente','Administrador')
def home():
     return render_template("/ecommerce/index.html")

@app.route("/panel/dashboard")
@roles_accepted('Compras','Almacenista','Vendedor','Produccion','Gerente','Administrador')
def panel():
    if not current_user.is_authenticated:
        return redirect(url_for('login.login_employees'))
    if hasattr(current_user, 'id_cliente'):
        return redirect(url_for('cliente_dashboard'))
    print(f"El nivel de usuario en suppliers es {current_user.nivel_acceso('suppliers')}")
    print(f"La url es {request.path} y deberia de ser {url_for('panel')}")
    return render_template("index.html")

if __name__ == '__main__':
	csrf.init_app(app)
	app.run()