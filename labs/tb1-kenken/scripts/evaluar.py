"""Mide la Fase 1 contra ground truth sintético.

Separa dos ejes que se confunden con facilidad:

* **condición**: tablero limpio (escaneo/PDF) frente a foto degradada.
* **tipografía**: fuentes que están en el banco de plantillas frente a fuentes
  que el clasificador no ha visto nunca. Sin este corte, la precisión del OCR
  está inflada.

Uso: ``uv run python scripts/evaluar.py [n_tableros]``
"""

from __future__ import annotations

import random
import sys
from collections import defaultdict

import numpy as np

from kenken_cv.cages import particionar
from kenken_cv.grid import encontrar_rejilla
from kenken_cv.pipeline import FUENTES_PLANTILLA, leer
from kenken_cv.render import FUENTES, degradar, random_instance, render


def evaluar(n_tableros: int = 60, semilla: int = 2026) -> dict:
    rng = random.Random(semilla)
    acc: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for _ in range(n_tableros):
        n = rng.choice([4, 5, 6, 7])
        idx = rng.randrange(len(FUENTES))
        tipo = "plantilla" if FUENTES[idx] in FUENTES_PLANTILLA else "holdout"
        instancia, _ = random_instance(n, rng)
        limpia = render(instancia, fuente=FUENTES[idx])
        verdad = instancia.canonical()
        jaulas_reales = {c.cells for c in verdad.cages}

        for condicion, imagen in (("limpio", limpia), ("foto", degradar(limpia, rng))):
            m = acc[(condicion, tipo)]
            m["tableros"] += 1
            a = np.array(imagen.convert("L"))

            try:
                rejilla = encontrar_rejilla(a)
            except Exception:
                continue
            m["rejilla_ok"] += rejilla.size == n
            if rejilla.size != n:
                continue

            particion = particionar(rejilla)
            m["jaulas_ok"] += set(particion.grupos) == jaulas_reales
            m["margen_x100"] += int(100 * min(particion.margen, 10))

            try:
                lectura = leer(a)
            except Exception:
                m["etiqueta_error"] += 1
                continue

            leida = lectura.instancia.canonical()
            m["instancia_ok"] += leida == verdad
            esperado = {c.cells: (c.op, c.target) for c in verdad.cages}
            m["etiquetas"] += len(esperado)
            m["etiquetas_ok"] += sum(
                1 for c in leida.cages if esperado.get(c.cells) == (c.op, c.target)
            )
    return acc


def informe(acc: dict) -> None:
    cab = f"{'condición':10s} {'tipografía':10s} {'n':>4s} {'rejilla':>9s} {'jaulas':>9s} {'etiquetas':>11s} {'instancia':>11s} {'margen':>7s}"
    print(cab)
    print("-" * len(cab))
    for clave in sorted(acc):
        m = acc[clave]
        t = m["tableros"]
        if not t:
            continue
        et = f"{m['etiquetas_ok']}/{m['etiquetas']}" if m["etiquetas"] else "-"
        pct_et = 100 * m["etiquetas_ok"] / m["etiquetas"] if m["etiquetas"] else 0
        print(
            f"{clave[0]:10s} {clave[1]:10s} {t:4d} "
            f"{100*m['rejilla_ok']/t:8.1f}% {100*m['jaulas_ok']/t:8.1f}% "
            f"{pct_et:7.1f}% {100*m['instancia_ok']/t:10.1f}% "
            f"{m['margen_x100']/t/100:6.2f}x"
        )


if __name__ == "__main__":
    informe(evaluar(int(sys.argv[1]) if len(sys.argv) > 1 else 60))
