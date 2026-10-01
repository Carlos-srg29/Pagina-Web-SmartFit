"""Clases principales de GymFit para la AA2.
Implementa orientación a objetos, objetos, herencia y generadores.
"""


class Usuario:
    """Clase padre para los usuarios de GymFit."""

    def __init__(self, id_usuario, nombre, apellido, correo, edad, rol):
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
    """Clase hija de Usuario para los clientes del gimnasio."""

    def __init__(self, id_usuario, nombre, apellido, correo, edad, objetivo="", nivel=""):
        super().__init__(id_usuario, nombre, apellido, correo, edad, "cliente")
        self.objetivo = objetivo or ""
        self.nivel = nivel or ""

    def configurar_entrenamiento(self, objetivo, nivel):
        self.objetivo = objetivo
        self.nivel = nivel

    def to_dict(self):
        datos = super().to_dict()
        datos.update({
            "objetivo": self.objetivo,
            "nivel": self.nivel,
        })
        return datos


class Entrenador(Usuario):
    """Clase hija de Usuario para los entrenadores."""

    def __init__(self, id_usuario, nombre, apellido, correo, edad, especialidad="Entrenamiento general"):
        super().__init__(id_usuario, nombre, apellido, correo, edad, "entrenador")
        self.especialidad = especialidad

    def to_dict(self):
        datos = super().to_dict()
        datos["especialidad"] = self.especialidad
        return datos


class Rutina:
    """Representa una rutina según el objetivo y nivel del cliente."""

    RUTINAS = {
        "Bajar de peso": {
            "Fácil": {
                "duracion": "30-45 min",
                "ejercicios": [
                    "Caminata ligera - 10 min",
                    "Bicicleta estática - 10 min",
                    "Sentadillas sin peso - 3x10",
                    "Movilidad y estiramiento - 5 min",
                ],
            },
            "Básico": {
                "duracion": "45-60 min",
                "ejercicios": [
                    "Caminata rápida - 10 min",
                    "Bicicleta estática - 15 min",
                    "Sentadillas - 3x12",
                    "Zancadas - 3x10",
                    "Cardio - 10 min",
                ],
            },
            "Avanzado": {
                "duracion": "60 min",
                "ejercicios": [
                    "Carrera/HIIT - 15 min",
                    "Burpees - 4x15",
                    "Mountain Climbers - 4x30s",
                    "Sentadillas con salto - 4x15",
                    "Cardio suave - 10 min",
                ],
            },
        },
        "Aumentar masa muscular": {
            "Fácil": {
                "duracion": "40 min",
                "ejercicios": [
                    "Calentamiento articular - 5 min",
                    "Sentadillas asistidas - 3x10",
                    "Flexiones apoyando rodillas - 3x8",
                    "Remo con mancuernas ligeras - 3x10",
                ],
            },
            "Básico": {
                "duracion": "50 min",
                "ejercicios": [
                    "Sentadillas con barra/mancuerna - 4x10",
                    "Press de banca o pechadas - 4x10",
                    "Peso muerto rumano - 3x10",
                    "Press militar con mancuernas - 3x10",
                ],
            },
            "Avanzado": {
                "duracion": "60-75 min",
                "ejercicios": [
                    "Sentadilla pesada - 4x6 a 8",
                    "Press de banca pesado - 4x6 a 8",
                    "Dominadas o Remo con barra - 4x8",
                    "Press militar pesado - 4x8",
                    "Curl bíceps / Tríceps - 3x12",
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
        """Generador: entrega un ejercicio por vez usando yield."""
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
