from pathlib import Path

from sqlalchemy import URL, create_engine, event, inspect

from modelos import Base


def crear_motor(ruta=None):
    (
        "Crea tablas sin borrar datos. Por defecto usa arriendos.db en el proyecto.\n\n"
        "    Para pruebas se puede indicar ':memory:' o una ruta temporal.\n    "
    )
    if ruta is None:
        ruta = Path(__file__).resolve().parents[1] / "arriendos.db"
    base = ":memory:" if str(ruta) == ":memory:" else str(Path(ruta).resolve())
    motor = create_engine(URL.create("sqlite", database=base))

    @event.listens_for(motor, "connect")
    def activar_claves_foraneas(conexion, registro):
        cursor = conexion.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

    with motor.begin() as conexion:
        conexion.exec_driver_sql("BEGIN IMMEDIATE")
        Base.metadata.create_all(conexion)
        columnas = inspect(conexion).get_columns("equipos")
        if all(columna["name"] != "tipo" for columna in columnas):
            conexion.exec_driver_sql(
                "ALTER TABLE equipos ADD COLUMN tipo VARCHAR NOT NULL DEFAULT 'general'"
            )
    return motor
