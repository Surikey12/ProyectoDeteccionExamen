import cv2
import time
import threading
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox

# Importar modulos
from region_selector import RegionSelector
from optical_flow_tracker import OpticalFlowTracker
from attention_analyzer import AttentionAnalyzer
from reporte import Reporte
from window_monitor import WindowMonitor

class Pantalla_UI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ventana de Examen de Cámara")

        # Estado
        self.cap = None
        self.running = False
        self.exam_active = False
        self.exam_end_ts = None
        self.frame_bgr = None
        self.window_focused = True

        # Instanciar módulos
        self.roi = None
        self.tracker = OpticalFlowTracker()
        self.analyzer = AttentionAnalyzer()
        self.winmonitor = WindowMonitor()

        # Estado adicional para mirada al frente
        self.neutral_center = None           # (nx, ny) capturado al seleccionar ROI
        self.front_hysteresis_ms = 250       # tiempo mínimo dentro de la zona neutral
        self._front_inside_since = None      # timestamp cuando entró a la zona


        # UI: Controles superiores
        top = tk.Frame(root)
        top.pack(fill=tk.X, padx=10, pady=6)

        tk.Label(top, text="Duración (min):").pack(side=tk.LEFT)
        self.duration_var = tk.StringVar(value="1")  # prueba corta por defecto
        tk.Entry(top, textvariable=self.duration_var, width=5).pack(side=tk.LEFT, padx=6)

        self.btn_start = tk.Button(top, text="Iniciar examen", command=self.toggle_exam, bg="#2e7d32", fg="white")
        self.btn_start.pack(side=tk.LEFT, padx=8)

        # Boton para seleccionar ROI
        self.btn_roi = tk.Button(top, text="Seleccionar Rostro a Detectar", command=self.seleccionar_roi)
        self.btn_roi.pack(side=tk.LEFT, padx=10)

        self.lbl_timer = tk.Label(top, text="00:00", font=("Arial", 12, "bold"))
        self.lbl_timer.pack(side=tk.RIGHT)

        # Área de video
        self.video_panel = tk.Label(root, bd=2, relief=tk.SUNKEN)
        self.video_panel.pack(padx=10, pady=10)

        # Iniciar captura y loop de UI
        self.start_camera()
        self.refresh_video()

        # Manejar foco de ventana (lo usaremos en el Paso 4)
        root.bind("<FocusIn>", self.on_focus_in)
        root.bind("<FocusOut>", self.on_focus_out)
        self.window_focused = True  # estado actual de foco

        # Hilo de actualización del timer
        self.root.after(200, self.update_timer)

        # ---------- Cámara ----------
    def start_camera(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "No se pudo abrir la cámara (índice 0).")
            return
        self.running = True
        t = threading.Thread(target=self.update_frame, daemon=True)
        t.start()

    def stop_camera(self):
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None

    def update_frame(self):
        while self.running and self.cap:
            ret, frame = self.cap.read()
            if not ret:
                continue
            self.frame_bgr = frame
            # Mostrar en Tkinter
            # self.show_frame(frame)
            # Reducir consumo de CPU
            time.sleep(0.01)

    def show_frame(self, frame_bgr):
        # Convertir BGR->RGB y mostrar
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        h, w = frame_rgb.shape[:2]
        max_w = 900
        scale = min(1.0, max_w / float(w))
        if scale < 1.0:
            frame_rgb = cv2.resize(frame_rgb, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

        # CAMSHIFT TRACKING
        if self.exam_active and self.roi_hist is not None and self.track_window is not None:
            hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

            # Backprojection idéntico al PDF
            backproj = cv2.calcBackProject([hsv], [0], self.roi_hist, [0, 180], 1)

            # Actualizar track_window con CamShift
            try:
                track_box, self.track_window = cv2.CamShift(backproj,
                                                            self.track_window,
                                                            self.term_crit)

                # Dibujar la elipse del PDF
                cv2.ellipse(frame_rgb, track_box, (0, 255, 0), 2)

                # Actualizar ROI actual basada en CamShift
                x, y, w, h = self.track_window
                x, y, w, h = int(x), int(y), int(w), int(h)
                self.roi = (x, y, w, h)

                # Mandar ROI nueva al OpticalFlowTracker
                if self.tracker.initialized:
                    self.tracker.update_roi(self.roi)

            except Exception:
                # Si CamShift falla, se pierde el tracking
                self.track_window = None
                self.roi_hist = None
                self.roi = None  # <-- AGREGADO: Resetear ROI para marcar "Rostro Perdido"

        # OPTICAL FLOW TRACKING
        if self.exam_active:
            if self.roi is None:
                # ROI perdido: marcar como falta de atención por pérdida de rostro
                self.analyzer.update(None, None, roi_present=False, window_focused=self.window_focused)
                txt = self._estado_desde_posicion(self.roi, frame_rgb.shape)  # Sin dx/dy, ya que ROI es None
            elif self.tracker.initialized:
                gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
                dxdy = self.tracker.track(gray)
                if dxdy:
                    dx, dy = dxdy
                    # Actualizar atención con movimiento detectado
                    self.analyzer.update(dx, dy, roi_present=True, window_focused=self.window_focused)
                    txt = self._estado_desde_posicion(self.roi, frame_rgb.shape, dx, dy)  # Pasar dx, dy
                else:
                    # No se pudo calcular movimiento (puntos perdidos), asumir atención (sin movimiento)
                    self.analyzer.update(0, 0, roi_present=True, window_focused=self.window_focused)
                    txt = self._estado_desde_posicion(self.roi, frame_rgb.shape, 0, 0)  # Pasar 0, 0 como sin movimiento
            else:
                # Examen activo pero tracker no inicializado (e.g., al inicio)
                txt = self._estado_desde_posicion(self.roi, frame_rgb.shape)
        else:
            # Examen no activo
            txt = self._estado_desde_posicion(self.roi, frame_rgb.shape)

        # Siempre mostrar el estado del rostro (incluso si no hay movimiento)
        cv2.putText(frame_rgb, txt, (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                    (255, 0, 0) if txt != "Mirando de frente" else (0, 255, 0), 2)

        # Dibujar ROI si está seleccionado
        if self.roi:
            x, y, w, h = self.roi
            cv2.rectangle(frame_rgb, (x, y), (x + w, y + h), (0, 255, 0), 2)

        im = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=im)
        # Guardar referencia para evitar garbage collection
        self.video_panel.imgtk = imgtk
        self.video_panel.configure(image=imgtk)

    def refresh_video(self):
        if self.frame_bgr is not None:
            self.show_frame(self.frame_bgr)

        # refrescar cada 20 ms (50 FPS)
        self.root.after(20, self.refresh_video)

    # Seleccion de la region de interes (ROI)
    def seleccionar_roi(self):
        if self.frame_bgr is None:
            messagebox.showwarning("ROI", "No hay imagen de cámara.")
            return

        selector = RegionSelector()

        clone = self.frame_bgr.copy()
        cv2.namedWindow("Seleccionar ROI")
        cv2.setMouseCallback("Seleccionar ROI", selector.select_roi)

        while True:
            temp = clone.copy()
            if selector.dragging or selector.roi_ready:
                cv2.rectangle(temp,
                              (selector.ix, selector.iy),
                              (selector.fx, selector.fy),
                              (0, 255, 0), 2)

            cv2.imshow("Seleccionar ROI", temp)

            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                cv2.destroyWindow("Seleccionar ROI")
                return
            if selector.roi_ready:
                break

        cv2.destroyWindow("Seleccionar ROI")

        self.roi = selector.get_roi()

        # Preparar CamShift como en el PDF
        x, y, w, h = self.roi
        # Limpiar bordes
        H, W = clone.shape[:2]
        x = max(0, min(x, W - 1))
        y = max(0, min(y, H - 1))
        w = max(10, min(w, W - x))
        h = max(10, min(h, H - y))

        # Guardar ROI principal
        self.roi = (x, y, w, h)

        roi_bgr = clone[y:y+h, x:x+w]
        hsv_roi = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv_roi, np.array((0., 20., 30.)),
                                    np.array((180., 255., 255.)))

        roi_hist = cv2.calcHist([hsv_roi], [0], mask, [180], [0, 180])
        # Normalizado (crítico para CamShift)
        cv2.normalize(roi_hist, roi_hist, 0, 255, cv2.NORM_MINMAX)

        self.roi_hist = roi_hist
        self.track_window = (x, y, w, h)

        
        # Guardar el centro neutral (calibración)
        nx = x + w / 2.0
        ny = y + h / 2.0
        self.neutral_center = (nx, ny)

        # Criterio de parada EXACTO al del PDF
        self.term_crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)

        messagebox.showinfo("ROI", f"ROI registrada: {self.roi}")

    def _estado_desde_posicion(self, roi, frame_shape, dx=None, dy=None):
        if roi is None:
            return "Rostro Perdido"

        # Si hay movimiento pequeño (dx, dy cercanos a 0), asumir mirando al frente
        if dx is not None and dy is not None:
            if abs(dx) < 2.0 and abs(dy) < 2.0:  # Umbral bajo para movimiento mínimo
                self.analyzer.last_direction = None
                return "Mirando de frente"

        # Si no hay dx/dy o movimiento grande, usar posición del ROI como respaldo
        x, y, w, h = roi
        cx = x + w / 2
        cy = y + h / 2
        H, W = frame_shape[:2]
        center_x = W / 2
        center_y = H / 2
        umbral_x = W * 0.1  # Aumentar umbral para más tolerancia (10% en lugar de 5%)
        umbral_y = H * 0.1

        if abs(cx - center_x) < umbral_x and abs(cy - center_y) < umbral_y:
            self.analyzer.last_direction = None
            return "Mirando de frente"""

        
        # Umbrales relativos al tamaño del rostro (ajusta si quieres)
        umbral_x = max(8.0, w * 0.12)   # mínimo en pixeles para evitar exceso de sensibilidad
        umbral_y = max(8.0, h * 0.15)

        # Si tenemos centro neutral, usamos esa referencia
        if self.neutral_center is not None:
            nx, ny = self.neutral_center
            dentro_neutral = (abs(cx - nx) < umbral_x) and (abs(cy - ny) < umbral_y)
            if dentro_neutral:
                # Histeresis temporal para declarar "frente" estable
                now = time.time()
                if self._front_inside_since is None:
                    self._front_inside_since = now
                elif (now - self._front_inside_since) * 1000.0 >= self.front_hysteresis_ms:
                    # Estable: resetear dirección y reportar "frente"
                    self.analyzer.last_direction = None
                    return "Mirando de frente"
            else:
                # Salió de la zona neutral
                self._front_inside_since = None


        # Usar dirección almacenada si hay movimiento
        direction = getattr(self.analyzer, "last_direction", None)
        if direction == "right":
            return "Mirando hacia la derecha"
        elif direction == "left":
            return "Mirando hacia la izquierda"
        elif direction == "up":
            return "Mirando hacia arriba"
        elif direction == "down":
            return "Mirando hacia abajo"

        return "Mirando de frente"  # Por defecto, si no hay dirección clara

    # ---------- Examen ----------
    def toggle_exam(self):
        if not self.exam_active:
            # Iniciar
            try:
                minutes = float(self.duration_var.get())
                assert minutes > 0
            except Exception:
                messagebox.showwarning("Duración inválida", "Ingresa un número de minutos mayor a 0.")
                return

                # Validar ROI
            if self.roi is None:
                messagebox.showwarning("ROI", "Debes seleccionar el ROI del rostro primero.")
                return

            # Reiniciar datos del analyzer para el nuevo examen
            self.analyzer.reset()

            # Inicializar tracker
            frame_gray = cv2.cvtColor(self.frame_bgr, cv2.COLOR_BGR2GRAY)
            ok = self.tracker.initialize(frame_gray, self.roi)
            if not ok:
                messagebox.showwarning("Tracker", "No se pudieron detectar puntos en el ROI seleccionado.")
                return

            # Iniciar examen
            self.exam_active = True
            self.btn_start.configure(text="Detener examen", bg="#c62828")
            self.exam_start_ts = time.time()
            self.exam_end_ts = self.exam_start_ts + minutes * 60.0
        else:
            # Detener manualmente
            self.finish_exam(manual=True)

    def update_timer(self):
        if self.exam_active:
            remaining = max(0.0, self.exam_end_ts - time.time())
            m = int(remaining // 60)
            s = int(remaining % 60)
            self.lbl_timer.configure(text=f"{m:02d}:{s:02d}")
            if remaining <= 0.0:
                self.finish_exam(manual=False)

        self.root.after(200, self.update_timer)

    def finish_exam(self, manual=False):
        self.exam_active = False
        self.btn_start.configure(text="Iniciar examen", bg="#2e7d32")
        elapsed = time.time() - self.exam_start_ts
        # m = int(elapsed // 60)
        # s = int(elapsed % 60)
        kind = "detenido" if manual else "finalizado"
        reporte = Reporte.construir_reporte(elapsed, self.analyzer)
        messagebox.showinfo("Examen " + kind, reporte)

        with open("reporte_atencion.txt", "w", encoding="utf-8") as f:
            f.write(reporte)

    # ---------- Foco de la ventana (para el Paso 4) ----------
    def on_focus_in(self, event):
        self.window_focused = True
        self.winmonitor.set_focus(True)

    def on_focus_out(self, event):
        self.window_focused = False
        self.winmonitor.set_focus(False)

    # ---------- Cierre ----------
    def cierre(self):
        self.stop_camera()
        self.root.destroy()