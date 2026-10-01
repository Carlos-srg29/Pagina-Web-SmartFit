"""Funciones avanzadas utilizadas por GymFit en la AA2."""
from functools import wraps
from flask import jsonify
import sqlite3


def manejar_errores(func):
    """Decorador para centralizar el manejo de errores de las rutas API."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ValueError, TypeError, KeyError) as error:
            return jsonify({
                "success": False,
                "message": f"Datos inválidos: {error}"
            }), 400
        except sqlite3.Error:
            return jsonify({
                "success": False,
                "message": "Ocurrió un error al acceder a la base de datos."
            }), 500
        except Exception as error:
            print(f"Error no controlado: {error}")
            return jsonify({
                "success": False,
                "message": "Ocurrió un error interno en el servidor."
            }), 500
    return wrapper


def ordenar_por_nombre(items):
    """Lambda: ordena una lista de diccionarios por nombre y apellido."""
    return sorted(items, key=lambda item: f"{item.get('nombre', '')} {item.get('apellido', '')}".lower())


def calcular_minutos_progreso(registros):
    """Lambda: suma los minutos registrados de cada entrenamiento."""
    return sum(map(lambda registro: int(registro.get("minutos", 0)), registros))
