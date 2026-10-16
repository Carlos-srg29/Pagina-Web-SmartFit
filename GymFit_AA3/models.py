"""Modelos principales de GymFit para la actividad AA3.

Se mantienen clases sencillas para representar usuarios, clientes, entrenadores y rutinas.
"""


class Usuario:
    """Clase base con los datos comunes a los usuarios del gimnasio."""

    def __init__(self, id_usuario, nombre, apellido, correo, edad, rol="cliente"):
        self.id = id_usuario
        self.nombre = nombre
        self.apellido = apellido
        self.correo = correo
        self.edad = edad
        self.rol = rol

    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}".strip()

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "apellido": self.apellido,
            "correo": self.correo,
            "edad": self.edad,
            "rol": self.rol,
        }


class Cliente(Usuario):
    """Cliente del gimnasio; agrega sus preferencias y datos físicos."""

    def __init__(self, id_usuario, nombre, apellido, correo, edad,
                 objetivo="", nivel="", peso=None, estatura=None):
        super().__init__(id_usuario, nombre, apellido, correo, edad, "cliente")
        self.objetivo = objetivo or ""
        self.nivel = nivel or ""
        self.peso = peso
        self.estatura = estatura

    def configurar_entrenamiento(self, objetivo, nivel):
        self.objetivo = objetivo
        self.nivel = nivel

    def calcular_imc(self):
        """Calcula el IMC solo si se registraron peso y estatura válidos."""
        if not self.peso or not self.estatura or self.estatura <= 0:
            return None
        return round(self.peso / ((self.estatura / 100) ** 2), 1)

    def to_dict(self):
        datos = super().to_dict()
        datos.update({
            "objetivo": self.objetivo,
            "nivel": self.nivel,
            "peso": self.peso,
            "estatura": self.estatura,
            "imc": self.calcular_imc(),
        })
        return datos


class Entrenador(Usuario):
    """Entrenador que consulta la información de los clientes asignados."""

    def __init__(self, id_usuario, nombre, apellido, correo, edad,
                 especialidad="Entrenamiento general"):
        super().__init__(id_usuario, nombre, apellido, correo, edad, "entrenador")
        self.especialidad = especialidad

    def to_dict(self):
        datos = super().to_dict()
        datos["especialidad"] = self.especialidad
        return datos


class Rutina:
    """Rutinas de ejemplo por objetivo y nivel de entrenamiento."""

    RUTINAS = {
        "Bajar de peso": {
            "Fácil": {
                "duracion": "30-45 min",
                "ejercicios": [
                    "Caminata ligera - 10 min",
                    "Bicicleta estática - 10 min",
                    "Sentadillas sin peso - 3 x 10",
                    "Movilidad y estiramiento - 5 min",
                ],
            },
            "Básico": {
                "duracion": "45-60 min",
                "ejercicios": [
                    "Caminata rápida - 10 min",
                    "Bicicleta estática - 15 min",
                    "Sentadillas - 3 x 12",
                    "Zancadas - 3 x 10",
                    "Cardio moderado - 10 min",
                ],
            },
            "Avanzado": {
                "duracion": "60 min",
                "ejercicios": [
                    "Calentamiento - 10 min",
                    "Intervalos de carrera - 15 min",
                    "Burpees - 3 x 12",
                    "Mountain climbers - 3 x 30 s",
                    "Vuelta a la calma - 5 min",
                ],
            },
        },
        "Aumentar masa muscular": {
            "Fácil": {
                "duracion": "40 min",
                "ejercicios": [
                    "Calentamiento articular - 5 min",
                    "Sentadillas asistidas - 3 x 10",
                    "Flexiones apoyando rodillas - 3 x 8",
                    "Remo con mancuernas ligeras - 3 x 10",
                ],
            },
            "Básico": {
                "duracion": "50 min",
                "ejercicios": [
                    "Sentadillas con mancuerna - 4 x 10",
                    "Press de banca o flexiones - 4 x 10",
                    "Peso muerto rumano ligero - 3 x 10",
                    "Press militar con mancuernas - 3 x 10",
                ],
            },
            "Avanzado": {
                "duracion": "60-75 min",
                "ejercicios": [
                    "Calentamiento - 10 min",
                    "Sentadilla - 4 x 6 a 8",
                    "Press de banca - 4 x 6 a 8",
                    "Remo con barra - 4 x 8",
                    "Curl de bíceps - 3 x 12",
                ],
            },
        },
    }

    def __init__(self, objetivo, nivel):
        self.objetivo = objetivo
        self.nivel = nivel

    def existe(self):
        return self.objetivo in self.RUTINAS and self.nivel in self.RUTINAS[self.objetivo]

    def generar_ejercicios(self):
        """Generador: entrega los ejercicios uno por uno mediante yield."""
        if not self.existe():
            return
        for ejercicio in self.RUTINAS[self.objetivo][self.nivel]["ejercicios"]:
            yield ejercicio

    def obtener_datos(self):
        if not self.existe():
            return None
        datos = self.RUTINAS[self.objetivo][self.nivel]
        return {
            "objetivo": self.objetivo,
            "nivel": self.nivel,
            "duracion": datos["duracion"],
            "ejercicios": list(self.generar_ejercicios()),
        }
