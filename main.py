import tkinter as tk
from Pantalla_UI import Pantalla_UI

if __name__ == "__main__":
    root = tk.Tk()
    app = Pantalla_UI(root)
    root.protocol("WM_DELETE_WINDOW", app.cierre)
    root.mainloop()
