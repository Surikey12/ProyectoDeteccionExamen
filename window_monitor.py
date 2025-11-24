# Clase para monitorear el estado de la ventana (si está enfocada o no)
class WindowMonitor:
    def __init__(self):
        # Estado inicial: se asume que la ventana está enfocada
        self.focused = True
    # Método para actualizar el estado de enfoque de la ventana
    def set_focus(self, state):
        self.focused = state # Actualiza el estado de enfoque
