"""Mide la lectura de etiquetas contra tableros REALES.

Requiere haber ejecutado antes ``scripts/dataset_real.py``.

Complementa a ``evaluar.py`` (que mide contra tableros generados) y existe
porque los dos no dicen lo mismo: lo sintético daba 100% donde lo real daba 0%,
por supuestos que el generador nunca puso a prueba.
"""

from __future__ import annotations

import glob
import sys
from collections import Counter
from pathlib import Path

import cv2

from kenken_cv.glyphs import EtiquetaIlegible, leer_recorte

SUFIJO = {"eq": "=", "plus": "+", "minus": "-", "times": "*", "div": "/"}


def main() -> None:
    raiz = Path(sys.argv[1] if len(sys.argv) > 1 else "dataset_real") / "etiquetas"
    archivos = sorted(glob.glob(str(raiz / "*.png")))
    if not archivos:
        sys.exit(f"no hay etiquetas en {raiz}; ejecuta antes scripts/dataset_real.py")

    ok = op_ok = 0
    fallos: Counter = Counter()
    for f in archivos:
        cola = Path(f).stem.split("_")[-1]
        op, objetivo = next(
            (v, int(cola[: -len(k)])) for k, v in SUFIJO.items() if cola.endswith(k)
        )
        try:
            leido_op, leido_num, _ = leer_recorte(
                cv2.imread(f, cv2.IMREAD_GRAYSCALE), unaria=(op == "=")
            )
        except EtiquetaIlegible:
            leido_op, leido_num = "?", -1
        op_ok += leido_op == op
        if (leido_op, leido_num) == (op, objetivo):
            ok += 1
        else:
            fallos[(f"{objetivo}{op}", f"{leido_num}{leido_op}")] += 1

    n = len(archivos)
    print(f"etiquetas reales     {n}")
    print(f"etiqueta completa    {100*ok/n:5.1f}%")
    print(f"solo la operación    {100*op_ok/n:5.1f}%")
    print(f"\nprobabilidad de leer un tablero entero sin fallos:")
    for jaulas in (11, 16, 23):
        print(f"  {jaulas:2d} jaulas -> {100*(ok/n)**jaulas:5.1f}%")
    print("\nconfusiones más frecuentes:")
    for (v, p), k in fallos.most_common(8):
        print(f"    {v:8s} -> {p:8s} x{k}")


if __name__ == "__main__":
    main()
