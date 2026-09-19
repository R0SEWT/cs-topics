import pytest

from kenken_cv.cages import particionar
from kenken_cv.grid import encontrar_rejilla
from tests.conftest import tablero


@pytest.mark.parametrize("n", [4, 5, 6, 7])
def test_recupera_exactamente_las_jaulas(rng, n):
    instancia, imagen, _ = tablero(rng, n=n)
    particion = particionar(encontrar_rejilla(imagen))
    assert set(particion.grupos) == {c.cells for c in instancia.cages}


@pytest.mark.parametrize("n", [4, 6, 7])
def test_recupera_las_jaulas_en_una_foto(rng, n):
    instancia, imagen, _ = tablero(rng, n=n, foto=True)
    particion = particionar(encontrar_rejilla(imagen))
    assert set(particion.grupos) == {c.cells for c in instancia.cages}


def test_las_dos_modas_de_grosor_quedan_bien_separadas(rng):
    """El margen es lo que avisa de que el umbral fino/grueso es dudoso."""
    _, imagen, _ = tablero(rng, n=6)
    particion = particionar(encontrar_rejilla(imagen))
    assert particion.fiable
    assert particion.margen > 1.8


def test_las_celdas_de_cada_jaula_se_tocan(rng):
    """Una partición con jaulas rotas pasaría el conteo pero no la validación."""
    _, imagen, _ = tablero(rng, n=6, foto=True)
    from kenken_cv.schema import Cage, _es_conexa

    for grupo in particionar(encontrar_rejilla(imagen)).grupos:
        assert _es_conexa(grupo)
