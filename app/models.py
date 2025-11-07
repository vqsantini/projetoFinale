from app import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    generos = db.relationship("UserGenero", back_populates="usuario")
    artistas = db.relationship("UserArtista", back_populates="usuario")


class Genero(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), unique=True, nullable=False)


class Artista(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), unique=True, nullable=False)

    musicas = db.relationship("Musica", backref="artista", lazy=True)


class Musica(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    artista_id = db.Column(db.Integer, db.ForeignKey("artista.id"), nullable=False)
    genero_id = db.Column(db.Integer, db.ForeignKey("genero.id"))


class UserGenero(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    genero_id = db.Column(db.Integer, db.ForeignKey("genero.id"))

    usuario = db.relationship("User", back_populates="generos")
    genero = db.relationship("Genero")


class UserArtista(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    artista_id = db.Column(db.Integer, db.ForeignKey("artista.id"))

    usuario = db.relationship("User", back_populates="artistas")
    artista = db.relationship("Artista")
