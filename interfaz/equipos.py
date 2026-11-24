import tkinter as tk
from tkinter import messagebox, ttk

from CRUD.categoria import listar_categorias
from CRUD.equipo import actualizar_equipo, crear_equipo, eliminar_equipo, listar_equipos
from interfaz.panel import Panel


_ETIQUETAS_TIPO = {
    "general": "General",
    "proteccion": "Protección",
    "entrenamiento": "Entrenamiento",
}
_TIPOS_POR_ETIQUETA = {etiqueta: tipo for tipo, etiqueta in _ETIQUETAS_TIPO.items()}


class VistaEquipos(Panel):
    def __init__(self, padre, motor):
        columnas = (
            ("id", "ID", 45), ("nombre", "Nombre", 140), ("categoria", "Categoría", 140),
            ("tipo", "Tipo", 100),
            ("precio", "Precio diario", 90), ("total", "Stock total", 80),
            ("disponible", "Disponible", 80),
        )
        super().__init__(padre, motor, "Datos del equipo", columnas)
        self.nombre = tk.StringVar(self)
        self.categoria = tk.StringVar(self)
        self.precio = tk.StringVar(self)
        self.stock = tk.StringVar(self)
        self.tipo = tk.StringVar(self, _ETIQUETAS_TIPO["general"])
        self.solo_disponibles = tk.BooleanVar(self)
        self.categorias = {}

        self.campo(0, "Nombre", self.nombre)
        self.combo_categoria = self.campo(1, "Categoría", self.categoria, selector=True)
        self.campo(2, "Precio diario", self.precio)
        self.campo(3, "Stock total", self.stock)
        self.combo_tipo = self.campo(4, "Tipo de equipamiento", self.tipo, selector=True)
        self.combo_tipo["values"] = tuple(_TIPOS_POR_ETIQUETA)
        self.boton("Nuevo", self.limpiar)
        self.boton_guardar = self.boton("Guardar", self.guardar)
        self.boton("Eliminar", self.eliminar)
        self.boton("Recargar", self.recargar)
        ttk.Checkbutton(self.controles, text="Solo disponibles", variable=self.solo_disponibles,
                        command=self.filtrar).pack(side="right")
        self.tabla.bind("<<TreeviewSelect>>", self.seleccionar)
        self.recargar()

    def leer_filas(self, sesion):
        etiquetas = {c.id: f"{c.id} - {c.nombre}" for c in listar_categorias(sesion)}
        equipos = listar_equipos(sesion, solo_disponibles=self.solo_disponibles.get())
        self.categorias = {texto: id_categoria for id_categoria, texto in etiquetas.items()}
        self.combo_categoria["values"] = list(self.categorias)
        if self.categoria.get() not in self.categorias:
            self.categoria.set("")
        return [
            (e.id, e.nombre, etiquetas.get(e.categoria_id, ""), _ETIQUETAS_TIPO.get(e.tipo, e.tipo),
             e.precio_diario, e.stock_total, e.stock_disponible)
            for e in equipos
        ]

    def filtrar(self):
        self.limpiar()
        self.recargar()

    def limpiar(self):
        fila = self.seleccion()
        if fila is not None:
            self.tabla.selection_remove(fila)
        for campo in (self.nombre, self.categoria, self.precio, self.stock):
            campo.set("")
        self.tipo.set(_ETIQUETAS_TIPO["general"])
        self.combo_tipo.configure(state="readonly")
        self.boton_guardar.configure(text="Guardar")

    def seleccionar(self, _evento):
        fila = self.seleccion()
        if fila is None:
            self.limpiar()
            return
        self.nombre.set(self.tabla.set(fila, "nombre"))
        self.categoria.set(self.tabla.set(fila, "categoria"))
        self.precio.set(self.tabla.set(fila, "precio"))
        self.stock.set(self.tabla.set(fila, "total"))
        self.tipo.set(self.tabla.set(fila, "tipo"))
        self.combo_tipo.configure(state="disabled")
        self.boton_guardar.configure(text="Guardar cambios")

    def guardar(self):
        categoria_id = self.categorias.get(self.categoria.get())
        if categoria_id is None:
            messagebox.showwarning("Categoría requerida", "Selecciona una categoría.", parent=self)
            return
        datos = (self.nombre.get(), categoria_id, self.precio.get(), self.stock.get())
        fila = self.seleccion()
        if fila is None:
            tipo = _TIPOS_POR_ETIQUETA.get(self.tipo.get())
            if tipo is None:
                messagebox.showwarning("Tipo requerido", "Selecciona un tipo de equipamiento.", parent=self)
                return
            guardado = self.ejecutar(crear_equipo, "Equipo guardado.", *datos, tipo=tipo)
        else:
            guardado = self.ejecutar(actualizar_equipo, "Equipo actualizado.", int(fila), *datos)
        if guardado:
            self.limpiar()

    def eliminar(self):
        fila = self.seleccion()
        if fila is None:
            messagebox.showwarning("Eliminar equipo", "Selecciona un equipo de la tabla.", parent=self)
        elif messagebox.askyesno("Eliminar equipo", "¿Eliminar el equipo seleccionado?", parent=self):
            if self.ejecutar(eliminar_equipo, "Equipo eliminado.", int(fila)):
                self.limpiar()
