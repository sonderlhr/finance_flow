from extensions import db


class Categoria(db.Model):
    
    __tablename__ = "categorias"
    
    id = db.Column(db.Integer, primary_key=True)
    
    nome = db.Column(
        db.String(80),
        nullable=False
    )
    
    tipo = db.Column(
        db.String(20),
        nullable=False
    )
    
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )
    
    usuario = db.relationship(
        "Usuario",
        backref="categorias"
    )
    
    def __repr__(self):
        return f"<Categoria {self.nome}>"