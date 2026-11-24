import sqlite3
import unittest
from contextlib import closing
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from sqlalchemy.orm import Session

from CRUD import ErrorValidacion
from CRUD.arriendo import crear_arriendo, devolver_arriendo, listar_arriendos, obtener_arriendo
from CRUD.categoria import actualizar_categoria, crear_categoria, eliminar_categoria, listar_categorias
from CRUD.cliente import actualizar_cliente, crear_cliente, eliminar_cliente, listar_clientes
from CRUD.conexion import crear_motor
from CRUD.equipo import actualizar_equipo, crear_equipo, eliminar_equipo, listar_equipos, obtener_equipo
from datos_ejemplo import generar_base_ejemplo
from modelos import Equipo, EquipoEntrenamiento, EquipoProteccion
from reportes import (
    arriendos_por_categoria, equipos_mas_arrendados,
    graficar_arriendos_por_categoria, graficar_equipos_mas_arrendados,
)


class PruebasSistema(unittest.TestCase):
    def setUp(self):
        temporal = TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        self.ruta = Path(temporal.name) / "prueba.db"
        self.motor = crear_motor(self.ruta)
        self.addCleanup(self.motor.dispose)

    def test_seis_pasos_de_la_pauta(self):
        with Session(self.motor) as sesion:
            categoria = crear_categoria(sesion, "Ciclismo")
            equipo = crear_equipo(sesion, "Casco", categoria.id, 3500, 5, tipo="proteccion")
            equipo_id = equipo.id
            self.assertEqual(equipo.stock_disponible, 5)
            cliente_id = crear_cliente(sesion, "Cliente", "cliente@example.com", "123456789").id
            arriendo_id = self.arrendar(sesion, equipo_id, cliente_id, 2).id
            self.assertEqual(obtener_equipo(sesion, equipo_id).stock_disponible, 3)
            self.assertEqual(obtener_arriendo(sesion, arriendo_id).estado, "ACTIVO")

            with self.assertRaisesRegex(ErrorValidacion, "stock disponible suficiente"):
                self.arrendar(sesion, equipo_id, cliente_id, 4)
            self.assertEqual(obtener_equipo(sesion, equipo_id).stock_disponible, 3)
            self.assertEqual(len(listar_arriendos(sesion)), 1)

            self.assertEqual(devolver_arriendo(sesion, arriendo_id).estado, "DEVUELTO")
            self.assertEqual(obtener_equipo(sesion, equipo_id).stock_disponible, 5)
            with self.assertRaisesRegex(ErrorValidacion, "ya fue devuelto"):
                devolver_arriendo(sesion, arriendo_id)
            self.assertEqual(obtener_equipo(sesion, equipo_id).stock_disponible, 5)

        self.motor.dispose()
        motor = crear_motor(self.ruta)
        self.addCleanup(motor.dispose)
        with Session(motor) as sesion:
            self.assertIsInstance(obtener_equipo(sesion, equipo_id), EquipoProteccion)
            self.assertEqual(obtener_equipo(sesion, equipo_id).stock_disponible, 5)
            self.assertEqual(obtener_arriendo(sesion, arriendo_id).estado, "DEVUELTO")
            self.assertEqual(listar_arriendos(sesion, estado="ACTIVO"), [])
            self.comprobar_grafico(graficar_arriendos_por_categoria, arriendos_por_categoria(sesion), [1])
            self.comprobar_grafico(graficar_equipos_mas_arrendados, equipos_mas_arrendados(sesion), [1])

    def test_crud_y_restricciones_de_registros_vinculados(self):
        with Session(self.motor) as sesion:
            categoria_id = crear_categoria(sesion, "Ciclismo").id
            cliente_id = crear_cliente(sesion, "Cliente", "cliente@example.com", "123456789").id
            equipo_id = crear_equipo(sesion, "Casco", categoria_id, 3500, 5).id
            self.assertEqual(actualizar_categoria(sesion, categoria_id, nombre="Montaña").nombre, "Montaña")
            self.assertEqual(actualizar_cliente(sesion, cliente_id, nombre="Cliente 2").nombre, "Cliente 2")
            self.assertEqual(actualizar_equipo(sesion, equipo_id, stock_total=6).stock_disponible, 6)
            self.arrendar(sesion, equipo_id, cliente_id, 6)
            self.assertEqual(listar_equipos(sesion, solo_disponibles=True), [])
            for eliminar, identificador in (
                (eliminar_categoria, categoria_id), (eliminar_equipo, equipo_id), (eliminar_cliente, cliente_id),
            ):
                with self.assertRaises(ErrorValidacion):
                    eliminar(sesion, identificador)
            self.assertEqual((len(listar_categorias(sesion)), len(listar_equipos(sesion)),
                              len(listar_clientes(sesion))), (1, 1, 1))

            otra_categoria = crear_categoria(sesion, "Natación").id
            otro_equipo = crear_equipo(sesion, "Tabla", otra_categoria, 2000, 0).id
            otro_cliente = crear_cliente(sesion, "Otro", "otro@example.com", "987654321").id
            self.assertTrue(eliminar_equipo(sesion, otro_equipo))
            self.assertTrue(eliminar_categoria(sesion, otra_categoria))
            self.assertTrue(eliminar_cliente(sesion, otro_cliente))

    def test_validaciones_revierten_sin_alterar_stock(self):
        with Session(self.motor) as sesion:
            categoria_id = crear_categoria(sesion, "Ciclismo").id
            cliente_id = crear_cliente(sesion, "Cliente", "cliente@example.com", "123456789").id
            equipo_id = crear_equipo(sesion, "Bicicleta", categoria_id, 4000, 5).id
            for operacion, argumentos in (
                (crear_categoria, ("ciclismo",)),
                (crear_cliente, ("Otro", "CLIENTE@example.com", "987654321")),
                (crear_cliente, ("Otro", "invalido", "987654321")),
                (crear_equipo, ("Inválido", categoria_id, 0, 5)),
                (crear_equipo, ("Inválido", categoria_id, 4000, -1)),
                (crear_equipo, ("Inválido", categoria_id, 4000, 5, 6)),
                (self.arrendar, (999, cliente_id, 2)),
                (self.arrendar, (equipo_id, 999, 2)),
                (self.arrendar, (equipo_id, cliente_id, 0)),
                (crear_arriendo, (equipo_id, cliente_id, "2026-01-03", "2026-01-02", 2)),
            ):
                with self.subTest(operacion=operacion.__name__, argumentos=argumentos):
                    with self.assertRaises(ErrorValidacion):
                        operacion(sesion, *argumentos)
            with self.assertRaisesRegex(ErrorValidacion, "tipo de equipamiento"):
                crear_equipo(sesion, "Inválido", categoria_id, 4000, 5, tipo="desconocido")
            self.assertEqual(obtener_equipo(sesion, equipo_id).stock_disponible, 5)
            self.assertEqual(listar_arriendos(sesion), [])

    def test_tipo_persistente_y_migracion_de_la_base_anterior(self):
        anterior = self.ruta.with_name("anterior.db")
        with closing(sqlite3.connect(anterior)) as conexion:
            conexion.executescript(
                "CREATE TABLE categorias (id INTEGER PRIMARY KEY, nombre VARCHAR UNIQUE NOT NULL,\n"
                "    descripcion VARCHAR NOT NULL);\n"
                "CREATE TABLE equipos (id INTEGER PRIMARY KEY, nombre VARCHAR NOT NULL,\n"
                "    categoria_id INTEGER NOT NULL REFERENCES categorias(id), precio_diario FLOAT NOT NULL,\n"
                "    stock_total INTEGER NOT NULL, stock_disponible INTEGER NOT NULL);\n"
                "INSERT INTO categorias VALUES (1, 'Entrenamiento', '');\n"
                "INSERT INTO equipos VALUES (1, 'Colchoneta', 1, 2000, 5, 3);"
            )
        motor = crear_motor(anterior)
        try:
            with Session(motor) as sesion:
                original = obtener_equipo(sesion, 1)
                self.assertIs(type(original), Equipo)
                self.assertEqual((original.tipo, original.stock_disponible), ("general", 3))
                equipo_id = crear_equipo(sesion, "Mancuernas", 1, 3000, 5, tipo="entrenamiento").id
        finally:
            motor.dispose()
        motor = crear_motor(anterior)
        self.addCleanup(motor.dispose)
        with Session(motor) as sesion:
            equipo = obtener_equipo(sesion, equipo_id)
            self.assertIsInstance(equipo, EquipoEntrenamiento)
            self.assertEqual(equipo.categoria.nombre, "Entrenamiento")
            self.assertEqual(len(equipo.categoria.equipos), 2)

    def test_ranking_limita_diez_y_distingue_equipos_del_mismo_nombre(self):
        with Session(self.motor) as sesion:
            categoria_id = crear_categoria(sesion, "Ciclismo").id
            crear_categoria(sesion, "Natación")
            cliente_id = crear_cliente(sesion, "Cliente", "cliente@example.com", "123456789").id
            ids = []
            for _ in range(11):
                equipo_id = crear_equipo(sesion, "Casco", categoria_id, 3500, 5).id
                self.arrendar(sesion, equipo_id, cliente_id, 2)
                ids.append(equipo_id)
            self.assertEqual(arriendos_por_categoria(sesion), [("Ciclismo", 11), ("Natación", 0)])
            self.assertEqual(equipos_mas_arrendados(sesion), [(identificador, "Casco", 1) for identificador in ids[:10]])

    def test_base_de_ejemplo_y_proteccion_de_archivos_existentes(self):
        destino = self.ruta.with_name("ejemplo.db")
        self.assertEqual(generar_base_ejemplo(destino), destino)
        contenido = destino.read_bytes()
        with self.assertRaises(FileExistsError):
            generar_base_ejemplo(destino)
        self.assertEqual(destino.read_bytes(), contenido)

        motor = crear_motor(destino)
        self.addCleanup(motor.dispose)
        with Session(motor) as sesion:
            self.assertEqual(len(listar_arriendos(sesion, estado="ACTIVO")), 4)
            self.assertEqual(len(listar_arriendos(sesion, estado="DEVUELTO")), 4)
            self.comprobar_grafico(graficar_arriendos_por_categoria, arriendos_por_categoria(sesion), [4, 3, 1, 0])
            self.comprobar_grafico(graficar_equipos_mas_arrendados, equipos_mas_arrendados(sesion), [3, 2, 1, 1, 1])

    @staticmethod
    def arrendar(sesion, equipo_id, cliente_id, cantidad):
        return crear_arriendo(sesion, equipo_id, cliente_id, "2026-01-01", "2026-01-02", cantidad)

    def comprobar_grafico(self, graficar, filas, cantidades):
        figura = Figure(layout="constrained")
        FigureCanvasAgg(figura)
        graficar(figura, filas)
        self.assertEqual([barra.get_width() for barra in figura.axes[0].patches], cantidades)
        png = BytesIO()
        figura.savefig(png, format="png")
        self.assertTrue(png.getvalue().startswith(b"\x89PNG\r\n\x1a\n"))
