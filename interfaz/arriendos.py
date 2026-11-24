import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

from CRUD.arriendo import crear_arriendo, devolver_arriendo, listar_arriendos
from CRUD.cliente import listar_clientes
from CRUD.equipo import listar_equipos
from interfaz.panel import Panel


class VistaArriendos(Panel):
    def __init__(self, padre, motor):
        columnas = (
            ("id", "ID", 45), ("equipo", "Equipo", 115), ("cliente", "Cliente", 115),
            ("inicio", "Inicio", 85), ("termino", "Término previsto", 100),
            ("cantidad", "Cantidad", 60), ("estado", "Estado", 80),
        )
        super().__init__(padre, motor, "Registrar arriendo", columnas)
        self.equipo = tk.StringVar(self)
        self.cliente = tk.StringVar(self)
        self.inicio = tk.StringVar(self, date.today().isoformat())
        self.termino = tk.StringVar(self, date.today().isoformat())
        self.cantidad = tk.StringVar(self, "1")
        self.solo_activos = tk.BooleanVar(self)
        self.equipos = {}
        self.clientes = {}

        self.combo_equipo = self.campo(0, "Equipo disponible", self.equipo, selector=True)
        self.combo_cliente = self.campo(1, "Cliente", self.cliente, selector=True)
        self.campo(2, "Inicio (AAAA-MM-DD)", self.inicio)
        self.campo(3, "Término (AAAA-MM-DD)", self.termino)
        self.campo(4, "Cantidad", self.cantidad)
        self.boton("Registrar arriendo", self.registrar)
        self.boton("Devolver seleccionado", self.devolver)
        self.boton("Recargar", self.recargar)
        ttk.Checkbutton(self.controles, text="Solo activos", variable=self.solo_activos,
                        command=self.recargar).pack(side="right")
        self.recargar()

    def leer_filas(self, sesion):
        equipos = listar_equipos(sesion)
        clientes = listar_clientes(sesion)
        estado = "ACTIVO" if self.solo_activos.get() else None
        arriendos = listar_arriendos(sesion, estado=estado)
        nombres_equipos = {e.id: f"{e.id} - {e.nombre}" for e in equipos}
        nombres_clientes = {c.id: f"{c.id} - {c.nombre}" for c in clientes}
        self.equipos = {nombres_equipos[e.id]: e.id for e in equipos if e.stock_disponible > 0}
        self.clientes = {nombre: id_cliente for id_cliente, nombre in nombres_clientes.items()}
        self.combo_equipo["values"] = list(self.equipos)
        self.combo_cliente["values"] = list(self.clientes)
        if self.equipo.get() not in self.equipos:
            self.equipo.set("")
        if self.cliente.get() not in self.clientes:
            self.cliente.set("")

        return [(a.id, nombres_equipos.get(a.equipo_id, a.equipo_id),
                 nombres_clientes.get(a.cliente_id, a.cliente_id), a.fecha_inicio.isoformat(),
                 a.fecha_fin_prevista.isoformat(), a.cantidad, a.estado) for a in arriendos]

    def registrar(self):
        equipo_id = self.equipos.get(self.equipo.get())
        cliente_id = self.clientes.get(self.cliente.get())
        if equipo_id is None or cliente_id is None:
            messagebox.showwarning("Faltan datos", "Selecciona un equipo y un cliente.", parent=self)
            return
        if self.ejecutar(crear_arriendo, "Arriendo registrado.", equipo_id, cliente_id,
                         self.inicio.get(), self.termino.get(), self.cantidad.get()):
            self.equipo.set("")
            self.cliente.set("")
            self.cantidad.set("1")

    def devolver(self):
        fila = self.seleccion()
        if fila is None:
            messagebox.showwarning("Devolución", "Selecciona un arriendo de la tabla.", parent=self)
            return
        if self.tabla.set(fila, "estado") != "ACTIVO":
            messagebox.showwarning("Devolución", "Este arriendo ya fue devuelto.", parent=self)
            return
        if messagebox.askyesno("Devolución", "¿Devolver todas las unidades del arriendo?", parent=self):
            self.ejecutar(devolver_arriendo, "Devolución registrada.", int(fila))
