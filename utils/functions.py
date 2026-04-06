from flask import request
from flask_login import current_user
from datetime import datetime
from models import mongo
from sqlalchemy import inspect
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64
import re

def parse_gs1_128(barcode_raw):
    """
    Descompone la cadena del escáner en datos de negocio.
    Ejemplo entrada: 010000001000000210LOT2024A
    """
    data = {
        'producto_id': None,
        'presentacion_id': None,
        'lote': None,
        'error': None
    }
    
    try:
        # 1. Extraer GTIN (AI 01 ocupa los siguientes 14 dígitos)
        if barcode_raw.startswith('01'):
            gtin_completo = barcode_raw[2:16]
            # Según nuestra lógica anterior: 7 dígitos prod, 7 dígitos pres
            data['producto_id'] = int(gtin_completo[:7])
            data['presentacion_id'] = int(gtin_completo[7:])
            
            # 2. Extraer Lote (AI 10 es lo que sigue después de la posición 16)
            if '10' in barcode_raw[16:18]:
                data['lote'] = barcode_raw[18:]
            else:
                # Si el código es variable, buscamos el identificador 10
                match_lote = re.search(r'10(.+)', barcode_raw[16:])
                if match_lote:
                    data['lote'] = match_lote.group(1)
        else:
            data['error'] = "Formato GS1-128 no reconocido (Falta AI 01)"
            
    except Exception as e:
        data['error'] = f"Error al procesar código: {str(e)}"
        
    return data

def generar_gs1_128(producto_id, presentacion_id, lote_nombre):
    # Estructura simplificada GS1-128:
    # (01) ID_PRODUCTO_PRES (14 chars) + (10) LOTE (Variable)
    
    # Rellenamos con ceros para cumplir los 14 dígitos del GTIN (AI 01)
    gtin = f"{producto_id:07d}{presentacion_id:07d}" 
    
    # Cadena completa siguiendo el estándar (sin paréntesis en la data real)
    # Los paréntesis se suelen usar solo en el texto visual
    codigo_data = f"01{gtin}10{lote_nombre}"
    
    # Crear el código de barras
    code128 = barcode.get('code128', codigo_data, writer=ImageWriter())
    
    # Guardar en memoria para enviarlo al HTML
    buffer = BytesIO()
    code128.write(buffer)
    
    # Convertir a Base64 para mostrar en el navegador
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return img_str

def object_to_dict(obj):
    """Convierte un objeto de SQLAlchemy en un diccionario de datos."""
    if obj is None:
        return None
    # Usamos el inspector de SQLAlchemy para obtener solo las columnas de la tabla
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}

def register_log_auto(accion, modulo, obj_puro_original=None, obj_puro_nuevo=None):
    """
    accion: 'Consulta' 'Busqueda' 'Creación', 'Actualización', 'Eliminación'
    modulo: Nombre del módulo (String)
    obj_puro_original: El objeto del modelo ANTES de los cambios
    obj_puro_nuevo: El objeto del modelo DESPUÉS de los cambios
    """

    """ Ejemplos de creaciond e los logs, recuerden que el nombre del modulo esta definido como variable en cada blueprint
    Ejemplo Creacion
    registrar_log_auto(
        accion="Creación", 
        modulo="Materia Prima", 
        obj_puro_nuevo=nueva_mp
    )

    Ejemplo Actualizacion
    registrar_log_auto(
        accion="Actualización", 
        modulo="Usuarios", 
        obj_puro_original=user_original, 
        obj_puro_nuevo=user
    )

    Ejemplo Eliminacion
    registrar_log_auto(
        accion="Eliminación", 
        modulo="Recetas", 
        obj_puro_original=receta_datos
    )

    registrar_log_auto(
        accion="Consulta", 
        modulo="Producción", 
        obj_puro_nuevo=orden 
    )
    """
    try:
        # 1. Convertir objetos a diccionarios automáticamente
        dict_antiguo = object_to_dict(obj_puro_original)
        dict_nuevo = object_to_dict(obj_puro_nuevo)
        
        # Obtener el ID afectado (buscando la primaria dinámicamente)
        id_afectado = None
        if obj_puro_nuevo:
            id_afectado = getattr(obj_puro_nuevo, inspect(obj_puro_nuevo).mapper.primary_key[0].name)
        elif obj_puro_original:
            id_afectado = getattr(obj_puro_original, inspect(obj_puro_original).mapper.primary_key[0].name)

        # 2. Construir descripción y detectar cambios
        cambios_detallados = {}
        descripcion = f"{accion} en {modulo}."

        if accion == 'Actualización' and dict_antiguo and dict_nuevo:
            lista_cambios = []
            for campo, valor_nuevo in dict_nuevo.items():
                valor_antiguo = dict_antiguo.get(campo)
                if valor_antiguo != valor_nuevo:
                    # No logueamos cambios en contraseñas por seguridad
                    if 'password' in campo.lower() or 'hash' in campo.lower():
                        lista_cambios.append(f"{campo}: [MODIFICADO]")
                    else:
                        lista_cambios.append(f"{campo}: '{valor_antiguo}' ➔ '{valor_nuevo}'")
                    
                    cambios_detallados[campo] = {"antes": valor_antiguo, "despues": valor_nuevo}
            
            if lista_cambios:
                descripcion = f"Editó {modulo}: " + " | ".join(lista_cambios)
        
        elif accion == 'Creación':
            descripcion = f"Creó nuevo registro en {modulo} (ID: {id_afectado})"
            cambios_detallados = dict_nuevo

        # 3. Guardar en MongoDB
        log_entry = {
            "evento": accion,
            "modulo": modulo,
            "usuario": current_user.username if current_user.is_authenticated else "Sistema",
            "usuario_id": current_user.id if current_user.is_authenticated else None,
            "descripcion": descripcion,
            "metadatos": {
                "ip": request.headers.get('X-Forwarded-For', request.remote_addr),
                "id_referencia": id_afectado,
                "detalles": cambios_detallados
            },
            "timestamp": datetime.utcnow()
        }

        mongo.db.logs_sistema.insert_one(log_entry)
        return True
    except Exception as e:
        print(f"Error en el log automático: {e}")
        return False