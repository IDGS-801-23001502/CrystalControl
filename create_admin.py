from app import app
from models import db, User, Role, Cliente, Modulo, perfil_modulo
from flask_security.utils import hash_password
import uuid

def create_admin():
    with app.app_context():
        # 1. Definir los perfiles
        roles_data = [
            {'name': 'Compras'},
            {'name': 'Almacenista'},
            {'name': 'Vendedor'},
            {'name': 'Produccion'},
            {'name': 'Gerente'},
            {'name': 'Cliente'},
            {'name': 'Administrador', 'description': 'Acceso total al sistema'}
        ]

        roles_dict = {}
        for r_data in roles_data:
            role = Role.query.filter_by(name=r_data['name']).first()
            if not role:
                role = Role(**r_data)
                db.session.add(role)
                db.session.flush() 
                print(f"Perfil '{r_data['name']}' creado.")
            else:
                print(f"ℹ El perfil '{r_data['name']}' ya existe.")
            roles_dict[r_data['name']] = role

        # 2. Definición de Módulos
        modulos_nombres = [
            'users', 'suppliers', 'raw_materials',
            'purchases', 'production',
            'analytics', 'sales', 'products', 'recipes'
        ]
        
        modulos_dict = {}
        for nombre in modulos_nombres:
            mod = Modulo.query.filter_by(name=nombre).first()
            if not mod:
                mod = Modulo(name=nombre)
                db.session.add(mod)
                db.session.flush()
                print(f"Módulo '{nombre}' creado.")
            else:
                print(f"ℹ El módulo '{nombre}' ya existe.")
            modulos_dict[nombre] = mod

        # 3. Configuración del Usuario Administrador
        username = "admin_crystal"
        raw_pass = "robloxianos"
        admin_role = roles_dict.get('Administrador')

        existing_user = User.query.filter_by(username=username).first()
        if not existing_user:
            admin = User(
                username=username,
                nombre="Admin",
                password=hash_password(raw_pass),
                estatus='Activo',
                fs_uniquifier=str(uuid.uuid4()),
                id_perfil=admin_role.id
            )
            db.session.add(admin)
            print(f"¡Usuario '{username}' creado!")
        
        db.session.commit()

        # 4. Creación de Usuario Cliente inicial
        email = "crystal@crystal.com"
        client_role = roles_dict.get('Cliente')
        existing_client_user = User.query.filter_by(username=email).first()

        if not existing_client_user:
            user_client = User(
                username=email,
                nombre="Cliente General",
                password=hash_password(raw_pass),
                fs_uniquifier=str(uuid.uuid4()),
                id_perfil=client_role.id,
                estatus='Activo'
            )
            db.session.add(user_client)
            db.session.flush()

            client_info = Cliente(
                id_usuario=user_client.id,
                direccion_envio="Tienda Fisica",
                telefono="1234567890"
            )
            db.session.add(client_info)
            print(f"Cliente '{email}' creado!")
        
        db.session.commit()

        # 5. ASIGNACIÓN DE PERMISOS (Niveles de acceso)
        # Nota: Cada nivel de acceso incluye a sus niveles anteriores
        # Nivel 1: Lectura, 2: Escritura parcial, 3: Edición, 4: Eliminado
        def asignar_permiso(role_name, modulo_name, nivel):
            r = roles_dict.get(role_name)
            m = modulos_dict.get(modulo_name)
            if r and m:
                # Verificar si ya existe la relación
                existe = db.session.query(perfil_modulo).filter_by(id_perfil=r.id, id_modulo=m.id).first()
                if not existe:
                    ins = perfil_modulo.insert().values(id_perfil=r.id, id_modulo=m.id, permiso_escritura=nivel)
                    db.session.execute(ins)

        for m_name in modulos_nombres:
            asignar_permiso('Administrador', m_name, 4)
        
        #Permisos Extra aqui
        
        db.session.commit()
        print("Configuración de módulos y permisos completada.")

if __name__ == "__main__":
    create_admin()