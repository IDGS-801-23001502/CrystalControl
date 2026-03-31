from flask import Blueprint, render_template, jsonify

module='purchases'

purchases_bp = Blueprint(
    module, 
    __name__,
    template_folder='templates',
    static_folder='static'
    )

#current_user.nivel_acceso('Inventario')
