import pytest

from kenken_cv.render import etiqueta, latin_square, random_instance
from kenken_cv.schema import Cage


def test_latin_square_no_repite_en_filas_ni_columnas(rng):
    n = 6
    cuadro = latin_square(n, rng)
    esperado = set(range(1, n + 1))
    for fila in cuadro:
        assert set(fila) == esperado
    for col in zip(*cuadro):
        assert set(col) == esperado


@pytest.mark.parametrize("n", [3, 4, 5, 6, 7, 9])
def test_las_instancias_generadas_son_validas(rng, n):
    instancia, _ = random_instance(n, rng)
    instancia.validate()


def test_los_objetivos_concuerdan_con_la_solucion(rng):
    """Si el objetivo no sale de los valores reales, el puzzle no tiene solución
    y todo lo que midamos encima carece de sentido."""
    import math

    instancia, solucion = random_instance(6, rng)
    for jaula in instancia.cages:
        valores = sorted((solucion[r][c] for r, c in jaula.cells), reverse=True)
        if jaula.op == "=":
            assert valores == [jaula.target]
        elif jaula.op == "+":
            assert sum(valores) == jaula.target
        elif jaula.op == "*":
            assert math.prod(valores) == jaula.target
        elif jaula.op == "-":
            assert valores[0] - valores[1] == jaula.target
        elif jaula.op == "/":
            assert valores[0] == jaula.target * valores[1]


def test_la_etiqueta_usa_los_glifos_impresos_no_ascii():
    assert etiqueta(Cage(cells=((0, 0), (0, 1)), op="*", target=12)) == "12×"
    assert etiqueta(Cage(cells=((0, 0), (0, 1)), op="/", target=3) ) == "3÷"
    assert etiqueta(Cage(cells=((0, 0),), op="=", target=4)) == "4"
