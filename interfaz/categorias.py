import tkinter as tk
from tkinter import messagebox, ttk

from CRUD.categoria import actualizar_categoria, crear_categoria, eliminar_categoria, listar_categorias
from interfaz.panel import Panel


class VistaCategorias(Panel):
    def __init__(self, padre, motor):
        columnas = (("id", "ID", 60), ("nombre", "Nombre", 200), ("descripcion", "Descripción", 400))
        super().__init__(padre, motor, "Datos de la categoría", columnas, desplazamiento_horizontal=True)
        self.filas = []
        self.nombre = tk.StringVar(self)
        self.descripcion = tk.StringVar(self)
        self.busqueda = tk.StringVar(self)
        self.resumen = tk.StringVar(self)

        self.entrada_nombre = self.campo(0, "Nombre", self.nombre)
        self.campo(1, "Descripción", self.descripcion)
        self.boton("Nuevo / Limpiar", self.limpiar)
        self.guardar = self.boton("Guardar", self.crear)
        self.actualizar = self.boton("Actualizar", self.modificar)
        self.eliminar = self.boton("Eliminar", self.borrar)
        self.boton("Recargar", self.recargar)
        ttk.Label(self.controles, text="Buscar").pack(side="left", padx=(8, 6))
        ttk.Entry(self.controles, textvariable=self.busqueda).pack(side="left", fill="x", expand=True)
        ttk.Label(self, textvariable=self.resumen).pack(anchor="w")
        self.tabla.bind("<<TreeviewSelect>>", self.seleccionar)
        self.busqueda.trace_add("write", self.filtrar)
        self.limpiar()
        self.recargar()

    def leer_filas(self, sesion):
        return [(c.id, c.nombre, c.descripcion or "") for c in listar_categorias(sesion)]

    def mostrar_filas(self, filas):
        self.filas = filas
        self.limpiar()
        self.filtrar()

    def filtrar(self, *_):
        consulta = self.busqueda.get().strip().casefold()
        visibles = [fila for fila in self.filas if consulta in " ".join(map(str, fila)).casefold()]
        seleccion = self.seleccion()
        super().mostrar_filas(visibles)
        if seleccion is not None and not self.tabla.exists(seleccion):
            self.limpiar()
        self.resumen.set(f"Mostrando {len(visibles)} de {len(self.filas)} categorías")

    def modo_edicion(self, activo):
        self.guardar.configure(state="disabled" if activo else "normal")
        for boton in (self.actualizar, self.eliminar):
            boton.configure(state="normal" if activo else "disabled")

    def limpiar(self):
        fila = self.seleccion()
        if fila is not None:
            self.tabla.selection_remove(fila)
        self.nombre.set("")
        self.descripcion.set("")
        self.estado.set("Nueva categoría")
        self.modo_edicion(False)
        self.entrada_nombre.focus_set()

    def seleccionar(self, _evento=None):
        fila = self.seleccion()
        if fila is not None:
            self.nombre.set(self.tabla.set(fila, "nombre"))
            self.descripcion.set(self.tabla.set(fila, "descripcion"))
            self.estado.set(f"Editando categoría ID: {fila}")
            self.modo_edicion(True)

    def crear(self):
        self.ejecutar(crear_categoria, "Categoría guardada.", self.nombre.get(), self.descripcion.get())

    def modificar(self):
        fila = self.seleccion()
        if fila is not None:
            self.ejecutar(actualizar_categoria, "Categoría actualizada.", fila, self.nombre.get(), self.descripcion.get())

    def borrar(self):
        fila = self.seleccion()
        if fila is not None and messagebox.askyesno(
            "Confirmar eliminación", f"¿Eliminar la categoría ID {fila}?", parent=self,
        ):
            self.ejecutar(eliminar_categoria, "Categoría eliminada.", fila)
