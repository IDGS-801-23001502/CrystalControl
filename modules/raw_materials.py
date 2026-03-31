from flask import Blueprint, render_template, jsonify

module = 'raw_materials'

raw_materials_bp = Blueprint(
    module, 
    __name__,
    template_folder='templates',
    static_folder='static'
    )