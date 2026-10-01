GYMFIT - ACTUALIZACION AA2

Esta versión parte del proyecto de la AA1 y agrega los requisitos técnicos de la AA2.

NUEVOS ARCHIVOS
- models.py: clases Usuario, Cliente, Entrenador y Rutina. Incluye herencia, objetos y generador.
- utils.py: decorador manejar_errores y funciones con Lambda.

CAMBIOS PRINCIPALES
- app.py usa las clases Cliente y Entrenador para crear objetos según el rol.
- Rutina se utiliza para generar las rutinas desde Python.
- /api/rutina devuelve la rutina usando el generador de ejercicios.
- Se agregó historial_entrenamientos a la base de datos.
- Se agregó la función para registrar entrenamientos realizados.
- Se agregó consulta del historial y cálculo de minutos acumulados.
- El panel del cliente muestra progreso e historial.
- El panel del entrenador mantiene el listado de clientes y ahora lo ordena mediante Lambda.
- Se mantiene try/except y se amplía el manejo de errores con un decorador.

COMO EJECUTAR
1. Abrir esta carpeta en Visual Studio Code.
2. Instalar dependencias:
   pip install -r requirements.txt
3. Ejecutar:
   python app.py
4. Abrir en el navegador:
   http://127.0.0.1:5000

CUENTA DEL ENTRENADOR
Correo: trainer@gymfit.com
Contraseña: 1234

REQUISITOS AA2 IMPLEMENTADOS
- Nuevos requerimientos: historial y registro de entrenamientos.
- Clases y objetos: models.py.
- Herencia: Cliente y Entrenador heredan de Usuario.
- try/except: validación de edad, datos y errores de API.
- Lambda: ordenamiento de clientes y cálculo de minutos.
- Decorador: manejar_errores.
- Generador: Rutina.generar_ejercicios() con yield.
