from extensions import db


class Cartao(db.Model):
    
    __tablename__ = "cartoes"
    
    id = db.Column(db.Integer, primary_key=True)
    
nome = db.Column(
    db.String(100),
    nullable=False
)

limite = db.Column(
    db.Numeric(12, 2), 
    nullable=False
)

dia_fechamento = db.Column(
    db.Integer,
    nullable=False
)

dia_vencimento = db.Column(
    db.Integer,
    nullable=False
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

def __repr__(self):
    return f"<Cartao {self.nome}>"
        