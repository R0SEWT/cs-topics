"""Generador sintético de tableros KenKen.

Cumple dos funciones:

1. **Ground truth para los tests.** Cada imagen viene con la `Instance` que la
   originó, así la precisión del pipeline se mide contra la verdad y no contra
   lo que uno cree ver.
2. **Mitad del dataset del entregable.** El enunciado pide >=10 imágenes en
   condiciones distintas, "versiones digitales e impresas". `degradar()` cubre
   las digitales simulando foto: perspectiva, iluminación desigual, ruido y
   desenfoque.
"""

from __future__ import annotations

import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from kenken_cv.schema import Cage, Cell, Instance

# Fuentes con las que se *dibujan* tableros de prueba. Deliberadamente incluye
# tipografías que NO están en el banco de plantillas de `glyphs.BANCO`, para que
# la evaluación pueda medir qué pasa con una fuente nunca vista.
FUENTES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf",
)

# Glifos tal y como los imprime un KenKen real (no ASCII).
GLIFO = {"+": "+", "-": "−", "*": "×", "/": "÷"}


def latin_square(n: int, rng: random.Random) -> list[list[int]]:
    """Cuadrado latino n x n aleatorio (base cíclica + permutaciones)."""
    base = [[(i + j) % n + 1 for j in range(n)] for i in range(n)]
    filas = list(range(n))
    cols = list(range(n))
    simbolos = list(range(1, n + 1))
    rng.shuffle(filas)
    rng.shuffle(cols)
    rng.shuffle(simbolos)
    mapa = {v: simbolos[v - 1] for v in range(1, n + 1)}
    return [[mapa[base[i][j]] for j in cols] for i in filas]


def _particionar(n: int, rng: random.Random, max_celdas: int = 4) -> list[list[Cell]]:
    """Reparte el tablero en jaulas contiguas de tamaño aleatorio."""
    libres = {(r, c) for r in range(n) for c in range(n)}
    jaulas: list[list[Cell]] = []
    while libres:
        inicio = rng.choice(sorted(libres))
        libres.discard(inicio)
        jaula = [inicio]
        # Tamaños pequeños son mucho más frecuentes en un KenKen real.
        objetivo = rng.choices(range(1, max_celdas + 1), weights=(3, 5, 3, 1))[0]
        while len(jaula) < objetivo:
            vecinos = [
                v
                for r, c in jaula
                for v in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1))
                if v in libres
            ]
            if not vecinos:
                break
            elegido = rng.choice(sorted(set(vecinos)))
            libres.discard(elegido)
            jaula.append(elegido)
        jaulas.append(sorted(jaula))
    return jaulas


def _operacion(valores: list[int], rng: random.Random) -> tuple[str, int]:
    """Elige operación y objetivo coherentes con los valores de la jaula."""
    if len(valores) == 1:
        return "=", valores[0]
    if len(valores) == 2:
        a, b = max(valores), min(valores)
        opciones = [("-", a - b), ("+", a + b), ("*", a * b)]
        if b and a % b == 0:
            opciones.append(("/", a // b))
        # La resta y la división son las que obligan a reificar; pesan más.
        pesos = [4 if op in ("-", "/") else 1 for op, _ in opciones]
        return rng.choices(opciones, weights=pesos)[0]
    if rng.random() < 0.75:
        return "+", sum(valores)
    return "*", math.prod(valores)


def random_instance(n: int, rng: random.Random | None = None) -> tuple[Instance, list[list[int]]]:
    """Devuelve una instancia válida y el cuadrado latino que la generó."""
    rng = rng or random.Random()
    solucion = latin_square(n, rng)
    jaulas = []
    for celdas in _particionar(n, rng):
        valores = [solucion[r][c] for r, c in celdas]
        op, objetivo = _operacion(valores, rng)
        jaulas.append(Cage(cells=tuple(celdas), op=op, target=objetivo))
    instancia = Instance(size=n, cages=tuple(jaulas))
    instancia.validate()
    return instancia, solucion


def etiqueta(cage: Cage) -> str:
    """Texto impreso en la esquina de la jaula: '12+', '3÷' o '5'."""
    if cage.op == "=":
        return str(cage.target)
    return f"{cage.target}{GLIFO[cage.op]}"


def _ancla(cage: Cage) -> Cell:
    """Celda donde se imprime la etiqueta: la superior-izquierda de la jaula."""
    return min(cage.cells)


def render(
    instancia: Instance,
    *,
    celda: int = 96,
    margen: int = 28,
    grosor_fino: int = 2,
    grosor_grueso: int = 7,
    fuente: str | None = None,
    solucion: list[list[int]] | None = None,
) -> Image.Image:
    """Dibuja el tablero. `solucion` rellena los dígitos (para depurar)."""
    n = instancia.size
    lado = n * celda + 2 * margen
    img = Image.new("L", (lado, lado), 255)
    dib = ImageDraw.Draw(img)

    def xy(r: int, c: int) -> tuple[int, int]:
        return margen + c * celda, margen + r * celda

    # Rejilla fina completa.
    for i in range(n + 1):
        p = margen + i * celda
        dib.line([(margen, p), (lado - margen, p)], fill=0, width=grosor_fino)
        dib.line([(p, margen), (p, lado - margen)], fill=0, width=grosor_fino)

    # Bordes gruesos: contorno exterior y fronteras entre jaulas.
    de_jaula = {cell: i for i, cage in enumerate(instancia.cages) for cell in cage.cells}
    for r in range(n):
        for c in range(n):
            x, y = xy(r, c)
            if c + 1 < n and de_jaula[(r, c)] != de_jaula[(r, c + 1)]:
                dib.line([(x + celda, y), (x + celda, y + celda)], fill=0, width=grosor_grueso)
            if r + 1 < n and de_jaula[(r, c)] != de_jaula[(r + 1, c)]:
                dib.line([(x, y + celda), (x + celda, y + celda)], fill=0, width=grosor_grueso)
    dib.rectangle(
        [margen, margen, lado - margen, lado - margen], outline=0, width=grosor_grueso
    )

    tipo = ImageFont.truetype(fuente or FUENTES[0], size=max(14, celda // 4))
    grande = ImageFont.truetype(fuente or FUENTES[0], size=celda // 2)
    for cage in instancia.cages:
        r, c = _ancla(cage)
        x, y = xy(r, c)
        dib.text((x + grosor_grueso + 4, y + grosor_grueso + 2), etiqueta(cage), fill=0, font=tipo)

    if solucion is not None:
        for r in range(n):
            for c in range(n):
                x, y = xy(r, c)
                dib.text(
                    (x + celda // 2, y + celda // 2),
                    str(solucion[r][c]),
                    fill=90,
                    font=grande,
                    anchor="mm",
                )
    return img


def degradar(
    img: Image.Image,
    rng: random.Random,
    *,
    perspectiva: float = 0.05,
    rotacion: float = 4.0,
    desenfoque: float = 1.2,
    ruido: float = 8.0,
    iluminacion: float = 0.35,
) -> Image.Image:
    """Simula una foto: perspectiva, giro, iluminación desigual, ruido y blur.

    Todos los parámetros son la *cota* del efecto; cada llamada sortea su
    intensidad dentro de ella. Sirve para medir robustez con la verdad conocida.
    """
    import cv2

    a = np.array(img.convert("L"), dtype=np.uint8)
    h, w = a.shape
    # NumPy necesita su propio generador; `random.Random` no sortea gaussianas.
    npr = np.random.default_rng(rng.getrandbits(32))

    # Fondo claro alrededor para que el giro no recorte el tablero.
    pad = int(0.18 * max(h, w))
    a = cv2.copyMakeBorder(a, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=248)
    h, w = a.shape

    # Homografía: giro suave + desplazamiento aleatorio de las cuatro esquinas.
    ang = math.radians(rng.uniform(-rotacion, rotacion))
    cen = (w / 2, h / 2)
    rot = cv2.getRotationMatrix2D(cen, math.degrees(ang), 1.0)
    a = cv2.warpAffine(a, rot, (w, h), borderValue=248)

    d = perspectiva * min(h, w)
    origen = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    destino = np.float32(
        [[p[0] + rng.uniform(-d, d), p[1] + rng.uniform(-d, d)] for p in origen]
    )
    a = cv2.warpPerspective(
        a, cv2.getPerspectiveTransform(origen, destino), (w, h), borderValue=248
    )

    # Iluminación desigual: gradiente lineal en una dirección arbitraria.
    if iluminacion > 0:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        theta = rng.uniform(0, 2 * math.pi)
        campo = (math.cos(theta) * xx + math.sin(theta) * yy) / max(h, w)
        campo = 1.0 - iluminacion * (campo - campo.min()) / (np.ptp(campo) + 1e-6)
        a = np.clip(a.astype(np.float32) * campo, 0, 255).astype(np.uint8)

    if desenfoque > 0:
        s = rng.uniform(0.4, desenfoque)
        k = max(3, int(s * 4) | 1)
        a = cv2.GaussianBlur(a, (k, k), s)

    if ruido > 0:
        a = np.clip(
            a.astype(np.float32) + npr.normal(0, rng.uniform(ruido / 3, ruido), a.shape),
            0,
            255,
        ).astype(np.uint8)

    return Image.fromarray(a)


def guardar(img: Image.Image, destino: str | Path) -> Path:
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    img.save(destino)
    return destino
