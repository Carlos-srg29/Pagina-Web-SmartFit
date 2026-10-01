import sqlite3

DB_NAME = 'gymfit.db'


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            correo TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            edad INTEGER,
            objetivo TEXT DEFAULT '',
            nivel TEXT DEFAULT '',
            rol TEXT DEFAULT 'cliente'
        )
    ''')

    # Nuevo requerimiento AA2: historial de entrenamientos.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial_entrenamientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            objetivo TEXT NOT NULL,
            nivel TEXT NOT NULL,
            minutos INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    ''')

    cursor.execute("SELECT * FROM usuarios WHERE correo = 'trainer@gymfit.com'")
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO usuarios (nombre, apellido, correo, password, edad, rol)
            VALUES ('Entrenador', 'GymFit', 'trainer@gymfit.com', '1234', 30, 'entrenador')
        ''')

    conn.commit()
    conn.close()
    print("Base de datos creada/verificada exitosamente.")


if __name__ == '__main__':
    init_db()
