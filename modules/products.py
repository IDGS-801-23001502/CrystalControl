from flask import Blueprint, render_template, jsonify

products_bp = Blueprint(
    'products', 
    __name__,
    template_folder='templates',
    static_folder='static'
    )