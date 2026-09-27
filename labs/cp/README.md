# Lab — Constraint Programming (Unidades 2–4)

Stack: **Python + OR-Tools CP-SAT**, gestionado con `uv`.

```bash
cd labs/cp
uv sync                      # instala dependencias (uv baja el Python compatible)
uv run pytest                # tests
uv run python models/nqueens.py
```

`models/nqueens.py` es el ejemplo de referencia (modelo → restricciones → solver);
copia su forma para los TPs de consistencia local y problemas sobrerrestringidos.

## TPs

| TP | Modelo | Tests |
|---|---|---|
| TP5 — TSP (`AddCircuit`, MTZ reificado, precedencias) | `models/tsp.py` | `tests/test_tsp.py` |

El ejercicio 4 del TP5 es teórico; su experimento de apoyo está en
`notebooks/tp5-ejercicio4.ipynb`. Jupyter va en un grupo aparte, que ni `uv sync` ni la CI
instalan:

```bash
uv run --group notebook jupyter lab notebooks/tp5-ejercicio4.ipynb
```

## Sobre la versión de Python

`requires-python` está fijado a `>=3.11,<3.14`: OR-Tools todavía no publica wheels
para el Python 3.14 del sistema. `uv sync` descarga un intérprete compatible solo
para este lab, sin tocar tu instalación.

## Si el curso exige MiniZinc

Varias sesiones del profe usan `.mzn`. No está instalado ni scaffoldeado — se añade
cuando haga falta, no antes:

```bash
sudo dnf install minizinc   # Fedora
```

Los modelos irían en `models/*.mzn` con sus datos `*.dzn` al lado.
