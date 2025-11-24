# Esta parte es de suma importancia para el seguimiento de flujo óptico
# Usa cv2.goodFeaturesToTrack() y cv2.calcOpticalFlowPyrLK()
# da seguimiento a puntos de interés en un ROI seleccionado manualmente
# calcula los vectores promedio de movimiento y clasifica la dirección del movimiento

import cv2
import numpy as np

# Clase que realiza el seguimiento de flujo óptico dentro de un ROI
class OpticalFlowTracker:
    def __init__(self):
        # Parametros recomendados para la detección de caracteristicas.
        self.feature_params = dict(
            maxCorners=300, #500 # Número máximo de puntos a detectar
            qualityLevel=0.01, # Umbral de calidad para aceptar puntos
            minDistance=7, #10 # Distancia mínima entre puntos detectados
            blockSize=7) # Tamaño del bloque para la detección de esquinas
        
        # Parámetros recomendados para el cálculo de flujo óptico LK
        self.lk_params = dict(
            winSize=(21, 21), #15,15 # Tamaño de la ventana de búsqueda
            maxLevel=3, #2 # Número de niveles en la pirámide
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01)) #10, 0.03 # Criterios de terminación
        
        self.initialized = False # Indica si el tracker ha sido inicializado
        self.prev_gray = None # Frame gris previo
        self.prev_points = None # Puntos detectados en el frame previo
        # ROI actual en forma (x, y, w, h)
        self.roi_box = None 

    # Inicializa el tracker con el primer frame y la ROI seleccionada
    def initialize(self, frame_gray, roi):
        x, y, w, h = roi # Desempaqueta coordenadas y dimenciones de la ROI
        roi_gray = frame_gray[y:y+h, x:x+w] # Extrae la región de interés del frame gris

        # Detectar puntos dentro del ROI
        puntos = cv2.goodFeaturesToTrack(roi_gray, mask=None, **self.feature_params)
        if puntos is None: # Si no se detectan puntos, no se puede inicializar
            return False
        
        # Ajustar coordenadas al frame completo}
        # Se suman x e y para posicionarlos en el sistema de coordenadas del frame completo
        puntos[:, 0, 0] += x
        puntos[:, 0, 1] += y

        self.prev_points = puntos # Guardar el estado previo para el calculo del flujo optico en el siguiente frame
        self.prev_gray = frame_gray.copy() # Copiar el frame actual como referencia previo
        self.roi_box = roi # Registrar la ROI actual
        self.initialized = True # Marcar como inicializado
        return True

   # Actuliza la ROI utilizada por el tracker. 
   # Cada vez que CamShift cambia la ROI, Pantalla_UI debe llamar a este método. 
    def update_roi(self, roi):
        self.roi_box = roi
    
    # Calcula el flujo óptico entre el frame previo y el frame actual para los puntos previos, 
    # filtra los puntos válidos y calcula el desplazamiento promedio (dx, dy).
    def track(self, frame_gray):
        # Validación de estado: no se puede trackear si no hay inicialización o puntos previos
        if not self.initialized or self.prev_points is None:
            return None, None
        
        # Calcular flujo óptico:
        # next_points: posiciones estimadas de los puntos en el frame actual
        # status: indica por punto si el seguimiento fue exitoso (1) o falló (0)
        next_points, status, _ = cv2.calcOpticalFlowPyrLK( 
            self.prev_gray, frame_gray, self.prev_points, None, **self.lk_params)
        
        # Si no se pudieron calcular los puntos siguientes, devolver None
        if next_points is None:
            return None, None
        
        # Filtrar puntos válidos
        good_new = next_points[status == 1]
        good_old = self.prev_points[status == 1]

        # Si se perdieron muchos puntos → intentar reinicializar en el ROI ACTUALIZADO
        # Umbral: menos de 10 puntos válidos pueden ser suficiente para un buen trabajo
        if len(good_new) < 10 and self.roi_box is not None:
            # Recortar nuevamente puntos en la ROI actual
            x, y, w, h = self.roi_box
            roi_gray = frame_gray[y:y + h, x:x + w]
            puntos = cv2.goodFeaturesToTrack(roi_gray, mask=None, **self.feature_params) # Detectar puntos dentro del ROI
            if puntos is not None:
                # Ajustar coordenadas al frame completo
                puntos[:, 0, 0] += x
                puntos[:, 0, 1] += y
                # Actualizar estado previo con los nuevos puntos y el frame actua
                self.prev_points = puntos
                self.prev_gray = frame_gray.copy()
                return None, None  # No devolver movimiento hasta el próximo frame
            else:
                # Si no se pueden detectar puntos, devolver None para marcar falta de atención
                return None, None

        # Calculo del movimiento promedio (vector medio entre pares de puntos good_old -> good_new)
        movimiento = good_new - good_old
        # Promedio de desplazamientos en X y Y. Se castea a float para garantizar tipo nativo de Python.
        dx = float(np.mean(movimiento[:, 0]))
        dy = float(np.mean(movimiento[:, 1]))

        # Actualizar estado previo para el próximo frame
        self.prev_points = good_new.reshape(-1, 1, 2)
        self.prev_gray = frame_gray.copy()

        return dx, dy # Devolver el desplazamiento promedio del frame actual
