import os

from flask import Flask

from config import Config
from extensions import db, login_manager
from models import Usuario
from routes.auth import auth
from routes.financeiro import financeiro


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(auth)
    app.register_blueprint(financeiro)

    @login_manager.user_loader
    def carregar_usuario(usuario_id):
        return db.session.get(Usuario, int(usuario_id))

    with app.app_context():
        os.makedirs(app.instance_path, exist_ok=True)
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)