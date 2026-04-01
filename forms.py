from flask_wtf import FlaskForm
from wtforms import DecimalField, StringField, PasswordField, SelectField, BooleanField, EmailField, HiddenField, FileField, IntegerField
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

class FormSupplier(FlaskForm):
    id = HiddenField('id')
        
    name = StringField('Nombre o Razón Social', [
        validators.DataRequired(message="El nombre del proveedor es requerido"),
        validators.Length(min=3, max=100)
    ])
    
    address = StringField('Domicilio', [
        validators.DataRequired(message="La dirección es requerida")
    ])
    
    phone = StringField('Teléfono', [
        validators.DataRequired(message="El teléfono es requerido"),
        validators.Length(min=10, max=20, message="Introduce un número válido")
    ])
    
    email = EmailField('Correo Electrónico', [
        validators.DataRequired(message="El email es requerido"),
        validators.Email(message="Introduce un email válido")
    ])
    status = HiddenField('Estatus', default='Activo')
    

class EditFormSupplier(FormSupplier): #Se hereda el formulario de proveedr para solo agregar los campos para la edicion
    unique_code = StringField('Número Único', render_kw={'readonly': True})
    
    status = SelectField('Estatus', choices=[
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo')
    ])

class FormProduct(FlaskForm):
    id = HiddenField('id')
        
    name = StringField('Nombre del producto', [
        validators.DataRequired(message="El nombre del producto es requerido"),
        validators.Length(min=3, max=100)
    ])
    
    price_men = DecimalField('Precio de menudeo', [
        validators.DataRequired(message="El precio de menudeo es requerido")
    ], places=2)
    
    price_may = DecimalField('Precio de mayoreo', [
        validators.DataRequired(message="El precio de mayoreo es requerido")
    ], places=2)

    presentation = StringField('Presentación', [
        validators.DataRequired(message="Ingresa una presentación valida")
    ])

    stock = IntegerField('stock_disponible', default=0)
    
    content = StringField('Contenido neto', [
        validators.DataRequired(message="El contenido del producto es requerido")
    ])

    picture = FileField('Foto del producto', [
        validators.Optional()
    ])

    status = HiddenField('Estatus', default='Activo')