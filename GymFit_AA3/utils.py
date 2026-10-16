"""Funciones de apoyo para validación y manejo de errores."""

from functools import wraps
import sqlite3
from flask import jsonify


def manejar_errores(func):
    """Centraliza errores comunes y muestra mensajes entendibles en la página."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ValueError, TypeError, KeyError) as error:
            return jsonify({"success": False, "message": f"Revisa los datos ingresados: {error}"}), 400
        except sqlite3.IntegrityError:
            return jsonify({"success": False, "message": "No se pudo guardar: revisa los datos y el correo registrado."}), 400
        except sqlite3.Error:
            return jsonify({"success": False, "message": "Ocurrió un problema al consultar la base de datos."}), 500
        except Exception as error:
            print(f"Error en la aplicación: {error}")
            return jsonify({"success": False, "message": "Ocurrió un error inesperado. Intenta nuevamente."}), 500
    return wrapper


def ordenar_por_nombre(items):
    """Ordena usuarios alfabéticamente utilizando una expresión lambda."""
    return sorted(items, key=lambda item: f"{item.get('nombre', '')} {item.get('apellido', '')}".lower())


def calcular_minutos_progreso(registros):
    """Suma los minutos del historial usando map y lambda."""
    return sum(map(lambda registro: int(registro.get("minutos", 0)), registros))
