from flask import Blueprint, render_template, jsonify

suppliers_bp = Blueprint(
    'suppliers', 
    __name__,
    template_folder='templates',
    static_folder='static')