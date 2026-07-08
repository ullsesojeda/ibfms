import os
import shutil
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

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
    ControlVehiculo
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

@app.route(
    "/registrar_salida/<int:id>"
)
@login_required
def registrar_salida(id):

    visitante = Visitante.query.get_or_404(id)

    visitante.salida = (
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
        url_for("visitantes")
    )

@app.route(
    "/exportar_visitantes"
)
@login_required
def exportar_visitantes():

    datos = Visitante.query.all()

    lista = []

    for v in datos:
        lista.append({
            "Fecha": v.fecha,
            "Nombre": v.nombre,
            "Identificación": v.identificacion,
            "Placas": v.placas,
            "Vehículo": v.vehiculo,
            "Visita": v.visita,
            "Motivo": v.motivo,
            "Entrada": v.entrada,
            "Salida": v.salida,
            "Guardia": v.guardia
        })

    df = pd.DataFrame(lista)

    archivo = "visitantes.xlsx"

    df.to_excel(
        archivo,
        index=False
    )

    return send_file(
        archivo,
        as_attachment=True
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

    if current_user.rol == "admin":
   
        datos = (
        Visitante.query
        .order_by(Visitante.id.desc())
        .all()
    )
    else:
         datos = (
        Visitante.query
        .filter_by(
            guardia=current_user.usuario
        )
        .order_by(Visitante.id.desc())
        .all()
    )

    return render_template(
        "visitantes.html",
        visitantes=datos
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

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)