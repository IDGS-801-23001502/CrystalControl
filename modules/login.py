from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash

from flask_security import login_required
from flask_security.utils import login_user, logout_user
from flask import Blueprint, render_template, jsonify

login_bp = Blueprint(
    'login', 
    __name__,
    template_folder='templates',
    static_folder='static'
    )