from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, EmailField, HiddenField, DecimalField, DateTimeLocalField, SubmitField, DateField
from wtforms import DecimalField, StringField, PasswordField, SelectField, BooleanField, EmailField, HiddenField, FileField, IntegerField, TextAreaField, FieldList,FormField
from wtforms import validators, ValidationError

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
    unidad_medida = SelectField('Unidad de Medida', coerce=int, choices=[
        (1, 'Kilos'),
        (2, 'Litros'),
        (3, 'Galones'),
        (4, 'Pieza')
    ], validators=[
        validators.DataRequired(message="La unidad de medida es obligatoria")
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
    
    category = SelectField('Categoria', choices=[
        ('Cuidado del Hogar', 'Cuidado del Hogar'),
        ('Lavanderia', 'Lavanderia'),
        ('Cocina', 'Cocina'),
        ('Cuidado Personal', 'Cuidado Personal')
    ])
    cant_may = IntegerField('Pzas para Mayoreo', [
        validators.Optional(),
        validators.NumberRange(min=0, message="Las piezas para venta a mayoreo debe ser positiva")  
    ])
    stock = IntegerField('Stock disponible', [
        validators.Optional(),
        validators.Disabled()
    ], default=0)
    picture = FileField('Foto del producto', [
        validators.Optional()
    ])
    status = HiddenField('Estatus', default='Activo')
    price_men = DecimalField('Precio de menudeo', [
        validators.DataRequired(message="El precio de menudeo es requerido"),
        validators.NumberRange(min=0, message="El precio de menudeo no puede ser negativo")
    ], places=2)
    
    price_may = DecimalField('Precio de mayoreo', [
        validators.DataRequired(message="El precio de mayoreo es requerido"),
        validators.NumberRange(min=0, message="El precio de menudeo no puede ser negativo")
    ], places=2)
    presentation = StringField('Presentación (Ej: Botella, Caja)', [
        validators.DataRequired(message="La presentación es requerida"),
        validators.Length(max=50)
    ])
    unit_size = DecimalField('Tamaño por Unidad', [
        validators.DataRequired(message="El tamaño por unidad es requerido"),
        validators.NumberRange(min = 0, message="La cantidad no puede ser negativa")
        ])
    unit_type = SelectField('Unidad Base', choices=[
            (1, 'Mililitros (ml) — líquidos'),
            (2, 'Gramos (g) — sólidos')
        ], coerce=int
    )

class PurchaseItemForm(FlaskForm):
    material_id = SelectField('Material', coerce=int, validators=[validators.DataRequired()])
    quantity = DecimalField('Cantidad', validators=[validators.DataRequired()])
    class Meta:
        csrf = False

# Este es el formulario principal
class PurchaseRequestForm(FlaskForm):
    items = FieldList(FormField(PurchaseItemForm), min_entries=1)
    admin_notes = TextAreaField('Notas')

class AnalysisForm(FlaskForm):
    status = SelectField('Decisión Final', coerce=int, validators=[validators.DataRequired()])
    analysis_notes = TextAreaField('Notas de Análisis')

# --- SUB-FORMULARIOS PARA FILAS DINÁMICAS ---
class FormRecipeDetail(FlaskForm):
    """Formulario para una fila de material/insumo"""
    material_id = SelectField('Material', coerce=int, validators=[
        validators.DataRequired(message="Selecciona un material")
    ])
    required_quantity = DecimalField('Cantidad', [
        validators.InputRequired(message="Requerido")
    ], places=2)
    # unit_med ha sido eliminado de aquí porque se traerá del modelo MateriaPrima

class FormRecipeStep(FlaskForm):
    """Formulario para una fila de pasos de la receta"""
    step_order = IntegerField('Orden', [validators.Optional()])
    stage_name = StringField('Etapa', [validators.Length(max=100)])
    step_description = TextAreaField('Descripción')
    estimated_time = IntegerField('Minutos', [validators.NumberRange(min=1)])
    process_type = SelectField('Tipo Proceso', coerce=int, choices=[
        # PREPARACIÓN Y MEZCLA
        (1,  'Mezclado / Homogeneización'),
        (2,  'Disolución (Sólido a Líquido)'),
        (3,  'Reacción Química (Control de Temp/pH)'),
        (4,  'Emulsificación'),
        # ACABADO
        (5,  'Reposo / Desaireación'),
        (6,  'Filtrado'),
        (7,  'Control de Calidad (Muestreo)'),
        # ACONDICIONAMIENTO
        (8,  'Envasado'),
        (9,  'Etiquetado y Codificado'),
        (10, 'Paletizado / Emplayado'),
        # ESPECIALES
        (11, 'Dilución de Concentrados'),
        (12, 'Neutralización'),
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
        (3, 'Galones'),
        (4, 'Pieza')
    ])
    
    status = HiddenField('Estatus', default=1)
    # Listas dinámicas
    # min_entries=1 asegura que al menos aparezca una fila al cargar
    materials = FieldList(FormField(FormRecipeDetail), min_entries=0)
    steps = FieldList(FormField(FormRecipeStep), min_entries=1)

class FormInventoryMovementItem(FlaskForm):
    material_id = SelectField('Materia Prima', coerce=int, validators=[
        validators.DataRequired(message="Seleccione material")
    ])
    movement_type = SelectField('Tipo', coerce=int, choices=[
        (1, 'Entrada'),
        (2, 'Salida')
    ], validators=[validators.DataRequired()])
    reason = SelectField('Motivo', coerce=int, choices=[
        (3, 'Ajuste'),
        (1, 'Merma')
    ], validators=[validators.DataRequired()])
    quantity = DecimalField('Cantidad', [
        validators.InputRequired(message="Requerido"),
        validators.NumberRange(min=0.01)
    ], places=2)
    class Meta:
        csrf = False # se deshabilita CSRF interno para las filas de la lista

class FormBulkInventoryMovement(FlaskForm):
    # Lista dinámica de movimientos
    movements = FieldList(FormField(FormInventoryMovementItem), min_entries=1)

class FormProductionOrder(FlaskForm):
    id = HiddenField('id')
    
    folio = StringField('Folio de Orden', render_kw={'readonly': True})
    
    recipe_id = SelectField('Seleccionar Receta', coerce=int, validators=[
        validators.DataRequired(message="Debe seleccionar una receta activa")
    ])
    
    requested_quantity = DecimalField('Cantidad a Producir', [
        validators.InputRequired(message="La cantidad es obligatoria"),
        validators.NumberRange(min=1, message="La cantidad debe ser mayor a 0")
    ])
    
    unit_med = IntegerField('Unidad de Medida')
    
    operator_id = HiddenField('Operador Responsable')
    
    scheduled_date = DateTimeLocalField('Fecha De solicitud', 
        format='%Y-%m-%dT%H:%M',
        validators=[validators.Optional()]
    )
    status = HiddenField('Estatus', default=2)

class FormCloseProductionOrder(FlaskForm):
    # Campos informativos (Readonly) para que el operador compare
    requested_quantity = DecimalField('Cantidad Programada', render_kw={'readonly': True})
    
    # --- DATOS DE PRODUCCIÓN REAL ---
    produced_qty = DecimalField('Cantidad Final Obtenida', [
        validators.DataRequired(message="Debe ingresar la cantidad resultante"),
        validators.NumberRange(min=0, message="La cantidad no puede ser negativa")
    ], places=2)
    real_waste = DecimalField('Merma Real Detectada', [
        validators.DataRequired(message="Ingrese la merma (puede ser 0)"),
        validators.NumberRange(min=0, message="La merma no puede ser negativa")
    ], places=2, default=0.00)
    # --- DATOS DEL LOTE (TRAZABILIDAD) ---
    expiry_date = DateField('Fecha de Caducidad', 
        format='%Y-%m-%d',
        validators=[validators.DataRequired(message="Indique la fecha de vencimiento")]
    )
    location = StringField('Ubicación en Almacén', [
        validators.DataRequired(message="Indique el pasillo o estante"),
        validators.Length(max=50)
    ], default="Almacén de Cuarentena")
    notes = TextAreaField('Observaciones de la Producción')

class FormQualityCheck(FlaskForm):
    # El ID del lote es oculto
    lot_id = HiddenField('lot_id')
    
    # Parámetros comunes en industria química (ajusta según tu producto)
    ph_level = StringField('Nivel de pH', [validators.DataRequired()])
    density = StringField('Densidad', [validators.DataRequired()])
    appearance = SelectField('Aspecto Visual', choices=[
        ('Correcto', 'Correcto'),
        ('Turbio', 'Turbio'),
        ('Color Incorrecto', 'Color Incorrecto')
    ])
    
    # Decisión final
    is_approved = SelectField('Dictamen Final', coerce=int, choices=[
        (1, 'Aprobado (Disponible para venta)'),
        (0, 'Rechazado (No disponible para venta)')
    ])
    
    comments = TextAreaField('Notas de Laboratorio')

# --- VENTAS ONLINE --- #
class AddToCartForm(FlaskForm):
    id_product = HiddenField('ID Producto', validators=[validators.DataRequired()])
    # Ahora el precio y presentación vendrán de esta selección
    id_presentacion_precio = SelectField('Selecciona Presentación', coerce=int, validators=[validators.DataRequired()])
    quantity = IntegerField('Cantidad', validators=[validators.DataRequired(), validators.NumberRange(min=1)], default=1)
    submit = SubmitField('Añadir al Carrito')
# Validación personalizada
    def validate_quantity(self, field):
        from models import Producto # Importa tu modelo aquí o arriba
        producto = Producto.query.get(self.id_product.data)
        if producto and field.data > producto.stock:
            raise ValidationError(f'Solo quedan {producto.stock} unidades disponibles.')


class CheckoutForm(FlaskForm):
    # Para la dirección de envío y completar la tabla 'Ventas'
    shipping_address = StringField('Dirección de Envío', validators=[validators.DataRequired(), validators.Length(max=50)])
    # El status se manejará internamente (1: Solicitada / 2: Esperando pago)
    submit = SubmitField('Confirmar Pedido')

class PaymentForm(FlaskForm):
    # Para la tabla 'ventas_pagos'
    id_sale = HiddenField('ID Venta')
    payment_method = SelectField('Método de Pago', choices=[
        (1, 'Efectivo'), (2, 'Tarjeta Débito'), (3, 'Tarjeta Crédito'),
        (4, 'Transferencia'), (5, 'Clip/Terminal'), (6, 'Crédito tienda')
    ], coerce=int)
    paid_amount = DecimalField('Monto a Pagar', validators=[validators.DataRequired()])
    reference = StringField('Referencia (opcional)')
    submit = SubmitField('Finalizar Pago')

class FormInventoryAdjustment(FlaskForm):
    product_id = SelectField('Producto', coerce=int, validators=[
        validators.DataRequired(message="Debe seleccionar un producto")
    ])
    type = SelectField('Tipo de Movimiento', coerce=int, choices=[
        (1, 'Entrada (+)'),
        (2, 'Salida (-)')
    ], validators=[validators.DataRequired()])
    
    quantity = DecimalField('Cantidad', [
        validators.InputRequired(message="La cantidad es obligatoria"),
        validators.NumberRange(min=0.1, message="La cantidad debe ser mayor a 0")
    ], places=2)
    
    reason = SelectField('Motivo', coerce=int, choices=[
        (3, 'Ajuste de Inventario'),
        (1, 'Merma / Daño')
    ], validators=[validators.DataRequired()])
    
    notes = TextAreaField('Observaciones', [
        validators.Optional(),
        validators.Length(max=255)
    ])

class AddressForm(FlaskForm):
    direccion = StringField('Dirección Completa', validators=[
        validators.DataRequired(message="La dirección es obligatoria"),
        validators.Length(min=10, max=255)
    ])
    telefono = StringField('Teléfono de contacto', validators=[
        validators.Optional(),
        validators.Length(max=20)
    ])
    submit = SubmitField('Guardar y continuar')

class FormEditProfile(FlaskForm):
    email = EmailField('Correo Electrónico', [validators.DataRequired(), validators.Email()])
    telefono = StringField('Teléfono', [validators.Optional(), validators.Length(max=20)])
    submit = SubmitField('Actualizar Perfil')

class FormChangePassword(FlaskForm):
    old_password = PasswordField('Contraseña Actual', [validators.DataRequired()])
    new_password = PasswordField('Nueva Contraseña', [
        validators.DataRequired(),
        validators.Length(min=8),
        validators.EqualTo('confirm', message='Las contraseñas deben coincidir')
    ])
    confirm = PasswordField('Repite la Nueva Contraseña')
    submit = SubmitField('Cambiar Contraseña')