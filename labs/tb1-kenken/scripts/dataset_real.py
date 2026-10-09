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


def rasterizar_pagina(pdf: Path, pagina: int, destino: Path) -> None:
    """Rasteriza una página del PDF a imagen PNG a 150 DPI."""
    try:
        import pypdfium2 as pdfium

        doc = pdfium.PdfDocument(str(pdf))
        page = doc[pagina - 1]
        img = page.render(scale=DPI / 72.0).to_pil()
        img.save(str(destino))
        return
    except ImportError:
        pass

    subprocess.run(
        ["pdftoppm", "-r", str(DPI), "-png", "-f", str(pagina), "-l", str(pagina),
         str(pdf), str(destino.parent / f"pg_{pdf.stem}")],
        check=True,
    )


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
                rasterizar_pagina(pdf, pagina, png)


def extraer_palabras_pagina(pdf: Path, pagina: int) -> list[tuple[float, float, float, float, str]]:
    """Extrae palabras del texto vectorial de la página (xMin, yMin, xMax, yMax, texto)."""
    try:
        import pypdfium2 as pdfium

        doc = pdfium.PdfDocument(str(pdf))
        page = doc[pagina - 1]
        _, h_pt = page.get_size()
        textpage = page.get_textpage()
        words = []
        curr_chars, curr_boxes = [], []
        for i in range(textpage.count_chars()):
            ch = textpage.get_text_range()[i]
            if ch.isspace():
                if curr_chars:
                    words.append((
                        min(b[0] for b in curr_boxes),
                        h_pt - max(b[3] for b in curr_boxes),
                        max(b[2] for b in curr_boxes),
                        h_pt - min(b[1] for b in curr_boxes),
                        "".join(curr_chars),
                    ))
                    curr_chars, curr_boxes = [], []
            else:
                curr_chars.append(ch)
                curr_boxes.append(textpage.get_charbox(i))
        if curr_chars:
            words.append((
                min(b[0] for b in curr_boxes),
                h_pt - max(b[3] for b in curr_boxes),
                max(b[2] for b in curr_boxes),
                h_pt - min(b[1] for b in curr_boxes),
                "".join(curr_chars),
            ))
        return [
            (a, b, c, d, t.strip())
            for a, b, c, d, t in words
            if t.strip() and (t.strip().isdigit() or t.strip() in OPERADORES)
        ]
    except ImportError:
        pass

    xml = subprocess.run(
        ["pdftotext", "-f", str(pagina), "-l", str(pagina), "-bbox", str(pdf), "-"],
        capture_output=True, text=True,
    ).stdout
    return [
        (float(a), float(b), float(c), float(d), t.strip())
        for a, b, c, d, t in PALABRA.findall(xml)
        if t.strip() and (t.strip().isdigit() or t.strip() in OPERADORES)
    ]


def verdad_de_pagina(pdf: Path, pagina: int, n: int, rejilla) -> dict[tuple[int, int], tuple[str, int]]:
    """{(fila, col): (operación, objetivo)} a partir del texto vectorial."""
    from kenken_cv.extractor import asociar_etiquetas_celdas

    crudas = extraer_palabras_pagina(pdf, pagina)
    return asociar_etiquetas_celdas(crudas, rejilla, n, punto_a_pixel=PUNTO_A_PIXEL)


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
