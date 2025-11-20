# Analiza el movimiento de la cabeza para determinar:
# atención, giro izquierda/derecha/arriba/abajo y pérdida de la region de interes
# Basado en los desplazamientos generados por optical_flow_tracker.py

import time

class AttentionAnalyzer:
    def __init__(self):
        self.last_movement_time = time.time()

        self.total_no_atention = 0
        self.no_attention_breakdown = {
            "left": 0,
            "right": 0,
            "up": 0,
            "down": 0,
            "lost_roi": 0,
            "focus_change": 0
        }

        self.attention_threshold = 3.0  # umbral de segundos para considerar falta de atención

    def reset(self):
        """Reinicia los contadores de atención para un nuevo examen."""
        self.total_no_atention = 0
        self.no_attention_breakdown = {
            "left": 0,
            "right": 0,
            "up": 0,
            "down": 0,
            "lost_roi": 0,
            "focus_change": 0
        }
        self.last_movement_time = time.time()  # Reinicia el tiempo también

    def update(self, dx, dy, roi_present = True, window_focused = True):
        now = time.time()
        dt = now - self.last_movement_time
        self.last_movement_time = now

        if not roi_present:
            self.total_no_atention += dt
            self.no_attention_breakdown["lost_roi"] += dt
            return 
        
        if not window_focused:
            self.total_no_atention += dt
            self.no_attention_breakdown["focus_change"] += dt
            return
        
        # Determinar dirección del movimiento
        if dx > self.attention_threshold:
            self.total_no_atention += dt
            self.no_attention_breakdown["right"] += dt
        
        elif dx < -self.attention_threshold:
            self.total_no_atention += dt
            self.no_attention_breakdown["left"] += dt

        elif dy > self.attention_threshold:
            self.total_no_atention += dt
            self.no_attention_breakdown["down"] += dt
        
        elif dy < -self.attention_threshold:
            self.total_no_atention += dt
            self.no_attention_breakdown["up"] += dt

        
            

        
