# Sistema Avanzado de Monitoreo de Atención

Una aplicación de visión por computadora para monitorear la atención durante exámenes, utilizando seguimiento óptico y análisis de movimientos faciales.

Este proyecto implementa un sistema inteligente para detectar y analizar la atención de un usuario durante un examen virtual. Utiliza la cámara del dispositivo para rastrear movimientos de la cabeza, detectar giros (izquierda, derecha, arriba, abajo), pérdida de rostro y cambios de foco en la ventana. Genera reportes detallados al finalizar el examen, ayudando a identificar comportamientos sospechosos como distracciones o intentos de hacer trampa.

---

## 📌 Características Principales

- **Selección manual de ROI (Región de Interés)**  
- **Seguimiento Óptico y CamShift**  
- **Análisis de Atención en tiempo real**  
- **Interfaz gráfica moderna con Tkinter**  
- **Reportes detallados al finalizar**  
- **Monitoreo de foco de ventana**  
- **Detección de mirada al frente por simetría facial**

---

## 🛠 Requisitos

- Python 3.7+
- Cámara web
- Bibliotecas necesarias:
  - `opencv-python`
  - `numpy`
  - `Pillow`
  - `tkinter` (incluido en Python estándar)
- Compatible con Windows, macOS y Linux

---

## 📥 Instalación

Clona este repositorio:

```bash
git clone https://github.com/tu-usuario/tu-repositorio.git
cd tu-repositorio
```

## 📥 Instalación de Dependencias

Instala las dependencias:

```bash
pip install opencv-python numpy Pillow
```

# 🧠 Monitoreo de Atención con Visión por Computadora

Aplicación en Python que utiliza visión por computadora para monitorear si un alumno mantiene la mirada en la pantalla durante un examen en línea. Registra distracciones, cambios de ventana y genera un reporte final.
---

## ▶️ Cómo Ejecutar

Ejecuta el archivo principal:

```bash
python main.py
```

## ▶️ Pasos básicos

- Selecciona el rostro con **👤 Seleccionar Rostro**
- Ingresa la **duración del examen (en minutos)**
- Inicia con **▶️ Iniciar Examen**
- Al finalizar, se generará el archivo:

```
reporte_atencion.txt
```

**Nota:** Si la cámara falla, cambia el índice en tu código:

```python
self.cap = cv2.VideoCapture(0)
```

---

## 📦 Módulos del Proyecto

### 1. `Pantalla_UI`
Controla toda la interfaz gráfica (Tkinter) y conecta todos los módulos.

### 2. `RegionSelector`
Permite seleccionar el ROI del rostro mediante una ventana de OpenCV.

### 3. `OpticalFlowTracker`
Realiza seguimiento del rostro mediante el método Lucas–Kanade:

```python
cv2.calcOpticalFlowPyrLK
```

### 4. `AttentionAnalyzer`
Analiza:
- Movimientos
- Giros de cabeza
- Pérdidas de rostro
- Cambios de ventana

### 5. `Reporte`
Genera reportes finales con porcentajes y tiempos acumulados.

### 6. `WindowMonitor`
Detecta si la ventana pierde el foco durante el examen.

---

## 🖥 Funcionamiento de la Interfaz

Elementos principales:

- Título superior  
- Controles: duración, selección de ROI, iniciar/detener  
- Vista en vivo de la cámara  
- Indicador de estado  
- Temporizador  
- Barra inferior de mensajes  

---

## 🔍 Flujo de Uso

1. Abrir la aplicación  
2. Seleccionar rostro  
3. Iniciar examen  
4. La app analiza movimientos en tiempo real  
5. Finaliza y genera reporte automáticamente  

---

## 📂 Ejemplos de Uso

- Detectar distracciones moviendo la cabeza  
- Cambiar de ventana para simular pérdida de foco  
- Revisar el archivo generado **reporte_atencion.txt**

---


## 👤 Créditos

Desarrollado por **[Surikey y Roberto Carlos]**  
Basado en **OpenCV, NumPy, Pillow y Tkinter**.

