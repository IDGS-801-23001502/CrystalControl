from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user

def roles_accepted(*role_names):
    """
    Permite el acceso si el usuario tiene AL MENOS UNO de los roles especificados.
    Uso: @roles_accepted('Administrador', 'Gerente')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 1. Verificar si está logueado
            if not current_user.is_authenticated:
                flash("Por favor, inicia sesión para acceder.", "info")
                return redirect(url_for('login.login_employees'))

            # 2. Verificar que sea un Usuario Empleado
            if current_user.is_client :
                flash("Acceso restringido al personal.", "warning")
                return redirect(url_for('index'))
            # 3. Verificar si tiene alguno de los roles permitidos
            has_permission = any(current_user.has_role(role) for role in role_names)
            if not has_permission:
                flash(f"No tienes los permisos necesarios ({', '.join(role_names)}).", "danger")
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def client_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Inicia sesión como cliente.", "info")
            return redirect(url_for('login.login_client'))
            
        if not current_user.is_client:
            flash("Sección exclusiva para clientes.", "warning")
            return redirect(url_for('index')) # Index de empleados
            
        return f(*args, **kwargs)
    return decorated_function