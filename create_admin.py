from app import app
from models import db, User, Role
from flask_security.utils import hash_password
import uuid

def create_admin():
    with app.app_context():
        # 1. Buscar o crear el Perfil (Role)
        admin_role = Role.query.filter_by(name='Administrador').first()
        if not admin_role:
            admin_role = Role(
                name='Administrador', 
                description='Acceso total al sistema'
            )
            db.session.add(admin_role)
            db.session.commit()
            print("Perfil 'Administrador' creado.")
        else:
            print("ℹEl perfil 'Administrador' ya existe.")

        username = "admin_crystal"
        raw_pass = "robloxianos"

        # 2. Verificar si el usuario ya existe
        existing_user = User.query.filter_by(username=username).first()
        
        if not existing_user:
            hashed_pass = hash_password(raw_pass)
            
            admin_data = {
                "username": username,
                "password": hashed_pass,
                "estatus": 'Activo',
                "fs_uniquifier": str(uuid.uuid4()),
                "id_perfil": admin_role.id
            }

            if hasattr(User, 'nombre'):
                admin_data["nombre"] = "Admin"
            if hasattr(User, 'apellidos'):
                admin_data["apellidos"] = ""

            admin = User(**admin_data)
            
            db.session.add(admin)
            db.session.commit()
            print(f"¡Usuario '{username}' creado con éxito!")
        else:
            # Si ya existe, podemos actualizar su id_perfil por si acaso
            existing_user.id_perfil = admin_role.id
            db.session.commit()
            print(f"ℹEl usuario '{username}' ya existe (Perfil actualizado).")

if __name__ == "__main__":
    create_admin()