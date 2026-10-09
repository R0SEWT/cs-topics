"""Compara formulaciones del modelo CP sobre los tableros reales, para que el informe no
afirme a ojo que las restricciones globales convienen.

Variantes (todas con el mismo solver y un solo hilo, para que ramas y conflictos sean
comparables y deterministas):
* global:    AllDifferent por fila y columna; resta y división con el par max/min (el modelo
             de kenken_cp.solver).
* binaria:   cada AllDifferent se reemplaza por sus n(n-1)/2 desigualdades x != y.
* reificada: AllDifferent, pero resta y división como disyunción reificada
             (b => a-b=T, not b => b-a=T), con una variable booleana por jaula.

Se mide sobre dos conjuntos: la verdad de los 70 tableros (puzzles con solución, salvo un
9x9 cuya verdad está mal) y lo que la Fase 1 lee de ellos, que incluye las 19 instancias
sin solución que el solver tiene que demostrar.

Uso: PYTHONPATH=. uv run python scripts/comparar_formulaciones.py [data_scraped/extraidos]
"""
from __future__ import annotations

import statistics, sys, time
from collections import defaultdict
from pathlib import Path

from ortools import __version__ as ORTOOLS
from ortools.sat.python import cp_model

from kenken_cv.pipeline import leer
from kenken_cv.schema import Instance


def modelo(inst: Instance, variante: str) -> cp_model.CpModel:
    n = inst.size
    m = cp_model.CpModel()
    x = [[m.NewIntVar(1, n, f"x_{r}_{c}") for c in range(n)] for r in range(n)]
    for i in range(n):
        for linea in (x[i], [x[j][i] for j in range(n)]):
            if variante == "binaria":
                for a in range(n):
                    for b in range(a + 1, n):
                        m.Add(linea[a] != linea[b])
            else:
                m.AddAllDifferent(linea)
    for k, cage in enumerate(inst.cages):
        v = [x[r][c] for r, c in cage.cells]
        T = cage.target
        if cage.op == "=":
            m.Add(v[0] == T)
        elif cage.op == "+":
            m.Add(sum(v) == T)
        elif cage.op == "*":
            m.AddMultiplicationEquality(T, v)
        elif cage.op in "-/":
            a, b = v
            if variante == "reificada":
                beta = m.NewBoolVar(f"b_{k}")
                if cage.op == "-":
                    m.Add(a - b == T).OnlyEnforceIf(beta)
                    m.Add(b - a == T).OnlyEnforceIf(beta.Not())
                else:
                    m.Add(a == T * b).OnlyEnforceIf(beta)
                    m.Add(b == T * a).OnlyEnforceIf(beta.Not())
            else:
                M = m.NewIntVar(1, n, f"M_{k}")
                mi = m.NewIntVar(1, n, f"m_{k}")
                m.AddMaxEquality(M, [a, b])
                m.AddMinEquality(mi, [a, b])
                m.Add(M - mi == T) if cage.op == "-" else m.Add(M == T * mi)
    return m


def medir(inst: Instance, variante: str) -> tuple[float, int, int, bool]:
    m = modelo(inst, variante)
    s = cp_model.CpSolver()
    s.parameters.num_workers = 1
    t0 = time.perf_counter()
    st = s.Solve(m)
    ms = 1000 * (time.perf_counter() - t0)
    return ms, s.NumBranches(), s.NumConflicts(), st in (cp_model.OPTIMAL, cp_model.FEASIBLE)


def main() -> None:
    raiz = Path(sys.argv[1] if len(sys.argv) > 1 else "data_scraped/extraidos")
    print(f"OR-Tools {ORTOOLS} · 1 hilo\n")
    verdad, leidas = [], []
    for js in sorted(raiz.glob("*/tableros/*.json")):
        verdad.append(Instance.from_json(js.read_text()))
        try:
            leidas.append(leer(js.with_suffix(".png")).instancia)
        except Exception:
            pass
    medir(verdad[0], "global")  # calienta CP-SAT
    for nombre, conjunto in (("verdad (70 tableros)", verdad), ("lo leído (67 instancias)", leidas)):
        print(f"== {nombre}")
        print(f"{'variante':10s} {'n':>2s} {'inst':>5s} {'med ms':>7s} {'máx ms':>7s} {'ramas med':>10s} {'ramas máx':>10s} {'confl máx':>10s} {'sin ramas':>10s} {'sin sol':>8s}")
        for variante in ("global", "binaria", "reificada"):
            por_n = defaultdict(list)
            for inst in conjunto:
                por_n[inst.size].append(medir(inst, variante))
            for n in sorted(por_n):
                r = por_n[n]
                ms = [a for a, *_ in r]; ra = [b for _, b, _, _ in r]; co = [c for _, _, c, _ in r]
                print(f"{variante:10s} {n:2d} {len(r):5d} {statistics.median(ms):7.1f} {max(ms):7.1f} "
                      f"{statistics.median(ra):10.0f} {max(ra):10d} {max(co):10d} "
                      f"{sum(b == 0 for b in ra):10d} {sum(not ok for *_, ok in r):8d}")
        print()


if __name__ == "__main__":
    main()
