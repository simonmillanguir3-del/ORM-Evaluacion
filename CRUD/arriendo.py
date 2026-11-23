from sqlalchemy import select

from CRUD._comun import (
    Arriendo, ErrorValidacion, entero, fecha, obtener, transaccion,
)
from CRUD.cliente import obtener_cliente
from CRUD.equipo import obtener_equipo


def _validar_fechas(fecha_inicio, fecha_fin_prevista):
    inicio = fecha(fecha_inicio, "La fecha de inicio")
    fin = fecha(fecha_fin_prevista, "La fecha de término prevista")
    if fin < inicio:
        raise ErrorValidacion("La fecha de término prevista no puede ser anterior a la fecha de inicio.")
    return inicio, fin


def _ajustar_stock(equipo, diferencia):
    nuevo_stock = equipo.stock_disponible + diferencia
    if nuevo_stock < 0:
        raise ErrorValidacion("No hay stock disponible suficiente.")
    if nuevo_stock > equipo.stock_total:
        raise ErrorValidacion("El stock disponible no puede superar el stock total.")
    equipo.stock_disponible = nuevo_stock


@transaccion
def crear_arriendo(sesion, equipo_id, cliente_id, fecha_inicio, fecha_fin_prevista, cantidad):
    inicio, fin = _validar_fechas(fecha_inicio, fecha_fin_prevista)
    cantidad = entero(cantidad, "La cantidad", minimo=1)
    equipo = obtener_equipo(sesion, equipo_id)
    cliente = obtener_cliente(sesion, cliente_id)
    _ajustar_stock(equipo, -cantidad)
    arriendo = Arriendo(
        equipo_id=equipo.id, cliente_id=cliente.id,
        fecha_inicio=inicio, fecha_fin_prevista=fin, cantidad=cantidad, estado="ACTIVO",
    )
    sesion.add(arriendo)
    return arriendo


def obtener_arriendo(sesion, arriendo_id):
    return obtener(sesion, Arriendo, arriendo_id, "el arriendo")


def listar_arriendos(sesion, estado=None, cliente_id=None, equipo_id=None):
    """Sin filtros devuelve el historial completo, incluidos los activos."""
    consulta = select(Arriendo).order_by(Arriendo.id)
    if estado is not None:
        if estado not in ("ACTIVO", "DEVUELTO"):
            raise ErrorValidacion("El estado debe ser ACTIVO o DEVUELTO.")
        consulta = consulta.where(Arriendo.estado == estado)
    if cliente_id is not None:
        cliente = obtener_cliente(sesion, cliente_id)
        consulta = consulta.where(Arriendo.cliente_id == cliente.id)
    if equipo_id is not None:
        equipo = obtener_equipo(sesion, equipo_id)
        consulta = consulta.where(Arriendo.equipo_id == equipo.id)
    return list(sesion.scalars(consulta))


def listar_arriendos_activos(sesion):
    return listar_arriendos(sesion, estado="ACTIVO")


@transaccion
def actualizar_arriendo(
    sesion, arriendo_id, equipo_id=None, cliente_id=None,
    fecha_inicio=None, fecha_fin_prevista=None, cantidad=None,
):
    """Modifica un arriendo activo y corrige el stock de los equipos."""
    arriendo = obtener_arriendo(sesion, arriendo_id)
    if arriendo.estado != "ACTIVO":
        raise ErrorValidacion("Solo se pueden modificar arriendos activos.")
    inicio, fin = _validar_fechas(
        arriendo.fecha_inicio if fecha_inicio is None else fecha_inicio,
        arriendo.fecha_fin_prevista if fecha_fin_prevista is None else fecha_fin_prevista,
    )
    if cantidad is None:
        cantidad = arriendo.cantidad
    cantidad = entero(cantidad, "La cantidad", minimo=1)
    nuevo_cliente = None
    if cliente_id is not None:
        nuevo_cliente = obtener_cliente(sesion, cliente_id)

    if equipo_id is not None or cantidad != arriendo.cantidad:
        equipo_anterior = obtener_equipo(sesion, arriendo.equipo_id)
        equipo = equipo_anterior if equipo_id is None else obtener_equipo(sesion, equipo_id)

        if equipo.id == equipo_anterior.id:
            _ajustar_stock(equipo, arriendo.cantidad - cantidad)
        else:
            _ajustar_stock(equipo, -cantidad)
            _ajustar_stock(equipo_anterior, arriendo.cantidad)
            arriendo.equipo = equipo

    if nuevo_cliente is not None:
        arriendo.cliente = nuevo_cliente
    arriendo.cantidad = cantidad
    arriendo.fecha_inicio = inicio
    arriendo.fecha_fin_prevista = fin
    return arriendo


@transaccion
def devolver_arriendo(sesion, arriendo_id):
    arriendo = obtener_arriendo(sesion, arriendo_id)
    if arriendo.estado != "ACTIVO":
        raise ErrorValidacion("El arriendo ya fue devuelto. No se permiten devoluciones duplicadas.")
    equipo = obtener_equipo(sesion, arriendo.equipo_id)
    _ajustar_stock(equipo, arriendo.cantidad)
    arriendo.estado = "DEVUELTO"
    return arriendo


@transaccion
def eliminar_arriendo(sesion, arriendo_id):
    """Elimina un registro devuelto; nunca borra un préstamo pendiente."""
    arriendo = obtener_arriendo(sesion, arriendo_id)
    if arriendo.estado != "DEVUELTO":
        raise ErrorValidacion("Debe devolver el arriendo antes de eliminar su registro.")
    sesion.delete(arriendo)
    return True
