import tkinter as tk # Importar la biblioteca tkinter para la interfaz gráfica
from Pantalla_UI import Pantalla_UI # Importar la clase Pantalla_UI desde el módulo Pantalla_UI

# Punto de entrada principal de la aplicación
if __name__ == "__main__":
    root = tk.Tk() # Crear la ventana principal de la aplicación
    app = Pantalla_UI(root) # Crear una instancia de Pantalla_UI, pasando la ventana principal
    root.protocol("WM_DELETE_WINDOW", app.cierre) # Configurar el protocolo de cierre de la ventana para llamar al método cierre de Pantalla_UI
    root.mainloop() # Iniciar el bucle principal de la interfaz gráfica
