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
    """Guarda toda la operación o la revierte. Use una sesión sin otros cambios pendientes."""
    @wraps(funcion)
    def ejecutar(sesion, *args, **kwargs):
        try:
            # SQLite reserva la escritura antes de leer el stock o el estado.
            # Así dos sesiones no pueden modificar el mismo saldo a la vez.
            conexion = sesion.connection()
            if conexion.dialect.name == "sqlite":
                sqlite = conexion.connection.driver_connection
                if not sqlite.in_transaction:
                    conexion.exec_driver_sql("BEGIN IMMEDIATE")

            resultado = funcion(sesion, *args, **kwargs)
            sesion.commit()
            return resultado
        except Exception as error:
            sesion.rollback()
            if isinstance(error, IntegrityError):
                raise ErrorValidacion(
                    "No se pudo guardar por datos duplicados, inválidos o vinculados."
                ) from error
            if isinstance(error, SQLAlchemyError):
                raise ErrorPersistencia("No se pudo completar la operación en la base de datos.") from error
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
        try:
            valor = int(valor)
        except ValueError as error:
            raise ErrorValidacion(f"{campo} supera el límite de SQLite.") from error
    if type(valor) is not int or valor < minimo:
        raise ErrorValidacion(f"{campo} debe ser un entero mayor o igual a {minimo}.")
    if valor > 2**63 - 1:
        raise ErrorValidacion(f"{campo} supera el límite de SQLite.")
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
    if type(valor) is date:
        return valor
    if isinstance(valor, str):
        valor = valor.strip()
        try:
            resultado = date.fromisoformat(valor)
            if resultado.isoformat() == valor:
                return resultado
        except ValueError:
            pass
    raise ErrorValidacion(f"{campo} debe ser una fecha válida (AAAA-MM-DD).")


def obtener(sesion, modelo, identificador, nombre):
    identificador = entero(identificador, f"El ID de {nombre}", minimo=1)
    registro = sesion.get(modelo, identificador, populate_existing=True)
    if registro is None:
        raise ErrorValidacion(f"No existe {nombre} con ID {identificador}.")
    return registro
