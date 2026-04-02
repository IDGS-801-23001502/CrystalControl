from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, EmailField, HiddenField, DecimalField, TextAreaField, FieldList, FormField
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

# --- SUB-FORMULARIOS PARA FILAS DINÁMICAS ---

class FormRecipeDetail(FlaskForm):
    """Formulario para una fila de material/insumo"""
    material_id = SelectField('Material', coerce=int, validators=[
        validators.DataRequired(message="Selecciona un material")
    ])
    required_quantity = DecimalField('Cantidad', [
        validators.InputRequired(message="Requerido")
    ], places=2)
    unit_med = SelectField('Unidad', coerce=int, choices=[
        (1, 'Kilos'),
        (2, 'Litros'),
        (3, 'Piezas')
    ])

class FormRecipeStep(FlaskForm):
    """Formulario para una fila de pasos de la receta"""
    step_order = IntegerField('Orden', [validators.Optional()])
    stage_name = StringField('Etapa', [validators.Length(max=50)])
    step_description = TextAreaField('Descripción')
    estimated_time = IntegerField('Minutos', [validators.NumberRange(min=1)])
    process_type = SelectField('Tipo Proceso', coerce=int, choices=[
        (1, 'Mezclado'),
        (2, 'Envasado'),
        (3, 'Reposo')
    ])

# --- FORMULARIO PRINCIPAL ---

class FormRecipe(FlaskForm):
    id = HiddenField('id')
    
    
    final_name = StringField('Nombre de la Receta', [
        validators.DataRequired(message="El nombre es obligatorio"),
        validators.Length(min=3, max=100)
    ])
    
    product_id = SelectField('Producto Final', coerce=int, validators=[
        validators.DataRequired(message="Selecciona el producto que resulta de esta receta")
    ])
    
    general_instructions = TextAreaField('Instrucciones Generales')
    
    estimated_time = IntegerField('Tiempo Total (min)', [validators.Optional()])
    
    expected_utility = DecimalField('Utilidad Esperada (%)', [validators.Optional()], places=2)
    
    estimated_waste = DecimalField('Merma Estimada (%)', [validators.Optional()], places=2)
    
    produced_quantity = IntegerField('Cantidad a Producir (Lote)', [validators.Optional()])

    unit_med = SelectField('Unidad de Medida del Lote', coerce=int, choices=[
        (1, 'Kilos'),
        (2, 'Litros'),
        (3, 'Piezas')
    ])
    
    status = HiddenField('Estatus', default=1)

    # Listas dinámicas
    # min_entries=1 asegura que al menos aparezca una fila al cargar
    materials = FieldList(FormField(FormRecipeDetail), min_entries=1)
    steps = FieldList(FormField(FormRecipeStep), min_entries=1)