"""Localización del tablero, corrección de perspectiva y rejilla.

Salida de este módulo: una imagen rectificada del tablero más las posiciones
exactas de las líneas de la rejilla. Todo lo posterior (jaulas, etiquetas)
trabaja sobre esas coordenadas, nunca sobre la foto original.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

LADO = 900  # lado en píxeles del tablero rectificado


@dataclass(frozen=True)
class Rejilla:
    """Tablero rectificado y las líneas que lo dividen."""

    warp: np.ndarray          # imagen en gris, LADO x LADO
    xs: tuple[int, ...]       # centros de las n+1 líneas verticales
    ys: tuple[int, ...]       # centros de las n+1 líneas horizontales
    homografia: np.ndarray    # para proyectar la solución sobre la foto original

    @property
    def size(self) -> int:
        return len(self.xs) - 1


class TableroNoEncontrado(RuntimeError):
    """No se pudo aislar un cuadrilátero que parezca un tablero."""


def _binarizar(gris: np.ndarray) -> np.ndarray:
    """Umbral adaptativo: la tinta queda en blanco y aguanta luz desigual."""
    suave = cv2.GaussianBlur(gris, (5, 5), 0)
    return cv2.adaptiveThreshold(
        suave, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 10
    )


def _ordenar_esquinas(pts: np.ndarray) -> np.ndarray:
    """Ordena cuatro puntos como TL, TR, BR, BL."""
    pts = pts.reshape(4, 2).astype(np.float32)
    suma = pts.sum(axis=1)
    dif = np.diff(pts, axis=1).ravel()
    return np.float32(
        [pts[np.argmin(suma)], pts[np.argmin(dif)], pts[np.argmax(suma)], pts[np.argmax(dif)]]
    )


def rectificar(imagen: np.ndarray, lado: int = LADO) -> tuple[np.ndarray, np.ndarray]:
    """Recorta el tablero y lo endereza a un cuadrado `lado` x `lado`."""
    gris = imagen if imagen.ndim == 2 else cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    binaria = _binarizar(gris)
    # Cerrar huecos para que el marco exterior salga como un contorno único.
    binaria = cv2.morphologyEx(binaria, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))

    contornos, _ = cv2.findContours(binaria, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contornos:
        raise TableroNoEncontrado("la imagen no tiene contornos")

    mejor = max(contornos, key=cv2.contourArea)
    if cv2.contourArea(mejor) < 0.05 * gris.size:
        raise TableroNoEncontrado("el contorno mayor es demasiado pequeño para ser un tablero")

    aprox = cv2.approxPolyDP(mejor, 0.02 * cv2.arcLength(mejor, True), True)
    if len(aprox) != 4:
        # Un borde partido por la iluminación deja de ser un cuadrilátero limpio;
        # el rectángulo de área mínima es una aproximación suficiente.
        aprox = cv2.boxPoints(cv2.minAreaRect(mejor))

    origen = _ordenar_esquinas(np.array(aprox, dtype=np.float32))
    destino = np.float32([[0, 0], [lado, 0], [lado, lado], [0, lado]])
    h = cv2.getPerspectiveTransform(origen, destino)
    return cv2.warpPerspective(gris, h, (lado, lado)), h


def _tramos(perfil: np.ndarray, umbral: float) -> list[tuple[int, int]]:
    """Intervalos contiguos donde el perfil supera el umbral."""
    activo = perfil > umbral
    tramos, inicio = [], None
    for i, v in enumerate(activo):
        if v and inicio is None:
            inicio = i
        elif not v and inicio is not None:
            tramos.append((inicio, i))
            inicio = None
    if inicio is not None:
        tramos.append((inicio, len(activo)))
    return tramos


def _perfil(mascara: np.ndarray, eje: int) -> np.ndarray:
    return mascara.sum(axis=eje).astype(np.float32) / 255.0


def _puntuar(perfil: np.ndarray, n: int, lado: int) -> float:
    """Tinta de la línea MÁS DÉBIL que predice una rejilla de n celdas.

    No se exige que cada línea cruce el tablero: en un KenKen impreso la línea
    fina se interrumpe allí donde una jaula la atraviesa, y un sesgo de medio
    grado la trocea en tramos a alturas distintas. Lo que sí se mantiene es la
    periodicidad.

    Se mide el mínimo y no la media a propósito. Promediar convierte la
    elección de n en un concurso entre medias, que se decide por márgenes de
    un 10% y se equivoca; el mínimo responde a la única pregunta que importa:
    *¿existe de verdad cada una de las líneas que este n predice?* Medido sobre
    tableros reales, el n correcto deja su línea más floja en ~29% del ancho,
    mientras que cualquier n equivocado cae a cero exacto, porque alguna de sus
    líneas no está. La ventana se estrecha con n, y eso es lo que impide que un
    n mayor cuele ventanas sobre espacio en blanco.
    """
    paso = lado / n
    ventana = max(3, int(0.28 * paso))
    picos = []
    for i in range(n + 1):
        centro = int(round(i * paso))
        a = max(0, centro - ventana)
        b = min(len(perfil), centro + ventana + 1)
        picos.append(float(perfil[a:b].max()) if b > a else 0.0)
    return float(min(picos))


def _posiciones(perfil: np.ndarray, n: int, lado: int) -> tuple[int, ...]:
    """Centro real de cada línea, refinado dentro de su ventana."""
    paso = lado / n
    ventana = max(3, int(0.28 * paso))
    centros = []
    for i in range(n + 1):
        centro = int(round(i * paso))
        a = max(0, centro - ventana)
        b = min(len(perfil), centro + ventana + 1)
        trozo = perfil[a:b]
        fuertes = np.flatnonzero(trozo >= 0.9 * trozo.max()) if trozo.size else np.array([0])
        centros.append(int(a + fuertes.mean()))
    return tuple(centros)


# Una línea real, por comida que esté, deja bastante más que esto; una línea
# inexistente deja cero. El umbral vive en la tierra de nadie entre ambas.
MINIMO_LINEA = 0.12


def _elegir_n(perfiles: tuple[np.ndarray, ...], lado: int, maximo: int = 12) -> int:
    """Mayor tamaño de tablero cuyas líneas están TODAS presentes en ambos ejes.

    Se toma el mayor y no el de mejor puntuación porque los divisores del n
    correcto también superan la prueba: en un tablero de 6, una rejilla de 3
    cae sobre líneas reales (la mitad de las suyas). Son explicaciones válidas
    pero incompletas, y la completa es siempre la más fina.
    """
    umbral = MINIMO_LINEA * lado
    validos = [
        n
        for n in range(3, maximo + 1)
        if min(_puntuar(p, n, lado) for p in perfiles) >= umbral
    ]
    if not validos:
        raise TableroNoEncontrado("ninguna rejilla regular explica las líneas encontradas")
    return max(validos)


def encontrar_rejilla(imagen: np.ndarray, lado: int = LADO) -> Rejilla:
    """Rectifica el tablero y localiza sus líneas. Deduce n de cuántas hay."""
    warp, h = rectificar(imagen, lado)
    binaria = _binarizar(warp)

    # Aislar trazos largos: así los dígitos no se confunden con líneas.
    largo = max(12, lado // 15)
    verticales = cv2.morphologyEx(
        binaria, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, largo))
    )
    horizontales = cv2.morphologyEx(
        binaria, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (largo, 1))
    )

    px = _perfil(verticales, eje=0)
    py = _perfil(horizontales, eje=1)
    if px.max() < 0.3 * lado or py.max() < 0.3 * lado:
        raise TableroNoEncontrado("no se ven líneas de rejilla tras rectificar")

    n = _elegir_n((px, py), lado)
    return Rejilla(
        warp=warp,
        xs=_posiciones(px, n, lado),
        ys=_posiciones(py, n, lado),
        homografia=h,
    )
