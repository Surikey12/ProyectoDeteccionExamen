# Permite que el usuario seleccione el ROI con el mouse.
# Esto es lo que describe Beyeler cuando habla de “manual ROI selection”

import cv2

# Clase para manejar la seleccion manual de la region de interes (ROI) usando el mouse
class RegionSelector:
    def __init__(self):
        # Estado de arrastre: se activa en EVENT_LBUTTONDOWN y se desactiva en EVENT_LBUTTONUP
        self.dragging = False
        # Coordenadas iniciales y finales del rectángulo dibujado por el usuario
        self.ix = self.iy = 0
        self.fx = self.fy = 0
        self.roi_ready = False # Bandera que indica si la ROI ha sido seleccionada
    
    # Reinicia el estado de selección de ROI
    def reset(self):
        self.roi_ready = False # Marca que la ROI no está lista para ser usada

    # Manejador de eventos del mouse para seleccionar la ROI
    def select_roi(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN: # Si el usuario presiona el botón izquierdo del mouse
            self.dragging = True # Inicia el arrastre
            self.ix, self.iy = x, y # Guarda las coordenadas iniciales

        elif event == cv2.EVENT_MOUSEMOVE and self.dragging:
            # Mientras se arrastra el mouse con el botón presionado, actualiza las coordenadas finales
            self.fx, self.fy = x, y

        elif event == cv2.EVENT_LBUTTONUP:
            # Cuando se suelta el botón izquierdo del mouse, finaliza el arrastre y guarda las coordenadas finales
            self.dragging = False
            self.fx, self.fy = x, y
            self.roi_ready = True # Marca que la ROI está lista para ser usada por la funcion get_roi

    # Devuelve la ROI seleccionada en formato (x, y, w, h)
    def get_roi(self):
        # Coord. superiores izquierda (x1, y1) como los mínimos de inicio/fin
        x1, y1 = min(self.ix, self.fx), min(self.iy, self.fy)
        # Coord. inferiores derecha (x2, y2) como los máximos de inicio/fin
        x2, y2 = max(self.ix, self.fx), max(self.iy, self.fy)
        # Convertir a (x, y, w, h): origen en (x1, y1), ancho = x2 - x1, alto = y2 - y1
        return (x1, y1, x2 - x1, y2 - y1) # Devuelve la ROI en formato (x, y, w, h)
