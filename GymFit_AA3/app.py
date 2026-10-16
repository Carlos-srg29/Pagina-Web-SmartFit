"""Aplicación web GymFit: proyecto académico AA3 basado en la versión AA2."""

import os
import re
from datetime import datetime
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, g, jsonify, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from database import get_db_connection, init_db
from models import Cliente, Entrenador, Rutina
from utils import manejar_errores, ordenar_por_nombre, calcular_minutos_progreso


load_dotenv()

# En Render se exige que las claves iniciales no queden publicadas como valores predeterminados.
if os.getenv("RENDER"):
    required_env = ["SECRET_KEY", "ADMIN_PASSWORD", "TRAINER_PASSWORD"]
    missing_env = [name for name in required_env if not os.getenv(name)]
    if missing_env:
        raise RuntimeError(
            "Configura estas variables en Render antes de desplegar: " + ", ".join(missing_env)
        )

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "gymfit-local-key-change-before-publishing"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(os.getenv("RENDER")),
    MAX_CONTENT_LENGTH=1 * 1024 * 1024,
)

init_db()

OBJETIVOS_VALIDOS = {"Bajar de peso", "Aumentar masa muscular"}
NIVELES_VALIDOS = {"Fácil", "Básico", "Avanzado"}
ROLES_ADMINISTRABLES = {"cliente", "entrenador"}


def _text(value):
    return str(value).strip() if value is not None else ""


def _optional_number(value, label, minimum, maximum):
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} debe ser un número.")
    if number < minimum or number > maximum:
        raise ValueError(f"{label} debe estar entre {minimum} y {maximum}.")
    return round(number, 1)


def _validated_age(value):
    try:
        age = int(value)
    except (ValueError, TypeError):
        raise ValueError("La edad debe ser un número entero.")
    if age < 14 or age > 100:
        raise ValueError("La edad debe estar entre 14 y 100 años.")
    return age


def _validated_email(value):
    correo = _text(value).lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", correo):
        raise ValueError("Ingresa un correo electrónico válido.")
    return correo


def _public_user(row):
    """Devuelve los datos visibles y nunca devuelve la contraseña."""
    if row is None:
        return None
    user = dict(row)
    user.pop("password", None)
    user["activo"] = bool(user.get("activo", 1))
    if user.get("peso") is not None:
        user["peso"] = float(user["peso"])
    if user.get("estatura") is not None:
        user["estatura"] = float(user["estatura"])
    return user


def _load_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if user is None or not user["activo"]:
        session.clear()
        return None
    return dict(user)


def require_roles(*roles):
    """Valida el inicio de sesión y los permisos en el servidor."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = _load_current_user()
            if user is None:
                return jsonify({"success": False, "message": "Inicia sesión para continuar."}), 401
            if roles and user["rol"] not in roles:
                return jsonify({"success": False, "message": "No tienes permiso para entrar a esta sección."}), 403
            g.current_user = user
            return func(*args, **kwargs)
        return wrapper
    return decorator


def _client_object(row):
    return Cliente(
        row["id"], row["nombre"], row["apellido"], row["correo"], row["edad"],
        row["objetivo"] or "", row["nivel"] or "", row["peso"], row["estatura"]
    )


def _history_for(user_id):
    conn = get_db_connection()
    records = conn.execute(
        """SELECT id, objetivo, nivel, minutos, fecha
           FROM historial_entrenamientos WHERE usuario_id = ? ORDER BY id DESC""",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(record) for record in records]


def _history_response(user_id):
    records = _history_for(user_id)
    return {
        "historial": records,
        "total_entrenamientos": len(records),
        "total_minutos": calcular_minutos_progreso(records),
    }


@app.route("/")
def index():
    whatsapp_number = re.sub(r"\D", "", os.getenv("WHATSAPP_NUMBER", ""))
    return render_template("index.html", whatsapp_number=whatsapp_number)


@app.get("/api/config")
def config_publica():
    return jsonify({"success": True, "whatsapp_configurado": bool(os.getenv("WHATSAPP_NUMBER", "").strip())})


@app.post("/api/registro")
@manejar_errores
def registro():
    data = request.get_json(silent=True) or {}
    nombre = _text(data.get("nombre"))
    apellido = _text(data.get("apellido"))
    correo = _validated_email(data.get("correo"))
    password = str(data.get("password", ""))
    edad = _validated_age(data.get("edad"))
    peso = _optional_number(data.get("peso"), "El peso", 25, 300)
    estatura = _optional_number(data.get("estatura"), "La estatura", 100, 250)
    objetivo = _text(data.get("objetivo"))
    nivel = _text(data.get("nivel"))

    if not nombre or not apellido:
        return jsonify({"success": False, "message": "Completa tu nombre y apellido."}), 400
    if len(password) < 8:
        return jsonify({"success": False, "message": "La contraseña debe tener al menos 8 caracteres."}), 400
    if bool(objetivo) != bool(nivel):
        return jsonify({"success": False, "message": "Selecciona un objetivo y un nivel, o deja ambos sin seleccionar."}), 400
    if objetivo and objetivo not in OBJETIVOS_VALIDOS:
        return jsonify({"success": False, "message": "Selecciona un objetivo válido."}), 400
    if nivel and nivel not in NIVELES_VALIDOS:
        return jsonify({"success": False, "message": "Selecciona un nivel válido."}), 400

    conn = get_db_connection()
    trainer = conn.execute(
        "SELECT id FROM usuarios WHERE rol = 'entrenador' AND activo = 1 ORDER BY id LIMIT 1"
    ).fetchone()
    try:
        conn.execute(
            """INSERT INTO usuarios
               (nombre, apellido, correo, password, edad, peso, estatura, objetivo, nivel,
                rol, activo, entrenador_id, creado_en)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'cliente', 1, ?, CURRENT_TIMESTAMP)""",
            (nombre, apellido, correo, generate_password_hash(password), edad, peso, estatura,
             objetivo, nivel, trainer["id"] if trainer else None),
        )
        conn.commit()
    except Exception as error:
        conn.close()
        if "UNIQUE" in str(error).upper():
            return jsonify({"success": False, "message": "Ese correo ya está registrado."}), 409
        raise
    conn.close()
    return jsonify({"success": True, "message": "Cuenta creada. Ya puedes iniciar sesión."}), 201


@app.post("/api/login")
@manejar_errores
def login():
    data = request.get_json(silent=True) or {}
    correo = _validated_email(data.get("correo"))
    password = str(data.get("password", ""))
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM usuarios WHERE correo = ?", (correo,)).fetchone()
    if row is None or not row["activo"]:
        conn.close()
        return jsonify({"success": False, "message": "Correo o contraseña incorrectos, o cuenta desactivada."}), 401

    stored_password = row["password"] or ""
    valid_password = False
    try:
        valid_password = check_password_hash(stored_password, password)
    except (ValueError, TypeError):
        valid_password = False
    # Compatibilidad con cuentas creadas en la primera versión AA2 (contraseña sin cifrar).
    if not valid_password and stored_password == password:
        valid_password = True
        conn.execute(
            "UPDATE usuarios SET password = ? WHERE id = ?",
            (generate_password_hash(password), row["id"]),
        )
        conn.commit()
    conn.close()

    if not valid_password:
        return jsonify({"success": False, "message": "Correo o contraseña incorrectos."}), 401

    session.clear()
    session["user_id"] = row["id"]
    current = _load_current_user()
    # POO: al iniciar sesión se crea el objeto que corresponde al rol de la cuenta.
    if current["rol"] == "entrenador":
        actor = Entrenador(
            current["id"], current["nombre"], current["apellido"],
            current["correo"], current["edad"]
        )
        public_data = actor.to_dict()
    elif current["rol"] == "cliente":
        public_data = _client_object(current).to_dict()
    else:
        public_data = _public_user(current)
    return jsonify({"success": True, "user": public_data})


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Sesión cerrada."})


@app.get("/api/me")
def me():
    user = _load_current_user()
    if user is None:
        return jsonify({"success": False, "message": "No hay una sesión activa."}), 401
    return jsonify({"success": True, "user": _public_user(user)})


@app.post("/api/cliente/perfil")
@manejar_errores
@require_roles("cliente")
def actualizar_perfil_cliente():
    data = request.get_json(silent=True) or {}
    edad = _validated_age(data.get("edad"))
    peso = _optional_number(data.get("peso"), "El peso", 25, 300)
    estatura = _optional_number(data.get("estatura"), "La estatura", 100, 250)
    objetivo = _text(data.get("objetivo"))
    nivel = _text(data.get("nivel"))
    if objetivo not in OBJETIVOS_VALIDOS or nivel not in NIVELES_VALIDOS:
        return jsonify({"success": False, "message": "Selecciona un objetivo y un nivel válidos."}), 400

    cliente = Cliente(
        g.current_user["id"], g.current_user["nombre"], g.current_user["apellido"],
        g.current_user["correo"], edad, objetivo, nivel, peso, estatura
    )
    conn = get_db_connection()
    conn.execute(
        """UPDATE usuarios SET edad = ?, peso = ?, estatura = ?, objetivo = ?, nivel = ?
           WHERE id = ? AND rol = 'cliente'""",
        (edad, peso, estatura, cliente.objetivo, cliente.nivel, cliente.id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM usuarios WHERE id = ?", (cliente.id,)).fetchone()
    conn.close()
    return jsonify({"success": True, "message": "Tus datos se guardaron correctamente.", "user": _public_user(row)})


@app.get("/api/cliente/rutina")
@manejar_errores
@require_roles("cliente")
def obtener_rutina_cliente():
    objetivo = _text(g.current_user.get("objetivo"))
    nivel = _text(g.current_user.get("nivel"))
    rutina = Rutina(objetivo, nivel)
    if not rutina.existe():
        return jsonify({"success": False, "message": "Guarda primero tu objetivo y nivel en tu perfil."}), 400
    cliente = Cliente(
        g.current_user["id"], g.current_user["nombre"], g.current_user["apellido"],
        g.current_user["correo"], g.current_user["edad"], objetivo, nivel,
        g.current_user.get("peso"), g.current_user.get("estatura")
    )
    return jsonify({"success": True, "rutina": rutina.obtener_datos(), "cliente": cliente.to_dict()})


@app.post("/api/cliente/entrenamientos")
@manejar_errores
@require_roles("cliente")
def registrar_entrenamiento_cliente():
    data = request.get_json(silent=True) or {}
    try:
        minutos = int(data.get("minutos", 0))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Ingresa los minutos con un número entero."}), 400
    if minutos < 1 or minutos > 600:
        return jsonify({"success": False, "message": "Los minutos deben estar entre 1 y 600."}), 400
    if not Rutina(g.current_user.get("objetivo", ""), g.current_user.get("nivel", "")).existe():
        return jsonify({"success": False, "message": "Guarda tu objetivo y nivel antes de registrar un entrenamiento."}), 400

    conn = get_db_connection()
    conn.execute(
        """INSERT INTO historial_entrenamientos (usuario_id, objetivo, nivel, minutos, fecha)
           VALUES (?, ?, ?, ?, ?)""",
        (g.current_user["id"], g.current_user["objetivo"], g.current_user["nivel"],
         minutos, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Entrenamiento agregado a tu historial."}), 201


@app.get("/api/cliente/historial")
@manejar_errores
@require_roles("cliente")
def historial_cliente():
    data = _history_response(g.current_user["id"])
    return jsonify({"success": True, **data})


@app.get("/api/entrenador/clientes")
@manejar_errores
@require_roles("entrenador")
def clientes_entrenador():
    conn = get_db_connection()
    rows = conn.execute(
        """SELECT u.id, u.nombre, u.apellido, u.correo, u.edad, u.peso, u.estatura,
                  u.objetivo, u.nivel, u.activo, u.creado_en,
                  (SELECT COUNT(*) FROM historial_entrenamientos h WHERE h.usuario_id = u.id) AS total_entrenamientos,
                  (SELECT COALESCE(SUM(minutos), 0) FROM historial_entrenamientos h WHERE h.usuario_id = u.id) AS total_minutos
           FROM usuarios u
           WHERE u.rol = 'cliente' AND u.activo = 1 AND u.entrenador_id = ?""",
        (g.current_user["id"],),
    ).fetchall()
    conn.close()
    clients = [_public_user(row) for row in rows]
    return jsonify({"success": True, "clientes": ordenar_por_nombre(clients)})


@app.get("/api/entrenador/clientes/<int:client_id>/historial")
@manejar_errores
@require_roles("entrenador")
def historial_cliente_entrenador(client_id):
    conn = get_db_connection()
    client = conn.execute(
        "SELECT id, nombre, apellido, correo FROM usuarios WHERE id = ? AND rol = 'cliente' AND entrenador_id = ? AND activo = 1",
        (client_id, g.current_user["id"]),
    ).fetchone()
    conn.close()
    if client is None:
        return jsonify({"success": False, "message": "No tienes acceso a ese cliente."}), 404
    return jsonify({"success": True, "cliente": dict(client), **_history_response(client_id)})


@app.get("/api/admin/resumen")
@manejar_errores
@require_roles("admin")
def resumen_admin():
    conn = get_db_connection()
    stats = {
        "usuarios": conn.execute("SELECT COUNT(*) AS n FROM usuarios").fetchone()["n"],
        "clientes": conn.execute("SELECT COUNT(*) AS n FROM usuarios WHERE rol = 'cliente' AND activo = 1").fetchone()["n"],
        "entrenadores": conn.execute("SELECT COUNT(*) AS n FROM usuarios WHERE rol = 'entrenador' AND activo = 1").fetchone()["n"],
        "inactivos": conn.execute("SELECT COUNT(*) AS n FROM usuarios WHERE activo = 0").fetchone()["n"],
        "entrenamientos": conn.execute("SELECT COUNT(*) AS n FROM historial_entrenamientos").fetchone()["n"],
    }
    conn.close()
    return jsonify({"success": True, "resumen": stats})


@app.get("/api/admin/entrenadores")
@manejar_errores
@require_roles("admin")
def listar_entrenadores_admin():
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, nombre, apellido, correo FROM usuarios WHERE rol = 'entrenador' AND activo = 1 ORDER BY nombre, apellido"
    ).fetchall()
    conn.close()
    return jsonify({"success": True, "entrenadores": [dict(row) for row in rows]})


@app.get("/api/admin/usuarios")
@manejar_errores
@require_roles("admin")
def listar_usuarios_admin():
    conn = get_db_connection()
    rows = conn.execute(
        """SELECT u.id, u.nombre, u.apellido, u.correo, u.edad, u.peso, u.estatura,
                  u.objetivo, u.nivel, u.rol, u.activo, u.entrenador_id, u.creado_en,
                  t.nombre AS entrenador_nombre, t.apellido AS entrenador_apellido,
                  (SELECT COUNT(*) FROM historial_entrenamientos h WHERE h.usuario_id = u.id) AS total_entrenamientos,
                  (SELECT COALESCE(SUM(minutos), 0) FROM historial_entrenamientos h WHERE h.usuario_id = u.id) AS total_minutos
           FROM usuarios u
           LEFT JOIN usuarios t ON t.id = u.entrenador_id
           ORDER BY CASE u.rol WHEN 'admin' THEN 0 WHEN 'entrenador' THEN 1 ELSE 2 END, u.nombre, u.apellido"""
    ).fetchall()
    conn.close()
    return jsonify({"success": True, "usuarios": [_public_user(row) for row in rows]})


@app.post("/api/admin/usuarios")
@manejar_errores
@require_roles("admin")
def crear_usuario_admin():
    data = request.get_json(silent=True) or {}
    nombre = _text(data.get("nombre"))
    apellido = _text(data.get("apellido"))
    correo = _validated_email(data.get("correo"))
    password = str(data.get("password", ""))
    edad = _validated_age(data.get("edad"))
    rol = _text(data.get("rol"))
    if not nombre or not apellido:
        return jsonify({"success": False, "message": "Ingresa el nombre y apellido."}), 400
    if rol not in ROLES_ADMINISTRABLES:
        return jsonify({"success": False, "message": "Puedes crear cuentas de cliente o entrenador."}), 400
    if len(password) < 8:
        return jsonify({"success": False, "message": "La contraseña temporal debe tener al menos 8 caracteres."}), 400

    conn = get_db_connection()
    trainer_id = None
    if rol == "cliente":
        requested_trainer = data.get("entrenador_id")
        if requested_trainer not in (None, "", 0, "0"):
            trainer = conn.execute(
                "SELECT id FROM usuarios WHERE id = ? AND rol = 'entrenador' AND activo = 1",
                (int(requested_trainer),),
            ).fetchone()
            if trainer is None:
                conn.close()
                return jsonify({"success": False, "message": "Selecciona un entrenador activo."}), 400
            trainer_id = trainer["id"]
        else:
            trainer = conn.execute("SELECT id FROM usuarios WHERE rol = 'entrenador' AND activo = 1 ORDER BY id LIMIT 1").fetchone()
            trainer_id = trainer["id"] if trainer else None
    try:
        cursor = conn.execute(
            """INSERT INTO usuarios (nombre, apellido, correo, password, edad, rol, activo,
                   entrenador_id, creado_en) VALUES (?, ?, ?, ?, ?, ?, 1, ?, CURRENT_TIMESTAMP)""",
            (nombre, apellido, correo, generate_password_hash(password), edad, rol, trainer_id),
        )
        conn.commit()
        new_id = cursor.lastrowid
    except Exception as error:
        conn.close()
        if "UNIQUE" in str(error).upper():
            return jsonify({"success": False, "message": "Ya existe una cuenta con ese correo."}), 409
        raise
    conn.close()
    return jsonify({"success": True, "message": "La cuenta se creó correctamente.", "id": new_id}), 201


@app.post("/api/admin/usuarios/<int:user_id>/estado")
@manejar_errores
@require_roles("admin")
def cambiar_estado_usuario(user_id):
    data = request.get_json(silent=True) or {}
    activo = bool(data.get("activo"))
    if user_id == g.current_user["id"] and not activo:
        return jsonify({"success": False, "message": "No puedes desactivar tu propia cuenta."}), 400
    conn = get_db_connection()
    target = conn.execute("SELECT id, rol, activo FROM usuarios WHERE id = ?", (user_id,)).fetchone()
    if target is None:
        conn.close()
        return jsonify({"success": False, "message": "No se encontró la cuenta."}), 404
    if target["rol"] == "admin" and not activo:
        active_admins = conn.execute("SELECT COUNT(*) AS n FROM usuarios WHERE rol = 'admin' AND activo = 1").fetchone()["n"]
        if active_admins <= 1:
            conn.close()
            return jsonify({"success": False, "message": "Debe quedar al menos un administrador activo."}), 400
    conn.execute("UPDATE usuarios SET activo = ? WHERE id = ?", (1 if activo else 0, user_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Cuenta activada." if activo else "Cuenta desactivada."})


@app.post("/api/admin/usuarios/<int:client_id>/entrenador")
@manejar_errores
@require_roles("admin")
def asignar_entrenador(client_id):
    data = request.get_json(silent=True) or {}
    trainer_value = data.get("entrenador_id")
    conn = get_db_connection()
    client = conn.execute("SELECT id, rol FROM usuarios WHERE id = ?", (client_id,)).fetchone()
    if client is None or client["rol"] != "cliente":
        conn.close()
        return jsonify({"success": False, "message": "Solo puedes asignar entrenador a una cuenta de cliente."}), 400
    if trainer_value in (None, "", 0, "0"):
        trainer_id = None
    else:
        trainer = conn.execute(
            "SELECT id FROM usuarios WHERE id = ? AND rol = 'entrenador' AND activo = 1",
            (int(trainer_value),),
        ).fetchone()
        if trainer is None:
            conn.close()
            return jsonify({"success": False, "message": "Selecciona un entrenador activo."}), 400
        trainer_id = trainer["id"]
    conn.execute("UPDATE usuarios SET entrenador_id = ? WHERE id = ?", (trainer_id, client_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Asignación de entrenador actualizada."})


@app.get("/api/admin/usuarios/<int:user_id>/historial")
@manejar_errores
@require_roles("admin")
def historial_admin(user_id):
    conn = get_db_connection()
    user = conn.execute(
        "SELECT id, nombre, apellido, correo, rol FROM usuarios WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    if user is None:
        return jsonify({"success": False, "message": "No se encontró la cuenta."}), 404
    return jsonify({"success": True, "usuario": dict(user), **_history_response(user_id)})


@app.errorhandler(413)
def archivo_demasiado_grande(_error):
    return jsonify({"success": False, "message": "La solicitud es demasiado grande."}), 413


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
