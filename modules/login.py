from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import current_user, login_user
from models import User, Cliente, Role, db
import uuid
from flask_security import verify_password, logout_user, hash_password

login_bp = Blueprint(
    'login', 
    __name__,
    template_folder='templates',
    static_folder='static'
)

@login_bp.route('/employees', methods=['GET', 'POST'])
def login_employees():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and verify_password(password, user.password):
            login_user(user)
            return redirect(url_for('panel'))
    return render_template('login/login_employees.html')

@login_bp.route('/client', methods=['GET', 'POST'])
def login_client():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        user = User.query.filter_by(username=email).first()
        if user and verify_password(password, user.password):
            if user.is_client:
                login_user(user, remember=remember)
                return redirect(url_for('home'))
            else:
                flash("Esta cuenta no tiene perfil de cliente.", "warning")
                
    return render_template('login/login_client.html')

@login_bp.route("/register")
def register():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        email = request.form.get('email')
        password = request.form.get("password")
        address = request.form.get("address")
        phone = request.form.get("phone")

        role_cliente = Role.query.filter_by(name="Cliente").first()

        user_client = User(
            username=email,
            nombre=nombre,
            password=hash_password(password),
            fs_uniquifier=str(uuid.uuid4()),
            id_perfil=role_cliente.id,
            estatus='Activo'
        )
        db.session.add(user_client)
        db.session.flush()

        client = Cliente(
            id_usuario=role_cliente.id,
            direccion_envio = address,
            telefono = phone
        )
        db.session.add(client)
        db.session.commit()
    return render_template("login/register.html")

# LOGOUT UNIVERSAL
@login_bp.route('/logout')
def logout():
    # Detectamos origen para saber a qué login regresar
    dest = url_for('login.login_employees')
    if current_user.is_authenticated and hasattr(current_user, 'id_cliente'):
        dest = url_for('login.login_client')
    
    logout_user()
    session.clear()
    flash("Has cerrado sesión correctamente.", "info")
    return redirect(dest)