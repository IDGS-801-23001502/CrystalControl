from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, EmailField, HiddenField, DecimalField
from wtforms import DecimalField, StringField, PasswordField, SelectField, BooleanField, EmailField, HiddenField, FileField, IntegerField
from wtforms import validators

class FormUsuarios(FlaskForm):
    id = HiddenField('id')
    username = StringField('Username', [
        validators.DataRequired(message="Username is required"),
        validators.Length(min=4, max=50)
    ])
    nombre = StringField('Full Name', [
        validators.DataRequired(message="Name is required"),
        validators.Length(min=2, max=50)
    ])
    password = PasswordField('Password', [
        validators.Optional(),
        validators.Length(min=8, max=50, message="Password must be at least 8 characters")
    ])
    id_perfil = SelectField('Role / Profile', coerce=int, validators=[
        validators.DataRequired(message="A role is required")
    ])
    estatus = SelectField('Status', choices=[
        ('Activo', 'Active'),
        ('Inactivo', 'Inactive')
    ], default='Activo')


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


class FormRaw_Materials(FlaskForm):
    id = HiddenField('id')
    name = StringField('Name', [
        validators.DataRequired(message="Name is required"),
        validators.Length(min=2, max=100)
    ])
    stock_min = DecimalField('Stock_min', [
            validators.InputRequired(message="Stock min is required")
        ], default=0.00)
    stock_max = DecimalField('Stock Máximo', [
        validators.InputRequired(message="Stock max is required")
    ], default=0.00)
    unidad_medida = StringField('Unidad de Medida', [
            validators.DataRequired(message="La unidad es obligatoria"),
            validators.Length(max=20)
        ])
    estatus = SelectField('Status', choices=[
        ('Activo', 'Active'),
        ('Inactivo', 'Inactive')
    ], default='Activo')


class FormRaw_Materials_Supplier(FlaskForm):
    id_material = HiddenField('ID Material', validators=[
            validators.DataRequired()
        ])
    
    id_supplier = SelectField('Proveedor', coerce=int, validators=[
        validators.DataRequired(message="Debe seleccionar un proveedor")
    ])
    
    price = DecimalField('Precio de Referencia', [
        validators.InputRequired(message="El precio es obligatorio"),
        validators.NumberRange(min=0, message="El precio no puede ser negativo")
    ], places=2)
    
    lot = DecimalField('Cantidad / Lote', [
        validators.InputRequired(message="La cantidad es obligatoria"),
        validators.NumberRange(min=0, message="La cantidad debe ser mayor a 0")
    ], places=2)
    
    # Basado en el diccionario que definiste en el modelo
    unidad_medida = SelectField('Unidad de Medida', coerce=int, choices=[
        (1, 'Kilos'),
        (2, 'Litros'),
        (3, 'Galones'),
        (4, 'Pieza')
    ], validators=[
        validators.DataRequired(message="La unidad de medida es obligatoria")
    ])


class FormProduct(FlaskForm):
    id = HiddenField('id')
    name = StringField('Nombre del producto', [
        validators.DataRequired(message="El nombre del producto es requerido"),
        validators.Length(min=3, max=100)
    ])
    
    barcode = IntegerField('Código de barras', [
        validators.Optional()
    ])

    stock = IntegerField('Stock disponible', [
        validators.DataRequired(message="El stock es requerido")
    ], default=0)

    picture = FileField('Foto del producto', [
        validators.Optional()
    ])

    status = HiddenField('Estatus', default='Activo')

    price_men = DecimalField('Precio de menudeo', [
        validators.DataRequired(message="El precio de menudeo es requerido")
    ], places=2)
    
    price_may = DecimalField('Precio de mayoreo', [
        validators.DataRequired(message="El precio de mayoreo es requerido")
    ], places=2)

    presentation = StringField('Presentación (Ej: Botella, Caja)', [
        validators.DataRequired(message="La presentación es requerida"),
        validators.Length(max=50)
    ])
