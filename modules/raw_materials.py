from flask import Blueprint, render_template, jsonify

raw_materials_bp = Blueprint(
    'raw_materials', 
    __name__,
    template_folder='templates',
    static_folder='static'
    )