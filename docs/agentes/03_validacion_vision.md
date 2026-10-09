# Validación de Visión Computacional (J2)

**Autor**: J2
**Fecha**: 2026-10-08

## Ejecución Real
Se corrió `benchmark_ocr.py` y `medir_solver.py` sobre los tableros obtenidos por web scraping.

### Métricas de OCR Obtenidas
- **Total de etiquetas evaluadas**: 895
- **Accuracy Exacta**: 95.98%
- **Cohen's Kappa**: 0.9566 (Acuerdo casi perfecto)
- **Top de confusiones**: `5+` confundido con `6+` (25 veces). Este parece ser un límite del banco de plantillas con la tipografía Inky.

### Métricas de Pipeline E2E
De 16 tableros reales complejos extraídos de PDFs completos:
- **Resueltos de punta a punta (Perfectos)**: 7/16 (43.7%).
- Cuando el OCR falla (ej. confunde un `5+` con `6+`), el solver determina "sin solución" en ~2ms a 14ms (debido a la infactibilidad matemática generada por el OCR). El sistema reporta el error limpiamente sin crashear.

## Verificación de Rúbrica
- ✅ **Precisión en detección de grilla, números y símbolos (3/3 pts)**: Se logró 95.98% de accuracy corregido por azar (Kappa > 0.95).
- ⚠️ **Robustez bajo distintas condiciones de imagen (0.5/1 pts)**: Aunque el extractor es robusto para PDFs (distintos tamaños), **no hay fotos físicas en `dataset_fotografico/`**. El equipo automatizó el scraping digital pero omitió capturas impresas con cámara, iluminación y rotación.
