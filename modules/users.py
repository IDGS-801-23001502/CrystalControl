from flask import Blueprint, render_template, jsonify

users_bp = Blueprint(
    'users',
    __name__,
    template_folder='templates',
    static_folder='static'
    )

@users_bp.route("/")
def index():
    return render_template("users/list.html")