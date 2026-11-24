import tkinter as tk
from tkinter import messagebox

from CRUD.cliente import actualizar_cliente, crear_cliente, eliminar_cliente, listar_clientes
from interfaz.panel import Panel


class VistaClientes(Panel):
    def __init__(self, padre, motor):
        columnas = (
            ("id", "ID", 45), ("nombre", "Nombre", 180),
            ("correo", "Correo", 200), ("telefono", "Teléfono", 130),
        )
        super().__init__(padre, motor, "Datos del cliente", columnas)
        self.nombre = tk.StringVar(self)
        self.correo = tk.StringVar(self)
        self.telefono = tk.StringVar(self)

        self.campo(0, "Nombre", self.nombre)
        self.campo(1, "Correo", self.correo)
        self.campo(2, "Teléfono", self.telefono)
        self.boton("Nuevo", self.limpiar)
        self.boton_guardar = self.boton("Guardar", self.guardar)
        self.boton("Eliminar", self.eliminar)
        self.tabla.bind("<<TreeviewSelect>>", self.seleccionar)
        self.recargar()

    def leer_filas(self, sesion):
        return [(c.id, c.nombre, c.correo, c.telefono) for c in listar_clientes(sesion)]

    def limpiar(self):
        fila = self.seleccion()
        if fila is not None:
            self.tabla.selection_remove(fila)
        self.nombre.set("")
        self.correo.set("")
        self.telefono.set("")
        self.boton_guardar.configure(text="Guardar")

    def seleccionar(self, _evento):
        fila = self.seleccion()
        if fila is None:
            self.limpiar()
            return
        self.nombre.set(self.tabla.set(fila, "nombre"))
        self.correo.set(self.tabla.set(fila, "correo"))
        self.telefono.set(self.tabla.set(fila, "telefono"))
        self.boton_guardar.configure(text="Guardar cambios")

    def guardar(self):
        datos = (self.nombre.get(), self.correo.get(), self.telefono.get())
        fila = self.seleccion()
        if fila is None:
            guardado = self.ejecutar(crear_cliente, "Cliente guardado.", *datos)
        else:
            guardado = self.ejecutar(actualizar_cliente, "Cliente actualizado.", int(fila), *datos)
        if guardado:
            self.limpiar()

    def eliminar(self):
        fila = self.seleccion()
        if fila is None:
            messagebox.showwarning("Eliminar cliente", "Selecciona un cliente de la tabla.", parent=self)
        elif messagebox.askyesno("Eliminar cliente", "¿Eliminar el cliente seleccionado?", parent=self):
            if self.ejecutar(eliminar_cliente, "Cliente eliminado.", int(fila)):
                self.limpiar()
