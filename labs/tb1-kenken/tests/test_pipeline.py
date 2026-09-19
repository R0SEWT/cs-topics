import numpy as np
import pytest

from kenken_cv.glyphs import BANCO
from kenken_cv.pipeline import leer
from tests.conftest import tablero


@pytest.mark.parametrize("n", [4, 5, 6])
def test_lee_el_tablero_completo(rng, n):
    instancia, imagen, _ = tablero(rng, n=n, fuente=BANCO[0])
    assert leer(imagen).instancia.canonical() == instancia.canonical()


def test_lee_una_foto_degradada(rng):
    instancia, imagen, _ = tablero(rng, n=5, fuente=BANCO[0], foto=True)
    assert leer(imagen).instancia.canonical() == instancia.canonical()


def test_lo_que_sale_siempre_es_una_instancia_valida(rng):
    """El pipeline valida antes de devolver: nunca entrega basura al solver."""
    instancia, imagen, _ = tablero(rng, n=6, fuente=BANCO[0], foto=True)
    leer(imagen).instancia.validate()


def test_una_imagen_en_blanco_falla_en_vez_de_devolver_algo(rng):
    with pytest.raises(Exception):
        leer(np.full((500, 500), 255, dtype=np.uint8))


def test_la_lectura_expone_la_evidencia_para_auditarla(rng):
    _, imagen, _ = tablero(rng, n=5, fuente=BANCO[0])
    lectura = leer(imagen)
    assert lectura.rejilla.size == 5
    assert lectura.particion.fiable
    assert 0.0 < lectura.confianza <= 1.0
