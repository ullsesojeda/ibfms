# ==========================================================
# SISTEMA INTEGRAL DE VIGILANCIA
# Módulo: ACCESO AL AUDITORIO
# models/acceso_auditorio.py
# ==========================================================

from datetime import datetime

from extensions import db


class AccesoAuditorio(db.Model):

    __tablename__ = "accesos_auditorio"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    fecha = db.Column(
        db.Date,
        nullable=False
    )

    hora_acceso = db.Column(
        db.Time,
        nullable=False
    )

    quien_accedio = db.Column(
        db.String(100),
        nullable=False
    )

    nombre_otro = db.Column(
        db.String(150),
        nullable=True
    )

    personas = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    motivo = db.Column(
        db.String(100),
        nullable=False
    )

    motivo_otro = db.Column(
        db.String(200),
        nullable=True
    )

    luces = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    hora_salida = db.Column(
        db.Time,
        nullable=True
    )

    guardia = db.Column(
        db.String(100),
        nullable=False
    )

    fecha_registro = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now
    )

    @property
    def estado(self):
        """
        Determina automáticamente el estado del acceso.
        """

        if self.hora_salida is None:
            return "DENTRO DEL AUDITORIO"

        return "SALIDA REGISTRADA"

    @property
    def persona_mostrar(self):
        """
        Devuelve el nombre capturado cuando se seleccionó OTRO.
        """

        if self.quien_accedio == "OTRO" and self.nombre_otro:
            return self.nombre_otro

        return self.quien_accedio

    @property
    def motivo_mostrar(self):
        """
        Devuelve el motivo capturado cuando se seleccionó OTRO.
        """

        if self.motivo == "OTRO" and self.motivo_otro:
            return self.motivo_otro

        return self.motivo