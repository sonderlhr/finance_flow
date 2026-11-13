from extensions import db


class Transacao(db.Model):
    
    
    __tablename__ = "transacoes"
    
    id = db.Column(db.Integer, primary_key=True)
    
    descricao = db.Column(
        db.String(150),
        nullable=False
    )
    
    valor = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )
    
    tipo = db.Column(
        db.String(20),
        nullable=False
    )
    
    data = db.Column(
        db.Date,
        nullable=False
    )
    
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )
    
    conta_id = db.Column(
        db.ForeignKey("contas.id"),
        nullable=False
    )
    
    categoria_id = db.Column(
        db.Integer,
        db.ForeignKey("categorias.id"),
        nullable=False
    )
    
    criado_em = db.Column(
        db.DateTime,
        nullable=False,
        default=db.func.current_timestamp()
    )
    
    conta = db.relationship("Conta", backref="transacoes")
    categoria = db.relationship("Categoria", backref="transacoes")
    
    def __repr__(self):
        return f"<Transacao {self.descricao}>"