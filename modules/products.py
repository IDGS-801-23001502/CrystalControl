from flask import Blueprint, render_template, jsonify

module='products'

products_bp = Blueprint(
    module, 
    __name__,
    template_folder='templates',
    static_folder='static'
    )