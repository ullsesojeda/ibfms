from models import db


class ServicioBitacora(db.Model):
    __tablename__ = 'bitacora_servicio'
    __table_args__ = (db.UniqueConstraint('fecha', 'puesto', 'turno', name='uq_bitacora_servicio'),)
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    puesto = db.Column(db.String(20), nullable=False)
    turno = db.Column(db.String(10), nullable=False)
    guardia = db.Column(db.String(100), nullable=False)
    culto = db.Column(db.Boolean, nullable=False)
    motivo_culto = db.Column(db.Text)
    inicio = db.Column(db.DateTime, nullable=False)
    cierre = db.Column(db.DateTime)
    nota_cierre = db.Column(db.Text)
    version = db.Column(db.Integer, default=1, nullable=False)
    __mapper_args__ = {'version_id_col': version}
    tareas = db.relationship('TareaBitacora', order_by='TareaBitacora.orden', lazy='selectin')
    anotaciones = db.relationship('AnotacionBitacora', order_by='AnotacionBitacora.id', lazy='selectin')
    eventos = db.relationship('EventoBitacora', order_by='EventoBitacora.id', lazy='selectin')


class TareaBitacora(db.Model):
    __tablename__ = 'bitacora_tarea'
    id = db.Column(db.Integer, primary_key=True)
    servicio_id = db.Column(db.Integer, db.ForeignKey('bitacora_servicio.id'), nullable=False)
    orden = db.Column(db.Integer, nullable=False)
    horario = db.Column(db.String(40), nullable=False)
    actividad = db.Column(db.Text, nullable=False)
    seccion = db.Column(db.String(40), nullable=False)
    referencia = db.Column(db.String(20))
    limite = db.Column(db.DateTime, nullable=False)
    estado = db.Column(db.String(20), default='Pendiente', nullable=False)
    nota = db.Column(db.Text)
    captura = db.Column(db.DateTime)
    version = db.Column(db.Integer, default=0, nullable=False)
    __mapper_args__ = {'version_id_col': version, 'version_id_generator': False}


class AnotacionBitacora(db.Model):
    __tablename__ = 'bitacora_anotacion'
    id = db.Column(db.Integer, primary_key=True)
    servicio_id = db.Column(db.Integer, db.ForeignKey('bitacora_servicio.id'), nullable=False)
    fecha = db.Column(db.DateTime, nullable=False)
    guardia = db.Column(db.String(100), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    referencia = db.Column(db.String(20))
    registro_id = db.Column(db.Integer)


class EventoBitacora(db.Model):
    __tablename__ = 'bitacora_evento'
    id = db.Column(db.Integer, primary_key=True)
    servicio_id = db.Column(db.Integer, db.ForeignKey('bitacora_servicio.id'), nullable=False)
    fecha = db.Column(db.DateTime, nullable=False)
    guardia = db.Column(db.String(100), nullable=False)
    detalle = db.Column(db.Text, nullable=False)
