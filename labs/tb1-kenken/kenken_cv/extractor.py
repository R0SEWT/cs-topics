"""Extractor de etiquetas y partición de páginas para tableros KenKen reales.

Soporta cuadernillos de 1 por página (_1pp) y de 4 por página (_4pp),
permitiendo segmentar cuadrantes, rectificar tableros individuales,
asociar el texto vectorial a cada celda y organizarlos por tamaño (4x4, 6x6, 9x9).
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np

if TYPE_CHECKING:
    from kenken_cv.grid import Rejilla

OPERADORES: dict[str, str] = {
    "+": "+",
    "-": "-",
    "−": "-",
    "×": "*",
    "x": "*",
    "/": "/",
    "÷": "/",
}

NOMBRE_OP: dict[str, str] = {
    "=": "eq",
    "+": "plus",
    "-": "minus",
    "*": "times",
    "/": "div",
}

PALABRA_XML = re.compile(
    r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]+)</word>'
)


def ruta_por_tamano(destino_raiz: Path, n: int) -> Path:
    """Devuelve la ruta organizada por tamaño: destino_raiz / '{n}x{n}'."""
    return destino_raiz / f"{n}x{n}"


def formatear_nombre_etiqueta(
    prefijo: str,
    ancla: tuple[int, int],
    objetivo: int,
    op: str,
) -> str:
    """Genera el nombre estándar del archivo PNG para un recorte de etiqueta."""
    op_str = NOMBRE_OP.get(op, op)
    return f"{prefijo}_{ancla[0]}{ancla[1]}_{objetivo}{op_str}.png"


def dividir_cuadrantes(
    imagen: np.ndarray,
) -> list[tuple[str, np.ndarray, tuple[int, int, int, int]]]:
    """Divide una imagen en 4 cuadrantes (2x2) para páginas con múltiples acertijos.

    Devuelve lista de tuplas: (nombre_cuadrante, sub_imagen, (y1, y2, x1, x2)).
    """
    alto, ancho = imagen.shape[:2]
    mid_y = alto // 2
    mid_x = ancho // 2

    return [
        ("q1_tl", imagen[:mid_y, :mid_x], (0, mid_y, 0, mid_x)),
        ("q2_tr", imagen[:mid_y, mid_x:], (0, mid_y, mid_x, ancho)),
        ("q3_bl", imagen[mid_y:, :mid_x], (mid_y, alto, 0, mid_x)),
        ("q4_br", imagen[mid_y:, mid_x:], (mid_y, alto, mid_x, ancho)),
    ]


def filtrar_palabras_cuadrante(
    palabras: list[tuple[float, float, float, float, str]],
    bbox_px: tuple[int, int, int, int],
    punto_a_pixel: float = 150.0 / 72.0,
) -> list[tuple[float, float, float, float, str]]:
    """Filtra palabras que caen dentro de un cuadrante y desplaza sus coordenadas."""
    y1, y2, x1, x2 = bbox_px
    shift_x = x1 / punto_a_pixel
    shift_y = y1 / punto_a_pixel

    filtradas: list[tuple[float, float, float, float, str]] = []
    for a, b, c, d, texto in palabras:
        cx_px = ((a + c) / 2.0) * punto_a_pixel
        cy_px = ((b + d) / 2.0) * punto_a_pixel
        if x1 <= cx_px < x2 and y1 <= cy_px < y2:
            filtradas.append((a - shift_x, b - shift_y, c - shift_x, d - shift_y, texto))

    return filtradas


def asociar_etiquetas_celdas(
    palabras: list[tuple[float, float, float, float, str]],
    rejilla: Rejilla,
    n: int,
    punto_a_pixel: float = 150.0 / 72.0,
) -> dict[tuple[int, int], tuple[str, int]]:
    """Mapea palabras vectoriales proyectadas por homografía a cada celda (fila, col)."""
    if not palabras:
        return {}

    lado = rejilla.warp.shape[0]
    paso = lado / float(n)

    puntos = np.array(
        [[[(a + c) / 2.0 * punto_a_pixel, (b + d) / 2.0 * punto_a_pixel]] for a, b, c, d, _ in palabras],
        dtype=np.float32,
    )
    proyectados = cv2.perspectiveTransform(puntos, rejilla.homografia).reshape(-1, 2)

    celdas: dict[tuple[int, int], list[tuple[float, str]]] = defaultdict(list)
    for (x, y), (*_, t) in zip(proyectados, palabras):
        if not (0 <= x < lado and 0 <= y < lado):
            continue
        dentro_y, dentro_x = (y % paso) / paso, (x % paso) / paso
        if dentro_y > 0.55 or dentro_x > 0.85:
            continue
        celdas[(int(y // paso), int(x // paso))].append((x, t))

    verdad: dict[tuple[int, int], tuple[str, int]] = {}
    for celda, trozos in celdas.items():
        ordenados = [t for _, t in sorted(trozos)]
        digitos = "".join(t for t in ordenados if t.isdigit())
        simbolos = [OPERADORES[t] for t in ordenados if t in OPERADORES]
        if digitos:
            verdad[celda] = (simbolos[-1] if simbolos else "=", int(digitos))

    return verdad


def rasterizar_pagina(pdf: Path, pagina: int, dpi: int = 150) -> np.ndarray:
    """Rasteriza la página (1-indexada) a imagen en escala de grises."""
    try:
        import pypdfium2 as pdfium

        doc = pdfium.PdfDocument(str(pdf))
        page = doc[pagina - 1]
        img = page.render(scale=dpi / 72.0).to_pil()
        return np.array(img.convert("L"))
    except ImportError:
        pass

    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        out_base = Path(tmp) / f"pg_{pdf.stem}"
        subprocess.run(
            ["pdftoppm", "-r", str(dpi), "-png", "-f", str(pagina), "-l", str(pagina), str(pdf), str(out_base)],
            check=True,
        )
        pngs = list(Path(tmp).glob("*.png"))
        if pngs:
            return cv2.imread(str(pngs[0]), cv2.IMREAD_GRAYSCALE)
    raise RuntimeError(f"No se pudo rasterizar la página {pagina} de {pdf}")


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

    import subprocess

    xml = subprocess.run(
        ["pdftotext", "-f", str(pagina), "-l", str(pagina), "-bbox", str(pdf), "-"],
        capture_output=True,
        text=True,
    ).stdout
    return [
        (float(a), float(b), float(c), float(d), t.strip())
        for a, b, c, d, t in PALABRA_XML.findall(xml)
        if t.strip() and (t.strip().isdigit() or t.strip() in OPERADORES)
    ]


def procesar_cuadernillo(
    pdf_path: Path,
    destino_raiz: Path,
    paginas: range | None = None,
    dpi: int = 150,
) -> dict[str, int]:
    """Procesa un cuadernillo PDF y guarda los tableros individuales y etiquetas organizados por tamaño."""
    from kenken_cv.cages import particionar
    from kenken_cv.glyphs import recortar_etiqueta
    from kenken_cv.grid import encontrar_rejilla
    from kenken_cv.schema import Cage, Instance

    if paginas is None:
        try:
            import pypdfium2 as pdfium

            doc = pdfium.PdfDocument(str(pdf_path))
            # La última página siempre es el solucionario en KrazyDad
            paginas = range(1, len(doc))
        except Exception:
            paginas = range(1, 9)

    match = re.search(r"INKY_(\d+)", pdf_path.name)
    n = int(match.group(1)) if match else 6
    es_4pp = "_4pp" in pdf_path.name

    dir_tamano = ruta_por_tamano(destino_raiz, n)
    dir_tableros = dir_tamano / "tableros"
    dir_etiquetas = dir_tamano / "etiquetas"
    dir_tableros.mkdir(parents=True, exist_ok=True)
    dir_etiquetas.mkdir(parents=True, exist_ok=True)

    punto_a_pixel = dpi / 72.0
    tot_tableros = 0
    tot_etiquetas = 0

    for pagina in paginas:
        try:
            imagen_gris = rasterizar_pagina(pdf_path, pagina, dpi=dpi)
            palabras = extraer_palabras_pagina(pdf_path, pagina)
        except Exception as e:
            print(f"  {pdf_path.name} p{pagina}: error al leer ({e})")
            continue

        if es_4pp:
            cuadrantes = dividir_cuadrantes(imagen_gris)
        else:
            cuadrantes = [("p", imagen_gris, (0, imagen_gris.shape[0], 0, imagen_gris.shape[1]))]

        for sub_id, sub_img, bbox in cuadrantes:
            if es_4pp:
                palabras_sub = filtrar_palabras_cuadrante(palabras, bbox, punto_a_pixel=punto_a_pixel)
                nombre_base = f"{pdf_path.stem}_p{pagina}_{sub_id}"
            else:
                palabras_sub = palabras
                nombre_base = f"{pdf_path.stem}_p{pagina}"

            try:
                rejilla = encontrar_rejilla(sub_img)
            except Exception:
                continue

            verdad = asociar_etiquetas_celdas(palabras_sub, rejilla, n, punto_a_pixel=punto_a_pixel)
            particion = particionar(rejilla)
            anclas = {min(g) for g in particion.grupos}

            # Guardar imagen individual rectificada del tablero (1000x1000)
            cv2.imwrite(str(dir_tableros / f"{nombre_base}.png"), rejilla.warp)

            # Si todas las jaulas tienen ancla identificada en verdad, guardar JSON de Instance
            jaulas = []
            completo = True
            for grupo in particion.grupos:
                ancla = min(grupo)
                if ancla in verdad:
                    op, target = verdad[ancla]
                    jaulas.append(Cage(cells=tuple(sorted(grupo)), op=op, target=target))
                else:
                    completo = False
                    break

            if completo:
                try:
                    instancia = Instance(size=n, cages=tuple(jaulas))
                    instancia.validate()
                    (dir_tableros / f"{nombre_base}.json").write_text(instancia.to_json(), encoding="utf-8")
                except Exception:
                    pass

            # Guardar recortes de etiquetas
            for ancla in anclas & set(verdad):
                op, target = verdad[ancla]
                recorte = recortar_etiqueta(rejilla, ancla)
                nombre_etiqueta = formatear_nombre_etiqueta(nombre_base, ancla, target, op)
                cv2.imwrite(str(dir_etiquetas / nombre_etiqueta), recorte)
                tot_etiquetas += 1

            tot_tableros += 1

    return {"n": n, "tableros": tot_tableros, "etiquetas": tot_etiquetas}
