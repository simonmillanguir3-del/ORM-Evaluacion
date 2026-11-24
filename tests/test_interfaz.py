import tkinter as tk
import unittest
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from tkinter import messagebox, ttk
from unittest.mock import patch

from CRUD.conexion import crear_motor
from main import crear_ventana


class PruebasInterfaz(unittest.TestCase):
    def setUp(self):
        carpeta = TemporaryDirectory()
        self.addCleanup(carpeta.cleanup)
        self.ruta = Path(carpeta.name) / "interfaz.db"

    def test_filtro_de_categorias_conserva_la_seleccion_visible(self):
        with self.ventana_abierta() as ventana:
            categorias = self.seleccionar(self.notebook(ventana), 0)
            for nombre in ("Ciclismo", "Natación"):
                categorias.nombre.set(nombre)
                categorias.guardar.invoke()

            ciclismo, natacion = categorias.tabla.get_children()
            categorias.tabla.selection_set(ciclismo)
            ventana.update()
            self.assertEqual(categorias.nombre.get(), "Ciclismo")

            categorias.busqueda.set("cicli")
            self.assertEqual(categorias.tabla.get_children(), (ciclismo,))
            self.assertEqual(categorias.seleccion(), ciclismo)

            categorias.busqueda.set("natación")
            self.assertEqual(categorias.tabla.get_children(), (natacion,))
            self.assertIsNone(categorias.seleccion())
            self.assertEqual(categorias.nombre.get(), "")
            self.assertIn("1 de 2", categorias.resumen.get())

    def test_registro_devolucion_y_reportes_al_reabrir(self):
        with (
            self.ventana_abierta() as ventana,
            patch.object(messagebox, "showerror") as error,
            patch.object(messagebox, "showwarning") as advertencia,
            patch.object(messagebox, "askyesno", return_value=True),
        ):
            pestanas = self.notebook(ventana)
            self.assertEqual(
                [pestanas.tab(tab, "text") for tab in pestanas.tabs()],
                ["Categorías", "Equipos", "Clientes", "Arriendos", "Reportes"],
            )
            categorias = self.seleccionar(pestanas, 0)
            categorias.nombre.set("Ciclismo")
            categorias.guardar.invoke()

            equipos = self.seleccionar(pestanas, 1)
            equipos.nombre.set("Casco")
            equipos.combo_categoria.current(0)
            equipos.combo_tipo.set("Protección")
            equipos.precio.set("3500")
            equipos.stock.set("5")
            equipos.boton_guardar.invoke()
            equipo_id, = equipos.tabla.get_children()
            self.assertEqual(equipos.tabla.set(equipo_id, "tipo"), "Protección")
            self.assertEqual(int(equipos.tabla.set(equipo_id, "disponible")), 5)

            clientes = self.seleccionar(pestanas, 2)
            clientes.nombre.set("Cliente de prueba")
            clientes.correo.set("cliente@example.com")
            clientes.telefono.set("123456789")
            clientes.boton_guardar.invoke()

            arriendos = self.seleccionar(pestanas, 3)
            self.registrar(arriendos, 2)
            arriendo_id, = arriendos.tabla.get_children()
            self.assertEqual(arriendos.tabla.set(arriendo_id, "estado"), "ACTIVO")
            self.registrar(arriendos, 4)
            error.assert_called_once()
            self.assertIn("stock", error.call_args.args[1])
            self.assertEqual(arriendos.tabla.get_children(), (arriendo_id,))
            self.seleccionar(pestanas, 1)
            self.assertEqual(int(equipos.tabla.set(equipo_id, "disponible")), 3)

            self.seleccionar(pestanas, 3)
            arriendos.tabla.selection_set(arriendo_id)
            devolver = self.boton(arriendos, "Devolver seleccionado")
            devolver.invoke()
            self.assertEqual(arriendos.tabla.set(arriendo_id, "estado"), "DEVUELTO")
            devolver.invoke()
            advertencia.assert_called_once()
            self.assertIn("ya fue devuelto", advertencia.call_args.args[1])
            self.seleccionar(pestanas, 1)
            self.assertEqual(int(equipos.tabla.set(equipo_id, "disponible")), 5)

        with self.ventana_abierta() as ventana:
            reportes = self.seleccionar(self.notebook(ventana), 4)
            for indice, (_, _, lienzo) in enumerate((reportes.categorias, reportes.equipos)):
                self.seleccionar(self.notebook(reportes), indice)
                lienzo.draw()
                self.assertEqual([barra.get_width() for barra in lienzo.figure.axes[0].patches], [1])

    @contextmanager
    def ventana_abierta(self):
        motor = crear_motor(self.ruta)
        try:
            try:
                ventana = crear_ventana(motor)
            except tk.TclError as error:
                if "display" in str(error):
                    self.skipTest(f"Tkinter requiere un entorno gráfico: {error}")
                raise
            try:
                errores = []
                ventana.attributes("-alpha", 0.0)
                ventana.report_callback_exception = lambda tipo, error, traza: errores.append(error)
                yield ventana
                self.assertEqual(errores, [])
            finally:
                ventana.destroy()
        finally:
            motor.dispose()

    @staticmethod
    def notebook(padre):
        return next(hijo for hijo in padre.winfo_children() if isinstance(hijo, ttk.Notebook))

    @staticmethod
    def seleccionar(pestanas, indice):
        panel = pestanas.tabs()[indice]
        pestanas.select(panel)
        pestanas.update()
        return pestanas.nametowidget(panel)

    @staticmethod
    def boton(panel, texto):
        return next(
            hijo for hijo in panel.controles.winfo_children()
            if isinstance(hijo, ttk.Button) and hijo.cget("text") == texto
        )

    def registrar(self, arriendos, cantidad):
        arriendos.combo_equipo.current(0)
        arriendos.combo_cliente.current(0)
        arriendos.inicio.set("2026-01-01")
        arriendos.termino.set("2026-01-02")
        arriendos.cantidad.set(str(cantidad))
        self.boton(arriendos, "Registrar arriendo").invoke()
