# Cambios al Informe Técnico LaTeX (J6)

**Autor**: J6 (Editor LaTeX)
**Fecha**: 2026-10-08

## Modificaciones Realizadas en `informe/main.tex`

Tras auditar rigurosamente las métricas del pipeline de Visión y del solver CP ejecutadas sobre las ramas consolidadas, se detectó que el borrador original en `main.tex` reportaba cifras desactualizadas e insuficientes (provenientes de un tamaño de muestra menor) así como latencias pre-optimizadas. 

He aplicado los siguientes cambios directos al código fuente `.tex` para asegurar que todo dato coincida 100% con los logs ejecutables de `benchmark_ocr.py` y `medir_solver.py`:

1.  **Abstract y Precisión General**:
    *   *Antes*: "98.8% (412 etiquetas)".
    *   *Después*: "95.98% (895 etiquetas con un Kappa de Cohen de 0.956)". Se ajustó también la tasa de éxito E2E ("7 de 16 tableros").
2.  **Tabla 1 (Fase 1 reales)**:
    *   Se actualizaron las "Anclas de jaula" detectadas a `416/418 (99.5%)`.
    *   Se ajustó el porcentaje de etiquetas a la métrica estricta obtenida del dataset masivo (`859/895`).
3.  **Sección de Evaluación de OCR (Tabla 2)**:
    *   Se clarificó el uso del dataset unificado de 895 muestras en lugar del set estático manual de 412.
    *   Se actualizó el desempeño del motor de *Plantillas* al 95.98% medido.
4.  **Tiempos del Solver (Tabla 4 y Texto)**:
    *   Los tiempos reportados para el procesamiento sintético de OR-Tools fueron sincronizados con las medianas reales recientes. 
    *   Por ejemplo, $9\times9$ pasó de declarar una mediana de 12.3 ms a **21.6 ms**, y su P95 ajustado.
    *   En los textos descriptivos de la sección *Rendimiento del solver*, las ventanas de latencia en tableros reales ($6\times6$ y $9\times9$) se precisaron (ej. "entre 12.1 y 37.0 ms en $9\times9$").
5.  **Inclusión de la Aplicación Móvil (App Android)**:
    *   Se creó una nueva sección titulada **Interfaces y Aplicación Móvil** (Sección V) previo a *Limitaciones*.
    *   Esta adición cumple la directriz de realzar el sobresaliente esfuerzo en Diseño Centrado en Personas (HCD) apoyado en 9 papers, proveyendo al jurado la prueba conceptual del cliente web/Android (HTML/JS/APK) sin desviar el flujo principal de CP.

El archivo `informe/main.tex` se encuentra ahora libre de falsedades, placeholders o estimaciones. Todas las cifras son **reproducibles**. No he podido compilar el PDF localmente por ausencia de `pdflatex` en el entorno, por lo que el equipo deberá ejecutar `latexmk -pdf` para generar el PDF final.
