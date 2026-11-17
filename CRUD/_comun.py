import re
from datetime import date
from functools import wraps
from importlib import import_module
from math import isfinite

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# import_module permite conservar la carpeta original, que contiene un guion.
modelos = import_module("Arriendos-deportivos.modelos")
Base = modelos.Base
Categoria = modelos.Categoria
Cliente = modelos.Cliente
Equipo = modelos.Equipo
Arriendo = modelos.Arriendo


class ErrorValidacion(ValueError):
    """Dato inválido o una operación que incumple las reglas de negocio."""


class ErrorPersistencia(RuntimeError):
    """No fue posible completar una operación en la base de datos."""


def transaccion(funcion):
    """Confirma toda la operación o revierte sus cambios si ocurre un error.

    Cada operación de escritura es una unidad completa de trabajo. La sesión
    recibida no debe contener cambios pendientes ajenos a esa operación.
    """
    @wraps(funcion)
    def ejecutar(sesion, *args, **kwargs):
        try:
            resultado = funcion(sesion, *args, **kwargs)
            sesion.commit()
            return resultado
        except IntegrityError as error:
            sesion.rollback()
            raise ErrorValidacion(
                "No se pudo guardar: hay datos duplicados, valores inválidos "
                "o registros relacionados."
            ) from error
        except SQLAlchemyError as error:
            sesion.rollback()
            raise ErrorPersistencia(
                "No se pudo completar la operación en la base de datos."
            ) from error
        except Exception:
            sesion.rollback()
            raise

    return ejecutar


def texto(valor, campo, obligatorio=True):
    if not isinstance(valor, str):
        raise ErrorValidacion(f"{campo} debe ser texto.")
    valor = valor.strip()
    if obligatorio and not valor:
        raise ErrorValidacion(f"{campo} no puede estar vacío.")
    return valor


def entero(valor, campo, minimo=0):
    if isinstance(valor, str) and re.fullmatch(r"[+-]?[0-9]+", valor.strip()):
        valor = int(valor)
    if type(valor) is not int or valor < minimo:
        raise ErrorValidacion(f"{campo} debe ser un entero mayor o igual a {minimo}.")
    return valor


def precio(valor):
    if isinstance(valor, bool):
        raise ErrorValidacion("El precio diario debe ser un número positivo.")
    try:
        valor = float(valor)
    except (ValueError, TypeError, OverflowError) as error:
        raise ErrorValidacion("El precio diario debe ser un número positivo.") from error
    if not isfinite(valor) or valor <= 0:
        raise ErrorValidacion("El precio diario debe ser finito y mayor a cero.")
    return valor


def fecha(valor, campo):
    if isinstance(valor, str):
        try:
            if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", valor.strip()):
                raise ValueError
            return date.fromisoformat(valor.strip())
        except ValueError as error:
            raise ErrorValidacion(f"{campo} debe ser una fecha válida (AAAA-MM-DD).") from error
    if type(valor) is not date:
        raise ErrorValidacion(f"{campo} debe ser una fecha válida (AAAA-MM-DD).")
    return valor


def obtener(sesion, modelo, identificador, nombre):
    identificador = entero(identificador, f"El ID de {nombre}", minimo=1)
    registro = sesion.get(modelo, identificador)
    if registro is None:
        raise ErrorValidacion(f"No existe {nombre} con ID {identificador}.")
    return registro
