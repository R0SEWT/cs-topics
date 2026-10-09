# Hallazgos y Objeciones (J7 Red Team)

**Autor**: J7
**Fecha**: 2026-10-08

## Observaciones Críticas a Resolver (PARADA 2)

1. **[H001] [Severidad: Alta] [Rama: develop] `dataset_fotografico/README.md`**
   - **Descripción**: El dataset fotográfico exigido por la rúbrica está vacío, lo cual invalida el punto de "Robustez bajo distintas condiciones de imagen".
   - **Acción**: Siendo IAs, no podemos tomar fotos físicas. Debemos emitir un warning absoluto y dejar el directorio y el placeholder intactos.

2. **[H002] [Severidad: Media] [Rama: feature/tb1-informe] `informe/main.tex`**
   - **Descripción**: El informe `main.tex` (en la versión del PR #4) declaraba "98.8% accuracy medido en 412 casos". Las métricas actuales de `benchmark_ocr.py` (con KrazyDad) muestran **95.98% sobre 895 etiquetas**.
   - **Acción**: J6 debe reescribir la sección del informe que aborda los resultados para empatarla 100% con los logs generados en `scripts.benchmark_ocr` y `scripts.medir_solver`.

3. **[H003] [Severidad: Baja] [Rama: feature/tb1-app-spec]**
   - **Descripción**: El código de la App móvil es sobresaliente pero la rúbrica no pide evaluar una App Android. Su inclusión distrae el foco del CLI que es evaluable primario.
   - **Acción**: Mantenerla en el repo porque aporta valor a portafolio, pero el Informe LaTeX debe enfocarse explícitamente en el E2E (pipeline IA->CP) y mencionar la App brevemente en "Trabajo Futuro" o "Interfaces".
