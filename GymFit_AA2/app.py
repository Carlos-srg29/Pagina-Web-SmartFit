import os
from datetime import datetime
import sqlite3

from flask import Flask, render_template, request, jsonify

from database import get_db_connection, init_db
from models import Cliente, Entrenador, Rutina
from utils import manejar_errores, ordenar_por_nombre, calcular_minutos_progreso

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'gymfit-aa2')

# Verifica que las tablas nuevas de AA2 existan al iniciar la aplicación.
init_db()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/registro', methods=['POST'])
@manejar_errores
def registro():
    data = request.get_json() or {}

    nombre = str(data['nombre']).strip()
    apellido = str(data.get('apellido', '')).strip()
    correo = str(data['correo']).strip().lower()
    password = str(data['password'])

    # try/except: validación de edad para evitar que un dato incorrecto detenga el programa.
    try:
        edad = int(data.get('edad', 0))
        if edad < 0 or edad > 120:
            raise ValueError('La edad debe estar entre 0 y 120.')
    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "La edad debe ser un número válido entre 0 y 120."
        }), 400

    if not nombre or not correo or not password:
        return jsonify({
            "success": False,
            "message": "Completa los campos requeridos."
        }), 400

    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO usuarios (nombre, apellido, correo, password, edad)
            VALUES (?, ?, ?, ?, ?)
        ''', (nombre, apellido, correo, password, edad))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"success": False, "message": "El correo ya está registrado"}), 400
    except Exception:
        conn.close()
        raise
    conn.close()

    return jsonify({"success": True, "message": "Usuario registrado exitosamente"})


@app.route('/api/login', methods=['POST'])
@manejar_errores
def login():
    data = request.get_json() or {}
    correo = str(data['correo']).strip().lower()
    password = str(data['password'])

    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM usuarios WHERE correo = ? AND password = ?',
        (correo, password)
    ).fetchone()
    conn.close()

    if not user:
        return jsonify({"success": False, "message": "Correo o contraseña incorrectos"}), 401

    # Objetos + herencia: se instancia Cliente o Entrenador según el rol.
    if user['rol'] == 'entrenador':
        usuario = Entrenador(
            user['id'], user['nombre'], user['apellido'], user['correo'], user['edad']
        )
    else:
        usuario = Cliente(
            user['id'], user['nombre'], user['apellido'], user['correo'], user['edad'],
            user['objetivo'], user['nivel']
        )

    return jsonify({"success": True, "user": usuario.to_dict()})


@app.route('/api/actualizar-perfil', methods=['POST'])
@manejar_errores
def actualizar_perfil():
    data = request.get_json() or {}
    user_id = int(data['user_id'])
    objetivo = str(data['objetivo']).strip()
    nivel = str(data['nivel']).strip()

    # Se utiliza el objeto Cliente para validar la combinación seleccionada.
    cliente = Cliente(user_id, '', '', '', 0, objetivo, nivel)
    rutina = Rutina(cliente.objetivo, cliente.nivel)

    if not rutina.existe():
        return jsonify({"success": False, "message": "Objetivo o nivel no válido."}), 400

    conn = get_db_connection()
    conn.execute('''
        UPDATE usuarios
        SET objetivo = ?, nivel = ?
        WHERE id = ? AND rol = 'cliente'
    ''', (cliente.objetivo, cliente.nivel, cliente.id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Preferencias guardadas con éxito"})


@app.route('/api/rutina', methods=['POST'])
@manejar_errores
def obtener_rutina():
    data = request.get_json() or {}
    rutina = Rutina(str(data['objetivo']), str(data['nivel']))

    if not rutina.existe():
        return jsonify({"success": False, "message": "No existe una rutina para esa selección."}), 404

    # Generador: Rutina.generar_ejercicios() utiliza yield y entrega un ejercicio por vez.
    datos = rutina.obtener_datos()
    return jsonify({"success": True, "rutina": datos})


@app.route('/api/registrar-entrenamiento', methods=['POST'])
@manejar_errores
def registrar_entrenamiento():
    """Nuevo requerimiento AA2: registrar un entrenamiento realizado."""
    data = request.get_json() or {}
    usuario_id = int(data['user_id'])
    objetivo = str(data['objetivo']).strip()
    nivel = str(data['nivel']).strip()
    minutos = int(data['minutos'])

    if minutos <= 0 or minutos > 600:
        return jsonify({"success": False, "message": "Los minutos deben estar entre 1 y 600."}), 400

    rutina = Rutina(objetivo, nivel)
    if not rutina.existe():
        return jsonify({"success": False, "message": "Rutina no válida."}), 400

    fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO historial_entrenamientos (usuario_id, objetivo, nivel, minutos, fecha)
        VALUES (?, ?, ?, ?, ?)
    ''', (usuario_id, objetivo, nivel, minutos, fecha))
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Entrenamiento registrado correctamente."
    })


@app.route('/api/historial/<int:user_id>', methods=['GET'])
@manejar_errores
def historial_usuario(user_id):
    conn = get_db_connection()
    registros = conn.execute('''
        SELECT id, objetivo, nivel, minutos, fecha
        FROM historial_entrenamientos
        WHERE usuario_id = ?
        ORDER BY id DESC
    ''', (user_id,)).fetchall()
    conn.close()

    historial = [dict(registro) for registro in registros]
    total_minutos = calcular_minutos_progreso(historial)  # Lambda

    return jsonify({
        "success": True,
        "historial": historial,
        "total_minutos": total_minutos,
        "total_entrenamientos": len(historial)
    })


@app.route('/api/entrenador/clientes', methods=['GET'])
@manejar_errores
def obtener_clientes():
    conn = get_db_connection()
    filas = conn.execute('''
        SELECT id, nombre, apellido, correo, edad, objetivo, nivel
        FROM usuarios
        WHERE rol = 'cliente'
    ''').fetchall()
    conn.close()

    # Objetos + herencia: cada fila se convierte en un objeto Cliente.
    clientes = [
        Cliente(
            fila['id'], fila['nombre'], fila['apellido'], fila['correo'], fila['edad'],
            fila['objetivo'], fila['nivel']
        ).to_dict()
        for fila in filas
    ]

    # Lambda: ordena los clientes alfabéticamente por nombre completo.
    clientes = ordenar_por_nombre(clientes)

    return jsonify({"success": True, "clientes": clientes})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
