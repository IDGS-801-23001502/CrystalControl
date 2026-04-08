from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from models import db, Recipe, RecipeDetail, RecipeStep, Producto, Raw_Material, Raw_Material_Supplier, ProductoPresentacionPrecio
from forms import FormRecipe, FormRecipeDetail, FormRecipeStep
from datetime import datetime

module = 'recipes'

recipes_bp = Blueprint(
    module, 
    __name__,
    template_folder='templates',
    static_folder='static')

@recipes_bp.route('/')
def index():
    # Seguimos ordenando por los primeros 8 caracteres (REC-XXXX)
    # 1 = Activa, 0 = Inactiva (Baja manual), 2 = Versionada (Histórica)
    all_recipes = Recipe.query.order_by(db.func.left(Recipe.unique_code, 8).asc()).all()
    
    return render_template('recipes/list.html', all_recipes=all_recipes)



@recipes_bp.route('/add_recipe', methods=['GET', 'POST'])
def add_recipe():
    materiales_db = Raw_Material.query.filter_by(estatus='Activo').all()
    material_choices = [(m.id, m.name) for m in materiales_db]
    # Esta línea es la UNICA que agregamos para que tu JS funcione
    materiales_info = {m.id: m.nombre_unidad for m in materiales_db} 

    product_choices = [(p.id, p.name) for p in Producto.query.filter_by(status='Activo').all()]
    process_choices = [(1, 'Mezclado'), (2, 'Envasado'), (3, 'Reposo')]

    form = FormRecipe()
    form.product_id.choices = product_choices
    
    for detail_form in form.materials:
        detail_form.material_id.choices = material_choices
        
    for step_form in form.steps:
        step_form.process_type.choices = process_choices

    if form.validate_on_submit():
        if not form.materials.data or len(form.materials.data) == 0:
            flash("Debes agregar al menos una materia prima a la receta.", "danger")
            return render_template('recipes/add.html', form=form, materiales_info=materiales_info)
        try:
            cant_lote = float(form.produced_quantity.data or 0)
            unidad_lote = int(form.unit_med.data or 1)

            total_production_cost = 0
            for mat in form.materials.data:
                best_price = Raw_Material_Supplier.query.filter_by(id_material=mat['material_id']).order_by(Raw_Material_Supplier.price.asc()).first()
                if best_price:
                    cost_unit = (float(mat['required_quantity']) / float(best_price.lot)) * float(best_price.price)
                    total_production_cost += cost_unit

            extra_unidad = {2: 0.3, 1: 0.2, 3: 0.05}.get(unidad_lote, 0.0)
            merma_acumulada = 1.0 + (len(form.materials.data) * 0.2) + extra_unidad
            
            for s in form.steps.data:
                t_proc = int(s.get('process_type') or 1)
                merma_acumulada += {1: 1.2, 2: 0.5, 3: 0.1}.get(t_proc, 0.1)

            factor = 1.25 if 0 < cant_lote < 15 else (0.90 if cant_lote > 50 else 1.0)
            final_waste = merma_acumulada * factor

            prod_precio = ProductoPresentacionPrecio.query.filter_by(id_producto=form.product_id.data).first()
            precio_v = float(prod_precio.price_men if prod_precio else 0)
            venta_lote = precio_v * cant_lote
            
            utilidad_calc = form.expected_utility.data or 30.0
            if venta_lote > 0 and not form.expected_utility.data:
                utilidad_calc = ((venta_lote - total_production_cost - 35.0) / venta_lote) * 100

            # --- GUARDADO ---
            recipe_data = {k: v for k, v in form.data.items() if k not in ['materials', 'steps', 'id', 'csrf_token', 'unique_code']}
            new_recipe = Recipe(**recipe_data)
            new_recipe.unique_code = "TEMP"
            new_recipe.status = 1
            new_recipe.estimated_time = sum(int(s.get('estimated_time') or 0) for s in form.steps.data)
            new_recipe.estimated_waste = final_waste
            new_recipe.expected_utility = utilidad_calc
            
            db.session.add(new_recipe)
            db.session.flush()

            for m in form.materials.data:
                m.pop('csrf_token', None)
                m.pop('unit_med', None) # IMPORTANTE: Evita el error de columna inexistente
                db.session.add(RecipeDetail(**m, recipe_id=new_recipe.id))
            
            for s in form.steps.data:
                s.pop('csrf_token', None)
                desc = s.pop('step_description', None)
                db.session.add(RecipeStep(**s, recipe_id=new_recipe.id, description=desc))

            db.session.commit()
            flash("Receta registrada con éxito", "success")
            return redirect(url_for('recipes.index'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")

    return render_template('recipes/add.html', form=form, materiales_info=materiales_info)


@recipes_bp.route('/edit_recipe/<int:id>', methods=['GET', 'POST'])
def edit_recipe(id):
    old_recipe = Recipe.query.get_or_404(id)
    materiales_db = Raw_Material.query.filter_by(estatus='Activo').all()
    material_choices = [(m.id, m.name) for m in materiales_db]
    materiales_info = {m.id: m.nombre_unidad for m in materiales_db} # Para el JS

    product_choices = [(p.id, p.name) for p in Producto.query.filter_by(status='Activo').all()]
    process_choices = [(1, 'Mezclado'), (2, 'Envasado'), (3, 'Reposo')]

    form = FormRecipe(obj=old_recipe)
    form.product_id.choices = product_choices
    
    if request.method == 'GET':
        form.materials.entries = []
        for det in old_recipe.details:
            df = FormRecipeDetail()
            df.material_id = det.material_id
            df.required_quantity = det.required_quantity
            # df.unit_med = det.unit_med  # Comentado porque ya no está en el form
            form.materials.append_entry(df)
            
        form.steps.entries = []
        for step in old_recipe.steps:
            sf = FormRecipeStep()
            sf.step_order = step.step_order
            sf.stage_name = step.stage_name
            sf.step_description = step.description 
            sf.estimated_time = step.estimated_time
            sf.process_type = step.process_type
            form.steps.append_entry(sf)

    for df in form.materials: df.material_id.choices = material_choices
    for sf in form.steps: sf.process_type.choices = process_choices

    if form.validate_on_submit():
        if form.validate_on_submit():
            if not form.materials.data or len(form.materials.data) == 0:
                flash("Debes agregar al menos una materia prima a la receta.", "danger")
                return render_template('recipes/add.html', form=form, materiales_info=materiales_info, is_edit=True, recipe=old_recipe)
        try:
            cant_lote = float(form.produced_quantity.data or 0)
            unidad_lote = int(form.unit_med.data or 1)

            total_cost = 0
            for mat in form.materials.data:
                best_p = Raw_Material_Supplier.query.filter_by(id_material=mat['material_id']).order_by(Raw_Material_Supplier.price.asc()).first()
                if best_p:
                    cost_unit = (float(mat['required_quantity']) / float(best_p.lot)) * float(best_p.price)
                    total_cost += cost_unit

            extra_u = {2: 0.3, 1: 0.2, 3: 0.05}.get(unidad_lote, 0.0)
            merma_base = 1.0 + (len(form.materials.data) * 0.2) + extra_u
            for s in form.steps.data:
                tp = int(s.get('process_type') or 1)
                merma_base += {1: 1.2, 2: 0.5, 3: 0.1}.get(tp, 0.1)
            
            factor = 1.25 if 0 < cant_lote < 15 else (0.90 if cant_lote > 50 else 1.0)
            final_waste = merma_base * factor

            # Desactivar vieja
            old_recipe.status = 2 

            recipe_dict = {k: v for k, v in form.data.items() if k not in ['materials', 'steps', 'id', 'csrf_token', 'unique_code']}
            
            new_recipe = Recipe(**recipe_dict)
            codigo_base = old_recipe.unique_code.split('-V')[0]
            total_versiones = Recipe.query.filter(Recipe.unique_code.like(f"{codigo_base}%")).count()
            new_recipe.unique_code = f"{codigo_base}-V{total_versiones + 1}"

            new_recipe.status = 1
            new_recipe.version = old_recipe.id
            new_recipe.estimated_time = sum(int(s.get('estimated_time') or 0) for s in form.steps.data)
            new_recipe.estimated_waste = final_waste
            
            prod_p = ProductoPresentacionPrecio.query.filter_by(id_producto=form.product_id.data).first()
            precio_v = float(prod_p.price_men if prod_p else 0)
            venta_l = precio_v * cant_lote
            new_recipe.expected_utility = ((venta_l - total_cost - 35.0) / venta_l * 100) if venta_l > 0 else 0.0
            
            db.session.add(new_recipe)
            db.session.flush() 

            for m in form.materials.data:
                m.pop('csrf_token', None)
                #m.pop('unit_med', None) # Quitar esto para que RecipeDetail no truene
                db.session.add(RecipeDetail(**m, recipe_id=new_recipe.id))
            
            for s in form.steps.data:
                s.pop('csrf_token', None)
                desc = s.pop('step_description', None)
                db.session.add(RecipeStep(**s, recipe_id=new_recipe.id, description=desc))

            db.session.commit()
            flash(f"Versión actualizada: {new_recipe.unique_code}", "success")
            return redirect(url_for('recipes.index'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error al versionar: {str(e)}", "danger")

    return render_template('recipes/add.html', form=form, materiales_info=materiales_info, is_edit=True, recipe=old_recipe)


@recipes_bp.route('/delete_recipe/<int:id>', methods=['GET', 'POST'])
#@roles_accepted('Administrador', 'Producción')
def delete_recipe(id):
    recipe = Recipe.query.get_or_404(id)

    # Si la receta es estatus 2, no debería poder alterarse desde aquí
    if recipe.status == 2:
        flash("Esta receta es una versión histórica y no puede ser modificada.", "danger")
        return redirect(url_for('recipes.index'))

    if request.method == 'POST':
        try:
            if recipe.status == 1:
                recipe.status = 0
                mensaje = f"Receta {recipe.unique_code} desactivada correctamente."
                categoria = "warning"
            else:
                recipe.status = 1
                mensaje = f"Receta {recipe.unique_code} activada y lista para producción."
                categoria = "success"

            db.session.commit()
            flash(mensaje, categoria)
            return redirect(url_for('recipes.index'))
        
        except Exception as e:
            db.session.rollback()
            flash(f"Error al cambiar estatus: {str(e)}", "danger")
            
    return render_template('recipes/delete.html', recipe=recipe)


@recipes_bp.route('/view_recipe/<int:id>')
def view_recipe(id):
    recipe = Recipe.query.get_or_404(id)
    return render_template('recipes/view.html', 
                           recipe=recipe, 
                           now=datetime.now())



@recipes_bp.route('/search_products')
def search_products():
    q = request.args.get('q', '').strip()
    productos = Producto.query.filter(
        Producto.status == 'Activo',
        Producto.name.ilike(f'%{q}%')
    ).limit(10).all()
    return jsonify([{'id': p.id, 'name': p.name, 'category': p.category} for p in productos])

@recipes_bp.route('/search_materials')
def search_materials():
    q = request.args.get('q', '').strip()
    materiales = Raw_Material.query.filter(
        Raw_Material.estatus == 'Activo',
        Raw_Material.name.ilike(f'%{q}%')
    ).limit(10).all()
    return jsonify([{'id': m.id, 'name': m.name, 'unit': m.nombre_unidad} for m in materiales])