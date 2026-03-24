from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_security import login_user, logout_user, current_user
from flask_security.utils import verify_password
from models import db, User, Cliente

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
            session['user_type'] = 'employee'
            return redirect(url_for('index'))
    return render_template('login/login_employees.html')

@login_bp.route('/client', methods=['GET', 'POST'])
def login_client():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        cliente = Cliente.query.filter_by(email=email).first()

        if cliente and verify_password(password, cliente.password):
            login_user(cliente)
            session['user_type'] = 'client'
            return redirect(url_for('customer_portal'))
    return render_template('login/login_client.html')

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