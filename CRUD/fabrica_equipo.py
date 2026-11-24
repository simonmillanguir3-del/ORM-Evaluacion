from abc import ABC, abstractmethod

from CRUD._comun import ErrorValidacion, entero, precio, texto
from modelos import Equipo, EquipoEntrenamiento, EquipoProteccion


class CreadorEquipo(ABC):
    "Valida los datos y delega la construcción al creador concreto."

    def crear_equipo(self, nombre, categoria_id, precio_diario, stock_total, stock_disponible):
        total = entero(stock_total, "El stock total")
        disponible = total if stock_disponible is None else entero(stock_disponible, "El stock disponible")
        if disponible > total:
            raise ErrorValidacion("El stock disponible no puede superar el stock total.")
        return self._crear_producto(
            nombre=texto(nombre, "El nombre del equipo"),
            categoria_id=categoria_id,
            precio_diario=precio(precio_diario),
            stock_total=total,
            stock_disponible=disponible,
        )

    @abstractmethod
    def _crear_producto(self, **datos):
        "Construye una instancia del tipo concreto de equipamiento."


class CreadorEquipoGeneral(CreadorEquipo):
    def _crear_producto(self, **datos):
        return Equipo(**datos)


class CreadorEquipoProteccion(CreadorEquipo):
    def _crear_producto(self, **datos):
        return EquipoProteccion(**datos)


class CreadorEquipoEntrenamiento(CreadorEquipo):
    def _crear_producto(self, **datos):
        return EquipoEntrenamiento(**datos)


_CREADORES = {
    "general": CreadorEquipoGeneral(),
    "proteccion": CreadorEquipoProteccion(),
    "entrenamiento": CreadorEquipoEntrenamiento(),
}


def obtener_creador(tipo):
    tipo = texto(tipo, "El tipo de equipamiento").casefold()
    try:
        return _CREADORES[tipo]
    except KeyError:
        opciones = ", ".join(_CREADORES)
        raise ErrorValidacion(f"El tipo de equipamiento debe ser uno de estos: {opciones}.") from None
