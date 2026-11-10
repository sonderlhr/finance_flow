from extensions import db
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash


class Usuario(UserMixin, db.Model):
    
    __tablename__ = "usuarios"
    
    id = db.Column(db.Integer, primary_key=True)
    
    nome = db.Column(db.String(100), nullable=False)
    
    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )
    
    senha_hash = db.Column(db.String(256), nullable=False)
    
    criado_em = db.Column(
        db.DateTime,
        nullable=False,
        default=db.func.current_timestamp()
    )
    
    contas = db.relationship(
        "Conta",
        back_populates="usuario",
        cascade="all, delete-orphan"
    )
    
    def definir_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)
    
    def __repr__(self):
        return f"<Usuario{self.nome}>"