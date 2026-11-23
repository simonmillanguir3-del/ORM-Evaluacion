import tkinter as tk
from tkinter import messagebox, ttk

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from CRUD._comun import ErrorPersistencia, ErrorValidacion
from CRUD.categoria import (
    actualizar_categoria, crear_categoria, eliminar_categoria, listar_categorias,
)


class VistaCategorias(ttk.Frame):
    """Gestiona la vista; las validaciones de negocio permanecen en CRUD."""

    def __init__(self, padre, motor):
        super().__init__(padre, padding=15)
        self.motor = motor
        self.seleccionada = None
        self.filas = []
        self.nombre = tk.StringVar(self)
        self.descripcion = tk.StringVar(self)
        self.busqueda = tk.StringVar(self)
        self.estado = tk.StringVar(self, "Nueva categoría")
        self.resumen = tk.StringVar(self)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self.crear_formulario()
        self.crear_tabla()
        self.busqueda.trace_add("write", self.filtrar)
        self.cargar()

    def crear_formulario(self):
        formulario = ttk.LabelFrame(self, text="Datos de la categoría", padding=15)
        formulario.grid(row=0, column=0, sticky="ew")
        formulario.columnconfigure(1, weight=1)
        for fila, (etiqueta, variable) in enumerate((
            ("Nombre", self.nombre), ("Descripción", self.descripcion),
        )):
            ttk.Label(formulario, text=etiqueta).grid(row=fila, column=0, sticky="w")
            entrada = ttk.Entry(formulario, textvariable=variable)
            entrada.grid(row=fila, column=1, sticky="ew", padx=10, pady=5)
            if fila == 0:
                self.entrada_nombre = entrada
        ttk.Label(formulario, textvariable=self.estado).grid(
            row=2, column=1, sticky="w", padx=10, pady=5,
        )
        botones = ttk.Frame(formulario)
        botones.grid(row=3, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(botones, text="Nuevo / Limpiar", command=self.limpiar).pack(side="left", padx=4)
        self.guardar = ttk.Button(botones, text="Guardar", command=self.crear)
        self.actualizar = ttk.Button(botones, text="Actualizar", command=self.modificar)
        self.eliminar = ttk.Button(botones, text="Eliminar", command=self.borrar)
        for boton in (self.guardar, self.actualizar, self.eliminar):
            boton.pack(side="left", padx=4)
        self.modo_edicion(False)

    def crear_tabla(self):
        filtros = ttk.Frame(self)
        filtros.grid(row=1, column=0, sticky="ew", pady=12)
        filtros.columnconfigure(1, weight=1)
        ttk.Label(filtros, text="Buscar").grid(row=0, column=0, padx=(0, 10))
        ttk.Entry(filtros, textvariable=self.busqueda).grid(row=0, column=1, sticky="ew")
        ttk.Button(filtros, text="Recargar", command=self.cargar).grid(row=0, column=2, padx=(10, 0))
        marco = ttk.Frame(self)
        marco.grid(row=2, column=0, sticky="nsew")
        marco.columnconfigure(0, weight=1)
        marco.rowconfigure(0, weight=1)
        self.tabla = ttk.Treeview(marco, columns=("id", "nombre", "descripcion"),
                                  show="headings", selectmode="browse")
        for columna, titulo, ancho in (
            ("id", "ID", 60), ("nombre", "Nombre", 200), ("descripcion", "Descripción", 400),
        ):
            self.tabla.heading(columna, text=titulo)
            self.tabla.column(columna, width=ancho, stretch=columna != "id")
        self.tabla.grid(row=0, column=0, sticky="nsew")
        vertical = ttk.Scrollbar(marco, orient="vertical", command=self.tabla.yview)
        horizontal = ttk.Scrollbar(marco, orient="horizontal", command=self.tabla.xview)
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        self.tabla.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.tabla.bind("<<TreeviewSelect>>", self.seleccionar)
        ttk.Label(self, textvariable=self.resumen).grid(row=3, column=0, sticky="w", pady=(8, 0))

    def modo_edicion(self, activo):
        self.guardar.configure(state="disabled" if activo else "normal")
        for boton in (self.actualizar, self.eliminar):
            boton.configure(state="normal" if activo else "disabled")

    def limpiar(self):
        self.seleccionada = None
        self.nombre.set("")
        self.descripcion.set("")
        seleccion = self.tabla.selection()
        if seleccion:
            self.tabla.selection_remove(*seleccion)
        self.estado.set("Nueva categoría")
        self.modo_edicion(False)
        self.entrada_nombre.focus_set()

    def cargar(self):
        try:
            with Session(self.motor) as sesion:
                filas = [(c.id, c.nombre, c.descripcion or "") for c in listar_categorias(sesion)]
        except (ErrorPersistencia, SQLAlchemyError):
            messagebox.showerror("Error", "No se pudieron cargar las categorías.", parent=self)
            return False
        self.filas = filas
        self.limpiar()
        self.filtrar()
        return True

    def filtrar(self, *_):
        # Filtrar en memoria evita consultar SQLite con cada tecla.
        consulta = self.busqueda.get().strip().casefold()
        visibles = [fila for fila in self.filas if consulta in " ".join(map(str, fila)).casefold()]
        seleccionada = self.seleccionada
        anteriores = self.tabla.get_children()
        if anteriores:
            self.tabla.delete(*anteriores)
        for fila in visibles:
            self.tabla.insert("", "end", iid=str(fila[0]), values=fila)
        if seleccionada is not None:
            if self.tabla.exists(str(seleccionada)):
                self.tabla.selection_set(str(seleccionada))
            else:
                self.limpiar()
        self.resumen.set(f"Mostrando {len(visibles)} de {len(self.filas)} categorías")

    def seleccionar(self, _evento=None):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        fila = seleccion[0]
        if int(fila) == self.seleccionada:
            return
        self.seleccionada = int(fila)
        self.nombre.set(self.tabla.set(fila, "nombre"))
        self.descripcion.set(self.tabla.set(fila, "descripcion"))
        self.estado.set(f"Editando categoría ID: {fila}")
        self.modo_edicion(True)

    def ejecutar(self, operacion, mensaje, *args):
        """Comparte el manejo de sesiones y errores entre las tres acciones."""
        try:
            with Session(self.motor) as sesion:
                operacion(sesion, *args)
        except (ErrorValidacion, ErrorPersistencia) as error:
            messagebox.showerror("No se pudo completar", str(error), parent=self)
            return
        except SQLAlchemyError:
            messagebox.showerror("Error", "No se pudo acceder a la base de datos.", parent=self)
            return
        self.limpiar()
        if self.cargar():
            self.estado.set(mensaje)
        else:
            self.estado.set(f"{mensaje} Pulsa Recargar para actualizar la tabla.")

    def crear(self):
        self.ejecutar(crear_categoria, "Categoría guardada.", self.nombre.get(), self.descripcion.get())

    def modificar(self):
        if self.seleccionada is not None:
            self.ejecutar(actualizar_categoria, "Categoría actualizada.",
                          self.seleccionada, self.nombre.get(), self.descripcion.get())

    def borrar(self):
        if self.seleccionada is not None and messagebox.askyesno(
            "Confirmar eliminación", f"¿Eliminar la categoría ID {self.seleccionada}?", parent=self,
        ):
            self.ejecutar(eliminar_categoria, "Categoría eliminada.", self.seleccionada)
