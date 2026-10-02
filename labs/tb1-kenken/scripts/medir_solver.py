"""Mide cuánto tarda el modelo CP-SAT, para que el informe no afirme tiempos a ojo.

Dos fuentes, por la misma razón que hay dos evaluadores de la Fase 1:

* **sintéticas**: `random_instance` para n de 4 a 9. Cubren tamaños que los
  cuadernillos reales no traen, pero sus jaulas son aleatorias y no garantizan
  solución única: miden el solver, no la dificultad de un puzzle publicado.
* **reales**: los 16 tableros de KrazyDad (6x6 y 9x9) pasados por la Fase 1
  entera. Se resuelve lo que el pipeline *lee*, no la verdad: si el OCR erró,
  el solver tiene que demostrar que no hay solución, y eso también cuenta.
  De paso se coteja la lectura con la verdad del PDF (`verdad_de_pagina`), que
  es la única forma de saber si el tablero salió bien **de punta a punta**: la
  tasa por etiqueta elevada al número de jaulas es una estimación, no una
  medida.

Cada tablero se mide con `resolver` (una solución) y con `contar_soluciones`
(tope 2: ¿única o no?), que es lo que necesita la reparación guiada por el
solver. El tiempo es de pared e incluye construir el modelo.

Uso: ``PYTHONPATH=. uv run python scripts/medir_solver.py [n_por_tamaño] [dataset_real]``
"""

from __future__ import annotations

import glob
import os
import platform
import random
import statistics
import sys
import time
from pathlib import Path

from ortools import __version__ as ORTOOLS

from kenken_cp.solver import contar_soluciones, resolver
from kenken_cv.render import random_instance


def _cronometrar(instancia) -> tuple[float, float, bool, int]:
    t0 = time.perf_counter()
    solucion = resolver(instancia)
    t1 = time.perf_counter()
    cuantas = contar_soluciones(instancia, tope=2)
    t2 = time.perf_counter()
    return 1000 * (t1 - t0), 1000 * (t2 - t1), solucion is not None, cuantas


def _p95(xs: list[float]) -> float:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, round(0.95 * (len(xs) - 1)))]


def sinteticas(por_tamano: int = 30, semilla: int = 2026) -> None:
    rng = random.Random(semilla)
    print(f"Sintéticas: {por_tamano} por tamaño, semilla {semilla}")
    cab = f"{'n':>3s} {'resolver med':>13s} {'p95':>8s} {'máx':>8s} {'contar med':>11s} {'máx':>8s} {'única':>7s}"
    print(cab)
    print("-" * len(cab))
    for n in range(4, 10):
        res, con, unicas = [], [], 0
        for _ in range(por_tamano):
            instancia, _ = random_instance(n, rng)
            t_res, t_con, ok, cuantas = _cronometrar(instancia)
            assert ok, "una instancia generada desde un cuadrado latino siempre tiene solución"
            res.append(t_res)
            con.append(t_con)
            unicas += cuantas == 1
        print(
            f"{n:3d} {statistics.median(res):10.1f} ms {_p95(res):5.1f} ms {max(res):5.1f} ms "
            f"{statistics.median(con):8.1f} ms {max(con):5.1f} ms {100 * unicas / por_tamano:6.0f}%"
        )


def reales(carpeta: Path) -> None:
    from kenken_cv.pipeline import leer

    sys.path.insert(0, str(Path(__file__).parent))
    from dataset_real import verdad_de_pagina

    paginas = sorted(glob.glob(str(carpeta / "pg_*.png")))
    if not paginas:
        print(f"\nReales: no hay páginas en {carpeta}; ejecuta antes scripts/dataset_real.py")
        return
    print(f"\nReales: {len(paginas)} tableros de {carpeta}")
    cab = f"{'tablero':24s} {'n':>3s} {'jaulas':>7s} {'resolver':>10s} {'contar':>10s} {'resultado':>14s} {'lectura':>9s}"
    print(cab)
    print("-" * len(cab))
    res, con, correctos = [], [], 0
    for png in map(Path, paginas):
        # pg_INKY_6H_b001_1pp-3.png -> INKY_6H_b001_1pp.pdf, página 3
        stem, pagina = png.stem.removeprefix("pg_").rsplit("-", 1)
        try:
            lectura = leer(png)
        except Exception as e:  # la Fase 1 no dio instancia: no hay nada que resolver
            print(f"{png.stem:24s} {'-':>3s} {'-':>7s} {'-':>10s} {'-':>10s} {'sin instancia':>14s} {'mal':>9s}  ({type(e).__name__})")
            continue
        instancia = lectura.instancia
        verdad = verdad_de_pagina(carpeta / f"{stem}.pdf", int(pagina), instancia.size, lectura.rejilla)
        leida = {min(c.cells): (c.op, c.target) for c in instancia.cages}
        correctos += leida == verdad
        t_res, t_con, ok, cuantas = _cronometrar(instancia)
        res.append(t_res)
        con.append(t_con)
        resultado = "sin solución" if not ok else ("única" if cuantas == 1 else "varias")
        print(
            f"{png.stem:24s} {instancia.size:3d} {len(instancia.cages):7d} "
            f"{t_res:7.1f} ms {t_con:7.1f} ms {resultado:>14s} {'bien' if leida == verdad else 'mal':>9s}"
        )
    print(f"leídos bien de punta a punta: {correctos}/{len(paginas)}")
    if res:
        print(f"máximo: resolver {max(res):.1f} ms, contar {max(con):.1f} ms")


if __name__ == "__main__":
    print(
        f"OR-Tools {ORTOOLS} · Python {platform.python_version()} · "
        f"{platform.processor() or platform.machine()} · {os.cpu_count()} hilos\n"
    )
    resolver(random_instance(4, random.Random(0))[0])  # calienta la importación de CP-SAT
    sinteticas(int(sys.argv[1]) if len(sys.argv) > 1 else 30)
    reales(Path(sys.argv[2] if len(sys.argv) > 2 else "dataset_real"))
