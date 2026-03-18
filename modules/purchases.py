from flask import Blueprint, render_template, jsonify

purchases_bp = Blueprint(
    'purchases', 
    __name__,
    template_folder='templates',
    static_folder='static'
    )