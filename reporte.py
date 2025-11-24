# Clase utilizada para generar reportes del examen de atención
class Reporte:

    @staticmethod
    #  Genera un reporte detallado del examen de atención.
    def construir_reporte(elapsed, analyzer):
        total_no = analyzer.total_no_atention # # Tiempo total sin atención acumulado por el analizador
        porcentaje_no = (total_no / elapsed) * 100.0 if elapsed > 0 else 0.0 # Porcentaje de tiempo sin atención respecto al tiempo total del examen
        # Desglose por causa (diccionario con claves: left, right, up, down, lost_roi, focus_change)
        b = analyzer.no_attention_breakdown
        # Evaluación básica: comportamiento sospechoso si más del 40% del tiempo sin atención
        sospechoso = "Sospechoso (mas del 40'%'sin atención)" if porcentaje_no > 40.0 else "Normal"
        # Construcción de reporte en formato legible
        reporte = (
            f"--- Reporte de Atención ---\n\n"
            f"Tiempo total del examen: {elapsed:.2f} s\n"
            f"Tiempo sin atención: {total_no:.2f} s ({porcentaje_no:.2f} %)\n\n"
            f"Desglose de falta de atención:\n"
            f" - Giro a la izquierda: {b['left']:.2f} s\n"
            f" - Giro a la derecha: {b['right']:.2f} s\n"
            f" - Giro hacia arriba: {b['up']:.2f} s\n"
            f" - Giro hacia abajo: {b['down']:.2f} s\n"
            f" - Pérdida del rostro: {b['lost_roi']:.2f} s\n"
            f" - Cambio de ventana: {b['focus_change']:.2f} s\n\n"
            f"Comportamiento: {sospechoso}\n"
        )

        return reporte