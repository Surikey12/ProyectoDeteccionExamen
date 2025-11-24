# Sistema Avanzado de Monitoreo de Atención

Este proyecto implementa un sistema para la detectección y analisis de la atención de un usuario durante un examen virtual. Utiliza la cámara del dispositivo para rastrear movimientos de cabeza, es decir, giros (izquierda, derecha, arriba, abajo), pérdida de rostro y cambios de foco en la ventana. Genera un reporte al finalizar el examen donde detalla el comportamiento durante el examen, ayudando a identificar comportamientos sospechosos como distracciones o intentos de hacer trampa.

---

## Características Principales

- **Selección manual de ROI (Región de Interés)**  
- **Seguimiento Óptico y CamShift**  
- **Análisis de Atención en tiempo real**  
- **Interfaz gráfica con Tkinter**  
- **Reporte al finalizar detallando el comportamiento**  
- **Monitoreo de foco de ventana**  
- **Detección de mirada al frente por simetría facial**

---

## Requisitos

- Python 3.7+
- Cámara web
- Bibliotecas necesarias:
  - `opencv-python`
  - `numpy`
  - `Pillow`
  - `tkinter` (incluido en Python estándar)

---

## Instalación

Clona este repositorio:

```bash
git clone https://github.com/tu-usuario/tu-repositorio.git
cd tu-repositorio
```

## Instalación de Dependencias

Instala las dependencias:

```bash
pip install opencv-python numpy Pillow
```

## Cómo Ejecutar

Ejecuta el archivo principal dende la carpeta del proyecto:

```bash
python main.py
```

## Pasos básicos

- Selecciona el rostro con **Seleccionar Rostro**
- Ingresa la **Duración del examen (en minutos)**
- Inicia dando click en **Iniciar Examen**
- Al finalizar, se generará el archivo:

```
reporte_atencion.txt
```

**Nota:** Si la cámara falla, cambia el índice en tu código:

```python
self.cap = cv2.VideoCapture(0)
```

---

## Módulos del Proyecto

### 1. `Pantalla_UI`
Controla toda la interfaz gráfica (Tkinter) y conecta todos los módulos.

### 2. `Region_Selector`
Permite seleccionar el ROI del rostro mediante una ventana de OpenCV.

### 3. `Optical_Flow_Tracker`
Realiza seguimiento del rostro mediante el métodos como:

```python
cv2.goodFeaturesToTrack()
cv2.calcOpticalFlowPyrLK()
```

### 4. `Attention_Analyzer`
Analiza:
- Movimientos
- Giros de cabeza
- Pérdidas de rostro
- Cambios de ventana

### 5. `Reporte`
Genera el reporte final con porcentajes y tiempos acumulados de cada acción.

### 6. `Window_Monitor`
Detecta si se cambia de ventana durante el examen.

### 7. `Main`
Punto principal donde se lleva a cabo el llamado y la ejecución de toda la aplicació.

---

## Funcionamiento de la Interfaz

Elementos principales:

- Título superior  
- Controles: duración, selección de ROI, iniciar/detener  
- Vista en vivo de la cámara  
- Indicador de estado  
- Temporizador  
- Barra inferior de mensajes  

---

## Ejemplos de Uso

- Detectar distracciones moviendo la cabear pérdida de foco za  
- Cambiar de ventana para simul 
- Revisar el archivo generado **reporte_atencion.txt**

---


## Equipo

Desarrollado por **[Surikey Hipolito Aguilar y Roberto Carlos Hernandez Aparicio]**  
Basado en **Jan Erik Solem — Programming Computer Vision with Python y Michael Beyeler — OpenCV Computer Vision with Python**.

