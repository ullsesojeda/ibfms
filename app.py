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
    Incidente
)

from datetime import datetime
import pandas as pd
from flask import send_file

app = Flask(__name__)
app.config.from_object(Config)

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

    visitantes = Visitante.query.count()

    incidentes = Incidente.query.count()

    usuarios = Usuario.query.count()

    return render_template(
        "dashboard.html",
        visitantes=visitantes,
        incidentes=incidentes,
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

    datos = (
        Visitante.query
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

    datos = (
        Incidente.query
        .order_by(Incidente.id.desc())
        .all()
    )

    return render_template(
        "incidentes.html",
        incidentes=datos
    )


if __name__ == "__main__":
    app.run(debug=True)