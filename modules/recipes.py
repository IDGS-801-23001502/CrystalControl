from flask import Blueprint, render_template, jsonify

recipes_bp = Blueprint(
    'recipes', 
    __name__,
    template_folder='templates',
    static_folder='static')