from flask import Blueprint, render_template, jsonify

module='production'

production_bp = Blueprint(
    module, 
    __name__,
    template_folder='templates',
    static_folder='static'
    )