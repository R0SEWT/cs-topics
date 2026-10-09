# Acta Inicial (Fase 1: Reconstrucción) - PARADA 1

**Panel de Agentes-Juez**
**Fecha**: 2026-10-08

## Resumen Ejecutivo del Estado del Repositorio
Se ha inspeccionado el repositorio remoto tras los últimos cambios del equipo. El desarrollo actual se concentra en el pulido final y la extensión de funcionalidades, evidenciando un esfuerzo sustancial para garantizar excelencia en los entregables.

### 1. Mapa de Ramas y Evolución
- El trabajo de **Constraint Programming (Fase 2)** y el **Fix del Entorno (Requirements)** ya han sido absorbidos exitosamente en `main` y `develop` mediante los PRs #4, #7, #8 y #9.
- Existen tres ramas `feature/*` huérfanas pero terminadas que encapsulan el progreso restante:
  1. `feature/tb1-informe`: Actualización del `.tex` e inclusión de `medir_solver.py`.
  2. `feature/tb1-scraper-kenken`: Extracción automatizada de KrazyDad y validación estadística rigurosa (Kappa de Cohen).
  3. `feature/tb1-app-spec`: Prototipo en HTML/JS (Android APK ready) y fundamentación de Diseño Centrado en Personas (HCD).

### 2. Flujo de Trabajo y Decisiones Clave Reconstruidas
- **Desarrollo Paralelo**: El equipo se dividió para atacar el informe, el scraper y una interfaz móvil en simultáneo desde `develop`.
- **Enfoque Académico Riguroso**: En lugar de limitarse a la CLI, se invirtió esfuerzo en crear una aplicación fundamentada con 9 papers académicos, superando la rúbrica básica y apuntando a una aplicación real.
- **Validación Robusta (Decisión clave)**: Se implementó la métrica *Kappa de Cohen* para medir el OCR, corrigiendo la probabilidad de acierto por azar.

### 3. Estado Integrado Propuesto
El código base más maduro se obtendrá al **fusionar (merge)** `tb1-informe`, `tb1-scraper-kenken` y `tb1-app-spec` sobre `develop` y posteriormente hacia `main`. Existe un único conflicto sintáctico mínimo en `labs/tb1-kenken/.gitignore` debido a adiciones simultáneas.

---

**El panel se detiene en este punto (PARADA 1) aguardando instrucciones del Orquestador/Humano** para proceder con la **Fase 2 (Validación empírica en paralelo por J2-J5)**.
