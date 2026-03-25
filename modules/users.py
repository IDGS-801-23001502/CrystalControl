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

@users_bp.route("/listadoUsuario")
def listUsers():
    create_form=forms.FormUsuarios(request.form)
    users=User.query.all()
    return render_template("users/list.html", form=create_form, users=users)

@users_bp.route("/agregarUsuario", methods=['GET','POST'])
def agregarUsuario():
    create_form=forms.FormUsuarios(request.form)
    if request.method == 'POST':
        user=User(nombreUsuario=create_form.username.data,
                  nombre=create_form.nombre.data,
                  apellido=create_form.apellidos.data,
                  password=create_form.password.data,
                  id_perfil=create_form.perfil.data,
                  )