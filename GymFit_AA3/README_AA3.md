# GymFit - AA3

Proyecto académico para Fundamentos de Desarrollo de Software. Parte del código de AA2 y usa Python, Flask, SQLite, HTML, CSS y JavaScript.

## Funciones

- Registro e inicio de sesión de clientes.
- Perfil con edad, peso, estatura, objetivo y nivel.
- Rutinas de ejemplo e historial de entrenamientos.
- Acceso de entrenador para revisar clientes asignados.
- Acceso de administrador para ver usuarios, crear cuentas, asignar entrenadores y activar o desactivar cuentas.
- Botón de contacto por WhatsApp.

## Ejecutar localmente

Necesitas Python 3.10 o superior. Abre esta carpeta en Visual Studio Code y ejecuta en la terminal:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Luego abre `http://127.0.0.1:5000` en el navegador. La base de datos se crea automáticamente.

Cuentas iniciales de demostración (solo uso local):

- Administrador: `admin@gymfit.com` / `Admin1234!`
- Entrenador: `trainer@gymfit.com` / `Trainer1234!`

Puedes crear un cliente desde el formulario de registro. Cambia las contraseñas y configura las variables de entorno antes de publicar la aplicación.

Para que WhatsApp dirija a un número específico, configura `WHATSAPP_NUMBER` en el archivo `.env`, usando el código de país y solo dígitos.

## Render

Configura el servicio de Render con estos valores:

| Campo | Valor |
| --- | --- |
| Root Directory | `GymFit_AA3` |
| Build Command | `pip install -r requirements-render.txt` |
| Start Command | `gunicorn app:app` |

El directorio raíz debe ser `GymFit_AA3`: si apuntas a `GymFit_AA2` o a la raíz del repositorio, Render despliega otro proyecto o no encuentra `requirements.txt`.

`gunicorn` también está incluido en `requirements.txt`, así que el deploy funciona incluso si dejas el comando de build por defecto de Render (`pip install -r requirements.txt`).

Variables de entorno obligatorias: `SECRET_KEY`, `ADMIN_PASSWORD` y `TRAINER_PASSWORD`; sin ellas la aplicación no arranca en Render. Opcionales: `ADMIN_EMAIL`, `TRAINER_EMAIL` y `WHATSAPP_NUMBER`. No publiques contraseñas reales en GitHub.

La base de datos SQLite vive en el disco efímero de Render, por lo que se reinicia en cada deploy. Para conservar los datos, monta un disco persistente en `/var/data` y define `DATABASE_PATH=/var/data/gymfit.db`.
