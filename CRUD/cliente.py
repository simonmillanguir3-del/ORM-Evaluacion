import re

from sqlalchemy import func, select

from CRUD._comun import Arriendo, Cliente, ErrorValidacion, obtener, texto, transaccion


def _validar_correo(sesion, correo, cliente_id=None):
    correo = texto(correo, "El correo").lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@.]+(?:\.[^\s@.]+)+", correo):
        raise ErrorValidacion("El correo debe tener un formato válido, por ejemplo nombre@dominio.cl.")
    consulta = select(Cliente.id).where(func.lower(Cliente.correo) == correo)
    if cliente_id is not None:
        consulta = consulta.where(Cliente.id != cliente_id)
    if sesion.scalar(consulta) is not None:
        raise ErrorValidacion("Ya existe un cliente con ese correo.")
    return correo


def _validar_telefono(telefono):
    telefono = texto(telefono, "El teléfono")
    if not re.fullmatch(r"\+?[0-9()\s-]+", telefono):
        raise ErrorValidacion("El teléfono solo admite números, espacios, paréntesis, guiones y + inicial.")
    cantidad_digitos = sum(caracter in "0123456789" for caracter in telefono)
    if not 7 <= cantidad_digitos <= 15:
        raise ErrorValidacion("El teléfono debe contener entre 7 y 15 dígitos.")
    return telefono


@transaccion
def crear_cliente(sesion, nombre, correo, telefono):
    cliente = Cliente(
        nombre=texto(nombre, "El nombre del cliente"),
        correo=_validar_correo(sesion, correo),
        telefono=_validar_telefono(telefono),
    )
    sesion.add(cliente)
    return cliente


def obtener_cliente(sesion, cliente_id):
    return obtener(sesion, Cliente, cliente_id, "el cliente")


def listar_clientes(sesion):
    return list(sesion.scalars(select(Cliente).order_by(Cliente.id)))


@transaccion
def actualizar_cliente(sesion, cliente_id, nombre=None, correo=None, telefono=None):
    cliente = obtener_cliente(sesion, cliente_id)
    if correo is not None:
        cliente.correo = _validar_correo(sesion, correo, cliente.id)
    if nombre is not None:
        cliente.nombre = texto(nombre, "El nombre del cliente")
    if telefono is not None:
        cliente.telefono = _validar_telefono(telefono)
    return cliente


@transaccion
def eliminar_cliente(sesion, cliente_id):
    cliente = obtener_cliente(sesion, cliente_id)
    if sesion.scalar(select(Arriendo.id).where(Arriendo.cliente_id == cliente.id).limit(1)):
        raise ErrorValidacion("No se puede eliminar el cliente porque tiene arriendos registrados.")
    sesion.delete(cliente)
    return True
