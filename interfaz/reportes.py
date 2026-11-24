import tkinter as tk
from tkinter import messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from reportes import (
    arriendos_por_categoria, equipos_mas_arrendados,
    graficar_arriendos_por_categoria, graficar_equipos_mas_arrendados,
)


class VistaReportes(ttk.Frame):
    def __init__(self, padre, motor):
        super().__init__(padre, padding=15)
        self.motor = motor
        ttk.Button(self, text="Actualizar gráficos", command=self.recargar).pack(anchor="e", pady=(0, 8))
        pestanas = ttk.Notebook(self)
        pestanas.pack(fill="both", expand=True)
        self.categorias = self._agregar_grafico(pestanas, "Por categoría")
        self.equipos = self._agregar_grafico(pestanas, "Equipos más arrendados")
        self.bind("<Map>", self.recargar)

    @staticmethod
    def _agregar_grafico(pestanas, nombre):
        panel = ttk.Frame(pestanas)
        pestanas.add(panel, text=nombre)
        area = tk.Canvas(panel, highlightthickness=0)
        barra = ttk.Scrollbar(panel, orient="vertical", command=area.yview)
        barra.pack(side="right", fill="y")
        area.configure(yscrollcommand=barra.set)
        area.pack(side="left", fill="both", expand=True)

        lienzo = FigureCanvasTkAgg(Figure(layout="constrained"), master=area)
        ventana = area.create_window(0, 0, anchor="nw", window=lienzo.get_tk_widget(), height=340)
        area.bind("<Configure>", lambda evento: area.itemconfigure(ventana, width=evento.width))
        lienzo.get_tk_widget().bind(
            "<Configure>", lambda _evento: area.configure(scrollregion=area.bbox(ventana)), add="+",
        )
        return area, ventana, lienzo

    def recargar(self, _evento=None):
        try:
            with Session(self.motor) as sesion:
                categorias = arriendos_por_categoria(sesion)
                equipos = equipos_mas_arrendados(sesion)
        except SQLAlchemyError:
            messagebox.showerror("Error", "No se pudieron cargar los arriendos.", parent=self)
            return

        for (area, ventana, lienzo), graficar, filas in (
            (self.categorias, graficar_arriendos_por_categoria, categorias),
            (self.equipos, graficar_equipos_mas_arrendados, equipos),
        ):
            graficar(lienzo.figure, filas)
            area.itemconfigure(ventana, height=max(340, 90 + 26 * len(filas)))
            lienzo.draw_idle()
