import tkinter as tk
from tkinter import ttk, messagebox

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from CRUD.conexion import crear_motor
from CRUD.categoria import (
    crear_categoria,
    listar_categorias,
    actualizar_categoria,
    eliminar_categoria,
)
from CRUD._comun import ErrorValidacion, ErrorPersistencia


motor = crear_motor()
categoria_seleccionada = None

# Ventana principal
ventana = tk.Tk()
ventana.title("Arriendo de equipamiento deportivo")
ventana.geometry("1000x600")

titulo = ttk.Label(
    ventana,
    text="Gestión de arriendos deportivos",
    font=("Arial", 20, "bold"),
)
titulo.pack(pady=20)

# Pestañas
pestanas = ttk.Notebook(ventana)
pestanas.pack(fill="both", expand=True, padx=20, pady=20)

categorias = ttk.Frame(pestanas)
equipos = ttk.Frame(pestanas)
clientes = ttk.Frame(pestanas)
arriendos = ttk.Frame(pestanas)

pestanas.add(categorias, text="Categorías")
pestanas.add(equipos, text="Equipos")
pestanas.add(clientes, text="Clientes")
pestanas.add(arriendos, text="Arriendos")

#Formulario de categorías
formulario = ttk.LabelFrame(
    categorias,
    text="Datos de la categoría",
    padding=20,
)
formulario.pack(fill="x", padx=20, pady=10)
formulario.columnconfigure(1, weight=1)

ttk.Label(formulario, text="Nombre").grid(
    row=0, column=0, sticky="w", pady=5
)

entrada_nombre = ttk.Entry(formulario, width=40)
entrada_nombre.grid(
    row=0, column=1, sticky="ew", padx=10, pady=5
)

ttk.Label(formulario, text="Descripción").grid(
    row=1, column=0, sticky="w", pady=5
)

entrada_descripcion = ttk.Entry(formulario, width=40)
entrada_descripcion.grid(
    row=1, column=1, sticky="ew", padx=10, pady=5
)

estado = ttk.Label(formulario, text="Nueva categoría")
estado.grid(row=2, column=1, sticky="w", padx=10, pady=5)

#Tabla de categorías
marco_tabla = ttk.Frame(categorias)
marco_tabla.pack(fill="both", expand=True, padx=20, pady=10)

tabla_categorias = ttk.Treeview(
    marco_tabla,
    columns=("id", "nombre", "descripcion"),
    show="headings",
    selectmode="browse",
)

tabla_categorias.heading("id", text="ID")
tabla_categorias.heading("nombre", text="Nombre")
tabla_categorias.heading("descripcion", text="Descripción")

tabla_categorias.column("id", width=60, stretch=False, anchor="center")
tabla_categorias.column("nombre", width=200)
tabla_categorias.column("descripcion", width=400)

barra_vertical = ttk.Scrollbar(
    marco_tabla,
    orient="vertical",
    command=tabla_categorias.yview,
)
tabla_categorias.configure(yscrollcommand=barra_vertical.set)

tabla_categorias.pack(side="left", fill="both", expand=True)
barra_vertical.pack(side="right", fill="y")


def limpiar_formulario():
    global categoria_seleccionada

    categoria_seleccionada = None

    entrada_nombre.delete(0, tk.END)
    entrada_descripcion.delete(0, tk.END)

    seleccion = tabla_categorias.selection()
    if seleccion:
        tabla_categorias.selection_remove(*seleccion)

    estado.config(text="Nueva categoría")
    boton_guardar.config(state="normal")
    boton_actualizar.config(state="disabled")
    boton_eliminar.config(state="disabled")

    entrada_nombre.focus_set()


def cargar_categorias():
    try:
        with Session(motor) as sesion:
            filas = [
                (
                    categoria.id,
                    categoria.nombre,
                    categoria.descripcion or "",
                )
                for categoria in listar_categorias(sesion)
            ]
    except (ErrorPersistencia, SQLAlchemyError):
        messagebox.showerror(
            "Error",
            "No se pudieron cargar las categorías.",
            parent=ventana,
        )
        return

    limpiar_formulario()

    for fila in tabla_categorias.get_children():
        tabla_categorias.delete(fila)

    for identificador, nombre, descripcion in filas:
        tabla_categorias.insert(
            "",
            tk.END,
            iid=str(identificador),
            values=(identificador, nombre, descripcion),
        )


def seleccionar_categoria(evento):
    global categoria_seleccionada

    seleccion = tabla_categorias.selection()
    if not seleccion:
        return

    fila = seleccion[0]
    categoria_seleccionada = int(fila)

    nombre = tabla_categorias.set(fila, "nombre")
    descripcion = tabla_categorias.set(fila, "descripcion")

    entrada_nombre.delete(0, tk.END)
    entrada_nombre.insert(0, nombre)

    entrada_descripcion.delete(0, tk.END)
    entrada_descripcion.insert(0, descripcion)

    estado.config(
        text=f"Editando categoría ID: {categoria_seleccionada}"
    )
    boton_guardar.config(state="disabled")
    boton_actualizar.config(state="normal")
    boton_eliminar.config(state="normal")


def guardar_categoria():
    nombre = entrada_nombre.get()
    descripcion = entrada_descripcion.get()

    try:
        with Session(motor) as sesion:
            crear_categoria(sesion, nombre, descripcion)
    except (ErrorValidacion, ErrorPersistencia) as error:
        messagebox.showerror(
            "No se pudo guardar",
            str(error),
            parent=ventana,
        )
        return

    cargar_categorias()

    messagebox.showinfo(
        "Categoría guardada",
        "La categoría se guardó correctamente.",
        parent=ventana,
    )


def modificar_categoria():
    if categoria_seleccionada is None:
        messagebox.showwarning(
            "Selecciona una categoría",
            "Selecciona una fila de la tabla para actualizarla.",
            parent=ventana,
        )
        return

    nombre = entrada_nombre.get()
    descripcion = entrada_descripcion.get()

    try:
        with Session(motor) as sesion:
            actualizar_categoria(
                sesion,
                categoria_seleccionada,
                nombre=nombre,
                descripcion=descripcion,
            )
    except (ErrorValidacion, ErrorPersistencia) as error:
        messagebox.showerror(
            "No se pudo actualizar",
            str(error),
            parent=ventana,
        )
        return

    cargar_categorias()

    messagebox.showinfo(
        "Categoría actualizada",
        "La categoría se actualizó correctamente.",
        parent=ventana,
    )


def borrar_categoria():
    if categoria_seleccionada is None:
        messagebox.showwarning(
            "Selecciona una categoría",
            "Selecciona una fila de la tabla para eliminarla.",
            parent=ventana,
        )
        return

    confirmar = messagebox.askyesno(
        "Confirmar eliminación",
        f"¿Quieres eliminar la categoría ID {categoria_seleccionada}?",
        parent=ventana,
    )

    if not confirmar:
        return

    try:
        with Session(motor) as sesion:
            eliminar_categoria(sesion, categoria_seleccionada)
    except (ErrorValidacion, ErrorPersistencia) as error:
        messagebox.showerror(
            "No se pudo eliminar",
            str(error),
            parent=ventana,
        )
        return

    cargar_categorias()

    messagebox.showinfo(
        "Categoría eliminada",
        "La categoría se eliminó correctamente.",
        parent=ventana,
    )


# Botones del formulario
botones = ttk.Frame(formulario)
botones.grid(row=3, column=1, sticky="e", padx=10, pady=10)

ttk.Button(
    botones,
    text="Nuevo / Limpiar",
    command=limpiar_formulario,
).pack(side="left", padx=5)

boton_guardar = ttk.Button(
    botones,
    text="Guardar",
    command=guardar_categoria,
)
boton_guardar.pack(side="left", padx=5)

boton_actualizar = ttk.Button(
    botones,
    text="Actualizar",
    command=modificar_categoria,
    state="disabled",
)
boton_actualizar.pack(side="left", padx=5)

boton_eliminar = ttk.Button(
    botones,
    text="Eliminar",
    command=borrar_categoria,
    state="disabled",
)
boton_eliminar.pack(side="left", padx=5)

tabla_categorias.bind("<<TreeviewSelect>>", seleccionar_categoria)

# Cargar los datos existentes e iniciar la aplicación
if __name__ == "__main__":
    cargar_categorias()
    try:
        ventana.mainloop()
    finally:
        motor.dispose()