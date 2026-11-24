import tkinter as tk
from tkinter import messagebox, ttk

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from CRUD import ErrorPersistencia, ErrorValidacion


class Panel(ttk.Frame):
    "Formulario, tabla y manejo de errores compartidos por las pestañas."

    def __init__(self, padre, motor, titulo, columnas, *, desplazamiento_horizontal=False):
        super().__init__(padre, padding=15)
        self.motor = motor
        self.formulario = ttk.LabelFrame(self, text=titulo, padding=10)
        self.formulario.pack(fill="x")
        self.formulario.columnconfigure(1, weight=1)

        self.controles = ttk.Frame(self)
        self.controles.pack(fill="x", pady=8)
        marco = ttk.Frame(self)
        marco.pack(fill="both", expand=True)
        marco.columnconfigure(0, weight=1)
        marco.rowconfigure(0, weight=1)
        self.tabla = ttk.Treeview(marco, columns=[clave for clave, _, _ in columnas],
                                  show="headings", selectmode="browse")
        for clave, etiqueta, ancho in columnas:
            self.tabla.heading(clave, text=etiqueta)
            self.tabla.column(clave, width=ancho, stretch=clave != "id")
        barra = ttk.Scrollbar(marco, orient="vertical", command=self.tabla.yview)
        barra.grid(row=0, column=1, sticky="ns")
        self.tabla.configure(yscrollcommand=barra.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        if desplazamiento_horizontal:
            horizontal = ttk.Scrollbar(marco, orient="horizontal", command=self.tabla.xview)
            horizontal.grid(row=1, column=0, sticky="ew")
            self.tabla.configure(xscrollcommand=horizontal.set)

        self.estado = tk.StringVar(self)
        ttk.Label(self, textvariable=self.estado).pack(anchor="w", pady=(6, 0))

    def campo(self, fila, etiqueta, variable, selector=False):
        ttk.Label(self.formulario, text=etiqueta).grid(row=fila, column=0, sticky="w")
        if selector:
            entrada = ttk.Combobox(self.formulario, textvariable=variable, state="readonly")
        else:
            entrada = ttk.Entry(self.formulario, textvariable=variable)
        entrada.grid(row=fila, column=1, sticky="ew", padx=8, pady=3)
        return entrada

    def boton(self, texto, accion):
        boton = ttk.Button(self.controles, text=texto, command=accion)
        boton.pack(side="left", padx=(0, 6))
        return boton

    def seleccion(self):
        filas = self.tabla.selection()
        return filas[0] if filas else None

    def recargar(self):
        try:
            with Session(self.motor) as sesion:
                filas = self.leer_filas(sesion)
        except (ErrorPersistencia, SQLAlchemyError):
            messagebox.showerror("Error", "No se pudieron cargar los datos.", parent=self)
            return False

        self.mostrar_filas(filas)
        return True

    def mostrar_filas(self, filas):
        "Actualiza las filas por ID y conserva la selección de los registros visibles."
        restantes = set(self.tabla.get_children())
        for indice, fila in enumerate(filas):
            clave = str(fila[0])
            if clave in restantes:
                self.tabla.item(clave, values=fila)
                self.tabla.move(clave, "", indice)
                restantes.remove(clave)
            else:
                self.tabla.insert("", indice, iid=clave, values=fila)
        if restantes:
            self.tabla.delete(*restantes)

    def ejecutar(self, operacion, mensaje, *datos, **opciones):
        try:
            with Session(self.motor) as sesion:
                operacion(sesion, *datos, **opciones)
        except (ErrorValidacion, ErrorPersistencia) as error:
            messagebox.showerror("No se pudo completar", str(error), parent=self)
            return False
        except SQLAlchemyError:
            messagebox.showerror("Error", "No se pudo acceder a la base de datos.", parent=self)
            return False

        if self.recargar():
            self.estado.set(mensaje)
        else:
            self.estado.set(f"{mensaje} No se pudo actualizar la tabla.")
        return True
