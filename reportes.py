from matplotlib.ticker import MaxNLocator
from sqlalchemy import func, select

from CRUD._comun import Arriendo, Categoria, Equipo


def arriendos_por_categoria(sesion):
    operaciones = func.count(Arriendo.id)
    consulta = (
        select(Categoria.nombre, operaciones)
        .select_from(Categoria)
        .outerjoin(Categoria.equipos)
        .outerjoin(Equipo.arriendos)
        .group_by(Categoria.id, Categoria.nombre)
        .order_by(operaciones.desc(), Categoria.nombre, Categoria.id)
    )
    return sesion.execute(consulta).all()


def equipos_mas_arrendados(sesion):
    operaciones = func.count(Arriendo.id)
    consulta = (
        select(Equipo.id, Equipo.nombre, operaciones)
        .join(Equipo.arriendos)
        .group_by(Equipo.id, Equipo.nombre)
        .order_by(operaciones.desc(), Equipo.nombre, Equipo.id)
        .limit(10)
    )
    return sesion.execute(consulta).all()


def graficar_arriendos_por_categoria(figura, filas):
    _graficar_barras(
        figura, filas, "Arriendos por categoría", "Aún no hay categorías registradas.",
    )


def graficar_equipos_mas_arrendados(figura, filas):
    valores = [(f"{nombre} (ID {equipo_id})", cantidad) for equipo_id, nombre, cantidad in filas]
    _graficar_barras(
        figura, valores, "Equipos con más arriendos (hasta 10)", "Aún no hay arriendos registrados.",
    )


def _graficar_barras(figura, filas, titulo, mensaje_vacio):
    figura.clear()
    eje = figura.add_subplot()
    eje.set_title(titulo, loc="left", pad=14)
    if not filas:
        eje.set_axis_off()
        eje.text(0.5, 0.5, mensaje_vacio, ha="center", va="center", transform=eje.transAxes)
        return

    etiquetas, cantidades = zip(*filas)
    posiciones = range(len(etiquetas))
    barras = eje.barh(posiciones, cantidades, color="#287a72", height=0.64)
    eje.set_yticks(posiciones, etiquetas, parse_math=False)
    eje.invert_yaxis()
    eje.set_xlabel("Operaciones de arriendo")
    eje.set_xlim(0, max(1, max(cantidades) * 1.15))
    eje.xaxis.set_major_locator(MaxNLocator(integer=True, min_n_ticks=1))
    eje.set_axisbelow(True)
    eje.grid(axis="x", alpha=0.25)
    eje.bar_label(barras, padding=4)
