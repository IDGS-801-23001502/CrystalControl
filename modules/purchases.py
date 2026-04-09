from flask import Blueprint, render_template, request, g, redirect, url_for, flash, make_response
from flask_login import current_user
from models import db, Purchase, PurchaseDetail, Raw_Material, Supplier, Raw_Material_Supplier, InventoryMovementPT as RawMaterialMovement
from utils.decorators import roles_accepted
from utils.functions import register_log_auto
from forms import PurchaseRequestForm, AnalysisForm
from datetime import date, datetime
import copy
from decimal import Decimal

module = 'purchases'

purchases_bp = Blueprint(
    module, 
    __name__,
    template_folder='templates',
    static_folder='static'
)

# 1. LIST VIEW (Dashboard de Compras)
@purchases_bp.route("/")
@roles_accepted('Administrador','Compras')
def index():
    purchases = Purchase.query.order_by(Purchase.request_date.desc()).all()
    register_log_auto("Consulta", module, obj_puro_nuevo=purchases)
    return render_template("purchases/list.html", purchases=purchases)

# 2. CREATE REQUEST (Paso 1: Solicitud inicial)
@purchases_bp.route("/demand", methods=['GET', 'POST'])
@roles_accepted('Administrador', 'Almacenista')
def demand():
    form = PurchaseRequestForm()
    try:
        materials = [(m.id, m.name) for m in Raw_Material.query.all()]
        for item in form.items:
            item.material_id.choices = materials
    except Exception as e:
        print(f"Error al cargar materiales: {e}")
        materials = []

    if form.validate_on_submit():
        try:
            # 1. Crear el encabezado de la compra
            new_purchase = Purchase(
                requester_id=current_user.id,
                request_date= date.today(),
                status=1  # Estatus Solicitud
            )
            db.session.add(new_purchase)
            
            # El flush es necesario para obtener el ID antes del commit final
            db.session.flush()

            # 2. Crear los detalles
            for item in form.items:
                detail = PurchaseDetail(
                    purchase_id=new_purchase.id,
                    material_id=item.material_id.data,
                    demand_quantity=item.quantity.data,
                    approved_quantity=0.0,
                    unit_price=0.0,
                    status=1
                )
                db.session.add(detail)
            # Si todo salió bien, guardamos permanentemente
            db.session.commit()

            #Registro de logs
            detalles_audit = []
            for d in new_purchase.details:
                detalles_audit.append({
                    "material": d.material.name, # ¡Incluso puedes guardar el nombre!
                    "cantidad": float(d.demand_quantity),
                    "status": d.status
                })

            datos_completos = {
                "id": new_purchase.id,
                "folio": new_purchase.folio,
                "detalles_articulos": detalles_audit # Metemos la lista aquí
            }

            register_log_auto(
                accion="Creación", 
                modulo="Compras", 
                obj_puro_nuevo=datos_completos
            )

            flash("Solicitud de compra generada con éxito", "success")
            return redirect(url_for('purchases.index'))
        except Exception as e:
            # Si algo falla (como el id_unidad null), deshacemos todo lo pendiente
            db.session.rollback()
            print(f"Error al registrar compra: {e}")
            flash("Hubo un error al procesar la solicitud. Verifica los datos.", "danger")
    return render_template('purchases/demand.html', form=form)


@purchases_bp.route("/analyze/<int:id>", methods=['GET', 'POST'])
@roles_accepted('Administrador', 'Compras')
def analyze_demand(id):
    purchase = Purchase.query.get_or_404(id)
    form = AnalysisForm()
    
    # Definir opciones: 2 es "En Análisis/Aprobado", 7 es "Cancelado" según tu modelo
    form.status.choices = [(2, 'Aprobar para Comparativa'), (7, 'Rechazar Solicitud')]

    if form.validate_on_submit():
        try:
            purchase_original = copy.copy(purchase)
            # 1. Actualizar encabezado
            purchase.status = form.status.data
            # Si decides añadir el campo de notas al modelo Purchase en el futuro:
            purchase.admin_notes = form.analysis_notes.data 

            # 2. Actualizar cada item del detalle
            # 2 es Aprobado, 3 es Rechazado
            new_item_status = 2 if form.status.data == 2 else 3
            
            for detail in purchase.details:
                detail.status = new_item_status
                # Si se aprueba, la cantidad aprobada inicia igual a la solicitada
            db.session.commit()
            register_log_auto(
                accion="Actualización",
                modulo="Análisis de Compras",
                obj_puro_original=purchase_original,
                obj_puro_nuevo=purchase
            )
            flash(f"Dictamen guardado para el Folio: {purchase.folio}", "success")
            return redirect(url_for('purchases.index'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error en el commit de análisis: {e}")
            flash("Error interno al procesar el dictamen.", "danger")

    return render_template("purchases/analyze.html", purchase=purchase, form=form)

# 4. COMPARISON (Paso 3: Selección de proveedores e histórico)
@purchases_bp.route("/compare/<int:id>", methods=['GET', 'POST'])
@roles_accepted('Administrador', 'Compras')
def compare_suppliers(id):
    purchase = Purchase.query.get_or_404(id)

    if request.method == 'POST':
        try:
            # 1. PROCESAR CADA DETALLE DE LA COMPRA
            purchase.generate_date = date.today()
            for detail in purchase.details:
                # Obtener el ID del proveedor ganador desde el Radio Button
                winner_id = request.form.get(f'winner_{detail.id}')
                
                if not winner_id:
                    continue # Si no se seleccionó ganador para este item, saltar
                
                winner_id = int(winner_id)
                # 2. ACTUALIZAR PRECIOS HISTÓRICOS DE TODOS LOS PROVEEDORES COTIZADOS
                # Recorremos los inputs de precio para este material específico
                for key, value in request.form.items():
                    if key.startswith(f'price_{detail.id}_'):
                        parts = key.split('_')
                        sup_id = int(parts[2])
                        nuevo_precio = float(value or 0)

                        # Actualizar la tabla de relación (Catálogo)
                        relacion = Raw_Material_Supplier.query.filter_by(
                            id_material=detail.material_id, 
                            id_supplier=sup_id
                        ).first()
                        
                        if relacion:
                            relacion.price = nuevo_precio

                # 3. ASIGNAR DATOS FINALES AL GANADOR EN EL DETALLE DE COMPRA
                # Tomamos los valores específicos del proveedor que marcaste como ganador
                qty_ganador = float(request.form.get(f'qty_{detail.id}_{winner_id}', 0))
                price_ganador = float(request.form.get(f'price_{detail.id}_{winner_id}', 0))
                days_ganador = int(request.form.get(f'days_{detail.id}_{winner_id}', 3))
                
                detail.supplier_id = winner_id
                detail.approved_quantity = qty_ganador
                detail.unit_price = price_ganador
                detail.delivery_days = days_ganador
                detail.status = 2  # Estado: Aprobado / Listo para Orden

            # 4. ACTUALIZAR ESTADO GENERAL DE LA COMPRA
            purchase.status = 4  # 4: Orden Generada
            db.session.commit()
            
            flash(f"Orden de compra {purchase.folio} generada y precios actualizados.", "success")
            return redirect(url_for('purchases.index'))

        except Exception as e:
            db.session.rollback()
            print(f"Error en Comparativa: {e}")
            flash("Error al procesar la comparativa de precios.", "danger")

    # --- LÓGICA PARA EL GET ---
    # Preparamos un diccionario con las ofertas de proveedores por cada material
    offers_by_detail = {}
    for detail in purchase.details:
        # Buscamos en la tabla de relación materia_prima_proveedor
        suppliers_relation = Raw_Material_Supplier.query.filter_by(id_material=detail.material_id).all()
        
        offers_list = []
        for rel in suppliers_relation:
            # Traemos el nombre del proveedor desde la tabla Proveedores
            prov = Supplier.query.get(rel.id_supplier)
            offers_list.append({
                'supplier_id': rel.id_supplier,
                'supplier_name': prov.name if prov else "Desconocido",
                'lot':rel.lot,
                'price': rel.price # Este es el precio histórico de referencia
            })
        
        offers_by_detail[detail.id] = offers_list

    return render_template("purchases/compare.html", 
                           purchase=purchase, 
                           offers_by_detail=offers_by_detail)

# 5. FINALIZE ORDER Y Ponerla en transito (Paso 4: Generar Orden de Compra final y Paso 5: La mercancía ha sido despachada)
@purchases_bp.route("/order/manage/<int:id>", methods=['GET', 'POST'])
@roles_accepted('Administrador', 'Compras')
def manage_generated_order(id):
    purchase = Purchase.query.get_or_404(id)
    
    # --- LÓGICA PARA CONFIRMAR ENVÍO (POST) ---
    if request.method == 'POST':
        try:
            # Cambiamos a Estatus 5: En Tránsito
            purchase.status = 5
            
            # También actualizamos el estatus de los ítems individuales a 4 (Recibiendo/En camino) 
            for detail in purchase.details:
                detail.status = 4 
                
            db.session.commit()
            flash(f"La orden {purchase.folio} ha sido marcada 'En Tránsito'. El almacén ya puede visualizarla.", "info")
            return redirect(url_for('purchases.index'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error al formalizar envío: {e}")
            flash("Error al actualizar el estatus de la orden.", "danger")
            return redirect(url_for('purchases.manage_generated_order', id=id))

    # --- LÓGICA PARA VISUALIZAR LA ORDEN (GET) ---
    # Calculamos el total sumando (cantidad_aprobada * precio_unitario_final)
    # Usamos float() porque tus campos son Numeric (Decimal)
    total_order = sum(
        float(d.approved_quantity or 0) * float(d.unit_price or 0) 
        for d in purchase.details
    )
    
    return render_template(
        "purchases/order_view.html", 
        purchase=purchase, 
        total_order=total_order
    )

@purchases_bp.route("/view/<int:id>")
@roles_accepted('Administrador', 'Almacenista', 'Compras')
def view_purchase_detail(id):
    purchase = Purchase.query.get_or_404(id)
    total_orden = float(sum((d.unit_price or 0) * (d.approved_quantity or d.demand_quantity) for d in purchase.details))
    total_con_iva = total_orden * 1.16
    return render_template("purchases/view_detail.html", 
                           purchase=purchase, 
                           total_orden=total_orden,
                           total_con_iva=total_con_iva)

@purchases_bp.route("/scheduled-deliveries")
@roles_accepted('Administrador', 'Almacenista', 'Compras')
def scheduled_deliveries():
    # Filtramos por estatus 4 (Orden Generada), 5 (En Tránsito) o 8 (Entrega Incompleta)
    scheduled = Purchase.query.filter(Purchase.status.in_([4, 5,8])).order_by(Purchase.generate_date.desc()).all()
    return render_template("purchases/scheduled.html", purchases=scheduled)

@purchases_bp.route("/receive/<int:id>", methods=['GET'])
@roles_accepted('Administrador', 'Almacenista')
def receive_purchase_view(id):
    purchase = Purchase.query.get_or_404(id)
    
    # Solo se puede recibir si está en orden generada (4), tránsito (5) o incompleta (8)
    if purchase.status not in [4, 5, 8]:
        flash("Esta orden no está en un estado válido para recepción.", "warning")
        return redirect(url_for('purchases.scheduled_deliveries'))
        
    return render_template("purchases/receive.html", purchase=purchase)

@purchases_bp.route("/receive/confirm/<int:id>", methods=['POST'])
@roles_accepted('Administrador', 'Almacenista')
def confirm_reception(id):
    purchase = Purchase.query.get_or_404(id)
    
    try:
        for detail in purchase.details:
            # 1. SALTAR si ya está cerrado (Status 4)
            if detail.status == 4:
                continue

            # 2. CAPTURAR datos del formulario
            qty_received_str = request.form.get(f'receive_qty_{detail.id}', '0')
            qty_received = Decimal(qty_received_str) if qty_received_str else Decimal('0')
            status_input = request.form.get(f'status_{detail.id}') 

            # --- EL FILTRO CRÍTICO ---
            # Si la cantidad es 0 y NO es un reporte de 'dañado', 
            # ignoramos este registro completamente. No guardamos NADA en la DB.
            if qty_received <= 0 and status_input != 'dañado':
                continue
            # -------------------------

            # 3. Lógica de cálculo 
            total_a_comprar = Decimal(str(detail.approved_quantity))
            
            if status_input == 'completo':
                pendiente_para_db = Decimal('0.00')
                detail.status = 4 
            elif status_input == 'dañado':
                pendiente_para_db = total_a_comprar 
                qty_received = Decimal('0.00')
            else: # CASO PARCIAL
                pendiente_para_db = total_a_comprar - qty_received
                detail.status = 5  # <--- AQUÍ: Marcamos como PARCIAL / PENDIENTE

            # 4. INSERTAR en movimientosinventariomp
            # Solo llegamos aquí si pasó el filtro de arriba
            new_move = RawMaterialMovement(
                material_id=detail.material_id,
                movement_type=1,
                reason=4,
                quantity=qty_received,
                pending_quantity=max(Decimal('0.00'), pendiente_para_db),
                status=1 if status_input == 'completo' else 2,
                user_id=current_user.id,
                timestamp=datetime.utcnow()
            )
            db.session.add(new_move)

            # 6. Actualizar stock del material
            if status_input != 'dañado' and qty_received > 0:
                detail.material.real_stock += qty_received
                detail.material.available_stock += qty_received

        # 7. Estatus de la compra: 6=Recibido completo, 8=Incompleto
        purchase.status = 6 if all(d.status == 4 for d in purchase.details) else 8

        db.session.commit()
        flash(f"Movimiento registrado. Folio: {purchase.folio}", "success")
        return redirect(url_for('purchases.scheduled_deliveries'))

    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('purchases.receive_purchase_view', id=id))