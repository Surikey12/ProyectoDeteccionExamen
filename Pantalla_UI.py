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

            # Si el examen está activo, procesar el frame
        if self.exam_active and self.tracker.initialized:
            gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
            dxdy = self.tracker.track(gray)
            if dxdy:
                dx, dy = dxdy
                self.analyzer.update(dx, dy, roi_present=True, window_focused=self.window_focused)
                txt = self._estado_desde_mov(dx, dy)
                cv2.putText(frame_rgb, txt, (20, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                            (255, 0, 0) if txt != "Mirando" else (0, 255, 0), 2)

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
        messagebox.showinfo("ROI", f"ROI registrada: {self.roi}")

    def _estado_desde_mov(self, dx, dy):
        threshold = self.analyzer.attention_threshold
        if dx > threshold:
            return "Giro a la derecha"
        elif dx < -threshold:
            return "Giro a la izquierda"
        elif dy > threshold:
            return "Giro hacia abajo"
        elif dy < -threshold:
            return "Giro hacia arriba"
        else:
            return "Mirando"

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