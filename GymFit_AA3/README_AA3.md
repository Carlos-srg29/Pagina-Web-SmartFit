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

La carpeta para configurar como directorio raíz del servicio es `GymFit_AA2` si se mezcla con el repositorio original. El comando de instalación es `pip install -r requirements-render.txt` y el comando de inicio es `gunicorn app:app`. Configura `SECRET_KEY`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `TRAINER_EMAIL`, `TRAINER_PASSWORD` y `WHATSAPP_NUMBER` en Render. No publiques contraseñas reales en GitHub.
