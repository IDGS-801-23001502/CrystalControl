from app import app
from models import db, User, Role, Cliente
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
            {'name': 'Cliente'},
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
        email ="crystal@crystal.com"
        name="Cliente"
        
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

        #Creamos ahora a un usuario cliente
        existing_client = User.query.filter_by(username=email).first()
        client_role = roles_dict.get('Cliente')

        if not existing_client:
            user_client = User(
                username=email,
                nombre=name,
                password=hash_password(raw_pass),
                fs_uniquifier=str(uuid.uuid4()),
                id_perfil=client_role.id, # Asignamos el perfil de cliente
                estatus='Activo'
            )
            db.session.add(user_client)
            db.session.flush()

            client = Cliente(
                id_usuario=user_client.id,
                direccion_envio= "Tienda Fisica",
                telefono="1234567890"
            )
            print(f"Cliente '{email}' creado!")
        else:
            print(f"ℹEl cliente '{email}' ya existe (Cliente Verificado).")

        db.session.commit()

if __name__ == "__main__":
    create_admin()