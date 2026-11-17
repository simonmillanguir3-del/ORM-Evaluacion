from sqlalchemy import delete, select, update

from CRUD._comun import (
    Arriendo, Cliente, Equipo, ErrorValidacion, entero, fecha, obtener, transaccion,
)


def _validar_fechas(fecha_inicio, fecha_fin_prevista):
    inicio = fecha(fecha_inicio, "La fecha de inicio")
    fin = fecha(fecha_fin_prevista, "La fecha de término prevista")
    if fin < inicio:
        raise ErrorValidacion("La fecha de término prevista no puede ser anterior a la fecha de inicio.")
    return inicio, fin


def _ajustar_stock(sesion, equipo_id, diferencia):
    # La condición se comprueba en la BD, en el mismo UPDATE que cambia el stock.
    # Así otra operación no puede consumir las mismas unidades entre la lectura
    # del disponible y su descuento.
    nuevo_stock = Equipo.stock_disponible + diferencia
    resultado = sesion.execute(
        update(Equipo)
        .where(Equipo.id == equipo_id, nuevo_stock >= 0, nuevo_stock <= Equipo.stock_total)
        .values(stock_disponible=nuevo_stock)
        .execution_options(synchronize_session="fetch")
    )
    if resultado.rowcount != 1:
        raise ErrorValidacion(
            "No hay stock disponible suficiente o el cambio supera el stock total del equipo."
        )


def _version_actual(arriendo):
    """Comprueba que el arriendo no cambió desde que fue consultado."""
    return (
        Arriendo.id == arriendo.id,
        Arriendo.estado == arriendo.estado,
        Arriendo.equipo_id == arriendo.equipo_id,
        Arriendo.cliente_id == arriendo.cliente_id,
        Arriendo.cantidad == arriendo.cantidad,
        Arriendo.fecha_inicio == arriendo.fecha_inicio,
        Arriendo.fecha_fin_prevista == arriendo.fecha_fin_prevista,
    )


@transaccion
def crear_arriendo(sesion, equipo_id, cliente_id, fecha_inicio, fecha_fin_prevista, cantidad):
    equipo = obtener(sesion, Equipo, equipo_id, "el equipo")
    cliente = obtener(sesion, Cliente, cliente_id, "el cliente")
    inicio, fin = _validar_fechas(fecha_inicio, fecha_fin_prevista)
    cantidad = entero(cantidad, "La cantidad", minimo=1)
    _ajustar_stock(sesion, equipo.id, -cantidad)
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
        cliente = obtener(sesion, Cliente, cliente_id, "el cliente")
        consulta = consulta.where(Arriendo.cliente_id == cliente.id)
    if equipo_id is not None:
        equipo = obtener(sesion, Equipo, equipo_id, "el equipo")
        consulta = consulta.where(Arriendo.equipo_id == equipo.id)
    return list(sesion.scalars(consulta))


def listar_arriendos_activos(sesion):
    return listar_arriendos(sesion, estado="ACTIVO")


@transaccion
def actualizar_arriendo(
    sesion, arriendo_id, equipo_id=None, cliente_id=None,
    fecha_inicio=None, fecha_fin_prevista=None, cantidad=None,
):
    """Modifica un arriendo activo y ajusta la diferencia de stock.

    Un arriendo devuelto conserva sus datos. El cambio a DEVUELTO se realiza
    exclusivamente mediante devolver_arriendo.
    """
    arriendo = obtener_arriendo(sesion, arriendo_id)
    if arriendo.estado != "ACTIVO":
        raise ErrorValidacion("Solo se pueden modificar arriendos activos.")
    equipo_anterior, cantidad_anterior = arriendo.equipo_id, arriendo.cantidad
    nuevo_equipo = equipo_anterior if equipo_id is None else obtener(
        sesion, Equipo, equipo_id, "el equipo"
    ).id
    nuevo_cliente = arriendo.cliente_id if cliente_id is None else obtener(
        sesion, Cliente, cliente_id, "el cliente"
    ).id
    nueva_cantidad = cantidad_anterior if cantidad is None else entero(cantidad, "La cantidad", minimo=1)
    inicio, fin = _validar_fechas(
        arriendo.fecha_inicio if fecha_inicio is None else fecha_inicio,
        arriendo.fecha_fin_prevista if fecha_fin_prevista is None else fecha_fin_prevista,
    )
    resultado = sesion.execute(
        update(Arriendo).where(*_version_actual(arriendo)).values(
            equipo_id=nuevo_equipo, cliente_id=nuevo_cliente,
            fecha_inicio=inicio, fecha_fin_prevista=fin, cantidad=nueva_cantidad,
        ).execution_options(synchronize_session="fetch")
    )
    if resultado.rowcount != 1:
        raise ErrorValidacion("El arriendo cambió. Consulte sus datos antes de intentar modificarlo.")
    if nuevo_equipo == equipo_anterior:
        _ajustar_stock(sesion, nuevo_equipo, cantidad_anterior - nueva_cantidad)
    else:
        _ajustar_stock(sesion, equipo_anterior, cantidad_anterior)
        _ajustar_stock(sesion, nuevo_equipo, -nueva_cantidad)
    return arriendo


@transaccion
def devolver_arriendo(sesion, arriendo_id):
    arriendo = obtener_arriendo(sesion, arriendo_id)
    if arriendo.estado != "ACTIVO":
        raise ErrorValidacion("El arriendo ya fue devuelto. No se permiten devoluciones duplicadas.")
    equipo_id, cantidad = arriendo.equipo_id, arriendo.cantidad
    resultado = sesion.execute(
        update(Arriendo).where(*_version_actual(arriendo))
        .values(estado="DEVUELTO").execution_options(synchronize_session="fetch")
    )
    if resultado.rowcount != 1:
        raise ErrorValidacion("El arriendo cambió o ya fue devuelto. Actualice la consulta.")
    _ajustar_stock(sesion, equipo_id, cantidad)
    return arriendo


@transaccion
def eliminar_arriendo(sesion, arriendo_id):
    """Elimina un registro devuelto; nunca borra un préstamo pendiente."""
    arriendo = obtener_arriendo(sesion, arriendo_id)
    if arriendo.estado != "DEVUELTO":
        raise ErrorValidacion("Debe devolver el arriendo antes de eliminar su registro.")
    resultado = sesion.execute(
        delete(Arriendo).where(*_version_actual(arriendo))
        .execution_options(synchronize_session="fetch")
    )
    if resultado.rowcount != 1:
        raise ErrorValidacion("El arriendo cambió. Actualice la consulta antes de eliminarlo.")
    return True
