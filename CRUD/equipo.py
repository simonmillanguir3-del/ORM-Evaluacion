from sqlalchemy import select, update

from CRUD._comun import (
    Arriendo, Categoria, Equipo, ErrorValidacion, entero, obtener,
    precio, texto, transaccion,
)


@transaccion
def crear_equipo(sesion, nombre, categoria_id, precio_diario, stock_total, stock_disponible=None):
    categoria = obtener(sesion, Categoria, categoria_id, "la categoría")
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
        categoria = obtener(sesion, Categoria, categoria_id, "la categoría")
        consulta = consulta.where(Equipo.categoria_id == categoria.id)
    return list(sesion.scalars(consulta))


def listar_equipos_disponibles(sesion):
    return listar_equipos(sesion, solo_disponibles=True)


@transaccion
def actualizar_equipo(
    sesion, equipo_id, nombre=None, categoria_id=None, precio_diario=None,
    stock_total=None, stock_disponible=None,
):
    """Al variar el total, conserva las unidades que están fuera del inventario.

    El disponible se calcula automáticamente: no permite recuperar unidades
    prestadas sin registrar su devolución.
    """
    equipo = obtener_equipo(sesion, equipo_id)
    nuevo_nombre = equipo.nombre if nombre is None else texto(nombre, "El nombre del equipo")
    nueva_categoria = equipo.categoria_id if categoria_id is None else obtener(
        sesion, Categoria, categoria_id, "la categoría"
    ).id
    nuevo_precio = equipo.precio_diario if precio_diario is None else precio(precio_diario)
    total = equipo.stock_total if stock_total is None else entero(stock_total, "El stock total")
    unidades_fuera = equipo.stock_total - equipo.stock_disponible
    if total < unidades_fuera:
        raise ErrorValidacion("El stock total no puede ser menor a las unidades no disponibles.")
    disponible = total - unidades_fuera
    if stock_disponible is not None:
        solicitado = entero(stock_disponible, "El stock disponible")
        if solicitado != disponible:
            raise ErrorValidacion(
                "El stock disponible se calcula a partir del total y las unidades prestadas. "
                "Registre un arriendo o una devolución para modificarlo."
            )
    # Si hubo un arriendo desde la lectura del equipo, no sobrescribir su stock
    # con el disponible calculado a partir de una copia desactualizada.
    resultado = sesion.execute(
        update(Equipo).where(
            Equipo.id == equipo.id,
            Equipo.stock_total == equipo.stock_total,
            Equipo.stock_disponible == equipo.stock_disponible,
        ).values(
            nombre=nuevo_nombre, categoria_id=nueva_categoria,
            precio_diario=nuevo_precio, stock_total=total,
            stock_disponible=disponible,
        ).execution_options(synchronize_session="fetch")
    )
    if resultado.rowcount != 1:
        raise ErrorValidacion("El inventario cambió. Consulte el equipo antes de modificarlo.")
    return equipo


@transaccion
def eliminar_equipo(sesion, equipo_id):
    equipo = obtener_equipo(sesion, equipo_id)
    if sesion.scalar(select(Arriendo.id).where(Arriendo.equipo_id == equipo.id).limit(1)):
        raise ErrorValidacion("No se puede eliminar el equipo porque tiene arriendos registrados.")
    sesion.delete(equipo)
    return True
