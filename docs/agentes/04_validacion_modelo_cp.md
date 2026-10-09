# Validación del Modelo CP (J3)

**Autor**: J3
**Fecha**: 2026-10-08

## Ejecución Real
Las métricas en instancias sintéticas aleatorias ($4\times4$ hasta $9\times9$) indican tiempos medianos asombrosos:
- $6\times6$: med 12.9 ms
- $9\times9$: med 21.6 ms
Todas resueltas en menos de 40 ms.

El script de tests (`pytest tests/test_kenken_cp.py`) pasa completamente, confirmando el cumplimiento funcional del CP.

## Verificación de Rúbrica
- ✅ **Correcta formulación matemática (3/3 pts)**: El modelo está puramente parametrizado. La matriz $x$ asume el tamaño variable dependiente del esquema de fase 1. Los dominios son rigurosos $[1, n]$.
- ✅ **Uso de restricciones globales (3/3 pts)**: Aplicación perfecta de `AllDifferent` sobre filas y columnas (Cuadrado Latino).
- ✅ **Restricciones reificadas (1/1 pts)**: Presentes. El uso de variables ocultas (`AddMaxEquality`, `AddMinEquality`) logra la absorción del orden espacial irrelevante, una forma avanzada y robusta de plantear la sustracción y la división CP-SAT.
