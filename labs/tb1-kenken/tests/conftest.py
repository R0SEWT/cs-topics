import random

import numpy as np
import pytest

from kenken_cv.render import degradar, random_instance, render


@pytest.fixture
def rng() -> random.Random:
    """Semilla fija: los tests de visión deben ser reproducibles."""
    return random.Random(2026)


def tablero(rng, n=5, fuente=None, foto=False):
    """Instancia + imagen en escala de grises lista para el pipeline."""
    instancia, solucion = random_instance(n, rng)
    img = render(instancia, fuente=fuente)
    if foto:
        img = degradar(img, rng)
    return instancia, np.array(img.convert("L")), solucion
