from functools import wraps
from flask import abort, redirect, url_for, flash, request
from flask_security import current_user

def employees_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # CAMBIO: Usar username en lugar de id_usuario
        if not current_user.is_authenticated or not hasattr(current_user, 'username'):
            flash("Acceso restringido a empleados.", "danger")
            return redirect(url_for('login.login_employees'))
        return f(*args, **kwargs)
    return decorated_function

def client_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Inicia sesión como cliente.", "info")
            return redirect(url_for('login.login_client'))
            
        # Verificar que sea Cliente (buscando 'id_cliente')
        if not hasattr(current_user, 'id_cliente'):
            flash("Sección exclusiva para clientes.", "warning")
            return redirect(url_for('index')) # Index de empleados
            
        return f(*args, **kwargs)
    return decorated_function