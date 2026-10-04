"""Extractor de etiquetas y partición de páginas para tableros KenKen reales.

Soporta cuadernillos de 1 por página (_1pp) y de 4 por página (_4pp),
permitiendo segmentar cuadrantes y asociar el texto vectorial a cada celda.
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
