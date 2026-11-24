import tkinter as tk
from tkinter import ttk

from CRUD.conexion import crear_motor
from interfaz.arriendos import VistaArriendos
from interfaz.categorias import VistaCategorias
from interfaz.clientes import VistaClientes
from interfaz.equipos import VistaEquipos
from interfaz.reportes import VistaReportes


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
        equipos = VistaEquipos(pestanas, motor)
        pestanas.add(equipos, text="Equipos")
        pestanas.add(VistaClientes(pestanas, motor), text="Clientes")
        arriendos = VistaArriendos(pestanas, motor)
        pestanas.add(arriendos, text="Arriendos")
        pestanas.add(VistaReportes(pestanas, motor), text="Reportes")

        def actualizar_pestana(_evento):
            activa = pestanas.select()
            if activa == str(equipos):
                equipos.recargar()
            elif activa == str(arriendos):
                arriendos.recargar()

        pestanas.bind("<<NotebookTabChanged>>", actualizar_pestana)
        ventana.mainloop()
    finally:
        motor.dispose()


if __name__ == "__main__":
    main()
