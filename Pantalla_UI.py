import cv2 
import time 
import threading 
import numpy as np 
from PIL import Image, ImageTk 
import tkinter as tk 
from tkinter import messagebox 

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

        # UI: Controles superiores 
        top = tk.Frame(root) 
        top.pack(fill=tk.X, padx=10, pady=6)

        tk.Label(top, text="Duración (min):").pack(side=tk.LEFT) 
        self.duration_var = tk.StringVar(value="1") # prueba corta por defecto 
        tk.Entry(top, textvariable=self.duration_var, width=5).pack(side=tk.LEFT, padx=6) 
        
        self.btn_start = tk.Button(top, text="Iniciar examen", command=self.toggle_exam, bg="#2e7d32", fg="white") 
        self.btn_start.pack(side=tk.LEFT, padx=8) 

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
        self.window_focused = True # estado actual de foco 
        
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
            #self.show_frame(frame) 
            # Reducir consumo de CPU 
            time.sleep(0.01) 
            
    def show_frame(self, frame_bgr): 
        # Convertir BGR->RGB y mostrar 
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB) 
        h, w = frame_rgb.shape[:2] 
        max_w = 900 
        scale = min(1.0, max_w / float(w)) 
        if scale < 1.0: 
            frame_rgb = cv2.resize(frame_rgb, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA) 
        
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
        m = int(elapsed // 60) 
        s = int(elapsed % 60) 
        kind = "detenido" if manual else "finalizado" 
        messagebox.showinfo("Examen", f"Examen {kind}. Duración: {m:02d}:{s:02d}.\n" f"(En el siguiente paso se añadirán las estadísticas.)") 
        
    # ---------- Foco de la ventana (para el Paso 4) ---------- 
    def on_focus_in(self, event): 
        self.window_focused = True 
        
    def on_focus_out(self, event): 
        self.window_focused = False 
        
    # ---------- Cierre ---------- 
    def cierre(self): 
        self.stop_camera() 
        self.root.destroy() 
            