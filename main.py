import tkinter as tk
from tkinter import ttk

from CRUD.conexion import crear_motor
from interfaz.categorias import VistaCategorias


def main():
    motor = crear_motor()
    try:
        ventana = tk.Tk()
        ventana.title("Arriendo de equipamiento deportivo")
        ventana.geometry("1000x650")
        ventana.minsize(720, 500)
        ttk.Label(ventana, text="Gestión de arriendos deportivos",
                  font=("Arial", 20, "bold")).pack(pady=20)
        pestanas = ttk.Notebook(ventana)
        pestanas.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        pestanas.add(VistaCategorias(pestanas, motor), text="Categorías")
        for nombre in ("Equipos", "Clientes", "Arriendos"):
            panel = ttk.Frame(pestanas, padding=20)
            ttk.Label(panel, text="Funcionalidad pendiente.").pack()
            pestanas.add(panel, text=nombre)
        ventana.mainloop()
    finally:
        motor.dispose()


if __name__ == "__main__":
    main()
