import argparse
from pathlib import Path
from shutil import copyfileobj
from tempfile import TemporaryDirectory

from sqlalchemy.orm import Session

from CRUD.arriendo import crear_arriendo, devolver_arriendo
from CRUD.categoria import crear_categoria
from CRUD.cliente import crear_cliente
from CRUD.conexion import crear_motor
from CRUD.equipo import crear_equipo


def _cargar_catalogo_y_arriendos(sesion):
    ciclismo = crear_categoria(sesion, "Ciclismo", "Equipos y accesorios para rutas.").id
    entrenamiento = crear_categoria(sesion, "Entrenamiento", "Material para acondicionamiento físico.").id
    senderismo = crear_categoria(sesion, "Senderismo", "Implementos para caminatas.").id
    crear_categoria(sesion, "Natación", "Material para piscina.")

    bicicleta = crear_equipo(sesion, "Bicicleta de montaña", ciclismo, 12000, 6).id
    casco = crear_equipo(sesion, "Casco de ciclismo", ciclismo, 3500, 8, tipo="proteccion").id
    mancuernas = crear_equipo(sesion, "Par de mancuernas", entrenamiento, 4500, 6, tipo="entrenamiento").id
    colchoneta = crear_equipo(sesion, "Colchoneta", entrenamiento, 2500, 5, tipo="entrenamiento").id
    bastones = crear_equipo(sesion, "Par de bastones", senderismo, 5000, 4).id

    camila = crear_cliente(sesion, "Camila Demo", "camila@example.com", "+56 9 0000 0001").id
    diego = crear_cliente(sesion, "Diego Demo", "diego@example.com", "+56 9 0000 0002").id
    valeria = crear_cliente(sesion, "Valeria Demo", "valeria@example.com", "+56 9 0000 0003").id

    for equipo, cliente, cantidad, inicio, fin, devuelto in (
        (bicicleta, camila, 2, "2026-11-15", "2026-11-16", True),
        (bicicleta, diego, 1, "2026-11-17", "2026-11-19", True),
        (bicicleta, valeria, 2, "2026-11-22", "2026-11-29", False),
        (casco, camila, 3, "2026-11-22", "2026-11-29", False),
        (mancuernas, diego, 4, "2026-11-18", "2026-11-20", True),
        (mancuernas, valeria, 1, "2026-11-23", "2026-11-30", False),
        (colchoneta, diego, 2, "2026-11-23", "2026-11-30", False),
        (bastones, camila, 1, "2026-11-20", "2026-11-21", True),
    ):
        arriendo = crear_arriendo(sesion, equipo, cliente, inicio, fin, cantidad)
        if devuelto:
            devolver_arriendo(sesion, arriendo.id)


def generar_base_ejemplo(ruta):
    destino = Path(ruta).resolve()
    if destino.exists():
        raise FileExistsError(f"Ya existe la base {destino}. Usa otra ruta.")

    with TemporaryDirectory(dir=destino.parent) as directorio:
        temporal = Path(directorio) / "ejemplo.db"
        motor = crear_motor(temporal)
        try:
            with Session(motor) as sesion:
                _cargar_catalogo_y_arriendos(sesion)
        finally:
            motor.dispose()

        with temporal.open("rb") as origen:
            salida = destino.open("xb")
            try:
                with salida:
                    copyfileobj(origen, salida)
            except OSError:
                destino.unlink()
                raise
    return destino


if __name__ == "__main__":
    argumentos = argparse.ArgumentParser(description="Genera una base SQLite con datos ficticios de demostración.")
    argumentos.add_argument("--base", type=Path, default=Path(__file__).with_name("arriendos-ejemplo.db"))
    try:
        ruta = generar_base_ejemplo(argumentos.parse_args().base)
    except OSError as error:
        argumentos.exit(1, f"No se pudo generar la base de ejemplo. {error}\n")
    print(f"Base de ejemplo creada en {ruta}")
