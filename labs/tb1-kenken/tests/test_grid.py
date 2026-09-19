import numpy as np
import pytest

from kenken_cv.grid import TableroNoEncontrado, encontrar_rejilla
from tests.conftest import tablero


@pytest.mark.parametrize("n", [4, 5, 6, 7, 9])
def test_deduce_el_tamano_del_tablero(rng, n):
    _, imagen, _ = tablero(rng, n=n)
    assert encontrar_rejilla(imagen).size == n


@pytest.mark.parametrize("n", [4, 6, 7])
def test_deduce_el_tamano_en_una_foto_torcida(rng, n):
    _, imagen, _ = tablero(rng, n=n, foto=True)
    assert encontrar_rejilla(imagen).size == n


def test_las_lineas_quedan_repartidas_de_forma_regular(rng):
    """Tras rectificar, las líneas deben estar casi equiespaciadas; si no, la
    homografía salió mal y todo lo que se mida encima estará desplazado."""
    _, imagen, _ = tablero(rng, n=6, foto=True)
    rejilla = encontrar_rejilla(imagen)
    huecos = np.diff(rejilla.xs)
    assert huecos.std() / huecos.mean() < 0.06


def test_una_imagen_sin_tablero_no_se_inventa_una_rejilla():
    with pytest.raises(TableroNoEncontrado):
        encontrar_rejilla(np.full((400, 400), 255, dtype=np.uint8))
