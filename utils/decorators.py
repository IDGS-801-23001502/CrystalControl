from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user

#? Este decorador acepta a todos los roles que le pases, si no tiene el rol, lo manda al login o al dashboard correspondiente.
def roles_accepted(*roles_permitidos):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login.login_employees'))
            user_roles = {r.name for r in current_user.roles}
            if not any(role in user_roles for role in roles_permitidos):
                flash("No tienes permiso para esta sección.", "warning")
                # REDIRECCIÓN INTELIGENTE
                if 'Cliente' in user_roles:
                    return redirect(url_for('home'))
                return redirect(url_for('panel'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

#? Este decorador acepta a los clientes y regresa al login de clientes si no eres cliente
def only_client(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login.login_client'))
            
        if not any(r.name == 'Cliente' for r in current_user.roles):
            flash("Esta zona es solo para clientes.", "info")
            return redirect(url_for('panel')) # Mandamos al admin a su lugar
            
        return f(*args, **kwargs)
    return decorated_function

#? este decorador rechaza a todo los roles que le pases y manda al panel administrativo o la tienda online
def exclude_roles(*roles_prohibidos):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.is_authenticated:
                user_roles = {r.name for r in current_user.roles}
                if any(role in user_roles for role in roles_prohibidos):
                    # Si ya está logueado, lo mandamos a su panel
                    if 'Cliente' in user_roles:
                        return redirect(url_for('home'))
                    return redirect(url_for('panel'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator