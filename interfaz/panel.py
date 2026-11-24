import tkinter as tk
from tkinter import messagebox, ttk

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from CRUD._comun import ErrorPersistencia, ErrorValidacion


class Panel(ttk.Frame):
    """Formulario, tabla y manejo de errores compartidos por las pestañas."""

    def __init__(self, padre, motor, titulo, columnas):
        super().__init__(padre, padding=15)
        self.motor = motor
        self.formulario = ttk.LabelFrame(self, text=titulo, padding=10)
        self.formulario.pack(fill="x")
        self.formulario.columnconfigure(1, weight=1)

        self.controles = ttk.Frame(self)
        self.controles.pack(fill="x", pady=8)
        marco = ttk.Frame(self)
        marco.pack(fill="both", expand=True)
        self.tabla = ttk.Treeview(marco, columns=[clave for clave, _, _ in columnas],
                                  show="headings", selectmode="browse")
        for clave, etiqueta, ancho in columnas:
            self.tabla.heading(clave, text=etiqueta)
            self.tabla.column(clave, width=ancho, stretch=clave != "id")
        barra = ttk.Scrollbar(marco, orient="vertical", command=self.tabla.yview)
        barra.pack(side="right", fill="y")
        self.tabla.configure(yscrollcommand=barra.set)
        self.tabla.pack(fill="both", expand=True)

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
        except SQLAlchemyError:
            messagebox.showerror("Error", "No se pudieron cargar los datos.", parent=self)
            return

        # Actualizar las filas en su sitio conserva la selección al cambiar de pestaña.
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

        self.estado.set(mensaje)
        self.recargar()
        return True
