import os
import shutil
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file
)

from io import BytesIO

from openpyxl import Workbook

from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from config import Config
from models import (
    db,
    Usuario,
    Visitante,
    Incidente,
    Actividad,
    BitacoraTurno,
    RegistroVIP,
    Empleado,
    ControlVehiculo,
    ObjetoCustodia,
    AccesoAuditorio
)

from datetime import datetime
import pandas as pd
from flask import send_file

app = Flask(__name__)
app.config.from_object(Config)

if os.name == "nt":

    RUTA_DB = os.path.join("instance", "ibfms.db")
    RUTA_BACKUPS = "backups"
    RUTA_EXPORTS = "exports"
    RUTA_UPLOADS = "uploads"

else:

    RUTA_DB = "/montesion/vigilancia/ibfms.db"
    RUTA_BACKUPS = "/montesion/vigilancia/backups"
    RUTA_EXPORTS = "/montesion/vigilancia/exports"
    RUTA_UPLOADS = "/montesion/vigilancia/uploads"

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


with app.app_context():
    db.create_all()

    admin = Usuario.query.filter_by(
        usuario="admin"
    ).first()

    if not admin:
        admin = Usuario(
            usuario="admin",
            password=generate_password_hash(
                "Admin2026!"
            ),
            rol="admin"
        )

        db.session.add(admin)

    for i in range(1, 13):
        nombre = f"G{i}"

        existe = Usuario.query.filter_by(
            usuario=nombre
        ).first()

        if not existe:
            nuevo = Usuario(
                usuario=nombre,
                password=generate_password_hash(
                    f"{nombre}123"
                ),
                rol="guardia"
            )

            db.session.add(nuevo)

    db.session.commit()

@app.route("/usuarios")
@login_required
def usuarios():

    if current_user.rol != "admin":
        flash(
            "No tiene permisos.",
            "danger"
        )
        return redirect(
            url_for("dashboard")
        )

    lista = Usuario.query.order_by(
        Usuario.usuario
    ).all()

    return render_template(
        "usuarios.html",
        usuarios=lista
    )

@app.route(
    "/nuevo_usuario",
    methods=["GET", "POST"]
)
@login_required
def nuevo_usuario():

    if current_user.rol != "admin":
        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        usuario = request.form["usuario"]
        password = request.form["password"]
        rol = request.form["rol"]

        existe = Usuario.query.filter_by(
            usuario=usuario
        ).first()

        if existe:
            flash(
                "El usuario ya existe.",
                "danger"
            )
            return redirect(
                url_for("nuevo_usuario")
            )

        nuevo = Usuario(
            usuario=usuario,
            password=generate_password_hash(
                password
            ),
            rol=rol
        )

        db.session.add(nuevo)
        db.session.commit()

        flash(
            "Usuario creado correctamente.",
            "success"
        )

        return redirect(
            url_for("usuarios")
        )

    return render_template(
        "nuevo_usuario.html"
    )

@app.route(
    "/eliminar_usuario/<int:id>"
)
@login_required
def eliminar_usuario(id):

    if current_user.rol != "admin":
        return redirect(
            url_for("dashboard")
        )

    usuario = Usuario.query.get_or_404(id)

    if usuario.usuario == "admin":
        flash(
            "No se puede eliminar el administrador principal.",
            "danger"
        )
        return redirect(
            url_for("usuarios")
        )

    db.session.delete(usuario)
    db.session.commit()

    flash(
        "Usuario eliminado.",
        "success"
    )

    return redirect(
        url_for("usuarios")
    )

@app.route(
    "/bitacora_turno",
    methods=["GET", "POST"]
)
@login_required
def bitacora_turno():

    if request.method == "POST":

        nueva = BitacoraTurno(
            fecha=datetime.now().strftime(
                "%d/%m/%Y %H:%M:%S"
            ),
            turno=request.form["turno"],
            asunto=request.form["asunto"],
            descripcion=request.form["descripcion"],
            guardia=current_user.usuario
        )

        db.session.add(nueva)
        db.session.commit()

        flash(
            "Bitácora guardada.",
            "success"
        )

        return redirect(
            url_for("bitacora_turno")
        )

    datos = (
        BitacoraTurno.query
        .order_by(
            BitacoraTurno.id.desc()
        )
        .all()
    )

    return render_template(
        "bitacora_turno.html",
        bitacora=datos
    )

@app.route("/registrar_salida/<int:id>")
@login_required
def registrar_salida(id):

    visitante = Visitante.query.get_or_404(id)

    visitante.salida = datetime.now().strftime(
        "%H:%M:%S"
    )

    visitante.guardia_salida = current_user.usuario

    db.session.commit()

    flash(
        "Salida registrada.",
        "success"
    )

    return redirect(
        url_for("visitantes")
    )

@app.route("/exportar_visitantes")
@login_required
def exportar_visitantes():

    # ==============================================
    # OBTENER FILTROS
    # ==============================================

    buscar = request.args.get(
        "buscar",
        ""
    ).strip()

    fecha_inicio = request.args.get(
        "fecha_inicio",
        ""
    ).strip()

    fecha_fin = request.args.get(
        "fecha_fin",
        ""
    ).strip()

    puesto_filtro = request.args.get(
        "puesto_filtro",
        ""
    ).strip()

    estado_filtro = request.args.get(
        "estado_filtro",
        ""
    ).strip()


    # ==============================================
    # CONSULTA BASE
    # ==============================================

    if current_user.rol == "admin":

        consulta = Visitante.query

    else:

        consulta = (
            Visitante.query
            .filter_by(
                guardia=current_user.usuario
            )
        )


    # ==============================================
    # BÚSQUEDA
    # ==============================================

    if buscar:

        texto = f"%{buscar}%"

        consulta = consulta.filter(
            db.or_(
                Visitante.nombre.ilike(texto),
                Visitante.identificacion.ilike(texto),
                Visitante.placas.ilike(texto),
                Visitante.vehiculo.ilike(texto),
                Visitante.visita.ilike(texto),
                Visitante.motivo.ilike(texto)
            )
        )


    # ==============================================
    # FILTRO POR PUESTO
    # ==============================================

    if puesto_filtro:

        consulta = consulta.filter(
            Visitante.puesto == puesto_filtro
        )


    # ==============================================
    # FILTRO POR ESTADO
    # ==============================================

    if estado_filtro == "dentro":

        consulta = consulta.filter(
            Visitante.salida.is_(None)
        )

    elif estado_filtro == "salida":

        consulta = consulta.filter(
            Visitante.salida.isnot(None)
        )


    # ==============================================
    # OBTENER REGISTROS
    # ==============================================

    datos = consulta.all()


    # ==============================================
    # FILTRO POR FECHAS
    # ==============================================

    if fecha_inicio or fecha_fin:

        registros_filtrados = []

        fecha_inicio_obj = None
        fecha_fin_obj = None


        if fecha_inicio:

            try:

                fecha_inicio_obj = datetime.strptime(
                    fecha_inicio,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                flash(
                    "La fecha inicial no es válida.",
                    "danger"
                )

                return redirect(
                    url_for("visitantes")
                )


        if fecha_fin:

            try:

                fecha_fin_obj = datetime.strptime(
                    fecha_fin,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                flash(
                    "La fecha final no es válida.",
                    "danger"
                )

                return redirect(
                    url_for("visitantes")
                )


        for registro in datos:

            try:

                fecha_registro = datetime.strptime(
                    registro.fecha,
                    "%d/%m/%Y"
                ).date()

            except (ValueError, TypeError):

                continue


            if (
                fecha_inicio_obj
                and fecha_registro < fecha_inicio_obj
            ):

                continue


            if (
                fecha_fin_obj
                and fecha_registro > fecha_fin_obj
            ):

                continue


            registros_filtrados.append(
                registro
            )


        datos = registros_filtrados


    # ==============================================
    # CREAR EXCEL
    # ==============================================

    from openpyxl import Workbook

    from openpyxl.styles import Font

    from io import BytesIO

    from flask import send_file


    libro = Workbook()

    hoja = libro.active

    hoja.title = "Visitantes"


    encabezados = [
        "ID",
        "Fecha",
        "Puesto",
        "Nombre",
        "Identificación",
        "Placas",
        "Vehículo",
        "Visita",
        "Motivo",
        "Entrada",
        "Salida",
        "Guardia Entrada",
        "Guardia Salida"
    ]


    hoja.append(encabezados)


    # Encabezados en negritas

    for celda in hoja[1]:

        celda.font = Font(
            bold=True
        )


    # ==============================================
    # AGREGAR REGISTROS
    # ==============================================

    for visitante in datos:

        hoja.append([
            visitante.id,
            visitante.fecha,
            visitante.puesto,
            visitante.nombre,
            visitante.identificacion,
            visitante.placas,
            visitante.vehiculo,
            visitante.visita,
            visitante.motivo,
            visitante.entrada,
            visitante.salida or "",
            visitante.guardia,
            visitante.guardia_salida or ""
        ])


    # ==============================================
    # AJUSTAR COLUMNAS
    # ==============================================

    anchos = {
        "A": 8,
        "B": 12,
        "C": 15,
        "D": 25,
        "E": 18,
        "F": 15,
        "G": 18,
        "H": 25,
        "I": 25,
        "J": 12,
        "K": 12,
        "L": 18,
        "M": 18
    }


    for columna, ancho in anchos.items():

        hoja.column_dimensions[
            columna
        ].width = ancho


    # ==============================================
    # FILTRO AUTOMÁTICO DE EXCEL
    # ==============================================

    hoja.auto_filter.ref = (
        hoja.dimensions
    )


    # ==============================================
    # PREPARAR ARCHIVO
    # ==============================================

    archivo = BytesIO()

    libro.save(archivo)

    archivo.seek(0)


    return send_file(
        archivo,
        as_attachment=True,
        download_name="reporte_visitantes.xlsx",
        mimetype=(
            "application/vnd.openxmlformats-officedocument"
            ".spreadsheetml.sheet"
        )
    )

@app.route("/", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        usuario = request.form["usuario"]
        password = request.form["password"]

        user = Usuario.query.filter_by(
            usuario=usuario
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):
            login_user(user)
            return redirect(
                url_for("dashboard")
            )

        flash(
            "Usuario o contraseña incorrectos",
            "danger"
        )

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():

    from datetime import datetime

    hoy = datetime.now().strftime("%d/%m/%Y")

    visitantes = Visitante.query.count()

    visitantes_dentro = Visitante.query.filter_by(
        salida=None
    ).count()

    empleados_dentro = Empleado.query.filter_by(
        salida=None
    ).count()

    vip_hoy = RegistroVIP.query.filter_by(
        fecha=hoy
    ).count()

    incidentes = Incidente.query.count()

    incidentes_hoy = Incidente.query.filter_by(
        fecha=hoy
    ).count()

    actividades_hoy = Actividad.query.filter_by(
        fecha=hoy
    ).count()

    usuarios = Usuario.query.count()

    return render_template(

        "dashboard.html",

        visitantes=visitantes,

        visitantes_dentro=visitantes_dentro,

        empleados_dentro=empleados_dentro,

        vip_hoy=vip_hoy,

        incidentes=incidentes,

        incidentes_hoy=incidentes_hoy,

        actividades_hoy=actividades_hoy,

        usuarios=usuarios

    )

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(
        url_for("login")
    )


@app.route(
    "/cambiar_password",
    methods=["GET", "POST"]
)
@login_required
def cambiar_password():

    if request.method == "POST":

        nueva = request.form["password"]

        current_user.password = (
            generate_password_hash(nueva)
        )

        db.session.commit()

        flash(
            "Contraseña actualizada.",
            "success"
        )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "cambiar_password.html"
    )

@app.route(
    "/visitantes",
    methods=["GET", "POST"]
)
@login_required
def visitantes():

    # ==============================================
    # REGISTRAR VISITANTE
    # ==============================================

    if request.method == "POST":

        nuevo = Visitante(
            fecha=datetime.now().strftime(
                "%d/%m/%Y"
            ),

            nombre=request.form["nombre"],

            identificacion=request.form["identificacion"],

            placas=request.form["placas"],

            vehiculo=request.form["vehiculo"],

            visita=request.form["visita"],

            motivo=request.form["motivo"],

            puesto=request.form["puesto"],

            entrada=datetime.now().strftime(
                "%H:%M:%S"
            ),

            guardia=current_user.usuario
        )

        db.session.add(nuevo)

        db.session.commit()

        flash(
            "Visitante registrado.",
            "success"
        )

        return redirect(
            url_for("visitantes")
        )


    # ==============================================
    # OBTENER FILTROS
    # ==============================================

    buscar = request.args.get(
        "buscar",
        ""
    ).strip()

    fecha_inicio = request.args.get(
        "fecha_inicio",
        ""
    ).strip()

    fecha_fin = request.args.get(
        "fecha_fin",
        ""
    ).strip()

    puesto_filtro = request.args.get(
        "puesto_filtro",
        ""
    ).strip()

    estado_filtro = request.args.get(
        "estado_filtro",
        ""
    ).strip()


    # ==============================================
    # CONSULTA BASE
    # ==============================================

    if current_user.rol == "admin":

        consulta = Visitante.query

    else:

        consulta = (
            Visitante.query
            .filter_by(
                guardia=current_user.usuario
            )
        )


    # ==============================================
    # BÚSQUEDA GENERAL
    # ==============================================

    if buscar:

        texto = f"%{buscar}%"

        consulta = consulta.filter(
            db.or_(
                Visitante.nombre.ilike(texto),
                Visitante.identificacion.ilike(texto),
                Visitante.placas.ilike(texto),
                Visitante.vehiculo.ilike(texto),
                Visitante.visita.ilike(texto),
                Visitante.motivo.ilike(texto)
            )
        )


    # ==============================================
    # FILTRO POR PUESTO
    # ==============================================

    if puesto_filtro:

        consulta = consulta.filter(
            Visitante.puesto == puesto_filtro
        )


    # ==============================================
    # FILTRO POR ESTADO
    # ==============================================

    if estado_filtro == "dentro":

        consulta = consulta.filter(
            Visitante.salida.is_(None)
        )

    elif estado_filtro == "salida":

        consulta = consulta.filter(
            Visitante.salida.isnot(None)
        )


    # ==============================================
    # OBTENER REGISTROS
    # ==============================================

    datos = consulta.all()


    # ==============================================
    # FILTRO POR FECHAS
    #
    # La fecha se guarda como DD/MM/YYYY,
    # por eso se convierte antes de comparar.
    # ==============================================

    if fecha_inicio or fecha_fin:

        registros_filtrados = []

        fecha_inicio_obj = None
        fecha_fin_obj = None


        # ------------------------------------------
        # FECHA INICIAL
        # ------------------------------------------

        if fecha_inicio:

            try:

                fecha_inicio_obj = datetime.strptime(
                    fecha_inicio,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                flash(
                    "La fecha inicial no es válida.",
                    "danger"
                )

                return redirect(
                    url_for("visitantes")
                )


        # ------------------------------------------
        # FECHA FINAL
        # ------------------------------------------

        if fecha_fin:

            try:

                fecha_fin_obj = datetime.strptime(
                    fecha_fin,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                flash(
                    "La fecha final no es válida.",
                    "danger"
                )

                return redirect(
                    url_for("visitantes")
                )


        # ------------------------------------------
        # REVISAR REGISTROS
        # ------------------------------------------

        for registro in datos:

            try:

                fecha_registro = datetime.strptime(
                    registro.fecha,
                    "%d/%m/%Y"
                ).date()

            except (ValueError, TypeError):

                continue


            if (
                fecha_inicio_obj
                and fecha_registro < fecha_inicio_obj
            ):

                continue


            if (
                fecha_fin_obj
                and fecha_registro > fecha_fin_obj
            ):

                continue


            registros_filtrados.append(
                registro
            )


        datos = registros_filtrados


    # ==============================================
    # ORDEN
    # ==============================================
    #
    # PRIMERO:
    # visitantes que todavía están dentro.
    #
    # DESPUÉS:
    # visitantes que ya salieron.
    #
    # Dentro de cada grupo:
    # registro más reciente primero.
    # ==============================================

    datos.sort(
        key=lambda visitante: (
            visitante.salida is not None,
            -visitante.id
        )
    )


    # ==============================================
    # MOSTRAR PÁGINA
    # ==============================================

    return render_template(
        "visitantes.html",
        visitantes=datos,

        buscar=buscar,

        fecha_inicio=fecha_inicio,

        fecha_fin=fecha_fin,

        puesto_filtro=puesto_filtro,

        estado_filtro=estado_filtro
    )
@app.route(
    "/incidentes",
    methods=["GET", "POST"]
)
@login_required
def incidentes():

    if request.method == "POST":

        nuevo = Incidente(
            fecha=datetime.now().strftime(
                "%d/%m/%Y %H:%M:%S"
            ),
            tipo=request.form["tipo"],
            descripcion=request.form["descripcion"],
            guardia=current_user.usuario
        )

        db.session.add(nuevo)
        db.session.commit()

        flash(
            "Incidente registrado.",
            "success"
        )

        return redirect(
            url_for("incidentes")
        )

    if current_user.rol == "admin":
        datos = (
        Incidente.query
        .order_by(Incidente.id.desc())
        .all()
    )
    else:
        datos = (
        Incidente.query
        .filter_by(
            guardia=current_user.usuario
        )
        .order_by(Incidente.id.desc())
        .all()
    )       

    return render_template(
        "incidentes.html",
        incidentes=datos
    )

    return render_template(
    "incidentes.html",
    incidentes=datos
)

@app.route(
        "/actividades",
        methods=["GET", "POST"]
    )
@login_required
   
def actividades():

        if request.method == "POST":

            nueva = Actividad(
                fecha=datetime.now().strftime(
                    "%d/%m/%Y %H:%M:%S"
                ),
                tipo=request.form["tipo"],
                descripcion=request.form["descripcion"],
                guardia=current_user.usuario
            )

            db.session.add(nueva)
            db.session.commit()

            flash(
                "Actividad registrada.",
                "success"
            )

            return redirect(
                url_for("actividades")
            )

        if current_user.rol == "admin":
            datos = (
                Actividad.query
                .order_by(Actividad.id.desc())
                .all()
            )
        else:
            datos = (
                Actividad.query
                .filter_by(
                    guardia=current_user.usuario
                )
                .order_by(Actividad.id.desc())
                .all()
            )

        return render_template(
            "actividades.html",
            actividades=datos
        )

@app.route(
    "/empleados",
    methods=["GET", "POST"]
)
@login_required
def empleados():

    if request.method == "POST":

        nuevo = Empleado(
            fecha=datetime.now().strftime(
                "%d/%m/%Y"
            ),
            chofer=request.form["chofer"],
            vehiculo=request.form["vehiculo"],
            puesto=request.form["puesto"],
            entrada=datetime.now().strftime(
                "%H:%M:%S"
            ),
            guardia=current_user.usuario
        )

        db.session.add(nuevo)
        db.session.commit()

        flash(
            "Entrada registrada.",
            "success"
        )

        return redirect(
            url_for("empleados")
        )

    datos = (
        Empleado.query
        .order_by(
            Empleado.id.desc()
        )
        .all()
    )

    return render_template(
        "empleados.html",
        empleados=datos
    )

@app.route(
    "/registrar_salida_empleado/<int:id>"
)
@login_required
def registrar_salida_empleado(id):

    empleado = Empleado.query.get_or_404(id)

    empleado.salida = (
        datetime.now().strftime(
            "%H:%M:%S"
        )
    )

    db.session.commit()

    flash(
        "Salida registrada.",
        "success"
    )

    return redirect(
        url_for("empleados")
    )

# ==========================================================
# ACCESO AL AUDITORIO
# ==========================================================

PERSONAS_AUDITORIO = [
    "CHAVEZ",
    "JABES",
    "PASTOR LUPE",
    "JOSUE ARANDA",
    "JOSUE ORTEGA",
    "CHEQUE",
    "PASTOR FLORENCIO",
    "PAEZ",
    "HNA ELIZABETH",
    "HNA SAMANTA",
    "HNA GABRIELA",
    "PASTOR AVILA",
    "A1",
    "CORA",
    "VIP",
    "OTRO"
]

MOTIVOS_AUDITORIO = [
    "PIANO",
    "ENSAYO",
    "ENSAYO AUDIO",
    "TRABAJO",
    "LIMPIEZA",
    "CAMARAS",
    "ORACION",
    "OFICINA",
    "OTRO"
]


@app.route(
    "/acceso_auditorio",
    methods=["GET", "POST"]
)
@login_required
def acceso_auditorio():

    if request.method == "POST":

        quien_accedio = request.form.get(
            "quien_accedio",
            ""
        ).strip()

        nombre_otro = request.form.get(
            "nombre_otro",
            ""
        ).strip()

        personas = request.form.get(
            "personas",
            "1"
        ).strip()

        motivo = request.form.get(
            "motivo",
            ""
        ).strip()

        motivo_otro = request.form.get(
            "motivo_otro",
            ""
        ).strip()

        luces = request.form.get(
            "luces",
            ""
        ).strip()

        # ==============================================
        # VALIDACIONES
        # ==============================================

        if not quien_accedio:
            flash(
                "Seleccione quién accedió al auditorio.",
                "danger"
            )
            return redirect(
                url_for("acceso_auditorio")
            )

        if quien_accedio == "OTRO" and not nombre_otro:
            flash(
                "Escriba el nombre de la persona.",
                "danger"
            )
            return redirect(
                url_for("acceso_auditorio")
            )

        try:
            personas = int(personas)
        except ValueError:
            flash(
                "El número de personas no es válido.",
                "danger"
            )
            return redirect(
                url_for("acceso_auditorio")
            )

        if personas < 1:
            flash(
                "Debe registrar al menos una persona.",
                "danger"
            )
            return redirect(
                url_for("acceso_auditorio")
            )

        if not motivo:
            flash(
                "Seleccione el motivo del acceso.",
                "danger"
            )
            return redirect(
                url_for("acceso_auditorio")
            )

        if motivo == "OTRO" and not motivo_otro:
            flash(
                "Escriba el motivo.",
                "danger"
            )
            return redirect(
                url_for("acceso_auditorio")
            )

        if luces not in ["SI", "NO"]:
            flash(
                "Indique si se encendieron las luces.",
                "danger"
            )
            return redirect(
                url_for("acceso_auditorio")
            )

        # ==============================================
        # CREAR REGISTRO
        # ==============================================

        nuevo = AccesoAuditorio(
            fecha=datetime.now().strftime(
                "%d/%m/%Y"
            ),

            hora_acceso=datetime.now().strftime(
                "%H:%M:%S"
            ),

            quien_accedio=quien_accedio,

            nombre_otro=(
                nombre_otro
                if quien_accedio == "OTRO"
                else None
            ),

            personas=personas,

            motivo=motivo,

            motivo_otro=(
                motivo_otro
                if motivo == "OTRO"
                else None
            ),

            luces=luces,

            hora_salida=None,

            guardia=current_user.usuario
        )

        db.session.add(nuevo)
        db.session.commit()

        flash(
            "Acceso al auditorio registrado correctamente.",
            "success"
        )

        return redirect(
            url_for("acceso_auditorio")
        )
    # ==============================================
    # FILTROS
    # ==============================================

    buscar = request.args.get(
        "buscar",
        ""
    ).strip()

    fecha_inicio = request.args.get(
        "fecha_inicio",
        ""
    ).strip()

    fecha_fin = request.args.get(
        "fecha_fin",
        ""
    ).strip()

    motivo_filtro = request.args.get(
        "motivo_filtro",
        ""
    ).strip()

    estado_filtro = request.args.get(
        "estado_filtro",
        ""
    ).strip()


    # ==============================================
    # CONSULTA BASE
    # ==============================================

    consulta = AccesoAuditorio.query


    # ==============================================
    # BÚSQUEDA POR PERSONA
    # ==============================================

    if buscar:

        consulta = consulta.filter(
            db.or_(
                AccesoAuditorio.quien_accedio.ilike(
                    f"%{buscar}%"
                ),
                AccesoAuditorio.nombre_otro.ilike(
                    f"%{buscar}%"
                )
            )
        )


        # ==============================================
    # FILTRO POR MOTIVO
    # ==============================================

    if motivo_filtro:

        consulta = consulta.filter(
            AccesoAuditorio.motivo == motivo_filtro
        )


    # ==============================================
    # FILTRO POR ESTADO
    # ==============================================

    if estado_filtro == "dentro":

        consulta = consulta.filter(
            AccesoAuditorio.hora_salida.is_(None)
        )

    elif estado_filtro == "salida":

        consulta = consulta.filter(
            AccesoAuditorio.hora_salida.isnot(None)
        )


    # ==============================================
    # OBTENER REGISTROS
    # ==============================================

    registros = consulta.all()


    # ==============================================
    # FILTRO POR FECHAS
    # ==============================================

    if fecha_inicio or fecha_fin:

        registros_filtrados = []

        fecha_inicio_obj = None
        fecha_fin_obj = None


        # ------------------------------------------
        # FECHA INICIAL
        # ------------------------------------------

        if fecha_inicio:

            try:

                fecha_inicio_obj = datetime.strptime(
                    fecha_inicio,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                flash(
                    "La fecha inicial no es válida.",
                    "danger"
                )

                return redirect(
                    url_for("acceso_auditorio")
                )


        # ------------------------------------------
        # FECHA FINAL
        # ------------------------------------------

        if fecha_fin:

            try:

                fecha_fin_obj = datetime.strptime(
                    fecha_fin,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                flash(
                    "La fecha final no es válida.",
                    "danger"
                )

                return redirect(
                    url_for("acceso_auditorio")
                )


        # ------------------------------------------
        # REVISAR CADA REGISTRO
        # ------------------------------------------

        for registro in registros:

            try:

                fecha_registro = datetime.strptime(
                    registro.fecha,
                    "%d/%m/%Y"
                ).date()

            except (ValueError, TypeError):

                continue


            # --------------------------------------
            # FECHA INICIAL
            # --------------------------------------

            if (
                fecha_inicio_obj
                and fecha_registro < fecha_inicio_obj
            ):

                continue


            # --------------------------------------
            # FECHA FINAL
            # --------------------------------------

            if (
                fecha_fin_obj
                and fecha_registro > fecha_fin_obj
            ):

                continue


            registros_filtrados.append(
                registro
            )


        registros = registros_filtrados


    # ==============================================
    # ORDEN DE LOS REGISTROS
    # ==============================================

    registros.sort(
        key=lambda registro: (
            registro.hora_salida is not None,
            -registro.id
        )
    )


    # ==============================================
    # PERSONAS ACTUALMENTE DENTRO
    # ==============================================

    personas_dentro = sum(
        registro.personas
        for registro in registros
        if registro.hora_salida is None
    )


    # ==============================================
    # MOSTRAR PÁGINA
    # ==============================================

    return render_template(
        "acceso_auditorio.html",
        registros=registros,
        personas_dentro=personas_dentro,
        personas_auditorio=PERSONAS_AUDITORIO,
        motivos_auditorio=MOTIVOS_AUDITORIO,
        buscar=buscar,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        motivo_filtro=motivo_filtro,
        estado_filtro=estado_filtro
    )

@app.route(
    "/exportar_acceso_auditorio"
)
@login_required
def exportar_acceso_auditorio():

    # ==============================================
    # RECIBIR FILTROS
    # ==============================================

    buscar = request.args.get(
        "buscar",
        ""
    ).strip()

    fecha_inicio = request.args.get(
        "fecha_inicio",
        ""
    ).strip()

    fecha_fin = request.args.get(
        "fecha_fin",
        ""
    ).strip()

    motivo_filtro = request.args.get(
        "motivo_filtro",
        ""
    ).strip()

    estado_filtro = request.args.get(
        "estado_filtro",
        ""
    ).strip()


    # ==============================================
    # CONSULTA BASE
    # ==============================================

    consulta = AccesoAuditorio.query


    # ==============================================
    # BÚSQUEDA POR PERSONA
    # ==============================================

    if buscar:

        consulta = consulta.filter(
            db.or_(
                AccesoAuditorio.quien_accedio.ilike(
                    f"%{buscar}%"
                ),
                AccesoAuditorio.nombre_otro.ilike(
                    f"%{buscar}%"
                )
            )
        )


    # ==============================================
    # FILTRO POR MOTIVO
    # ==============================================

    if motivo_filtro:

        consulta = consulta.filter(
            AccesoAuditorio.motivo == motivo_filtro
        )


    # ==============================================
    # FILTRO POR ESTADO
    # ==============================================

    if estado_filtro == "dentro":

        consulta = consulta.filter(
            AccesoAuditorio.hora_salida.is_(None)
        )

    elif estado_filtro == "salida":

        consulta = consulta.filter(
            AccesoAuditorio.hora_salida.isnot(None)
        )


    # ==============================================
    # OBTENER REGISTROS
    # ==============================================

    registros = consulta.all()


    # ==============================================
    # FILTRO POR FECHAS
    # ==============================================

    if fecha_inicio or fecha_fin:

        registros_filtrados = []

        fecha_inicio_obj = None
        fecha_fin_obj = None


        if fecha_inicio:

            try:

                fecha_inicio_obj = datetime.strptime(
                    fecha_inicio,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                flash(
                    "La fecha inicial no es válida.",
                    "danger"
                )

                return redirect(
                    url_for("acceso_auditorio")
                )


        if fecha_fin:

            try:

                fecha_fin_obj = datetime.strptime(
                    fecha_fin,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                flash(
                    "La fecha final no es válida.",
                    "danger"
                )

                return redirect(
                    url_for("acceso_auditorio")
                )


        for registro in registros:

            try:

                fecha_registro = datetime.strptime(
                    registro.fecha,
                    "%d/%m/%Y"
                ).date()

            except (ValueError, TypeError):

                continue


            if (
                fecha_inicio_obj
                and fecha_registro < fecha_inicio_obj
            ):

                continue


            if (
                fecha_fin_obj
                and fecha_registro > fecha_fin_obj
            ):

                continue


            registros_filtrados.append(
                registro
            )


        registros = registros_filtrados


    # ==============================================
    # ORDENAR
    # ==============================================

    registros.sort(
        key=lambda registro: (
            registro.hora_salida is not None,
            -registro.id
        )
    )


    # ==============================================
    # CREAR ARCHIVO EXCEL
    # ==============================================

    wb = Workbook()

    ws = wb.active

    ws.title = "Acceso Auditorio"


    # ==============================================
    # ENCABEZADO
    # ==============================================

    ws["A1"] = "REPORTE DE ACCESO AL AUDITORIO"

    ws["A2"] = (
        "Generado el: "
        + datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )
    )


    # ==============================================
    # COLUMNAS
    # ==============================================

    encabezados = [
        "ID",
        "Fecha",
        "Hora acceso",
        "Quién accedió",
        "Nombre",
        "Personas",
        "Motivo",
        "Motivo otro",
        "Luces",
        "Hora salida",
        "Estado",
        "Guardia"
    ]

    ws.append([])

    ws.append(encabezados)


    # ==============================================
    # REGISTROS
    # ==============================================

    for registro in registros:

        nombre = (
            registro.nombre_otro
            if registro.quien_accedio == "OTRO"
            else ""
        )

        estado = (
            "DENTRO DEL AUDITORIO"
            if not registro.hora_salida
            else "SALIDA REGISTRADA"
        )

        ws.append([
            registro.id,
            registro.fecha,
            registro.hora_acceso,
            registro.quien_accedio,
            nombre,
            registro.personas,
            registro.motivo,
            registro.motivo_otro or "",
            registro.luces,
            registro.hora_salida or "",
            estado,
            registro.guardia
        ])


    # ==============================================
    # ANCHO DE COLUMNAS
    # ==============================================

    anchos = {
        "A": 8,
        "B": 14,
        "C": 14,
        "D": 22,
        "E": 25,
        "F": 12,
        "G": 20,
        "H": 25,
        "I": 12,
        "J": 14,
        "K": 25,
        "L": 20
    }

    for columna, ancho in anchos.items():

        ws.column_dimensions[
            columna
        ].width = ancho


    # ==============================================
    # ARCHIVO EN MEMORIA
    # ==============================================

    archivo = BytesIO()

    wb.save(archivo)

    archivo.seek(0)


    # ==============================================
    # DESCARGAR
    # ==============================================

    return send_file(
        archivo,
        as_attachment=True,
        download_name=(
            "reporte_acceso_auditorio.xlsx"
        ),
        mimetype=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        )
    )

@app.route(
    "/registrar_salida_auditorio/<int:id>"
)
@login_required
def registrar_salida_auditorio(id):

    registro = (
        AccesoAuditorio.query
        .get_or_404(id)
    )
    
    # ==============================================
    # EVITAR REGISTRAR SALIDA DOS VECES
    # ==============================================

    if registro.hora_salida:
        flash(
            "La salida de este registro ya fue realizada.",
            "warning"
        )

        return redirect(
            url_for("acceso_auditorio")
        )

    # ==============================================
    # REGISTRAR HORA DE SALIDA
    # ==============================================

    registro.hora_salida = (
        datetime.now().strftime(
            "%H:%M:%S"
        )
    )

    db.session.commit()

    flash(
        "Salida del auditorio registrada correctamente.",
        "success"
    )

    return redirect(
        url_for("acceso_auditorio")
    )

@app.route(
    "/registro_vip",
    methods=["GET", "POST"]
)
@login_required
def registro_vip():

    if request.method == "POST":

        nuevo = RegistroVIP(
            fecha=datetime.now().strftime(
                "%d/%m/%Y %H:%M:%S"
            ),
            vip=request.form["vip"],
            movimiento=request.form["movimiento"],
            puesto=request.form["puesto"],
            guardia=current_user.usuario
        )

        db.session.add(nuevo)
        db.session.commit()

        flash(
            "Registro VIP guardado.",
            "success"
        )

        return redirect(
            url_for("registro_vip")
        )

    return render_template(
        "registro_vip.html"
    )

@app.route("/control_vehiculos", methods=["GET", "POST"])
@login_required
def control_vehiculos():

    if request.method == "POST":

        fecha = datetime.now().strftime("%d/%m/%Y")
        hora = datetime.now().strftime("%H:%M:%S")

        nuevo = ControlVehiculo(

            fecha=fecha,
            hora=hora,
            chofer=request.form["chofer"],
            vehiculo=request.form["vehiculo"],
            movimiento=request.form["movimiento"],
            puesto=request.form["puesto"],
            guardia=current_user.usuario

        )

        db.session.add(nuevo)
        db.session.commit()

        flash(
            "Movimiento registrado correctamente.",
            "success"
        )

        return redirect(
            url_for("control_vehiculos")
        )

    movimientos = ControlVehiculo.query.order_by(
        ControlVehiculo.id.desc()
    ).all()

    return render_template(
        "control_vehiculos.html",
        movimientos=movimientos
    )

@app.route("/historial_vip")
@login_required
def historial_vip():

    if current_user.rol != "admin":
        flash(
            "No tiene permisos para acceder a esta página.",
            "danger"
        )
        return redirect(
            url_for("dashboard")
        )

    datos = (
        RegistroVIP.query
        .order_by(
            RegistroVIP.id.desc()
        )
        .all()
    )

    return render_template(
        "historial_vip.html",
        registros=datos
    )
@app.route(
    "/recibir_bitacora/<int:id>"
)
@login_required
def recibir_bitacora(id):

    registro = (
        BitacoraTurno.query
        .get_or_404(id)
    )

    if not registro.recibido:
        registro.recibido = True
        registro.recibido_por = (
            current_user.usuario
        )

        db.session.commit()

        flash(
            "Bitácora recibida.",
            "success"
        )

    return redirect(
        url_for("bitacora_turno")
    )

@app.route("/administracion")
@login_required
def administracion():

    if current_user.rol != "admin":

        flash(
            "No tiene permisos.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "administracion.html"
    )

@app.route("/crear_respaldo")
@login_required
def crear_respaldo():

    # Solo el administrador puede crear respaldos
    if current_user.rol != "admin":
        flash(
            "No tienes permisos.",
            "danger"
        )
        return redirect(url_for("dashboard"))

    carpeta_backups = RUTA_BACKUPS

    origen = RUTA_DB

    os.makedirs(
        carpeta_backups,
        exist_ok=True
    )

    origen = "/montesion/vigilancia/ibfms.db"

    fecha = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    destino = os.path.join(
        carpeta_backups,
        f"ibfms_{fecha}.db"
    )

    shutil.copy2(
        origen,
        destino
    )

    flash(
        "Respaldo creado correctamente.",
        "success"
    )

    return redirect(
        url_for("respaldos")
    )

@app.route("/respaldos")
@login_required
def respaldos():

    if current_user.rol != "admin":
        return redirect(url_for("dashboard"))

    carpeta = RUTA_BACKUPS

    os.makedirs(
        carpeta,
        exist_ok=True
    )

    archivos = sorted(
        os.listdir(carpeta),
        reverse=True
    )

    return render_template(
        "respaldos.html",
        archivos=archivos
    )

@app.route("/restaurar_respaldo/<nombre>")
@login_required
def restaurar_respaldo(nombre):

    if current_user.rol != "admin":
        flash("No tienes permisos.", "danger")
        return redirect(url_for("dashboard"))

    origen = os.path.join(
    RUTA_BACKUPS,
    nombre
    )

    destino = RUTA_DB    

    if not os.path.exists(origen):

        flash("El respaldo no existe.", "danger")
        return redirect(url_for("respaldos"))

    shutil.copy2(origen, destino)

    flash(
        "Respaldo restaurado correctamente. Reinicia la aplicación.",
        "success"
    )

    return redirect(url_for("respaldos"))

@app.route("/eliminar_respaldo/<nombre>")
@login_required
def eliminar_respaldo(nombre):

    if current_user.rol != "admin":

        flash(
            "No tienes permisos.",
            "danger"
        )

        return redirect(url_for("dashboard"))

    archivo = os.path.join(
    RUTA_BACKUPS,
    nombre
    )

    archivos = os.listdir(RUTA_BACKUPS)

    if not os.path.exists(archivo):

        flash(
            "El respaldo no existe.",
            "warning"
        )

        return redirect(url_for("respaldos"))

    archivos = os.listdir("/montesion/vigilancia/backups")

    if len(archivos) <= 1:

        flash(
            "No se puede eliminar el último respaldo.",
            "warning"
        )

        return redirect(url_for("respaldos"))

    os.remove(archivo)

    flash(
        "Respaldo eliminado correctamente.",
        "success"
    )

    return redirect(url_for("respaldos"))
@app.route(
    "/objetos_custodia",
    methods=["GET", "POST"]
)

@login_required
def objetos_custodia():

    if request.method == "POST":

        ultimo = (
            ObjetoCustodia.query
            .order_by(
                ObjetoCustodia.id.desc()
            )
            .first()
        )

        if ultimo:
            siguiente = ultimo.id + 1
        else:
            siguiente = 1

        numero = f"OC-{siguiente:04d}"

        nuevo = ObjetoCustodia(
            numero_registro=numero,

            fecha_recepcion=datetime.now().strftime(
                "%d/%m/%Y %H:%M:%S"
            ),

            tipo_objeto=request.form[
                "tipo_objeto"
            ],

            descripcion=request.form[
                "descripcion"
            ],

            entregado_por=request.form[
                "entregado_por"
            ],

            recibido_por=current_user.usuario,

            puesto_recepcion=request.form[
                "puesto_recepcion"
            ],

            observaciones_recepcion=request.form.get(
                "observaciones_recepcion",
                ""
            ),

            estado="En custodia"
        )

        db.session.add(nuevo)
        db.session.commit()

        flash(
            f"Objeto {numero} registrado correctamente.",
            "success"
        )

        return redirect(
            url_for("objetos_custodia")
        )

    # ==============================
    # BUSQUEDA
    # ==============================

    busqueda = request.args.get(
        "buscar",
        ""
    ).strip()

    # ==============================
    # CONSULTA GENERAL
    # TODOS PUEDEN VER LOS OBJETOS
    # ==============================

    consulta = ObjetoCustodia.query

    # ==============================
    # APLICAR BUSQUEDA
    # ==============================

    if busqueda:

        consulta = consulta.filter(
            db.or_(

                ObjetoCustodia.numero_registro.ilike(
                    f"%{busqueda}%"
                ),

                ObjetoCustodia.tipo_objeto.ilike(
                    f"%{busqueda}%"
                ),

                ObjetoCustodia.descripcion.ilike(
                    f"%{busqueda}%"
                ),

                ObjetoCustodia.entregado_por.ilike(
                    f"%{busqueda}%"
                ),

                ObjetoCustodia.recibido_por.ilike(
                    f"%{busqueda}%"
                ),

                ObjetoCustodia.entregado_a.ilike(
                    f"%{busqueda}%"
                ),

                ObjetoCustodia.entregado_por_guardia.ilike(
                    f"%{busqueda}%"
                ),

                ObjetoCustodia.observaciones_recepcion.ilike(
                    f"%{busqueda}%"
                ),

                ObjetoCustodia.observaciones_entrega.ilike(
                    f"%{busqueda}%"
                )
            )
        )

    # ==============================
    # ORDENAR
    # ==============================

    datos = (
        consulta
        .order_by(
            ObjetoCustodia.id.desc()
        )
        .all()
    )

    # ==============================
    # SEPARAR POR ESTADO
    # ==============================

    objetos_custodia_actual = [
        objeto
        for objeto in datos
        if objeto.estado == "En custodia"
    ]

    objetos_entregados = [
        objeto
        for objeto in datos
        if objeto.estado == "Entregado"
    ]

    return render_template(
        "objetos_custodia.html",
        objetos_custodia=objetos_custodia_actual,
        objetos_entregados=objetos_entregados
    )

@app.route(
    "/entregar_objeto/<int:id>",
    methods=["GET", "POST"]
)
@login_required
def entregar_objeto(id):

    objeto = ObjetoCustodia.query.get_or_404(id)

    # ==============================
    # VERIFICAR ESTADO
    # ==============================

    if objeto.estado == "Entregado":

        flash(
            "Este objeto ya fue entregado.",
            "warning"
        )

        return redirect(
            url_for("objetos_custodia")
        )

    # ==============================
    # REGISTRAR ENTREGA
    # ==============================

    if request.method == "POST":

        # Fecha y hora automática
        objeto.fecha_entrega = (
            datetime.now().strftime(
                "%d/%m/%Y %H:%M:%S"
            )
        )

        # Persona que recibe el objeto
        objeto.entregado_a = request.form[
            "entregado_a"
        ]

        # Vigilante que realiza la entrega
        objeto.entregado_por_guardia = (
            current_user.usuario
        )

        # Se conserva el mismo puesto
        # donde fue recibido
        objeto.puesto_entrega = (
            objeto.puesto_recepcion
        )

        # Observaciones de la entrega
        objeto.observaciones_entrega = (
            request.form.get(
                "observaciones_entrega",
                ""
            )
        )

        # Cambiar estado
        objeto.estado = "Entregado"

        db.session.commit()

        flash(
            f"Objeto {objeto.numero_registro} "
            "entregado correctamente.",
            "success"
        )

        return redirect(
            url_for("objetos_custodia")
        )

    return render_template(
        "entregar_objeto.html",
        objeto=objeto
    )

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(
        host="127.0.0.1",
        port=5001,
        debug=True
    )