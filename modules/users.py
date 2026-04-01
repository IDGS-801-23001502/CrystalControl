from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, User, Role
from flask_security.utils import hash_password
from utils.decorators import roles_accepted
import secrets
import string

module = 'users'

users_bp = Blueprint(
    module,
    __name__,
    template_folder='templates',
    static_folder='static'
)


def generate_random_password(length=10):
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(characters) for _ in range(length))


@users_bp.route('/')
@roles_accepted('Administrador')
def index():
    q = request.args.get('q', '').strip()
    status_filter = request.args.get('status', 'all')

    query = User.query

    if q:
        like = f'%{q}%'
        query = query.filter(
            (User.username.ilike(like)) |
            (User.nombre.ilike(like))
        )

    if status_filter == 'active':
        query = query.filter_by(estatus='Activo')
    elif status_filter == 'inactive':
        query = query.filter_by(estatus='Inactivo')

    usuarios = query.order_by(User.id).all()
    roles = Role.query.all()

    return render_template(
        'users/list.html',
        usuarios=usuarios,
        roles=roles,
        q=q,
        status_filter=status_filter
    )


@users_bp.route('/crear', methods=['GET', 'POST'])
@roles_accepted('Administrador')
def crear():
    roles = Role.query.all()

    if request.method == 'POST':
        username  = request.form.get('username', '').strip()
        nombre    = request.form.get('nombre', '').strip()
        id_perfil = request.form.get('id_perfil', type=int)
        raw_pass  = request.form.get('password', '').strip()

        errors = []
        if not username or len(username) < 4:
            errors.append('El nombre de usuario debe tener al menos 4 caracteres.')
        if not nombre or len(nombre) < 2:
            errors.append('El nombre es requerido.')
        if not id_perfil:
            errors.append('Debe seleccionar un perfil.')
        if User.query.filter_by(username=username).first():
            errors.append(f'El nombre de usuario "{username}" ya esta en uso.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('users/crearUsuario.html', roles=roles,
                                   form_data=request.form)

        generated = False
        if not raw_pass:
            raw_pass = generate_random_password()
            generated = True

        nuevo = User(
            username=username,
            nombre=nombre,
            password=hash_password(raw_pass),
            id_perfil=id_perfil,
            estatus='Activo',
            fs_uniquifier=secrets.token_hex(32)
        )

        try:
            db.session.add(nuevo)
            db.session.commit()
            if generated:
                flash(
                    f'Usuario "{username}" creado. Contrasena generada: {raw_pass} — anotela ahora.',
                    'success'
                )
            else:
                flash(f'Usuario "{username}" creado exitosamente.', 'success')
            return redirect(url_for('users.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear usuario: {str(e)}', 'danger')

    return render_template('users/crearUsuario.html', roles=roles, form_data={})


@users_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@roles_accepted('Administrador')
def editar(id):
    usuario = User.query.get_or_404(id)
    roles   = Role.query.all()

    if request.method == 'POST':
        username  = request.form.get('username', '').strip()
        nombre    = request.form.get('nombre', '').strip()
        id_perfil = request.form.get('id_perfil', type=int)
        raw_pass  = request.form.get('password', '').strip()

        errors = []
        if not username or len(username) < 4:
            errors.append('El nombre de usuario debe tener al menos 4 caracteres.')
        if not nombre or len(nombre) < 2:
            errors.append('El nombre es requerido.')
        if not id_perfil:
            errors.append('Debe seleccionar un perfil.')

        existing = User.query.filter(
            User.username == username, User.id != id
        ).first()
        if existing:
            errors.append(f'El nombre de usuario "{username}" ya esta en uso.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('users/editarUsuario.html', usuario=usuario,
                                   roles=roles, form_data=request.form)

        usuario.username  = username
        usuario.nombre    = nombre
        usuario.id_perfil = id_perfil

        if raw_pass:
            usuario.password = hash_password(raw_pass)

        try:
            db.session.commit()
            flash(f'Usuario "{usuario.username}" actualizado correctamente.', 'success')
            return redirect(url_for('users.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'danger')

    return render_template('users/editarUsuario.html', usuario=usuario,
                           roles=roles, form_data={})


@users_bp.route('/estatus/<int:id>', methods=['POST'])
@roles_accepted('Administrador')
def cambiar_estatus(id):
    usuario = User.query.get_or_404(id)
    usuario.estatus = 'Inactivo' if usuario.estatus == 'Activo' else 'Activo'
    try:
        db.session.commit()
        action = 'activado' if usuario.estatus == 'Activo' else 'desactivado'
        flash(f'Usuario "{usuario.username}" {action} correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar estatus: {str(e)}', 'danger')
    return redirect(url_for('users.index'))


@users_bp.route('/permisos')
@roles_accepted('Administrador')
def permisos():
    from models import Modulo, perfil_modulo
    roles = Role.query.all()
    modulos = Modulo.query.all()
    return render_template('users/permisos.html', roles=roles, modulos=modulos)


@users_bp.route('/permisos/guardar', methods=['POST'])
@roles_accepted('Administrador')
def guardar_permisos():
    from models import Modulo, perfil_modulo
    try:
        roles = Role.query.all()
        modulos = Modulo.query.all()

        for role in roles:
            for modulo in modulos:
                field_name = f'perm_{role.id}_{modulo.id}'
                has_access = request.form.get(field_name) == '1'
                write_perm = request.form.get(f'write_{role.id}_{modulo.id}') == '1'

                current = db.session.execute(
                    perfil_modulo.select().where(
                        perfil_modulo.c.id_perfil == role.id,
                        perfil_modulo.c.id_modulo == modulo.id
                    )
                ).first()

                if has_access and not current:
                    db.session.execute(perfil_modulo.insert().values(
                        id_perfil=role.id,
                        id_modulo=modulo.id,
                        permiso_escritura=1 if write_perm else 0
                    ))
                elif not has_access and current:
                    db.session.execute(perfil_modulo.delete().where(
                        perfil_modulo.c.id_perfil == role.id,
                        perfil_modulo.c.id_modulo == modulo.id
                    ))
                elif has_access and current:
                    db.session.execute(perfil_modulo.update().where(
                        perfil_modulo.c.id_perfil == role.id,
                        perfil_modulo.c.id_modulo == modulo.id
                    ).values(permiso_escritura=1 if write_perm else 0))

        db.session.commit()
        flash('Permisos actualizados correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al guardar permisos: {str(e)}', 'danger')

    return redirect(url_for('users.permisos'))
