from flask import Blueprint, render_template, jsonify

analytics_bp = Blueprint(
    'analytics', 
    __name__,
    template_folder='templates',
    static_folder='static'
    )