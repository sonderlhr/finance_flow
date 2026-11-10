from extensions import db


class Meta(db.Model):
    
    
    __tablename__ = "metas"
    
    id = db.Column(db.Integer, primary_key=True)
    
    nome = db.Column(
        db.String(100),
        nullable=False
    )
    
    valor_objetivo = db.Column(
        db.Numeric(12, 2),
        nullable=False  
    )
    
    valor_atual = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )
    
    prazo = db.Column(
        db.Date,
        nullable=True
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
        return f"<Meta {self.nome}>"