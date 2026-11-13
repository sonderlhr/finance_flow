from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from extensions import db
from models import Categoria, Conta, Usuario

auth = Blueprint("auth", __name__)



@auth.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if request.method == "POST":
        
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
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
        
        conta_padrao = Conta(
            nome="Carteira",
            tipo="Carteira",
            saldo_inicial=0,
            usuario_id=novo_usuario.id
        )
        db.session.add(conta_padrao)

        categorias_padrao = [
            ("Salário", "receita"),
            ("Outros Ganhos", "receita"),
            ("Alimentação", "despesa"),
            ("Transporte", "despesa"),
            ("Moradia", "despesa"),
            ("Lazer", "despesa"),
        ]
        for nome_cat, tipo_cat in categorias_padrao:
            db.session.add(
                Categoria(nome=nome_cat, tipo=tipo_cat, usuario_id=novo_usuario.id)
            )

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
            return redirect(url_for("financeiro.dashboard"))

        flash("E-mail ou senha incorretos.")

    return render_template("login.html")



@auth.route("/logout")
@login_required
def logout():
    
    logout_user()
    
    return redirect(url_for("auth.login"))
        