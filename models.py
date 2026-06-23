from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)
    rol = db.Column(db.String(20), default="guardia")


class Visitante(db.Model):
    __tablename__ = "visitantes"

    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.String(30))
    nombre = db.Column(db.String(200))
    identificacion = db.Column(db.String(100))
    placas = db.Column(db.String(100))
    vehiculo = db.Column(db.String(100))
    visita = db.Column(db.String(200))
    motivo = db.Column(db.String(300))
    entrada = db.Column(db.String(20))
    salida = db.Column(db.String(20))
    guardia = db.Column(db.String(50))


class Incidente(db.Model):
    __tablename__ = "incidentes"

    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.String(50))
    tipo = db.Column(db.String(200))
    descripcion = db.Column(db.Text)
    guardia = db.Column(db.String(50))