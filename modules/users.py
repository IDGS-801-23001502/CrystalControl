from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from models import db, User, Role  
from forms import FormUsuarios
import string
import random
import secrets

users_bp = Blueprint(
    'users',
    __name__,
    template_folder='templates',
    static_folder='static'
)

def generar_password_aleatorio(length=8):
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(characters) for i in range(length))

@users_bp.route("/")
def index():
    query = request.args.get('q', '')
    if query:
        usuarios = User.query.filter(
            (User.username.like(f'%{query}%')) | 
            (User.nombre.like(f'%{query}%')) | 
            (User.apellidos.like(f'%{query}%'))
        ).all()
    else:
        usuarios = User.query.all()
    
    return render_template("users/list.html", usuarios=usuarios)

@users_bp.route("/crear", methods=["GET", "POST"])
def crear():
    form = FormUsuarios()
    form.id_perfil.choices = [(p.id, p.name) for p in Role.query.all()]
    
    if form.validate_on_submit():
        password_final = form.password.data if form.password.data else generar_password_aleatorio()
        nuevo_usuario = User(
            username=form.username.data,
            nombre=form.nombre.data,
            apellidos=form.apellidos.data,
            email=form.email.data,
            password=password_final,
            id_perfil=form.id_perfil.data,
            active=form.active.data,
            fs_uniquifier=secrets.token_hex(16)
        )
        
        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash(f"Usuario creado con éxito. Contraseña: {password_final if not form.password.data else 'la ingresada'}", "success")
            return redirect(url_for('users.index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al crear usuario: {str(e)}", "danger")

    return render_template("users/crearUsuario.html", form=form)

@users_bp.route("/editarUsuario/<int:id>", methods=["GET", "POST"])
def editar(id):
    """
    RDF 1.4: Actualizar Usuario
    Permite modificar username, nombre, apellidos y perfil.
    """
    usuario = User.query.get_or_404(id)
    # Pasamos el objeto usuario al formulario para precargar los datos
    form = FormUsuarios(obj=usuario)
    
    # RDF 1.6: Cargar perfiles para el SelectField
    form.id_perfil.choices = [(p.id, p.name) for p in Role.query.all()]
    
    if form.validate_on_submit():
        usuario.username = form.username.data
        usuario.nombre = form.nombre.data
        usuario.apellidos = form.apellidos.data
        usuario.id_perfil = form.id_perfil.data
        usuario.estatus = form.estatus.data # RDF 1.5
        
        # Opcional: Actualizar contraseña solo si se escribe algo nuevo
        if form.password.data:
            usuario.password = generate_password_hash(form.password.data)
        
        try:
            db.session.commit()
            flash(f"Usuario '{usuario.username}' actualizado correctamente.", "success")
            return redirect(url_for('users.index'))
        except Exception as e:
            db.session.rollback()
            flash("Error al actualizar: el nombre de usuario ya existe.", "danger")
            
    return render_template("users/editarUsuario.html", form=form, usuario=usuario)


@users_bp.route("/eliminarUsuario/<int:id>", methods=["GET", "POST"])
def eliminar(id):
    usuario = User.query.get_or_404(id)
    if request.method == "POST":
        db.session.delete(usuario)
        db.session.commit()
        flash(f"Usuario '{usuario.username}' eliminado.", "success")
        return redirect(url_for('users.index'))
    return render_template("users/eliminarUsuario.html", usuario=usuario)