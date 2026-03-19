from flask import Blueprint, render_template, jsonify

login_bp = Blueprint(
    'login', 
    __name__,
    template_folder='templates',
    static_folder='static'
    )