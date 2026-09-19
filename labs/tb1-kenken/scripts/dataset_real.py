"""Descarga tableros KenKen REALES y extrae etiquetas con verdad exacta.

Fuente: cuadernillos "Inkies" de KrazyDad (https://krazydad.com/inkies/).
Su página autoriza expresamente la reproducción "for personal, church, school,
hospital or institutional use" y prohíbe el uso comercial. Son © KrazyDad.com:
se descargan bajo demanda y **no se versionan en este repositorio**; el informe
debe citarlos.

Los PDF son vectoriales, así que llevan las etiquetas como texto con su caja.
Proyectando cada palabra con la homografía del tablero se obtiene la celda a la
que pertenece, y con ella una verdad exacta sin etiquetar nada a mano. La celda
sale de la geometría, no del detector de jaulas, así que no se está midiendo el
detector contra sí mismo.

Uso: ``PYTHONPATH=. uv run python scripts/dataset_real.py [destino]``
"""

from __future__ import annotations

import re
import subprocess
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

from kenken_cv.cages import particionar
from kenken_cv.glyphs import recortar_etiqueta
from kenken_cv.grid import encontrar_rejilla

BASE = "https://krazydad.com/inkies/sfiles/"
CUADERNILLOS = (("INKY_6H_b001_1pp.pdf", 6), ("INKY_9H_b001_1pp.pdf", 9))
PAGINAS = range(1, 9)  # la 9 es el solucionario, no un tablero
DPI = 150
PUNTO_A_PIXEL = DPI / 72.0

PALABRA = re.compile(
    r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]+)</word>'
)
OPERADORES = {"+": "+", "-": "-", "−": "-", "×": "*", "x": "*", "/": "/", "÷": "/"}
NOMBRE_OP = {"=": "eq", "+": "plus", "-": "minus", "*": "times", "/": "div"}


def descargar(destino: Path) -> None:
    destino.mkdir(parents=True, exist_ok=True)
    for archivo, _ in CUADERNILLOS:
        pdf = destino / archivo
        if not pdf.exists():
            # El servidor devuelve 403 al User-Agent por defecto de urllib.
            peticion = urllib.request.Request(
                BASE + archivo, headers={"User-Agent": "Mozilla/5.0 (tb1-kenken; uso académico)"}
            )
            with urllib.request.urlopen(peticion) as r:
                pdf.write_bytes(r.read())
            print(f"  descargado {archivo}")
        for pagina in PAGINAS:
            png = destino / f"pg_{pdf.stem}-{pagina}.png"
            if not png.exists():
                subprocess.run(
                    ["pdftoppm", "-r", str(DPI), "-png", "-f", str(pagina), "-l", str(pagina),
                     str(pdf), str(destino / f"pg_{pdf.stem}")],
                    check=True,
                )


def verdad_de_pagina(pdf: Path, pagina: int, n: int, rejilla) -> dict[tuple[int, int], tuple[str, int]]:
    """{(fila, col): (operación, objetivo)} a partir del texto vectorial."""
    xml = subprocess.run(
        ["pdftotext", "-f", str(pagina), "-l", str(pagina), "-bbox", str(pdf), "-"],
        capture_output=True, text=True,
    ).stdout
    crudas = [
        (float(a), float(b), float(c), float(d), t.strip())
        for a, b, c, d, t in PALABRA.findall(xml)
        if t.strip() and (t.strip().isdigit() or t.strip() in OPERADORES)
    ]
    if not crudas:
        return {}

    lado = rejilla.warp.shape[0]
    paso = lado / n
    puntos = np.array(
        [[[(a + c) / 2 * PUNTO_A_PIXEL, (b + d) / 2 * PUNTO_A_PIXEL]] for a, b, c, d, _ in crudas],
        dtype=np.float32,
    )
    # Fuera del tablero quedan el encabezado, el título y las instrucciones del
    # pie, que también traen dígitos y ensuciarían el reparto por celdas.
    proyectados = cv2.perspectiveTransform(puntos, rejilla.homografia).reshape(-1, 2)

    celdas: dict[tuple[int, int], list[tuple[float, str]]] = defaultdict(list)
    for (x, y), (*_, t) in zip(proyectados, crudas):
        if not (0 <= x < lado and 0 <= y < lado):
            continue
        # La etiqueta va impresa en la esquina superior izquierda de su celda.
        # Sin esta condición se colaba el "© 2026 KrazyDad.com" del pie, que
        # cae dentro del tablero rectificado y convertía la verdad de la última
        # celda en cosas como "22026/".
        dentro_y, dentro_x = (y % paso) / paso, (x % paso) / paso
        if dentro_y > 0.55 or dentro_x > 0.85:
            continue
        celdas[(int(y // paso), int(x // paso))].append((x, t))

    verdad = {}
    for celda, trozos in celdas.items():
        ordenados = [t for _, t in sorted(trozos)]
        digitos = "".join(t for t in ordenados if t.isdigit())
        simbolos = [OPERADORES[t] for t in ordenados if t in OPERADORES]
        if digitos:
            verdad[celda] = (simbolos[-1] if simbolos else "=", int(digitos))
    return verdad


def main() -> None:
    raiz = Path(sys.argv[1] if len(sys.argv) > 1 else "dataset_real")
    descargar(raiz)
    recortes = raiz / "etiquetas"
    recortes.mkdir(exist_ok=True)

    tot_n = ok_n = tot_anclas = ok_anclas = guardados = 0
    for archivo, n in CUADERNILLOS:
        pdf = raiz / archivo
        for pagina in PAGINAS:
            png = raiz / f"pg_{pdf.stem}-{pagina}.png"
            imagen = cv2.imread(str(png), cv2.IMREAD_GRAYSCALE)
            if imagen is None:
                continue
            tot_n += 1
            try:
                rejilla = encontrar_rejilla(imagen)
            except Exception as e:  # noqa: BLE001
                print(f"  {png.name}: {e}")
                continue
            if rejilla.size != n:
                print(f"  {png.name}: n={rejilla.size}, esperado {n}")
                continue
            ok_n += 1

            verdad = verdad_de_pagina(pdf, pagina, n, rejilla)
            anclas = {min(g) for g in particionar(rejilla).grupos}
            tot_anclas += len(verdad)
            ok_anclas += len(anclas & set(verdad))

            for ancla in anclas & set(verdad):
                op, objetivo = verdad[ancla]
                recorte = recortar_etiqueta(rejilla, ancla)
                nombre = f"{pdf.stem}_p{pagina}_{ancla[0]}{ancla[1]}_{objetivo}{NOMBRE_OP[op]}.png"
                cv2.imwrite(str(recortes / nombre), recorte)
                guardados += 1

    print(f"\ntamaño de tablero  {ok_n}/{tot_n}")
    print(f"anclas de jaula    {ok_anclas}/{tot_anclas} ({100*ok_anclas/max(1,tot_anclas):.1f}%)")
    print(f"etiquetas reales   {guardados} en {recortes}/")


if __name__ == "__main__":
    main()
