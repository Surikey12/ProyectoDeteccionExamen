# monitoreo_atencion_ui.py
# Interfaz completa: UI moderna + lógica de tracking y análisis.
import cv2  # Biblioteca para procesamiento de imágenes y video
import time  # Para manejo de tiempos y delays
import threading  # Para ejecutar tareas en hilos separados (como captura de video)
import numpy as np  # Para operaciones numéricas y arrays
from PIL import Image, ImageTk  # Para conversión y manejo de imágenes en Tkinter
import tkinter as tk  # Biblioteca principal para la interfaz gráfica
from tkinter import messagebox  # Para mostrar mensajes emergentes
from tkinter import ttk  # Para estilos modernos en Tkinter

# Importar módulos personalizados que manejan funcionalidades específicas
from region_selector import RegionSelector  # Para seleccionar la región de interés (ROI) del rostro
from optical_flow_tracker import OpticalFlowTracker  # Para seguimiento óptico de movimiento
from attention_analyzer import AttentionAnalyzer  # Para analizar la atención basada en movimientos
from reporte import Reporte  # Para generar reportes al final del examen
from window_monitor import WindowMonitor  # Para monitorear si la ventana está enfocada


class Pantalla_UI:
    def __init__(self, root):
        # Asignar la ventana raíz de Tkinter
        self.root = root
        # Configurar título de la ventana
        self.root.title("Sistema Avanzado de Monitoreo de Atención")
        # Establecer tamaño inicial de la ventana
        self.root.geometry("1200x800")  # Tamaño optimizado para una experiencia inmersiva
        # Configurar color de fondo de la ventana
        self.root.configure(bg="#F0F8FF")  # Fondo azul cielo suave para un look moderno y relajante
        # Permitir que la ventana se pueda redimensionar
        self.root.resizable(True, True)  # Permitir redimensionar para flexibilidad

        # Configurar estilos avanzados usando ttk para una apariencia profesional
        style = ttk.Style()
        # Intentar usar un tema moderno; si no está disponible, dejar el predeterminado
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Estilos básicos para varios widgets de la interfaz
        style.configure("TFrame", background="#F0F8FF")
        style.configure("TLabel", background="#F0F8FF", foreground="#1565C0", font=("Helvetica", 12, "bold"))
        style.configure("Title.TLabel", background="#F0F8FF", foreground="#FF6F00", font=("Helvetica", 24, "bold"))
        style.configure("Status.TLabel", background="#E8F5E8", foreground="#2E7D32", font=("Helvetica", 10))
        style.configure("Timer.TLabel", background="#FFF3E0", foreground="#E65100", font=("Helvetica", 16, "bold"),
                        relief="raised", borderwidth=2)
        style.configure("TButton", font=("Helvetica", 11, "bold"), padding=10, relief="raised", borderwidth=2)
        style.map("TButton",
                  background=[("active", "#81C784"), ("!active", "#4CAF50")],
                  foreground=[("active", "#FFFFFF"), ("!active", "#FFFFFF")])
        style.configure("Start.TButton", background="#4CAF50", foreground="#FFFFFF")
        style.configure("Stop.TButton", background="#F44336", foreground="#FFFFFF")
        style.configure("ROI.TButton", background="#2196F3", foreground="#FFFFFF")
        style.configure("TEntry", font=("Helvetica", 11), relief="sunken", borderwidth=2)

        # Variables de estado para controlar la aplicación
        self.cap = None  # Objeto de captura de video
        self.running = False  # Indica si la captura de video está activa
        self.exam_active = False  # Indica si un examen está en curso
        self.exam_end_ts = None  # Timestamp de fin del examen
        self.frame_bgr = None  # Último frame capturado en formato BGR
        self.window_focused = True  # Indica si la ventana está enfocada

        # Instanciar módulos personalizados
        self.roi = None  # Región de interés (rostro)
        self.tracker = OpticalFlowTracker()  # Rastreador óptico
        self.analyzer = AttentionAnalyzer()  # Analizador de atención
        self.winmonitor = WindowMonitor()  # Monitor de foco de ventana

        # Variables adicionales para detectar si se mira al frente
        self.neutral_center = None  # Centro neutral del rostro
        self.front_hysteresis_ms = 250  # Tiempo de histéresis para confirmar mirada al frente
        self._front_inside_since = None  # Timestamp desde que se detectó dentro del área neutral

        # Variables necesarias para CamShift / tracking
        self.roi_hist = None # Histograma de la ROI para CamShift
        self.track_window = None # Ventana de seguimiento para CamShift
        self.term_crit = None # Criterios de terminación para CamShift

        # Crear marco para el título principal de la aplicación
        title_frame = ttk.Frame(root, style="TFrame")
        title_frame.pack(fill=tk.X, pady=20)
        ttk.Label(title_frame, text=" Monitoreo Inteligente de Atención ", style="Title.TLabel").pack()

        # Crear marco para controles superiores (entrada duración, botones, temporizador)
        controls_frame = ttk.Frame(root, style="TFrame")
        controls_frame.pack(fill=tk.X, padx=30, pady=15)

        # Submarco izquierdo: Para duración y entrada de tiempo
        left_controls = ttk.Frame(controls_frame, style="TFrame")
        left_controls.pack(side=tk.LEFT)
        ttk.Label(left_controls, text="⏱️ Duración (min):", style="TLabel").pack(side=tk.LEFT, padx=(0, 10))
        self.duration_var = tk.StringVar(value="1")
        duration_entry = ttk.Entry(left_controls, textvariable=self.duration_var, width=8, style="TEntry")
        duration_entry.pack(side=tk.LEFT, padx=(0, 30))

        # Submarco central: Para botones principales (Seleccionar ROI, Iniciar/Detener Examen)
        center_controls = ttk.Frame(controls_frame, style="TFrame")
        center_controls.pack(side=tk.LEFT, expand=True)
        self.btn_roi = ttk.Button(center_controls, text="👤 Seleccionar Rostro", command=self.seleccionar_roi,
                                  style="ROI.TButton")
        self.btn_roi.pack(side=tk.LEFT, padx=(0, 20))
        self.btn_start = ttk.Button(center_controls, text="▶️ Iniciar Examen", command=self.toggle_exam,
                                    style="Start.TButton")
        self.btn_start.pack(side=tk.LEFT)

        # Submarco derecho: Para el temporizador de cuenta regresiva
        right_controls = ttk.Frame(controls_frame, style="TFrame")
        right_controls.pack(side=tk.RIGHT)
        ttk.Label(right_controls, text="Tiempo Restante:", style="TLabel").pack(side=tk.TOP)
        self.lbl_timer = ttk.Label(right_controls, text="00:00", style="Timer.TLabel")
        self.lbl_timer.pack(side=tk.TOP, pady=(5, 0))

        # Crear contenedor para el área de video
        video_container = ttk.Frame(root, style="TFrame")
        video_container.pack(padx=30, pady=15, expand=True, fill=tk.BOTH)
        # Panel para mostrar el video con borde elegante
        self.video_panel = tk.Label(video_container, bd=5, relief=tk.GROOVE, bg="#FFFFFF",
                                    highlightbackground="#4CAF50", highlightthickness=4)
        self.video_panel.pack(expand=True, fill=tk.BOTH)

        # Crear marco para la barra de estado inferior
        status_frame = ttk.Frame(root, style="TFrame")
        status_frame.pack(fill=tk.X, padx=30, pady=15)
        self.status_label = ttk.Label(status_frame,
                                      text="💡 Estado: Sistema listo. Selecciona el rostro y comienza el examen.",
                                      style="Status.TLabel")
        self.status_label.pack(side=tk.LEFT)
        ttk.Label(status_frame, text="🔒 Asegúrate de mantener la ventana enfocada.", style="Status.TLabel").pack(
            side=tk.RIGHT)

        # Iniciar captura de cámara y bucle de actualización de video
        self.start_camera()
        self.refresh_video()

        # Vincular eventos de foco de ventana
        root.bind("<FocusIn>", self.on_focus_in)
        root.bind("<FocusOut>", self.on_focus_out)
        self.window_focused = True

        # Iniciar hilo para actualizar el temporizador
        self.root.after(200, self.update_timer)

    # Sección de manejo de la cámara 
    def start_camera(self):
        # Abrir la cámara (índice 0)
        self.cap = cv2.VideoCapture(0)
        # Verificar si la cámara se abrió correctamente
        if not self.cap.isOpened():
            messagebox.showerror("Error", "No se pudo abrir la cámara (índice 0).")
            return
        self.running = True # Marcar que la cámara está activa
        t = threading.Thread(target=self.update_frame, daemon=True) # Hilo para realizar captura continua de frames
        t.start() # Iniciar el hilo de captura
        self.status_label.configure(text="Estado: Cámara iniciada.") # Actualizar estado

    # Detener la cámara y liberar recursos
    def stop_camera(self):
        self.running = False # Marcar que la cámara ya no está activa
        if self.cap: # Si la cámara estaba abierta
            self.cap.release() # Liberar el recurso de la cámara
            self.cap = None # Limpiar la referencia a la cámara
        self.status_label.configure(text="Estado: Cámara detenida.") # Actualizar estado

    # Hilo para capturar frames continuamente desde la cámara
    def update_frame(self):
        while self.running and self.cap: # Mientras la cámara esté activa
            ret, frame = self.cap.read() # Leer un frame
            if not ret: # Si no se pudo leer el frame,
                continue # intentar de nuevo
            self.frame_bgr = frame # Guardar el frame capturado
            time.sleep(0.01) # Pequeña pausa para evitar sobrecarga

    # Mostrar el frame actual en el panel de video
    def show_frame(self, frame_bgr):
        # Convertir de BGR a RGB y mostrar
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        h, w = frame_rgb.shape[:2] # Obtener las dimensiones del frame
        max_w = 1100 # Ancho máximo permitido para la ventana de video
        scale = min(1.0, max_w / float(w)) # Calcular escala para ajustar al ancho máximo
        if scale < 1.0: # Si es necesario escalar
            # Redimensionar el frame manteniendo la relación de aspecto
            frame_rgb = cv2.resize(frame_rgb, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA) 

        # CAMSHIFT TRACKING
        # Solo si el examen está activo y la ROI y ventana de seguimiento están definidas
        if self.exam_active and self.roi_hist is not None and self.track_window is not None:
            hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV) # Convertir frame a HSV para CamShift
            backproj = cv2.calcBackProject([hsv], [0], self.roi_hist, [0, 180], 1) # Calcular proyección inversa
             # Aplicar CamShift para actualizar la posición de la ROI
            try:
                track_box, self.track_window = cv2.CamShift(backproj, self.track_window, self.term_crit) # Actualizar ventana de seguimiento
                cv2.ellipse(frame_rgb, track_box, (0, 255, 0), 2)
                x, y, w_t, h_t = self.track_window # Desempaquetar la ventana de seguimiento
                # Actualizar la ROI basada en la ventana de seguimiento
                x, y, w_t, h_t = int(x), int(y), int(w_t), int(h_t) # Asegurar que sean enteros
                self.roi = (x, y, w_t, h_t) # Actualizar la ROI global
                # Actualizar el tracker óptico con la nueva ROI
                if self.tracker.initialized: 
                    self.tracker.update_roi(self.roi) # Actualizar la ROI utilizada por el tracker óptico
            except Exception:
                # Si CamShift falla, resetear estado de tracking
                self.track_window = None # Resetear ventana de seguimiento
                self.roi_hist = None # Resetear histograma de la ROI
                self.roi = None # Resetear la ROI
                self.status_label.configure(text="Estado: Tracking perdido (CamShift falló).") # Actualizar estado

        # OPTICAL FLOW TRACKING
        # Solo si el examen está activo
        if self.exam_active:
            if self.roi is None: # Si no hay ROI definida
                # ROI perdido: marcar como falta de atención por pérdida de rostro
                self.analyzer.update(None, None, roi_present=False, window_focused=self.window_focused)
                txt = self._estado_desde_posicion(self.roi, frame_rgb.shape) # Estado basado en posición (sin ROI)
            elif self.tracker.initialized: # Si el tracker óptico está inicializado
                # Calcular flujo óptico
                gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY) # Convertir frame a escala de grises
                dxdy = self.tracker.track(gray) # Obtener desplazamientos (dx, dy)
                # Obtener puntos actuales del tracker para análisis adicional
                points = getattr(self.tracker, "good_new", None)
                if dxdy: # Si se pudo calcular movimiento
                    dx, dy = dxdy # Se asigna el valor de dxdy a las variables de horizontal y vertical
                    # 1) Actualizar giro natural
                    self.analyzer.update(dx, dy, roi_present=True, window_focused=self.window_focused)
                    # 2) Detectar si está de frente con tu función especial
                    if points is not None and len(points) > 0:
                        try: # En este caso realizar
                            # Se llama a la función para verificar si esta mirando hacia el frente
                            if self.analyzer.is_facing_forward(points, self.roi): 
                                txt = "Mirando de frente" # Si es asi, se actualiza el estado
                                self.analyzer.last_direction = None # Y la dirección anterior se resetea
                            else: # Sino
                                # Se llama a la funcion de posisción para identificar hacia donde se realizo el giro
                                txt = self._estado_desde_posicion(self.roi, frame_rgb.shape, dx, dy)
                        except Exception:
                            # Si is_facing_forward falla por cualquier motivo, fallback
                            txt = self._estado_desde_posicion(self.roi, frame_rgb.shape, dx, dy)
                    else:
                        # Si no hay puntos expuestos por el tracker, calcular estado solo con ROI y desplazamientos
                        txt = self._estado_desde_posicion(self.roi, frame_rgb.shape, dx, dy)
                else:
                    # No se pudo calcular movimiento (puntos perdidos), asumir atención (sin movimiento)
                    self.analyzer.update(0, 0, roi_present=True, window_focused=self.window_focused)
                    txt = self._estado_desde_posicion(self.roi, frame_rgb.shape, 0, 0)
            else:
                # Si el tracker óptico no está inicializado, deducir estado con la info disponible
                txt = self._estado_desde_posicion(self.roi, frame_rgb.shape)
        else:
            # Si el examen NO está activo, igualmente mostrar estado (p. ej., “Sin examen / ROI no definida”)
            txt = self._estado_desde_posicion(self.roi, frame_rgb.shape)

        # Elegir color para el texto del estado: verde si de frente, naranja para otros estados
        color = (0, 255, 0) if txt == "Mirando de frente" else (255, 165, 0)
        cv2.putText(frame_rgb, txt, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)

        # Dibujar ROI si está seleccionado
        if self.roi:
            x, y, w_r, h_r = self.roi
            cv2.rectangle(frame_rgb, (x, y), (x + w_r, y + h_r), (0, 191, 255), 3)

        # Convertir el array RGB a imagen PIL y luego a PhotoImage para Tkinter
        im = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=im)
        # Mantener referencia y actualizar el widget del panel de video en la UI
        self.video_panel.imgtk = imgtk
        self.video_panel.configure(image=imgtk)

    def refresh_video(self):
        # Bucle para refrescar video 
        if self.frame_bgr is not None:
            try:
                # Intenta mostrar el ultimo frame disponible
                self.show_frame(self.frame_bgr)
            except Exception as e:
                # Capturar errores visuales para no romper la UI
                print("Error al mostrar frame:", e)
        self.root.after(20, self.refresh_video) # Reprogramar la actualización para dentro de 20 ms

    
    # Permite al usuario seleccionar manualmente la ROI (región de interés) en el frame actual,
    # genera el histograma de la ROI (HSV con máscara) y configura CamShift para el seguimiento.
    # También calibra el centro neutral y el criterio de parada de CamShift

    def seleccionar_roi(self):
        # Si no hay imagen disponible desde la cámara, avisar y salir
        if self.frame_bgr is None:
            messagebox.showwarning("ROI", "No hay imagen de cámara.")
            return

        selector = RegionSelector() # Crear un selector y fijar la ventana de selección
        clone = self.frame_bgr.copy() # Copiar el frame actual
        cv2.namedWindow("Seleccionar ROI") # Crear ventana para la interacción
        cv2.setMouseCallback("Seleccionar ROI", selector.select_roi) # Registrar callback del mouse

        while True: # Bucle de interacción con el usuario: arrastrar y soltar para definir ROI
            temp = clone.copy() # Imagen temporal para dibujar rectangulo sin afectar "clone"
            # Si el usuario está arrastrando o ya cerró la selección, dibujar el rectángulo verde
            if selector.dragging or selector.roi_ready:
                cv2.rectangle(temp,
                              (selector.ix, selector.iy),
                              (selector.fx, selector.fy),
                              (0, 255, 0), 2)

            cv2.imshow("Seleccionar ROI", temp) # Mostrar la imagen temporal

            key = cv2.waitKey(1) & 0xFF # Leer teclado (1 ms). Se enmascara a 8 bits.
            if key == 27:  # ESC para cancelar la selección (cierra ventana y retorna)
                cv2.destroyWindow("Seleccionar ROI")
                return
            if selector.roi_ready: # Si el usuario soltó el mouse y la ROI está lista, salir del bucle
                break # Romper

        cv2.destroyWindow("Seleccionar ROI") # Cerrar ventana de selección una vez terminada

        self.roi = selector.get_roi() # Obtener la ROI (x, y, w, h) normalizada desde el selector

        # Preparar CamShif
        x, y, w, h = self.roi
        # Limpiar bordes: asegurarse de que la ROI esté dentro de la imagen y tenga tamaño mínimo
        H, W = clone.shape[:2] # Alto y ancho del frame
        x = max(0, min(x, W - 1)) # Limitar x a [0, W-1] 
        y = max(0, min(y, H - 1)) # Limitar y a [0, H-1]
        w = max(10, min(w, W - x)) # Limitar ancho para que no salga del borde; mínimo 10 px
        h = max(10, min(h, H - y)) # Limitar alto para que no salga del borde; mínimo 10 px

        # Guardar ROI principal ya limpia/normalizada
        self.roi = (x, y, w, h)

        # Recortar la región en BGR y convertir a HSV para construir histograma
        roi_bgr = clone[y:y + h, x:x + w]
        hsv_roi = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)
        # Construir máscara para filtrar tonos/valores no deseados (según rangos recomendados)
        mask = cv2.inRange(hsv_roi, np.array((0., 20., 30.)), # límite inferior (H, S, V)
                                    np.array((180., 255., 255.))) # límite superior (H, S, V)

        roi_hist = cv2.calcHist([hsv_roi], [0], mask, [180], [0, 180]) # Histogramar el canal H (0..180) con la máscara para CamShift
        cv2.normalize(roi_hist, roi_hist, 0, 255, cv2.NORM_MINMAX) # Normalizar histograma a rango [0, 255] para estabilidad numérica

        # Guardar histograma y ventana inicial para CamShif
        self.roi_hist = roi_hist
        self.track_window = (x, y, w, h)

        # Calibrar centro neutral (de frente)
        nx = x + w / 2.0
        ny = y + h / 2.0
        self.neutral_center = (nx, ny)

        # Criterio de parada: hasta 10 iteraciones o epsilon=1
        self.term_crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)
        # Notificar por UI y actualizar etiqueta de estado
        messagebox.showinfo("ROI", f"ROI registrada: {self.roi}")
        self.status_label.configure(text=f"Estado: ROI registrada {self.roi}")

    # Determina un estado textual en función de la posición del ROI y (opcionalmente) desplazamientos.
    def _estado_desde_posicion(self, roi, frame_shape, dx=None, dy=None):
        # Retorna una cadena de estado ("Mirando de frente", "Mirando hacia la derecha", etc.)
        if roi is None: # Sino
            return "Rostro Perdido"

        # Calcular centro del ROI y compararlo con el centro del frame
        x, y, w, h = roi
        cx = x + w / 2.0
        cy = y + h / 2.0

        # Centro del frame para referencia posiciona
        H, W = frame_shape[:2]
        center_x = W / 2.0
        center_y = H / 2.0
        # Umbrales posicionales relativos al tamaño del frame (5%)
        umbral_x_pos = W * 0.05
        umbral_y_pos = H * 0.05

        # Umbrales relativos al tamaño del rostro (evitar sensibilidd excesiva)
        umbral_x = max(8.0, w * 0.12)
        umbral_y = max(8.0, h * 0.15)

        # Si tenemos centro neutral, usamos esa referencia (histeresis temporal para "frente")
        if self.neutral_center is not None:
            nx, ny = self.neutral_center
            # Dentro de la ventana neutral si desviaciones en x/y son menores a umbral relativo al rostro
            dentro_neutral = (abs(cx - nx) < umbral_x) and (abs(cy - ny) < umbral_y)
            if dentro_neutral:
                now = time.time()
                if self._front_inside_since is None:
                    # Marcar que entro a la zona neutral
                    self._front_inside_since = now
                elif (now - self._front_inside_since) * 1000.0 >= self.front_hysteresis_ms:
                    # Si se mantiene en zona neutral más tiempo que la histeresis, considerar "frente"
                    self.analyzer.last_direction = None
                    return "Mirando de frente"
            else:
                # Salió de la zona neutral, reiniciar temporizador de histeresis
                self._front_inside_since = None

        # Si la posición del ROI está centrada respecto al frame considerar "mirando al frnete"
        if abs(cx - center_x) < umbral_x_pos and abs(cy - center_y) < umbral_y_pos:
            self.analyzer.last_direction = None
            return "Mirando de frente"

        # Si existe una dirección almacenada por el analizador, usarla para estados descriptivos
        direction = getattr(self.analyzer, "last_direction", None)
        if direction == "right":
            return "Mirando hacia la derecha"
        elif direction == "left":
            return "Mirando hacia la izquierda"
        elif direction == "up":
            return "Mirando hacia arriba"
        elif direction == "down":
            return "Mirando hacia abajo"

        # Si no hay información, por defecto asumir frente
        return "Mirando de frente"

    # Examen: Inicia o detiene el examen de atención 
    def toggle_exam(self):
        if not self.exam_active:
            # Si el examen no esta activo, inicia examen
            try:
                # Obtener valor de minutos desde el control de la UI y convertir a float
                minutes = float(self.duration_var.get())
                assert minutes > 0 # Validación: debe ser mayor a 0
            except Exception:
                # Si la entrada no es valida, advertir al usuario
                messagebox.showwarning("Duración inválida", "Ingresa un número de minutos mayor a 0.")
                return

            # Validar si existe ROI previamente seleccionada
            if self.roi is None:
                messagebox.showwarning("ROI", "Debes seleccionar el ROI del rostro primero.")
                return

            # Reiniciar datos del analyzer para un nuevo examen (limpia acumulados/estado)
            try:
                self.analyzer.reset()
            except Exception:
                # Si el analizador no implementa reset, continuar sin romper
                pass

            # Inicializar tracker óptico con el frame actual
            if self.frame_bgr is None:
                messagebox.showwarning("Tracker", "No hay frame disponible para inicializar el tracker.")
                return

            frame_gray = cv2.cvtColor(self.frame_bgr, cv2.COLOR_BGR2GRAY) # Convertir a escala de grises
            ok = self.tracker.initialize(frame_gray, self.roi) # Intentar inicializar puntos dentro de la ROI
            if not ok:
                # Si no se detectaron puntos dentro de la ROI, no iniciar examen
                messagebox.showwarning("Tracker", "No se pudieron detectar puntos en el ROI seleccionado.")
                return

            # Marcar examen como activo
            self.exam_active = True
            # Cambiar apariencia/texto del botón de inicio (intenta usar estilo ttk; si falla, usa texto simple)
            try:
                self.btn_start.configure(text="⏸️ Detener Examen", style="Stop.TButton")
            except Exception:
                self.btn_start.configure(text="Detener examen")

            # Guardar marcas de tiempo de inicio y fin del examen
            self.exam_start_ts = time.time()
            self.exam_end_ts = self.exam_start_ts + minutes * 60.0 # Minutos a segundos
            self.status_label.configure(text="Estado: Examen iniciado.") # Actualizar etiqueta de estado en la UI
        else:
            # Si el examen ya está activo, detenerlo manualmente
            self.finish_exam(manual=True)

    # Actualiza el temporizador visible del examen de atención
    def update_timer(self):
        if self.exam_active:
            # Tiempo restante en segundos (no negativo)
            remaining = max(0.0, self.exam_end_ts - time.time())
            # Minutos y segundos enteros
            m = int(remaining // 60)
            s = int(remaining % 60)
            self.lbl_timer.configure(text=f"{m:02d}:{s:02d}") # Mostrar en formato mm:ss
            # Si se agotó el tiempo, finalizar automáticamente (manual=False)
            if remaining <= 0.0:
                self.finish_exam(manual=False)
        self.root.after(200, self.update_timer) # Reprogramar llamada para mantener el temporizador actualizado

    # Finaliza el examen de atención y genera/guarda el reporte.
    def finish_exam(self, manual=False):
        # Evitar doble finalización
        if not self.exam_active:
            return

        self.exam_active = False # Marcar examen como inactivo
        # Restaurar apariencia/texto del botón para iniciar un nuevo examen
        try:
            self.btn_start.configure(text="▶️ Iniciar Examen", style="Start.TButton")
        except Exception:
            self.btn_start.configure(text="Iniciar examen")
        # Calcular duración real del examen (protegiendo si faltara exam_start_ts)
        elapsed = time.time() - getattr(self, "exam_start_ts", time.time())
        kind = "detenido" if manual else "finalizado" # Texto de tipo de finalización
        # Construir reporte de atención (si el módulo Reporte está disponible/funciona)
        try:
            reporte = Reporte.construir_reporte(elapsed, self.analyzer)
        except Exception:
            # Fallback si no se puede generar reporte detallado
            reporte = f"Examen {kind}. Duración: {elapsed:.1f} s. (No se pudo generar reporte detallado)"

        # Mostrar reporte en un dialogo informativo
        messagebox.showinfo("Examen " + kind, reporte)
        # Guardar reporte en formato UTF-8
        try:
            with open("reporte_atencion.txt", "w", encoding="utf-8") as f:
                f.write(reporte)
        except Exception as e:
            # Si falla el guardado (permisos, ruta, etc.), registrar en consola
            print("No se pudo guardar reporte:", e)

        self.status_label.configure(text=f"Estado: Examen {kind}. Reporte guardado.") # Actualizar estado visible en la UI
        # Reset seguimiento CamShift/tracker si hace falta
        # (no liberamos la cámara porque la UI sigue abierta)
        self.track_window = None
        self.roi_hist = None
        self.roi = None

    #  Maneja el evento de ganancia de foco de la ventana (focus in).
    def on_focus_in(self, event):
        self.window_focused = True
        try:
            # Si hay un monitor de ventana (propio), actualiza su estado
            self.winmonitor.set_focus(True)
        except Exception:
            # Ignorar si no existe o falla
            pass
        self.status_label.configure(text="Estado: Ventana enfocada.")

    # Maneja el evento de pérdida de foco de la ventana (focus out).
    def on_focus_out(self, event):
        self.window_focused = False
        try:
            self.winmonitor.set_focus(False)
        except Exception:
            pass
        self.status_label.configure(text="Estado: Ventana fuera de foco.")

    # Cierra ordenadamente la aplicación/UI
    def cierre(self):
        self.stop_camera() # Detener captura de cámara antes de destruir la UI
        try:
            self.root.destroy()
        except Exception:
            # Ignorar errores al destruir (p. ej., si ya está destruida)
            pass