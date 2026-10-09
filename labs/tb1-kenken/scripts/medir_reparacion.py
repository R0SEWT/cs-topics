"""Mide la reparación guiada por el solver sobre las lecturas reales que no tienen solución.

Para cada tablero con verdad cuya lectura no tiene solución: ¿la reparación devuelve la
solución verdadera, una distinta (error silencioso, lo grave) o se abstiene?

Uso: PYTHONPATH=. uv run python scripts/medir_reparacion.py [data_scraped/extraidos]
"""
from __future__ import annotations

import sys, time
from collections import Counter
from pathlib import Path

from kenken_cp.reparar import reparar
from kenken_cp.solver import resolver
from kenken_cv.pipeline import leer
from kenken_cv.schema import Instance


def main() -> None:
    raiz = Path(sys.argv[1] if len(sys.argv) > 1 else "data_scraped/extraidos")
    cuenta, tiempos = Counter(), []
    for js in sorted(raiz.glob("*/tableros/*.json")):
        verdad = Instance.from_json(js.read_text())
        sol_verdad = resolver(verdad)
        try:
            leida = leer(js.with_suffix(".png")).instancia
        except Exception:
            continue
        if resolver(leida) is not None:
            continue
        t0 = time.perf_counter()
        r = reparar(leida)
        tiempos.append(1000 * (time.perf_counter() - t0))
        if r is None:
            res = "se abstiene"
        elif sol_verdad is not None and r.solucion == sol_verdad:
            res = "repara bien"
        else:
            res = "ERROR silencioso"
        cuenta[res] += 1
        cambios = ", ".join(f"{c.leido[1]}{c.leido[0]}->{c.corregido[1]}{c.corregido[0]}" for c in (r.correcciones if r else ()))
        print(f"{js.stem:32s} {res:16s} {cambios}")
    print(dict(cuenta), f"· máx {max(tiempos):.0f} ms")


if __name__ == "__main__":
    main()
