# Mapa de Ramas y Flujo de Trabajo (J1)

**Autor**: J1 (Historiador de Ramas)
**Fecha**: 2026-10-08

## 1. Inventario de Ramas y Análisis
Se han identificado las siguientes ramas activas en el repositorio:

### `main`
- **Autor**: Múltiples (integración principal).
- **Propósito**: Rama productiva estable. Actualmente incluye la Fase 1 (Visión Computacional) y la Fase 2 (Constraint Programming, integrada vía PR #4), así como el andamiaje del informe IEEE en LaTeX.
- **Estado**: Base sólida, pero carece de las últimas métricas, del scraper y de la aplicación móvil.

### `develop`
- **Autor**: Múltiples (integración en desarrollo).
- **Propósito**: Rama de integración intermedia. Absorbió los cambios de configuración del entorno (`requirements.txt`, tipografías) a través de PRs #8 y #9, y está sincronizada con `main` (PR #7).

### `feature/tb1-informe`
- **Autor**: Equipo.
- **Base**: `develop` (a través de `main`).
- **Divergencia vs Base**: 2 commits.
- **Propósito**: Actualiza `informe/main.tex` con las métricas medidas reales y añade un script `medir_solver.py` que calcula tiempos E2E de lectura + resolución.
- **Estado**: Listo para integrar. No tiene conflictos severos.

### `feature/tb1-scraper-kenken`
- **Autor**: Equipo.
- **Base**: `develop`.
- **Divergencia vs Base**: 4 commits.
- **Propósito**: Añade un web scraper (`scrapear_kenken.py`) para descargar automáticamente PDFs de KrazyDad, un extractor robusto de etiquetas y un benchmark de OCR usando la métrica Kappa de Cohen (`benchmark_ocr.py`).
- **Estado**: Listo para integrar, presenta un conflicto textual menor en `labs/tb1-kenken/.gitignore` si se hace octopus merge con otras ramas, fácilmente subsanable.

### `feature/tb1-app-spec`
- **Autor**: Equipo.
- **Base**: `develop`.
- **Divergencia vs Base**: 4 commits.
- **Propósito**: Agrega el código fuente de un cliente web/Android (`app.js`, HTML, CSS) y una documentación extensa basando la interfaz en Diseño Centrado en Personas (HCD) apoyada por papers académicos.
- **Estado**: Excede los requerimientos mínimos de la rúbrica pero añade gran valor visual/arquitectónico.

---

## 2. Flujo de Trabajo y Decisiones Reconstruidas
1. **Delegación Estructurada (Git Flow)**: El equipo utiliza un modelo estilo Git Flow modificado. Las funcionalidades pesadas (scraper, informe, app) se bifurcaron de `develop` en paralelo.
2. **Decisión de Reemplazar Dataset Manual por Scraper**: Se optó por construir un pipeline de scraping automatizado (KrazyDad) en lugar de depender de descargas manuales; esto asegura que cualquier tamaño de cuadrícula pueda ser evaluado (Decisión fundamentada en la robustez pedida por la rúbrica).
3. **Métrica Kappa de Cohen**: El uso de esta métrica en `benchmark_ocr.py` sugiere que el equipo decidió evaluar la precisión del OCR corrigiendo el acierto por azar, una práctica rigurosa.
4. **Diseño Centrado en el Humano (HCD)**: La inclusión de `tb1-app-spec` refleja la intención de no dejar el solver en CLI, sino empaquetarlo en una aplicación Android apoyada por literatura académica (9 papers).

## 3. Estado Integrado Recomendado
El **estado integrado más completo** se logrará haciendo merge de las tres ramas `feature/*` (informe, scraper, app-spec) hacia `develop`, resolviendo el leve conflicto en `.gitignore`. Esta integración unirá el modelo matemático con las métricas finales (LaTeX), la extracción masiva de datos (Scraper) y la interfaz extendida (App).
