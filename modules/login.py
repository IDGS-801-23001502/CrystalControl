from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import current_user, login_user
from models import User, Cliente, Role, db
import uuid
import random
from datetime import datetime, timedelta
from twilio.rest import Client
from flask_security import verify_password, logout_user, hash_password
from utils.functions import register_log_auto

# Configuración de Twilio
TWILIO_SID = 'AC_tu_sid_aqui'
TWILIO_TOKEN = 'tu_token_aqui'
TWILIO_PHONE = '+1234567890'

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
            register_log_auto("Login","login",obj_puro_nuevo=user)
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
                # OBTENER EL TELÉFONO (Relación con la tabla Cliente)
                cliente_data = Cliente.query.filter_by(id_usuario=user.id).first()
                
                if cliente_data and cliente_data.telefono:
                    if send_otp(cliente_data.telefono):
                        # NO iniciamos sesión aún, guardamos el ID temporalmente
                        session['temp_user_id'] = user.id
                        session['temp_remember'] = remember
                        flash("Código enviado a tu celular", "info")
                        return redirect(url_for('login.verify_otp'))
                    else:
                        flash("Error al enviar el SMS. Intenta más tarde.", "danger")
                else:
                    flash("No hay un teléfono registrado para esta cuenta.", "warning")
            else:
                flash("Esta cuenta no tiene perfil de cliente.", "warning")
        else:
            flash("Credenciales incorrectas", "danger")
    return render_template('login/login_client.html')

@login_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    # Si no hay un ID de usuario temporal, no deberían estar aquí
    if 'temp_user_id' not in session:
        return redirect(url_for('login.login_client'))

    if request.method == 'POST':
        user_code = request.form.get('otp_code')
        stored_code = session.get('otp_code')
        expiry = session.get('otp_expiry')

        # Validaciones de seguridad
        if not expiry or datetime.now().timestamp() > expiry:
            flash("El código ha expirado.", "danger")
            return redirect(url_for('login.login_client'))

        if user_code == stored_code:
            # TODO OK: Iniciamos sesión formalmente
            user = User.query.get(session['temp_user_id'])
            login_user(user, remember=session.get('temp_remember', False))
            # Limpiar sesión temporal
            session.pop('temp_user_id')
            session.pop('otp_code')
            session.pop('otp_expiry')
            
            register_log_auto("Login-2FA","Ecommerce", obj_puro_nuevo=user)
            return redirect(url_for('home'))
        else:
            flash("Código incorrecto.", "danger")

    return render_template('login/verify_2fa.html')

@login_bp.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        email = request.form.get('email')
        password = request.form.get("password")
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
            id_usuario=user_client.id,
            telefono = phone
        )
        db.session.add(client)
        db.session.flush()
        db.session.commit()
        register_log_auto("Creación","Usuario",obj_puro_nuevo=user_client)
        register_log_auto("Creación","Ecommerce",obj_puro_nuevo=client)
        return redirect(url_for('login.login_client'))
    return render_template("login/register.html")

# LOGOUT UNIVERSAL
@login_bp.route('/logout')
def logout():
    # Detectamos origen para saber a qué login regresar
    dest = url_for('login.login_employees')
    if current_user.is_authenticated and current_user.is_client:
        dest = url_for('login.login_client')
    logout_user()
    session.clear()
    flash("Has cerrado sesión correctamente.", "info")
    return redirect(dest)

def send_otp(phone_number):
    code = str(random.randint(100000, 999999))
    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        client.messages.create(
            body=f"Crystal Control: Tu código de acceso es {code}. Expira en 5 min.",
            from_=TWILIO_PHONE,
            to=phone_number
        )
        # Guardamos en sesión para comparar luego
        session['otp_code'] = code
        session['otp_expiry'] = (datetime.now() + timedelta(minutes=5)).timestamp()
        return True
    except Exception as e:
        print(f"Error enviando SMS: {e}")
        return False