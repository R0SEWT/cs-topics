"""Fase 1 completa: imagen de un KenKen -> `Instance` lista para el solver."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

from kenken_cv.cages import Particion, particionar
from kenken_cv.glyphs import EtiquetaIlegible, leer_etiqueta
from kenken_cv.grid import Rejilla, encontrar_rejilla
from kenken_cv.glyphs import BANCO
from kenken_cv.schema import Cage, Instance

# El banco de plantillas vive en `glyphs`. `scripts/evaluar.py` renderiza
# tableros con fuentes de dentro y de fuera de él para medir generalización.
FUENTES_PLANTILLA: tuple[str, ...] = BANCO


@dataclass
class Lectura:
    """Resultado de la Fase 1, con la evidencia para poder auditarlo."""

    instancia: Instance
    rejilla: Rejilla
    particion: Particion
    confianza: float
    avisos: list[str] = field(default_factory=list)


def leer(
    imagen: np.ndarray | str | Path,
    *,
    fuentes: tuple[str, ...] = FUENTES_PLANTILLA,
) -> Lectura:
    """Lee un tablero. Lanza si la imagen no da para una instancia válida."""
    if isinstance(imagen, (str, Path)):
        cargada = cv2.imread(str(imagen), cv2.IMREAD_GRAYSCALE)
        if cargada is None:
            raise FileNotFoundError(f"no pude abrir {imagen}")
        imagen = cargada

    rejilla = encontrar_rejilla(imagen)
    particion = particionar(rejilla)
    avisos: list[str] = []
    if not particion.fiable:
        avisos.append(
            f"separación fino/grueso de solo {particion.margen:.2f}x: "
            "las jaulas pueden estar mal cortadas"
        )

    jaulas, confianzas = [], []
    for grupo in particion.grupos:
        op, objetivo, conf = leer_etiqueta(
            rejilla, min(grupo), fuentes, unaria=len(grupo) == 1
        )
        jaulas.append(Cage(cells=tuple(grupo), op=op, target=objetivo))
        confianzas.append(conf)

    instancia = Instance(size=rejilla.size, cages=tuple(jaulas))
    instancia.validate()  # la red de seguridad antes de pasar al solver
    return Lectura(
        instancia=instancia,
        rejilla=rejilla,
        particion=particion,
        confianza=float(np.min(confianzas)) if confianzas else 0.0,
        avisos=avisos,
    )
