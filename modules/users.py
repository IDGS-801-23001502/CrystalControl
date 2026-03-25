from flask import Blueprint, render_template, jsonify, request
from flask import g
import forms
from models import db, Perfil,User


users_bp = Blueprint(
    'users', 
    __name__,
    template_folder='templates',
    static_folder='static'
    )

@users_bp.route("/")
def index():
    return render_template("users/list.html")