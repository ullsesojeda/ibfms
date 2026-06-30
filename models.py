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


class Actividad(db.Model):
    __tablename__ = "actividades"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    fecha = db.Column(
        db.String(50)
    )

    tipo = db.Column(
        db.String(200)
    )

    descripcion = db.Column(
        db.Text
    )

    guardia = db.Column(
        db.String(50)
    )


class BitacoraTurno(db.Model):
    __tablename__ = "bitacora_turno"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    fecha = db.Column(db.String(50))
    turno = db.Column(db.String(30))
    asunto = db.Column(db.String(200))
    descripcion = db.Column(db.Text)
    guardia = db.Column(db.String(50))

    recibido = db.Column(
        db.Boolean,
        default=False
    )

    recibido_por = db.Column(
        db.String(50)
    )


class RegistroVIP(db.Model):
    __tablename__ = "registro_vip"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    fecha = db.Column(
        db.String(30),
        nullable=False
    )

    vip = db.Column(
        db.String(20),
        nullable=False
    )

    movimiento = db.Column(
        db.String(20),
        nullable=False
    )

    puesto = db.Column(
        db.String(20),
        nullable=False
    )

    guardia = db.Column(
        db.String(100),
        nullable=False
    )


class Empleado(db.Model):
    __tablename__ = "empleados"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    fecha = db.Column(
        db.String(20)
    )

    chofer = db.Column(
        db.String(100),
        nullable=False
    )

    vehiculo = db.Column(
        db.String(100),
        nullable=False
    )
    puesto = db.Column(
    db.String(20),
    nullable=False
    )

    entrada = db.Column(
        db.String(20)
    )

    salida = db.Column(
        db.String(20)
    )

    guardia = db.Column(
        db.String(50)
    )