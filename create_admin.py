from app import app
from models import db, User, Role
from flask_security.utils import hash_password
import uuid

def create_admin():
    with app.app_context():
        # 1. Definir los perfiles a crear
        roles_data = [
            {'name': 'Compras'},
            {'name': 'Almacenista'},
            {'name': 'Vendedor'},
            {'name': 'Produccion'},
            {'name': 'Gerente'},
            {'name': 'Administrador', 'description': 'Acceso total al sistema'}
        ]

        # Crear roles si no existen
        roles_dict = {}
        for r_data in roles_data:
            role = Role.query.filter_by(name=r_data['name']).first()
            if not role:
                role = Role(**r_data)
                db.session.add(role)
                db.session.flush() # Para obtener el ID antes del commit final
                print(f"Perfil '{r_data['name']}' creado.")
            else:
                print(f"ℹEl perfil '{r_data['name']}' ya existe.")
            roles_dict[r_data['name']] = role

        # 2. Configuración del Usuario Administrador
        username = "admin_crystal"
        raw_pass = "robloxianos"
        
        # Obtenemos específicamente el objeto del rol Administrador
        admin_role = roles_dict.get('Administrador')

        existing_user = User.query.filter_by(username=username).first()
        
        if not existing_user:
            admin = User(
                username=username,
                password=hash_password(raw_pass),
                estatus='Activo',
                fs_uniquifier=str(uuid.uuid4()),
                id_perfil=admin_role.id
            )
            
            # Manejo dinámico de campos adicionales
            if hasattr(User, 'nombre'): admin.nombre = "Admin"
            if hasattr(User, 'apellidos'): admin.apellidos = ""

            db.session.add(admin)
            print(f"¡Usuario '{username}' creado como Administrador!")
        else:
            # Asegurar que el usuario existente tenga el rol de Administrador
            existing_user.id_perfil = admin_role.id
            print(f"ℹEl usuario '{username}' ya existe (Perfil Administrador verificado).")

        # Un solo commit para toda la operación
        db.session.commit()

if __name__ == "__main__":
    create_admin()