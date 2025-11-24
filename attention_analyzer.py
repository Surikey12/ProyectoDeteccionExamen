# Analiza el movimiento de la cabeza para determinar:
# atención, giro izquierda/derecha/arriba/abajo y pérdida de la region de interes
# Basado en los desplazamientos generados por optical_flow_tracker.py

import time

# Analiza la atención del usuario a partir de desplazamientos (dx, dy), presencia de ROI y foco de ventana
class AttentionAnalyzer:
    def __init__(self):
        # Marca el momento de la última actualización (ultimo frame procesado)
        self.last_movement_time = time.time()

        self.total_no_atention = 0 # Acumula el tiempo sin atención (en segundos)
        # Desglose del tiempo sin atención por tipo
        self.no_attention_breakdown = {
            "left": 0, # Timepo acumulado girando a la izquierda
            "right": 0, # Tiempo acumulado girando a la derecha
            "up": 0, # Tiempo acumulado girando hacia arriba
            "down": 0, # Tiempo acumulado girando hacia abajo
            "lost_roi": 0, # Tiempo acumulado sin ROI detectado
            "focus_change": 0 # Tiempo acumulado com cambio de ventana
        }

        self.attention_threshold = 3.0  # umbral de segundos para considerar falta de atención

    # Función para reiniciar los contadores para un nuevo examen
    def reset(self):
        self.total_no_atention = 0  # Reinicia el tiempo total sin atención
        # Reinicia el desglose por tipo
        self.no_attention_breakdown = {
            "left": 0,
            "right": 0,
            "up": 0,
            "down": 0,
            "lost_roi": 0,
            "focus_change": 0
        }
        self.last_movement_time = time.time()  # Reinicia la marca de tiempo (evita que se acumule tiempo previo)

    # Actuliza el estado de usando el desplazamiento del frame actual
    def update(self, dx, dy, roi_present=True, window_focused=True):
        now = time.time() # Marca de tiempo actual
        dt = now - self.last_movement_time # Diferencia de tiempo desde la última actualización
        self.last_movement_time = now # Actualiza la marca de tiempo para el próximo frame

        if not roi_present: # Si la ROI no está presente en el frame actual:
            self.total_no_atention += dt # Acumula tiempo sin atención
            self.no_attention_breakdown["lost_roi"] += dt # Acumula a la causa específica
            return # No evalua más condiciones, sale 

        if not window_focused: #Si la ventana de examen no es la que esta al frente o se cambio de ventana:
            self.total_no_atention += dt # Acumula tiempo sin atención
            self.no_attention_breakdown["focus_change"] += dt # Acumula a la causa específica
            return # No evalua más condiciones, sale

        direction = None # Inicializa la dirección del movimiento como None
        # Determinar dirección del movimiento (solo si dx y dy no son None)
        if dx is not None and dy is not None:
            # Se usa un umbral para evitar falsas detecciones por ruido
            if dx > self.attention_threshold: # Dezplazamiento positivo fuerte en X 
                direction = "right" # Giro a la derecha
            elif dx < -self.attention_threshold: # Desplazamiento negativo fuerte en X
                direction = "left" # Giro a la izquierda
            elif dy > self.attention_threshold: # Desplazamiento positivo fuerte en Y
                direction = "down" # Giro hacia abajo
            elif dy < -self.attention_threshold: # Desplazamiento negativo fuerte en Y
                direction = "up" # Giro hacia arriba

        # Si hubo un giro reciente, mantenemos ese estado hasta nuevo movimiento:
        if direction:
            self.last_direction = direction
        else:
            # Si no hay movimiento, mantener la última dirección
            direction = getattr(self, "last_direction", None)

        # Si hay una dirección de giro detectada, acumular tiempo sin atención
        if direction:
            self.total_no_atention += dt # Acumula tiempo sin atención
            self.no_attention_breakdown[direction] += dt # Acumula a la causa específica

    # Detecta si el alumno está mirando al frente usando simetría vertical
    def is_facing_forward(self, points, roi):
        # Verifica si los puntos detectados dentro del ROI son simétricos
        # Validación minima: requiere al menos 6 puntos para una euristica razonable
        if points is None or len(points) < 6:
            return False

        x, y, w, h = roi # Desempaqueta la ROI (posición y tamaño)
        cx_split = x + w / 2  # Calcula la mitad de la roi de forma vertical

        left = 0 # Contador de puntos a la izquierda de la línea central
        right = 0 # Contador de puntos a la derecha de la línea central

        # Contar puntos en izquierda y derecha del ROI
        for (px, py) in points:
            if px < cx_split:
                left += 1
            else:
                right += 1

        # Si solo hay puntos en un lado, no hay simetría suficiente
        if left == 0 or right == 0:
            return False

        # Calcula la simetría como min/max
        ratio = min(left, right) / max(left, right)

        # Umbral recomendado: 70% de simetría
        return ratio > 0.7
