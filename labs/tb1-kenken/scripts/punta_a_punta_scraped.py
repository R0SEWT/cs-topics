"""De punta a punta sobre los tableros que extrajo scripts/extraer_dataset.py.

Cada tablero trae su verdad (<nombre>.json, sacada del texto vectorial del PDF). Se pasa la
imagen por la Fase 1 entera, se coteja la instancia leída con la verdad y se resuelve lo
leído. Aparte se cronometra el solver sobre la verdad: puzzles publicados, de solución única.

Uso: PYTHONPATH=. uv run python scripts/punta_a_punta_scraped.py [data_scraped/extraidos]
"""
from __future__ import annotations

import os, platform, statistics, sys, time
from collections import Counter, defaultdict
from pathlib import Path

from ortools import __version__ as ORTOOLS
from kenken_cp.solver import contar_soluciones, resolver
from kenken_cv.pipeline import leer
from kenken_cv.schema import Instance


def cronometrar(inst):
    t0 = time.perf_counter(); sol = resolver(inst); t1 = time.perf_counter()
    k = contar_soluciones(inst, tope=2); t2 = time.perf_counter()
    return 1000 * (t1 - t0), 1000 * (t2 - t1), sol is not None, k


def main() -> None:
    raiz = Path(sys.argv[1] if len(sys.argv) > 1 else "data_scraped/extraidos")
    print(f"OR-Tools {ORTOOLS} · Python {platform.python_version()} · {platform.processor() or platform.machine()} · {os.cpu_count()} hilos\n")
    resolver(Instance.from_json((next(raiz.glob('*/tableros/*.json'))).read_text()))  # calienta CP-SAT
    por_n = defaultdict(Counter); t_verdad = defaultdict(list); t_leida = []
    for js in sorted(raiz.glob("*/tableros/*.json")):
        verdad = Instance.from_json(js.read_text()).canonical()
        n = verdad.size; c = por_n[n]; c["tableros"] += 1
        tr, tc, ok, k = cronometrar(verdad)
        t_verdad[n].append(tr); c["verdad_unica"] += k == 1
        try:
            lect = leer(js.with_suffix(".png"))
            inst = lect.instancia.canonical()
        except Exception as e:
            c["sin_instancia"] += 1; c[f"exc:{type(e).__name__}"] += 1; continue
        c["n_ok"] += inst.size == n
        part_ok = sorted(x.cells for x in inst.cages) == sorted(x.cells for x in verdad.cages)
        c["particion_ok"] += part_ok
        if inst == verdad:
            c["bien"] += 1
        tr, tc, ok, k = cronometrar(inst); t_leida.append(tr)
        res = "sin_solucion" if not ok else ("unica" if k == 1 else "varias")
        c[f"leida_{res}"] += 1
        if inst != verdad and ok and k == 1:
            # la lectura tiene un error y aun así da una solución única: ¿coincide con la de la verdad?
            c["error_silencioso"] += resolver(inst) != resolver(verdad)
    print(f"{'n':>3} {'tabl':>5} {'n ok':>5} {'partición':>10} {'bien':>5} {'sin inst':>9} {'única':>6} {'varias':>7} {'sin sol':>8} {'silenc.':>8} {'verdad única':>13}")
    tot = Counter()
    for n in sorted(por_n):
        c = por_n[n]; tot.update(c)
        print(f"{n:3d} {c['tableros']:5d} {c['n_ok']:5d} {c['particion_ok']:10d} {c['bien']:5d} {c['sin_instancia']:9d} {c['leida_unica']:6d} {c['leida_varias']:7d} {c['leida_sin_solucion']:8d} {c['error_silencioso']:8d} {c['verdad_unica']:13d}")
    print(f"tot {tot['tableros']:5d} {tot['n_ok']:5d} {tot['particion_ok']:10d} {tot['bien']:5d} {tot['sin_instancia']:9d} {tot['leida_unica']:6d} {tot['leida_varias']:7d} {tot['leida_sin_solucion']:8d} {tot['error_silencioso']:8d} {tot['verdad_unica']:13d}")
    print("excepciones:", {k: v for k, v in tot.items() if k.startswith("exc:")})
    print("\nresolver sobre la verdad (ms):")
    for n in sorted(t_verdad):
        xs = sorted(t_verdad[n])
        print(f"  n={n}: {len(xs)} tableros · mediana {statistics.median(xs):.1f} · máx {max(xs):.1f}")
    if t_leida: print(f"resolver sobre lo leído: máx {max(t_leida):.1f} ms")


if __name__ == "__main__":
    main()
