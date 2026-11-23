from sqlalchemy import select

from CRUD._comun import (
    Arriendo, Equipo, ErrorValidacion, entero, obtener,
    precio, texto, transaccion,
)
from CRUD.categoria import obtener_categoria


@transaccion
def crear_equipo(sesion, nombre, categoria_id, precio_diario, stock_total, stock_disponible=None):
    categoria = obtener_categoria(sesion, categoria_id)
    total = entero(stock_total, "El stock total")
    disponible = total if stock_disponible is None else entero(stock_disponible, "El stock disponible")
    if disponible > total:
        raise ErrorValidacion("El stock disponible no puede superar el stock total.")
    equipo = Equipo(
        nombre=texto(nombre, "El nombre del equipo"),
        categoria_id=categoria.id,
        precio_diario=precio(precio_diario),
        stock_total=total,
        stock_disponible=disponible,
    )
    sesion.add(equipo)
    return equipo


def obtener_equipo(sesion, equipo_id):
    return obtener(sesion, Equipo, equipo_id, "el equipo")


def listar_equipos(sesion, solo_disponibles=False, categoria_id=None):
    consulta = select(Equipo).order_by(Equipo.id)
    if solo_disponibles:
        consulta = consulta.where(Equipo.stock_disponible > 0)
    if categoria_id is not None:
        categoria = obtener_categoria(sesion, categoria_id)
        consulta = consulta.where(Equipo.categoria_id == categoria.id)
    return list(sesion.scalars(consulta))


def listar_equipos_disponibles(sesion):
    return listar_equipos(sesion, solo_disponibles=True)


@transaccion
def actualizar_equipo(
    sesion, equipo_id, nombre=None, categoria_id=None, precio_diario=None,
    stock_total=None, stock_disponible=None,
):
    """Al cambiar el total, conserva las unidades que no están disponibles."""
    equipo = obtener_equipo(sesion, equipo_id)
    if categoria_id is not None:
        equipo.categoria = obtener_categoria(sesion, categoria_id)
    if nombre is not None:
        equipo.nombre = texto(nombre, "El nombre del equipo")
    if precio_diario is not None:
        equipo.precio_diario = precio(precio_diario)

    total = equipo.stock_total if stock_total is None else entero(stock_total, "El stock total")
    unidades_fuera = equipo.stock_total - equipo.stock_disponible
    disponible = total - unidades_fuera
    if disponible < 0:
        raise ErrorValidacion("El stock total no puede ser menor a las unidades no disponibles.")
    if stock_disponible is not None:
        solicitado = entero(stock_disponible, "El stock disponible")
        if solicitado != disponible:
            raise ErrorValidacion(f"Con el nuevo total, el stock disponible debe ser {disponible}.")
    equipo.stock_total = total
    equipo.stock_disponible = disponible
    return equipo


@transaccion
def eliminar_equipo(sesion, equipo_id):
    equipo = obtener_equipo(sesion, equipo_id)
    if sesion.scalar(select(Arriendo.id).where(Arriendo.equipo_id == equipo.id).limit(1)):
        raise ErrorValidacion("No se puede eliminar el equipo porque tiene arriendos registrados.")
    sesion.delete(equipo)
    return True
