"""Lectura de la etiqueta de cada jaula: '12+', '3÷', '5'.

El reconocimiento es por correlación normalizada contra plantillas de glifos
renderizadas en varias tipografías. Se probó añadir rasgos estructurales
(número de huecos cerrados, tramos de tinta en la banda central) como
bonificación para separar '3' de '8' y '+' de '÷': medido con
``scripts/evaluar.py``, **empeoraba** la precisión de 99.4% a 95.4% porque
agrupaba 0/6/9 y la correlación no los volvía a separar. Lo que sí resolvió la
confusión fue ampliar el banco tipográfico. Para un puzzle impreso basta y no arrastra dependencias del
sistema (no hace falta instalar Tesseract).

Detalle que importa: el '÷' se imprime como tres manchas sueltas (punto, barra,
punto). Un etiquetado de componentes conexas lo partiría en tres caracteres, así
que antes de clasificar se reagrupan las componentes que se solapan en x.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from kenken_cv.grid import Rejilla
from kenken_cv.schema import Cell, Op

BANCO: tuple[str, ...] = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Regular.ttf",
)

CARACTERES = "0123456789+-−×x÷/"
# El glifo impreso -> la operación del contrato. Cada editor imprime los
# suyos: KrazyDad usa '/' y '-' ASCII donde otros usan '÷' y '−', y hay
# quien pone 'x' latina en vez de '×'. Todas las variantes deben leerse.
OPERACION: dict[str, Op] = {
    "+": "+",
    "-": "-",
    "−": "-",
    "×": "*",
    "x": "*",
    "÷": "/",
    "/": "/",
}
LADO_PLANTILLA = 28


class EtiquetaIlegible(ValueError):
    """No se pudo leer la etiqueta de una jaula."""


@lru_cache(maxsize=4)
def _plantillas(fuentes: tuple[str, ...]) -> dict[str, list[np.ndarray]]:
    """Renderiza cada carácter en cada fuente y lo normaliza a un patch fijo."""
    banco: dict[str, list[np.ndarray]] = {c: [] for c in CARACTERES}
    for ruta in fuentes:
        tipo = ImageFont.truetype(ruta, size=64)
        for ch in CARACTERES:
            lienzo = Image.new("L", (128, 128), 0)
            ImageDraw.Draw(lienzo).text((64, 64), ch, fill=255, font=tipo, anchor="mm")
            a = np.array(lienzo)
            ys, xs = np.nonzero(a)
            if not len(xs):
                continue
            recorte = a[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
            banco[ch].append(_normalizar(recorte))
    return banco


def _normalizar(patch: np.ndarray) -> np.ndarray:
    """Lleva un glifo a un cuadrado fijo conservando su proporción."""
    h, w = patch.shape
    escala = (LADO_PLANTILLA - 6) / max(h, w)
    nuevo = cv2.resize(
        patch, (max(1, int(w * escala)), max(1, int(h * escala))), interpolation=cv2.INTER_AREA
    )
    lienzo = np.zeros((LADO_PLANTILLA, LADO_PLANTILLA), dtype=np.uint8)
    y0 = (LADO_PLANTILLA - nuevo.shape[0]) // 2
    x0 = (LADO_PLANTILLA - nuevo.shape[1]) // 2
    lienzo[y0 : y0 + nuevo.shape[0], x0 : x0 + nuevo.shape[1]] = nuevo
    return lienzo.astype(np.float32) / 255.0


def _correlacion(a: np.ndarray, b: np.ndarray) -> float:
    """Correlación normalizada entre dos patches ya centrados."""
    x, y = a.ravel() - a.mean(), b.ravel() - b.mean()
    d = float(np.linalg.norm(x) * np.linalg.norm(y))
    return float(x @ y / d) if d else 0.0


def clasificar(patch: np.ndarray, fuentes: tuple[str, ...]) -> tuple[str, float]:
    """Devuelve el carácter más parecido y su puntuación."""
    objetivo = _normalizar(patch)
    mejor, puntos = "", -1.0
    for ch, muestras in _plantillas(fuentes).items():
        for plantilla in muestras:
            s = _correlacion(objetivo, plantilla)
            if s > puntos:
                mejor, puntos = ch, s
    return mejor, puntos


def _agrupar(cajas: list[tuple[int, int, int, int]]) -> list[list[int]]:
    """Une componentes apiladas verticalmente (el caso del '÷')."""
    orden = sorted(range(len(cajas)), key=lambda i: cajas[i][0])
    grupos: list[list[int]] = []
    for i in orden:
        x, _, w, _ = cajas[i]
        for g in grupos:
            gx0 = min(cajas[j][0] for j in g)
            gx1 = max(cajas[j][0] + cajas[j][2] for j in g)
            solape = min(gx1, x + w) - max(gx0, x)
            if solape > 0.5 * min(gx1 - gx0, w):
                g.append(i)
                break
        else:
            grupos.append([i])
    return grupos


def _borde(banda: np.ndarray, tope: int) -> int:
    """Hasta dónde llega la línea de la rejilla, contando desde el margen.

    Se avanza mientras la franja siga siendo oscura: eso es la línea. Al
    aclararse, empieza el interior de la celda.

    El umbral es relativo al contraste de la propia banda, no un valor fijo:
    con un fondo oscurecido por la iluminación, un corte absoluto no se cumple
    nunca y el recorte se comía la celda entera. El `tope` es la segunda red:
    ninguna línea de rejilla ocupa esa fracción de la celda.
    """
    if banda.size == 0:
        return 0
    medias = banda.mean(axis=1)
    umbral = (float(medias.min()) + float(medias.max())) / 2
    for i, m in enumerate(medias[:tope]):
        if m > umbral:
            return i
    return min(tope, len(medias))


def recortar_etiqueta(rejilla: Rejilla, ancla: Cell) -> np.ndarray:
    """Zona superior-izquierda de la celda donde se imprime la etiqueta.

    El margen se mide, no se fija. Era una constante (10% de la celda) y resultó
    ser el mayor error del pipeline entero: cortaba la parte de arriba de los
    dígitos, y un '40' se leía '4U'. Barrido sobre tableros reales, la lectura
    pasaba de 79.9% (4%) a 95.6% (7%) y bajaba a 83.5% (10%) — demasiada
    pendiente para dejarlo en un número elegido a mano. Midiendo el grosor real
    de la línea y dejando un respiro fijo, el recorte se ajusta solo a la
    resolución y al estilo de cada editor.
    """
    r, c = ancla
    x0, x1 = rejilla.xs[c], rejilla.xs[c + 1]
    y0, y1 = rejilla.ys[r], rejilla.ys[r + 1]
    alto, ancho = y1 - y0, x1 - x0
    celda = min(ancho, alto)

    respiro = max(2, int(0.025 * celda))
    tope = max(3, int(0.12 * celda))
    arriba = y0 + _borde(
        rejilla.warp[y0 : y0 + celda // 3, x0 + ancho // 3 : x0 + 2 * ancho // 3], tope
    )
    izquierda = x0 + _borde(
        rejilla.warp[y0 + alto // 3 : y0 + 2 * alto // 3, x0 : x0 + celda // 3].T, tope
    )
    return rejilla.warp[
        arriba + respiro : y0 + int(0.58 * alto),
        izquierda + respiro : x0 + int(0.97 * ancho),
    ]


def leer_etiqueta(
    rejilla: Rejilla, ancla: Cell, fuentes: tuple[str, ...] = BANCO, *, unaria: bool = False
) -> tuple[Op, int, float]:
    """Lee la etiqueta de una jaula del tablero. `unaria` => jaula de una celda."""
    return leer_recorte(
        recortar_etiqueta(rejilla, ancla), fuentes, unaria=unaria, donde=str(ancla)
    )


def leer_recorte(
    recorte: np.ndarray,
    fuentes: tuple[str, ...] = BANCO,
    *,
    unaria: bool = False,
    donde: str = "recorte",
) -> tuple[Op, int, float]:
    """Lee '12+' de un recorte suelto y devuelve ('*', 12, confianza).

    Separado de la geometría a propósito: así la lectura se puede medir contra
    recortes reales sin montar un tablero entero.
    """
    ancla = donde
    if recorte.size == 0:
        raise EtiquetaIlegible(f"celda {ancla}: recorte vacío")

    binaria = cv2.adaptiveThreshold(
        cv2.GaussianBlur(recorte, (3, 3), 0),
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        21,
        8,
    )
    nro, etiquetas, stats, _ = cv2.connectedComponentsWithStats(binaria, 8)
    alto, ancho = recorte.shape
    candidatas = [(i, *stats[i][:5]) for i in range(1, nro)]
    if not candidatas:
        raise EtiquetaIlegible(f"celda {ancla}: no se ve ningún glifo")

    # El umbral de tamaño es *relativo* al glifo mayor. Un mínimo absoluto en
    # altura borraría la barra del '\u2212' y los puntos del '\u00f7', que son
    # bajos por naturaleza; este criterio solo descarta el ruido del binarizado.
    area_max = max(c[5] for c in candidatas)
    cajas, mascaras = [], []
    for i, x, y, w, h, area in candidatas:
        if h > 0.95 * alto or w > 0.6 * ancho:
            continue  # resto de una línea de la rejilla
        if x + w >= ancho - 1:
            # Toca el borde derecho: es la línea vertical de la celda vecina,
            # que colándose se leía como un '1' ('4×' salía '41×'). Ningún
            # glifo de la etiqueta llega ahí, porque la etiqueta empieza a la
            # izquierda. Con esto el recorte puede ser ancho sin pagarlo, y
            # caben las etiquetas de cuatro cifras ('2400×') que antes se
            # quedaban sin operador.
            continue
        if area < max(8, 0.06 * area_max):
            continue  # mota del umbral adaptativo
        cajas.append((x, y, w, h))
        mascaras.append((etiquetas == i).astype(np.uint8) * 255)
    if not cajas:
        raise EtiquetaIlegible(f"celda {ancla}: no se ve ningún glifo")

    texto, confianzas = "", []
    for grupo in _agrupar(cajas):
        x0 = min(cajas[j][0] for j in grupo)
        y0 = min(cajas[j][1] for j in grupo)
        x1 = max(cajas[j][0] + cajas[j][2] for j in grupo)
        y1 = max(cajas[j][1] + cajas[j][3] for j in grupo)
        junto = np.zeros_like(mascaras[0])
        for j in grupo:
            junto = np.maximum(junto, mascaras[j])
        ch, s = clasificar(junto[y0:y1, x0:x1], fuentes)
        texto += ch
        confianzas.append(s)

    digitos = "".join(ch for ch in texto if ch.isdigit())
    simbolos = [ch for ch in texto if ch in OPERACION]
    if not digitos:
        raise EtiquetaIlegible(f"celda {ancla}: leí {texto!r}, sin dígitos")

    confianza = float(np.mean(confianzas))
    if unaria:
        return "=", int(digitos), confianza
    if not simbolos:
        raise EtiquetaIlegible(f"celda {ancla}: leí {texto!r}, falta la operación")
    return OPERACION[simbolos[-1]], int(digitos), confianza
