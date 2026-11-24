from sqlalchemy import func, select

from CRUD._comun import ErrorValidacion, obtener, texto, transaccion
from modelos import Categoria, Equipo


def _validar_nombre(sesion, nombre, categoria_id=None):
    nombre = texto(nombre, "El nombre de la categoría")
    consulta = select(Categoria.id).where(func.lower(Categoria.nombre) == nombre.lower())
    if categoria_id is not None:
        consulta = consulta.where(Categoria.id != categoria_id)
    if sesion.scalar(consulta) is not None:
        raise ErrorValidacion("Ya existe una categoría con ese nombre.")
    return nombre


@transaccion
def crear_categoria(sesion, nombre, descripcion=""):
    categoria = Categoria(
        nombre=_validar_nombre(sesion, nombre),
        descripcion=texto(descripcion, "La descripción", obligatorio=False),
    )
    sesion.add(categoria)
    return categoria


def obtener_categoria(sesion, categoria_id):
    return obtener(sesion, Categoria, categoria_id, "la categoría")


def listar_categorias(sesion):
    return list(sesion.scalars(select(Categoria).order_by(Categoria.id)))


@transaccion
def actualizar_categoria(sesion, categoria_id, nombre=None, descripcion=None):
    categoria = obtener_categoria(sesion, categoria_id)
    if nombre is not None:
        categoria.nombre = _validar_nombre(sesion, nombre, categoria.id)
    if descripcion is not None:
        categoria.descripcion = texto(descripcion, "La descripción", obligatorio=False)
    return categoria


@transaccion
def eliminar_categoria(sesion, categoria_id):
    categoria = obtener_categoria(sesion, categoria_id)
    if sesion.scalar(select(Equipo.id).where(Equipo.categoria_id == categoria.id).limit(1)):
        raise ErrorValidacion("No se puede eliminar la categoría porque tiene equipos asociados.")
    sesion.delete(categoria)
    return True
