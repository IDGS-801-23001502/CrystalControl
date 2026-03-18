from flask import Blueprint, render_template, jsonify

sales_bp = Blueprint(
    'sales', 
    __name__,
    template_folder='templates',
    static_folder='static')