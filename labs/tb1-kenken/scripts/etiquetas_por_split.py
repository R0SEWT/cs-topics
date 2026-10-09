"""Exactitud y kappa de Cohen de la lectura de etiquetas, separando cuadernillos
de desarrollo (INKY_6H, INKY_9H: los 16 tableros con que se ajustó el pipeline)
de los no usados en desarrollo (INKY_4E, INKY_4H, INKY_6E).

Misma lógica que scripts/benchmark_ocr.py (rama feature/tb1-scraper-kenken). Kappa implementado
a mano con la fórmula de sklearn.metrics.cohen_kappa_score sin pesos (sklearn no
está instalado en el venv); se valida reproduciendo el 0.969 del total.

Uso (desde labs/tb1-kenken):
  PYTHONPATH=. uv run python <este>.py data_scraped/extraidos
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

import cv2

from kenken_cv.glyphs import EtiquetaIlegible, leer_recorte

SUFIJO = {"eq": "=", "plus": "+", "minus": "-", "times": "*", "div": "/"}
DEV = {"INKY_6H", "INKY_9H"}


def kappa(y_true, y_pred) -> float:
    n = len(y_true)
    po = sum(a == b for a, b in zip(y_true, y_pred)) / n
    ct, cp = Counter(y_true), Counter(y_pred)
    pe = sum(ct[k] * cp[k] for k in set(ct) | set(cp)) / n**2
    return (po - pe) / (1 - pe) if pe != 1 else 1.0


def main() -> None:
    raiz = Path(sys.argv[1])
    datos = defaultdict(lambda: ([], []))
    fallos = defaultdict(Counter)
    for f in sorted(raiz.glob("*/etiquetas/*.png")):
        cuad = "_".join(f.stem.split("_")[:2])
        cola = f.stem.split("_")[-1]
        k = next(k for k in SUFIJO if cola.endswith(k))
        op, obj = SUFIJO[k], int(cola[: -len(k)])
        gt = f"{obj}{op}"
        try:
            lo, ln, _ = leer_recorte(cv2.imread(str(f), cv2.IMREAD_GRAYSCALE), unaria=(op == "="))
            pr = f"{ln}{lo}"
        except EtiquetaIlegible:
            pr = "??"
        for clave in (cuad, "DEV" if cuad in DEV else "HELDOUT", "TOTAL"):
            datos[clave][0].append(gt)
            datos[clave][1].append(pr)
            if gt != pr:
                fallos[clave][(gt, pr)] += 1
    print(f"{'grupo':10s} {'n':>5s} {'ok':>5s} {'exact%':>8s} {'kappa':>7s}")
    for clave in ["INKY_4E", "INKY_4H", "INKY_6E", "INKY_6H", "INKY_9H", "DEV", "HELDOUT", "TOTAL"]:
        yt, yp = datos[clave]
        ok = sum(a == b for a, b in zip(yt, yp))
        print(f"{clave:10s} {len(yt):5d} {ok:5d} {100*ok/len(yt):8.2f} {kappa(yt, yp):7.4f}")
    for clave in ["DEV", "HELDOUT"]:
        print(f"\nfallos {clave}:", dict(fallos[clave].most_common()))


if __name__ == "__main__":
    main()
