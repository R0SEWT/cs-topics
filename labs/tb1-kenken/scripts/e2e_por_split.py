"""Punta a punta (misma lógica que scripts/punta_a_punta_scraped.py, sin cronómetro)
con desglose por cuadernillo y por split dev (INKY_6H, INKY_9H) / held-out
(INKY_4E, INKY_4H, INKY_6E).

Uso (desde labs/tb1-kenken):
  PYTHONPATH=. uv run python <este>.py data_scraped/extraidos
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

from kenken_cp.solver import contar_soluciones, resolver
from kenken_cv.pipeline import leer
from kenken_cv.schema import Instance

DEV = {"INKY_6H", "INKY_9H"}


def main() -> None:
    raiz = Path(sys.argv[1])
    acc = defaultdict(Counter)
    detalle = []
    for js in sorted(raiz.glob("*/tableros/*.json")):
        cuad = "_".join(js.stem.split("_")[:2])
        verdad = Instance.from_json(js.read_text()).canonical()
        verdad_sol = resolver(verdad)
        try:
            inst = leer(js.with_suffix(".png")).instancia.canonical()
        except Exception as e:
            res = "rechazado"
        else:
            sol = resolver(inst)
            k = contar_soluciones(inst, tope=2) if sol is not None else 0
            if inst == verdad:
                res = "bien"
            elif sol is None:
                res = "sin_solucion"
            elif k == 1 and verdad_sol is None:
                res = "verdad_erronea"  # la verdad no tiene solución, lo leído sí (INKY_9H p2)
            elif k == 1 and sol != verdad_sol:
                res = "error_silencioso"
            elif k == 1:
                res = "mal_leido_misma_solucion"
            else:
                res = "varias_soluciones"
        detalle.append((js.stem, res))
        for clave in (cuad, "DEV" if cuad in DEV else "HELDOUT", "TOTAL"):
            acc[clave]["tableros"] += 1
            acc[clave][res] += 1
    cols = ["tableros", "bien", "verdad_erronea", "rechazado", "sin_solucion",
            "error_silencioso", "mal_leido_misma_solucion", "varias_soluciones"]
    print(f"{'grupo':9s} " + " ".join(f"{c[:12]:>12s}" for c in cols))
    for clave in ["INKY_4E", "INKY_4H", "INKY_6E", "INKY_6H", "INKY_9H", "DEV", "HELDOUT", "TOTAL"]:
        print(f"{clave:9s} " + " ".join(f"{acc[clave][c]:12d}" for c in cols))
    print("\nno-bien:", [d for d in detalle if d[1] != "bien"])


if __name__ == "__main__":
    main()
