from pathlib import Path

from sqlalchemy import URL, create_engine, event

from CRUD._comun import Base


def crear_motor(ruta=None):
    """Crea tablas sin borrar datos. Por defecto usa arriendos.db en el proyecto.

    Para pruebas se puede indicar ':memory:' o una ruta temporal.
    """
    if ruta is None:
        ruta = Path(__file__).resolve().parents[1] / "arriendos.db"
    base = ":memory:" if str(ruta) == ":memory:" else str(Path(ruta).resolve())
    motor = create_engine(URL.create("sqlite", database=base))

    @event.listens_for(motor, "connect")
    def activar_claves_foraneas(conexion, registro):
        cursor = conexion.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

    Base.metadata.create_all(motor)
    return motor
