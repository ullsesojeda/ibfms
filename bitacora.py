from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
import hmac
import secrets

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, session, current_app
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError
from models import db, Actividad, BitacoraTurno, Incidente, ControlVehiculo
from bitacora_models import ServicioBitacora, TareaBitacora, AnotacionBitacora, EventoBitacora
from bitacora_catalogo import CATALOGO

bp = Blueprint('bitacora', __name__, url_prefix='/bitacora')
ESTADOS = ('Pendiente', 'Realizada', 'No realizada', 'No aplica')
REFERENCIAS = {'entrega': (BitacoraTurno, 'bitacora_turno', 'Cambio de Turno'),
               'incidente': (Incidente, 'incidentes', 'Incidencias'),
               'vehiculos': (ControlVehiculo, 'control_vehiculos', 'Control de vehículos')}


def ahora():
    # Fechas locales de operación: independencia del huso horario de Render.
    return datetime.now(ZoneInfo(current_app.config.get('BITACORA_TIMEZONE', 'America/Mexico_City'))).replace(tzinfo=None)


def token():
    if 'bitacora_csrf' not in session:
        session['bitacora_csrf'] = secrets.token_urlsafe(32)
    return session['bitacora_csrf']


@bp.before_request
def proteger_formularios():
    if request.method == 'POST' and current_user.is_authenticated:
        if not hmac.compare_digest(str(session.get('bitacora_csrf', '')), request.form.get('csrf_token', '')) or not session.get('bitacora_csrf'):
            abort(400, 'La sesión del formulario venció. Recarga la página.')


@bp.context_processor
def contexto():
    return dict(bitacora_token=token, estados_bitacora=ESTADOS, referencias_bitacora=REFERENCIAS)


@bp.errorhandler(StaleDataError)
def conflicto_concurrente(error):
    db.session.rollback()
    return 'El servicio cambió en otra ventana. Recarga la bitácora antes de guardar.', 409


def resumen(servicio):
    return {estado: sum(t.estado == estado for t in servicio.tareas) for estado in ESTADOS}


def obtener(ident, editar=False):
    consulta = ServicioBitacora.query
    if editar:
        consulta = consulta.with_for_update()
    servicio = consulta.get_or_404(ident)
    if servicio.guardia != current_user.usuario and (editar or current_user.rol != 'admin'):
        abort(403)
    if editar and servicio.cierre:
        abort(409, 'La bitácora ya está cerrada.')
    return servicio


def evento(servicio, detalle):
    servicio.version = (servicio.version or 1) + 1
    db.session.add(EventoBitacora(servicio_id=servicio.id, fecha=ahora(), guardia=current_user.usuario, detalle=detalle))


def limite_tarea(fecha, turno, horario):
    fin_turno = datetime.combine(fecha + timedelta(days=turno == 'Noche'), time(7, 30) if turno == 'Noche' else time(22, 30))
    if '-' not in horario:
        return fin_turno
    hora = datetime.strptime(horario.split('-')[1], '%H:%M').time()
    dia = fecha + timedelta(days=turno == 'Noche' and hora < time(12))
    return datetime.combine(dia, hora)


@bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    hoy = ahora().date()
    fecha_default = hoy - timedelta(days=ahora().time() < time(7, 30))
    if request.method == 'POST':
        puesto, turno = request.form.get('puesto'), request.form.get('turno')
        try:
            fecha = date.fromisoformat(request.form.get('fecha', ''))
        except ValueError:
            abort(400, 'Fecha inválida.')
        if (puesto, turno) not in CATALOGO or fecha > hoy:
            abort(400, 'Revisa fecha, puesto y turno.')
        if fecha < hoy - timedelta(days=1):
            abort(400, 'Solo puedes iniciar servicios de hoy o ayer.')
        culto = request.form.get('culto') == '1'
        motivo = request.form.get('motivo_culto', '').strip()
        if turno == 'Día' and culto != (fecha.weekday() in (2, 3)) and not motivo:
            flash('Explica el cambio de actividades de culto para esa fecha.', 'warning')
            return redirect(url_for('.index'))
        existente = ServicioBitacora.query.filter_by(fecha=fecha, puesto=puesto, turno=turno).first()
        if existente:
            if existente.guardia == current_user.usuario or current_user.rol == 'admin':
                flash('Ya existe una bitácora para ese puesto, turno y fecha.', 'info')
                return redirect(url_for('.detalle', ident=existente.id))
            flash('Ese servicio ya tiene una bitácora asignada a otro guardia.', 'warning')
            return redirect(url_for('.index'))
        servicio = ServicioBitacora(fecha=fecha, puesto=puesto, turno=turno, guardia=current_user.usuario,
                                    culto=culto if turno == 'Día' else False, motivo_culto=motivo or None, inicio=ahora())
        db.session.add(servicio)
        try:
            db.session.flush()
            for orden, fila in enumerate(CATALOGO[puesto, turno]):
                horario, actividad, seccion, *ref = fila
                if seccion == 'Culto' and not servicio.culto:
                    continue
                db.session.add(TareaBitacora(servicio_id=servicio.id, orden=orden, horario=horario,
                    actividad=actividad, seccion=seccion, referencia=ref[0] if ref else None,
                    limite=limite_tarea(fecha, turno, horario)))
            evento(servicio, 'Servicio iniciado' + (f'. Ajuste de culto: {motivo}' if motivo else ''))
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('El servicio ya fue creado. Consulta la lista para abrirlo.', 'warning')
            return redirect(url_for('.index'))
        return redirect(url_for('.detalle', ident=servicio.id))
    consulta = ServicioBitacora.query
    historico = Actividad.query
    if current_user.rol != 'admin':
        consulta = consulta.filter_by(guardia=current_user.usuario)
        historico = historico.filter_by(guardia=current_user.usuario)
    for campo in ('puesto', 'turno', 'guardia'):
        valor = request.args.get(campo, '').strip()
        if valor:
            consulta = consulta.filter(getattr(ServicioBitacora, campo) == valor)
    if request.args.get('fecha'):
        try:
            consulta = consulta.filter_by(fecha=date.fromisoformat(request.args['fecha']))
        except ValueError:
            abort(400, 'Fecha inválida.')
    pagina = consulta.order_by(ServicioBitacora.fecha.desc(), ServicioBitacora.id.desc()).paginate(per_page=30, error_out=False)
    return render_template('bitacora_index.html', pagina=pagina, resumen=resumen, fecha_default=fecha_default,
                           turno_default='Noche' if ahora().time() < time(7, 30) or ahora().time() >= time(22, 20) else 'Día',
                           historico=historico.order_by(Actividad.id.desc()).all())


@bp.route('/<int:ident>')
@login_required
def detalle(ident):
    servicio = obtener(ident)
    return render_template('bitacora_detalle.html', servicio=servicio, resumen=resumen(servicio), ahora=ahora(),
                           editable=not servicio.cierre and servicio.guardia == current_user.usuario)


@bp.route('/<int:ident>/tarea/<int:tarea_id>', methods=['POST'])
@login_required
def tarea(ident, tarea_id):
    servicio = obtener(ident, editar=True)
    tarea = TareaBitacora.query.filter_by(id=tarea_id, servicio_id=ident).first_or_404()
    estado = request.form.get('estado')
    nota = request.form.get('nota', '').strip()
    if estado not in ESTADOS or (estado in ('No realizada', 'No aplica') and not nota):
        flash('Selecciona un estado y explica por qué no se realizó o no aplica.', 'warning')
        return redirect(url_for('.detalle', ident=ident))
    if request.form.get('version') != str(tarea.version):
        abort(409, 'Esta actividad cambió en otra ventana. Recarga antes de guardar.')
    evento(servicio, f'Actividad #{tarea.orden + 1}: {tarea.estado} → {estado}. Nota anterior: {tarea.nota or "—"}. Nota nueva: {nota or "—"}')
    tarea.estado, tarea.nota, tarea.captura = estado, nota or None, ahora()
    tarea.version += 1
    db.session.commit()
    flash('Actividad guardada.', 'success')
    return redirect(url_for('.detalle', ident=ident) + f'#tarea-{tarea_id}')


@bp.route('/<int:ident>/anotacion', methods=['POST'])
@login_required
def anotacion(ident):
    servicio = obtener(ident, editar=True)
    texto = request.form.get('texto', '').strip()
    ref, registro_id = request.form.get('referencia', ''), request.form.get('registro_id', '').strip()
    if not texto:
        flash('Escribe la anotación.', 'warning')
        return redirect(url_for('.detalle', ident=ident))
    if bool(ref) != bool(registro_id) or (ref and ref not in REFERENCIAS):
        abort(400, 'Indica módulo y número de registro para enlazarlo, o deja ambos vacíos.')
    if ref:
        try:
            registro_id = int(registro_id)
        except ValueError:
            abort(400, 'Número de registro inválido.')
        registro = db.session.get(REFERENCIAS[ref][0], registro_id)
        if registro is None:
            abort(400, 'No existe el registro indicado.')
        if ref == 'incidente' and current_user.rol != 'admin' and registro.guardia != current_user.usuario:
            abort(403)
    db.session.add(AnotacionBitacora(servicio_id=ident, texto=texto, fecha=ahora(), guardia=current_user.usuario,
                                    referencia=ref or None, registro_id=registro_id or None))
    evento(servicio, 'Anotación añadida')
    db.session.commit()
    return redirect(url_for('.detalle', ident=ident) + '#anotaciones')


@bp.route('/<int:ident>/cerrar', methods=['GET', 'POST'])
@login_required
def cerrar(ident):
    servicio = obtener(ident, editar=True)
    conteo = resumen(servicio)
    if request.method == 'POST':
        nota = request.form.get('nota_cierre', '').strip()
        if conteo['Pendiente'] and not nota:
            flash('Explica por qué quedan actividades pendientes antes de cerrar.', 'warning')
            return render_template('bitacora_cierre.html', servicio=servicio, resumen=conteo), 400
        servicio.cierre, servicio.nota_cierre = ahora(), nota or None
        evento(servicio, 'Servicio cerrado. ' + str(conteo) + '. ' + nota)
        db.session.commit()
        flash('Bitácora cerrada. Se conserva el estado real de cada actividad.', 'success')
        return redirect(url_for('.detalle', ident=ident))
    return render_template('bitacora_cierre.html', servicio=servicio, resumen=conteo)


@bp.route('/<int:ident>/referencia/<int:anotacion_id>')
@login_required
def referencia(ident, anotacion_id):
    obtener(ident)
    anotacion = AnotacionBitacora.query.filter_by(id=anotacion_id, servicio_id=ident).first_or_404()
    if anotacion.referencia not in REFERENCIAS:
        abort(404)
    registro = db.session.get(REFERENCIAS[anotacion.referencia][0], anotacion.registro_id)
    if registro is None:
        abort(404)
    if anotacion.referencia == 'incidente' and current_user.rol != 'admin' and registro.guardia != current_user.usuario:
        abort(403)
    return render_template('bitacora_referencia.html', registro=registro, anotacion=anotacion, ident=ident)
