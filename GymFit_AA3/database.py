"""Conexión y preparación de la base de datos SQLite de GymFit."""

import os
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB = BASE_DIR / "instance" / "gymfit.db"
DB_PATH = Path(os.getenv("DATABASE_PATH", str(DEFAULT_DB)))


def get_db_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _add_column_if_missing(conn, table, column, definition):
    current_columns = {
        row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }
    if column not in current_columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _create_account_if_missing(conn, nombre, apellido, correo, password, rol, edad=30):
    exists = conn.execute("SELECT id FROM usuarios WHERE correo = ?", (correo,)).fetchone()
    if exists:
        return exists["id"]
    cursor = conn.execute(
        """INSERT INTO usuarios
           (nombre, apellido, correo, password, edad, rol, activo, creado_en)
           VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)""",
        (nombre, apellido, correo, generate_password_hash(password), edad, rol),
    )
    return cursor.lastrowid


def init_db():
    """Crea las tablas, actualiza una base AA2 existente y prepara cuentas iniciales."""
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL DEFAULT '',
            correo TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            edad INTEGER,
            objetivo TEXT DEFAULT '',
            nivel TEXT DEFAULT '',
            rol TEXT DEFAULT 'cliente',
            peso REAL,
            estatura REAL,
            activo INTEGER NOT NULL DEFAULT 1,
            entrenador_id INTEGER,
            creado_en TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (entrenador_id) REFERENCES usuarios(id)
        )
    """)
    # Permite reutilizar una base de datos creada en la versión anterior de AA2.
    _add_column_if_missing(conn, "usuarios", "peso", "REAL")
    _add_column_if_missing(conn, "usuarios", "estatura", "REAL")
    _add_column_if_missing(conn, "usuarios", "activo", "INTEGER NOT NULL DEFAULT 1")
    _add_column_if_missing(conn, "usuarios", "entrenador_id", "INTEGER")
    _add_column_if_missing(conn, "usuarios", "creado_en", "TEXT")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS historial_entrenamientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            objetivo TEXT NOT NULL,
            nivel TEXT NOT NULL,
            minutos INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    admin_email = os.getenv("ADMIN_EMAIL", "admin@gymfit.com").strip().lower()
    trainer_email = os.getenv("TRAINER_EMAIL", "trainer@gymfit.com").strip().lower()
    admin_password = os.getenv("ADMIN_PASSWORD", "Admin1234!")
    trainer_password = os.getenv("TRAINER_PASSWORD", "Trainer1234!")

    admin_id = _create_account_if_missing(
        conn, "Administrador", "GymFit", admin_email, admin_password, "admin", 30
    )
    trainer_id = _create_account_if_missing(
        conn, "Entrenador", "GymFit", trainer_email, trainer_password, "entrenador", 30
    )

    conn.execute(
        "UPDATE usuarios SET activo = 1 WHERE activo IS NULL"
    )
    conn.execute(
        "UPDATE usuarios SET creado_en = CURRENT_TIMESTAMP WHERE creado_en IS NULL OR creado_en = ''"
    )
    # Los clientes existentes en AA2 quedan asignados al entrenador inicial si no tenían uno.
    conn.execute(
        "UPDATE usuarios SET entrenador_id = ? WHERE rol = 'cliente' AND entrenador_id IS NULL",
        (trainer_id,),
    )
    conn.commit()
    conn.close()
    return {"admin_id": admin_id, "trainer_id": trainer_id}
