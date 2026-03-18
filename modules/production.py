from flask import Blueprint, render_template, jsonify

production_bp = Blueprint(
    'production', 
    __name__,
    template_folder='templates',
    static_folder='static'
    )