from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, EmailField, HiddenField
from wtforms import validators

class FormUsuarios(FlaskForm):
    id = HiddenField('id')  
    username = StringField('Nombre de Usuario', [
        validators.DataRequired(message="El nombre de usuario es requerido"),
        validators.Length(min=4, max=50)
    ])
    nombre = StringField('Nombre', [
        validators.DataRequired(message="El nombre es requerido"),
        validators.Length(min=2, max=50)
    ])
    apellidos = StringField('Apellidos', [
        validators.DataRequired(message="El apellido es requerido"),
        validators.Length(min=2, max=50)
    ])
    email = EmailField('Correo Electrónico', [
        validators.DataRequired(message="El email es requerido"),
        validators.Email(message="Introduce un email válido")
    ])
    password = PasswordField('Contraseña', [
        validators.Optional(),
        validators.Length(min=8, max=20, message="La contraseña debe tener al menos 8 caracteres")
    ])
    id_perfil = SelectField('Perfil', coerce=int, validators=[
        validators.DataRequired(message="El perfil es requerido")
    ])
    active = BooleanField('Usuario Activo', default=True)
