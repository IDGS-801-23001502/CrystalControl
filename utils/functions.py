from flask import request, current_app
from flask_login import current_user
from flask import current_app
from datetime import datetime
from models import mongo, db, Sales, SaleDetail,Producto, InventoryMovementPT
from sqlalchemy import inspect
import threading
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

def formatear_cadena_gs1_128(producto_id, presentacion_id, lote_nombre):
    """
    Genera la cadena de texto bajo el estándar GS1-128.
    AI 01: GTIN (14 chars)
    AI 10: Lote (Variable)
    """
    # Rellenamos con ceros para cumplir los 14 dígitos del GTIN
    gtin = f"{producto_id:07d}{presentacion_id:07d}" 
    
    # Retorna la cadena de datos real (sin paréntesis)
    return f"01{gtin}10{lote_nombre}"

def generar_imagen_barcode(codigo_data):
    """
    Convierte una cadena de texto en una imagen Code128 en formato Base64.
    """
    # Crear el código de barras
    code128 = barcode.get('code128', codigo_data, writer=ImageWriter())
    # Guardar en memoria
    buffer = BytesIO()
    code128.write(buffer)
    # Convertir a Base64
    return base64.b64encode(buffer.getvalue()).decode()


def generar_gs1_128(producto_id, presentacion_id, lote_nombre):
    # 1. Obtenemos la cadena estándar
    codigo_data = formatear_cadena_gs1_128(producto_id, presentacion_id, lote_nombre)
    
    # 2. La convertimos en imagen y la retornamos
    return generar_imagen_barcode(codigo_data)

def object_to_dict(obj):
    if obj is None: return None
    if isinstance(obj, dict): return obj # Soporte para dicts manuales
    
    try:
        from sqlalchemy import inspect
        from decimal import Decimal
        from datetime import datetime, date

        # Solo columnas reales de la tabla
        data = {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}
        
        # Limpieza profunda para MongoDB
        for key, value in data.items():
            if isinstance(value, Decimal):
                data[key] = float(value)
            elif isinstance(value, (datetime, date)):
                data[key] = value.isoformat()
        return data
    except Exception:
        # Si es una lista (como los detalles), la procesamos
        if isinstance(obj, list):
            return [object_to_dict(i) for i in obj]
        return str(obj)

# Esta es la función que realmente escribe en Mongo, corre en segundo plano
def _write_log_to_mongo(app, log_entry):
    with app.app_context(): # Necesitamos el contexto de la app para usar 'mongo'
        try:
            mongo.db.logs_sistema.insert_one(log_entry)
        except Exception as e:
            print(f"Error asíncrono en MongoDB: {e}")

def register_log_auto(accion, modulo, obj_puro_original=None, obj_puro_nuevo=None):
    try:
        # --- 1. PROCESAMIENTO INMEDIATO (Síncrono) ---
        # Convertimos a dict y extraemos IDs AHORA, antes de que el objeto cambie o se pierda
        dict_antiguo = object_to_dict(obj_puro_original) if obj_puro_original else None
        dict_nuevo = object_to_dict(obj_puro_nuevo) if obj_puro_nuevo else None
        
        id_afectado = None
        if dict_nuevo and 'id' in dict_nuevo:
            id_afectado = dict_nuevo['id']
        elif dict_antiguo and 'id' in dict_antiguo:
            id_afectado = dict_antiguo['id']

        # Extraer datos de la request AHORA (luego el objeto request muere)
        ip_cliente = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        # Extraer datos del usuario AHORA
        try:
            u_id = getattr(current_user, 'id', None)
            u_name = getattr(current_user, 'username', 'Sistema')
        except:
            u_id = id_afectado if accion == 'Login' else None
            u_name = "Procesando"

        # --- 2. CONSTRUIR DESCRIPCIÓN ---
        cambios_detallados = {}
        descripcion = f"{accion} en {modulo}."

        if accion == 'Actualización' and dict_antiguo and dict_nuevo:
            lista_cambios = []
            for campo, valor_nuevo in dict_nuevo.items():
                valor_antiguo = dict_antiguo.get(campo)
                if valor_antiguo != valor_nuevo:
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
        elif accion == 'Login':
            descripcion = f"Inicio de sesión exitoso"
            cambios_detallados = {"username": dict_nuevo.get('username') if dict_nuevo else "N/A"}

        # --- 3. PREPARAR EL DOCUMENTO ---
        log_entry = {
            "evento": accion,
            "modulo": modulo,
            "usuario": u_name,
            "usuario_id": u_id,
            "descripcion": descripcion,
            "metadatos": {
                "ip": ip_cliente,
                "id_referencia": id_afectado,
                "detalles": cambios_detallados
            },
            "timestamp": datetime.utcnow()
        }

        # --- 4. LANZAR HILO ASÍNCRONO ---
        # Obtenemos la instancia real de la app para el contexto
        app_instance = current_app._get_current_object()
        
        thread = threading.Thread(target=_write_log_to_mongo, args=(app_instance, log_entry))
        thread.start() # El hilo se encarga de insertar, la función principal termina YA.

        return True
    except Exception as e:
        print(f"Error al preparar log: {e}")
        return False
    
def sale_out(sale_id, status = 2):
    try:
        #Obtener la venta y sus detalles
        venta = Sales.query.get(sale_id)
        if not venta:
            return False, "Venta no encontrada."

        detalles = SaleDetail.query.filter_by(id_sale=venta.id).all()
        if not detalles:
            return False, "La venta no tiene productos registrados en el detalle."

        for item in detalles:
            producto = Producto.query.get(item.id_product)
            if not producto:
                continue
            # Guardamos estado original para el log de auditoría
            stock_anterior = producto.stock or 0
            
            #Actualizar Stock en la tabla Producto
            cantidad_vendida = item.lot
            producto.stock = stock_anterior - cantidad_vendida

            #Crear el movimiento de Inventario PT
            nuevo_movimiento = InventoryMovementPT(
                product_id=producto.id,
                type=2,           
                reason=2,         
                quantity=cantidad_vendida,
                resulting_stock=producto.stock,
                user_id=current_user.id if current_user.is_authenticated else None,
                timestamp=datetime.now(),
                status = status
            )
            db.session.add(nuevo_movimiento)

            #Registrar en el Log de Auditoría
            register_log_auto(
                accion="Actualización",
                modulo="Inventario PT (Venta)",
                obj_puro_original=None,
                obj_puro_nuevo=producto
            )
        db.session.commit()
        return True, f"Inventario actualizado para la venta {venta.folio}"

    except Exception as e:
        db.session.rollback()
        print(f"Error al procesar salida de inventario: {e}")
        return False, str(e)