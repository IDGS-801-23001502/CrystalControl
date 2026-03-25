from wtforms import Form
from wtforms import StringField, IntegerField, PasswordField, FloatField, SelectField
from wtforms import EmailField
from wtforms import validators

from wtforms import Form, StringField, IntegerField, PasswordField, SelectField, BooleanField, EmailField, validators

class FormUsuarios(Form):
    id = IntegerField('id')
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
        validators.Email(message="Introduce un email válido"),
        validators.Length(max=255)
    ])
    password = PasswordField('Contraseña', [
        validators.Optional(), # O DataRequired si decides no autogenerarla
        validators.Length(min=8, max=20)
    ])
    
    # Cambiado a SelectField para manejar los IDs de la tabla Perfiles
    # Los 'choices' se deben cargar desde la base de datos en la ruta (view)
    id_perfil = SelectField('Perfil', coerce=int, validators=[
        validators.DataRequired(message="El perfil es requerido")
    ])
    active = BooleanField('Usuario Activo')
