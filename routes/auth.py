from extensions import db
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user
from models import Usuario

auth = Blueprint("auth", __name__)



@auth.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if request.method == "POST":
        
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "")


        if not nome or not email or not senha:
            flash("Preencha todos os campos.")
            return redirect(url_for("auth.cadastro"))
        
        usuario_existente = Usuario.query.filter_by(email=email).first()
        
        if usuario_existente:
            flash("Este email já está cadastrado.")
            return redirect(url_for("auth.cadastro"))
        
        novo_usuario = Usuario(
            nome=nome,
            email=email
        ) 
        
        novo_usuario.definir_senha(senha)
        
        db.session.add(novo_usuario)
        db.session.commit()
        
        flash("Cadastro realizado com sucesso!")
        return redirect(url_for("auth.login"))
    
    return render_template("cadastro.html")



@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        usuario = Usuario.query.filter_by(email=email).first()
        
        print("E-mail digitado:", email)
        print("Usuário encontrado:", usuario)

        if usuario and usuario.verificar_senha(senha):
            login_user(usuario)
            return redirect(url_for("home"))

        flash("E-mail ou senha incorretos.")

    return render_template("login.html")



@auth.route("/logout")
@login_required
def logout():
    
    logout_user()
    
    return redirect(url_for("auth.login"))
        