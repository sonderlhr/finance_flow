from extensions import db


class Conta(db.Model):
    
    __tablename__ = "contas"
    
    id = db.Column(db.Integer, primary_key=True)
    
    nome = db.Column(db.String(100), nullable=False)
    
    tipo = db.Column(db.String(30), nullable=False)
    
    saldo_inicial = db.Column(
        db.Numeric(12, 2),
        nullable=False,
    )
    
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )
    
    criado_em = db.Column(
        db.DateTime, 
        nullable=False,
        default=db.func.current_timestamp()
    )
    
    usuario =db.relationship(
        "Usuario",
        back_populates="contas"
    )
    
    def __repr__(self):
        return f"<Conta {self.nome}>"