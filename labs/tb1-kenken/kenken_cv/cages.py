"""Detección de jaulas: qué celdas están separadas por un borde grueso.

Es el paso crítico del KenKen y el que no tienen los demás acertijos. La idea
es puramente geométrica, sin aprendizaje: una vez rectificado el tablero se
sabe *dónde* está cada arista interior, así que basta medir su **grosor** y
partir la población en dos. Los grosores son bimodales por construcción (el
puzzle se imprime con dos anchos de pluma), y el umbral sale de Otsu sobre esa
población, con el marco exterior como referencia de "grueso".
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from kenken_cv.grid import Rejilla
from kenken_cv.schema import Cell


@dataclass(frozen=True)
class Particion:
    """Celdas agrupadas en jaulas, más la evidencia de cómo se decidió."""

    grupos: tuple[tuple[Cell, ...], ...]
    umbral: float
    margen: float  # separación entre las dos modas; <1.35 es terreno dudoso

    @property
    def fiable(self) -> bool:
        return self.margen >= 1.35


def _binaria(rejilla: Rejilla) -> np.ndarray:
    suave = cv2.GaussianBlur(rejilla.warp, (3, 3), 0)
    return cv2.adaptiveThreshold(
        suave, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 8
    )


def _grosor_en(binaria: np.ndarray, centro: int, recorrido: range, vertical: bool) -> float:
    """Grosor mediano de la línea en `centro`, medido a lo largo de `recorrido`.

    Para cada muestra se busca el trazo de tinta más cercano al centro previsto
    y se mide su ancho. La mediana descarta los cruces con otras líneas y con
    los dígitos.

    Lo que se busca es el trazo *más cercano*, no el que cubre el centro exacto.
    Exigir tinta justo en el píxel predicho funcionaba con tableros generados
    —ahí la línea cae donde se la espera— pero en un tablero real la rectifica-
    ción deja un error de unos píxeles, la arista salía con grosor cero, se
    tomaba por línea fina y dos jaulas distintas acababan fundidas en una.
    """
    medidas = []
    radio = 14
    tolerancia = 6  # cuánto puede desviarse la línea del centro previsto
    for t in recorrido:
        if vertical:
            franja = binaria[t, max(0, centro - radio) : centro + radio + 1]
        else:
            franja = binaria[max(0, centro - radio) : centro + radio + 1, t]
        medio = min(radio, centro)
        if franja.size <= medio:
            medidas.append(0.0)
            continue
        tinta = np.flatnonzero(franja)
        if not tinta.size:
            medidas.append(0.0)
            continue
        cerca = tinta[np.argmin(np.abs(tinta - medio))]
        if abs(int(cerca) - medio) > tolerancia:
            medidas.append(0.0)
            continue
        i = j = int(cerca)
        while i > 0 and franja[i - 1]:
            i -= 1
        while j + 1 < franja.size and franja[j + 1]:
            j += 1
        medidas.append(float(j - i + 1))
    return float(np.median(medidas)) if medidas else 0.0


def _otsu_1d(valores: np.ndarray) -> float:
    """Umbral de Otsu sobre una muestra pequeña de valores continuos."""
    v = np.sort(valores)
    if v[0] == v[-1]:
        return float(v[0])
    mejor, corte = -1.0, float(v[0])
    for k in range(1, len(v)):
        if v[k] == v[k - 1]:
            continue
        a, b = v[:k], v[k:]
        peso = len(a) * len(b) * (a.mean() - b.mean()) ** 2
        if peso > mejor:
            mejor, corte = peso, float((v[k] + v[k - 1]) / 2)
    return corte


def medir_aristas(rejilla: Rejilla) -> tuple[dict[tuple[Cell, Cell], float], float]:
    """Grosor de cada arista interior y del marco exterior (referencia)."""
    binaria = _binaria(rejilla)
    n, xs, ys = rejilla.size, rejilla.xs, rejilla.ys
    aristas: dict[tuple[Cell, Cell], float] = {}

    def tramo(a: int, b: int) -> range:
        """Franja central de una celda: evita las esquinas, donde las líneas se cruzan."""
        pad = max(3, int(0.28 * (b - a)))
        return range(a + pad, b - pad)

    for r in range(n):
        for c in range(n - 1):  # aristas verticales
            g = _grosor_en(binaria, xs[c + 1], tramo(ys[r], ys[r + 1]), vertical=True)
            aristas[((r, c), (r, c + 1))] = g
    for r in range(n - 1):  # aristas horizontales
        for c in range(n):
            g = _grosor_en(binaria, ys[r + 1], tramo(xs[c], xs[c + 1]), vertical=False)
            aristas[((r, c), (r + 1, c))] = g

    marco = [
        _grosor_en(binaria, xs[0], tramo(ys[r], ys[r + 1]), vertical=True) for r in range(n)
    ] + [
        _grosor_en(binaria, ys[0], tramo(xs[c], xs[c + 1]), vertical=False) for c in range(n)
    ]
    return aristas, float(np.median(marco))


def particionar(rejilla: Rejilla) -> Particion:
    """Agrupa las celdas que no están separadas por un borde grueso."""
    aristas, marco = medir_aristas(rejilla)
    valores = np.array(list(aristas.values()), dtype=np.float32)

    umbral = _otsu_1d(valores)
    gruesas = valores[valores > umbral]
    finas = valores[valores <= umbral]

    # Si Otsu parte una población que en realidad es unimodal (tablero de una
    # sola jaula, o todas las celdas sueltas), el marco exterior desempata.
    if len(gruesas) == 0 or len(finas) == 0:
        umbral = 0.6 * marco
        gruesas = valores[valores > umbral]
        finas = valores[valores <= umbral]

    margen = (
        float(gruesas.mean() / finas.mean()) if len(gruesas) and len(finas) else float("inf")
    )

    padre: dict[Cell, Cell] = {}

    def raiz(x: Cell) -> Cell:
        padre.setdefault(x, x)
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    def unir(a: Cell, b: Cell) -> None:
        ra, rb = raiz(a), raiz(b)
        if ra != rb:
            padre[ra] = rb

    n = rejilla.size
    for r in range(n):
        for c in range(n):
            raiz((r, c))
    for (a, b), grosor in aristas.items():
        if grosor <= umbral:  # línea fina => misma jaula
            unir(a, b)

    grupos: dict[Cell, list[Cell]] = {}
    for celda in sorted(padre):
        grupos.setdefault(raiz(celda), []).append(celda)

    return Particion(
        grupos=tuple(tuple(sorted(g)) for g in grupos.values()),
        umbral=float(umbral),
        margen=margen,
    )
