# Esta parte es de suma importancia para el seguimiento de flujo óptico
# Usa cv2.goodFeaturesToTrack() y cv2.calcOpticalFlowPyrLK()
# da seguimiento a puntos de interés en un ROI seleccionado manualmente
# calcula los vectores prmedio de movimiento y clasifica la dirección del movimiento

import cv2
import numpy as np

class OpticalFlowTracker:
    def __init__(self):
        # Parametros recomendados
        self.feature_params = dict(
            maxCorners=300, #500
            qualityLevel=0.01, 
            minDistance=7, #10
            blockSize=7)
        
        self.lk_params = dict(
            winSize=(21, 21), #15,15
            maxLevel=3, #2
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01)) #10, 0.03
        
        self.initialized = False
        self.prev_gray = None
        self.prev_points = None
        # ROI actual (esta debe venir de CAMSHIFT)
        self.roi_box = None  

    def initialize(self, frame_gray, roi):
        x, y, w, h = roi
        roi_gray = frame_gray[y:y+h, x:x+w]

        # Detectar puntos dentro del ROI
        puntos = cv2.goodFeaturesToTrack(roi_gray, mask=None, **self.feature_params)
        if puntos is None:
            return False
        
        # Ajustar coordenadas al frame completo
        puntos[:, 0, 0] += x
        puntos[:, 0, 1] += y

        self.prev_points = puntos
        self.prev_gray = frame_gray.copy()
        self.roi_box = roi
        self.initialized = True
        return True
    
    def update_roi(self, roi):
        """
        Cada vez que CamShift cambia la ROI, Pantalla_UI debe llamar a este método.
        """
        self.roi_box = roi
    
    def track(self, frame_gray):
        if not self.initialized or self.prev_points is None:
            return None, None
        
        # Calcular flujo óptico
        next_points, status, _ = cv2.calcOpticalFlowPyrLK(
            self.prev_gray, frame_gray, self.prev_points, None, **self.lk_params)
        
        if next_points is None:
            return None, None
        
        # Filtrar puntos válidos
        good_new = next_points[status == 1]
        good_old = self.prev_points[status == 1]

        # Si se perdieron muchos puntos → volver a detectar en la ROI ACTUALIZADA
        if len(good_new) < 10 and self.roi_box is not None:
            x, y, w, h = self.roi_box
            roi_gray = frame_gray[y:y+h, x:x+w]

            puntos = cv2.goodFeaturesToTrack(
                roi_gray, mask=None, **self.feature_params)

            if puntos is not None:
                puntos[:, 0, 0] += x
                puntos[:, 0, 1] += y

                self.prev_points = puntos
                self.prev_gray = frame_gray.copy()
                return None, None

        # Calculo del movimiento promedio
        movimiento = good_new - good_old
        dx = float(np.mean(movimiento[:, 0]))
        dy = float(np.mean(movimiento[:, 1]))


        # Actualizar estado para la siguiente iteración
        self.prev_points = good_new.reshape(-1, 1, 2)
        self.prev_gray = frame_gray.copy()

        return dx, dy
