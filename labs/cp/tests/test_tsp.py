"""Especificación del TP5 (materials/week-05/TP5.pdf): TSP con CP-SAT.

Cada tarea se resuelve en models/tsp.py. El oráculo es fuerza bruta sobre las
(n-1)! rutas que salen de 0, así que las instancias se quedan chicas.
"""

import itertools
import random

import pytest

from models.tsp import solve_tsp_circuit_basic, solve_tsp_mtz_cp, solve_tsp_precedence

# Asimétrica a propósito: el sentido del recorrido importa. Su óptimo libre
# visita la ciudad 4 antes que la 2, así que exigir 2 -> 4 lo encarece.
SEIS_CIUDADES = [
    [0, 5, 19, 28, 26, 25],
    [3, 0, 9, 4, 16, 25],
    [15, 16, 0, 21, 13, 26],
    [7, 4, 16, 0, 1, 29],
    [27, 13, 14, 20, 0, 25],
    [25, 1, 23, 15, 9, 0],
]


def aleatoria(n: int, seed: int) -> list[list[int]]:
    rng = random.Random(seed)
    return [[0 if i == j else rng.randint(1, 100) for j in range(n)] for i in range(n)]


def costo(ruta: list[int], dist: list[list[int]]) -> int:
    return sum(dist[a][b] for a, b in itertools.pairwise(ruta))


def fuerza_bruta(dist: list[list[int]], antes: tuple[int, int] | None = None) -> int:
    n = len(dist)
    rutas = ([0, *perm, 0] for perm in itertools.permutations(range(1, n)))
    if antes:
        a, b = antes
        rutas = (r for r in rutas if r.index(a) < r.index(b))
    return min(costo(r, dist) for r in rutas)


def assert_ciclo_hamiltoniano(ruta: list[int], n: int) -> None:
    assert ruta[0] == ruta[-1] == 0, "la ruta sale de 0 y vuelve a 0"
    assert sorted(ruta[:-1]) == list(range(n)), "cada ciudad aparece exactamente una vez"


# --- Tareas 1 y 2: dos modelos distintos, mismo contrato -----------------------

MODELOS = pytest.mark.parametrize(
    "solve",
    [solve_tsp_circuit_basic, solve_tsp_mtz_cp],
    ids=["tarea1-circuit", "tarea2-mtz"],
)


@MODELOS
def test_devuelve_un_ciclo_hamiltoniano(solve):
    _, ruta = solve(SEIS_CIUDADES)
    assert_ciclo_hamiltoniano(ruta, len(SEIS_CIUDADES))


@MODELOS
def test_el_costo_reportado_es_el_de_la_ruta(solve):
    total, ruta = solve(SEIS_CIUDADES)
    assert total == costo(ruta, SEIS_CIUDADES)


@MODELOS
def test_encuentra_el_optimo(solve):
    total, _ = solve(SEIS_CIUDADES)
    assert total == fuerza_bruta(SEIS_CIUDADES)


@MODELOS
@pytest.mark.parametrize("seed", [0, 1, 2])
def test_encuentra_el_optimo_en_instancias_aleatorias(solve, seed):
    dist = aleatoria(7, seed)
    total, ruta = solve(dist)
    assert_ciclo_hamiltoniano(ruta, 7)
    assert total == costo(ruta, dist) == fuerza_bruta(dist)


# --- Tarea 3: circuito + precedencia --------------------------------------------


def test_la_instancia_obliga_a_reordenar():
    """Sin esto, la Tarea 3 podría pasar sin imponer nada."""
    assert fuerza_bruta(SEIS_CIUDADES, antes=(2, 4)) > fuerza_bruta(SEIS_CIUDADES)


@pytest.mark.parametrize("antes, despues", [(2, 4), (4, 2), (5, 1)])
def test_respeta_la_precedencia(antes, despues):
    total, ruta = solve_tsp_precedence(SEIS_CIUDADES, antes=antes, despues=despues)
    assert_ciclo_hamiltoniano(ruta, len(SEIS_CIUDADES))
    assert ruta.index(antes) < ruta.index(despues), f"{antes} debía ir antes que {despues}"
    assert total == costo(ruta, SEIS_CIUDADES)
    assert total == fuerza_bruta(SEIS_CIUDADES, antes=(antes, despues))
