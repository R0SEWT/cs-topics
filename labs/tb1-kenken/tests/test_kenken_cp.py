"""Batería en rojo para el modelo CP de la Fase 2.

Los fixtures no se creyeron a ojo: `_soluciones` enumera los 576 cuadrados
latinos 4x4 y filtra por jaulas, sin tocar CP-SAT. Sirve para dos cosas —
comprobar que un puzzle que decimos de solución única la tiene de verdad, y
contrastar el modelo contra algo que no es el modelo. Se queda en n=4 a
propósito: en 6x6 hay 812 millones de cuadrados latinos.
"""

from itertools import permutations
from math import prod

import pytest

from kenken_cp.solver import contar_soluciones, resolver
from kenken_cv.schema import Instance

# --------------------------------------------------------------------------
# Oráculo independiente
# --------------------------------------------------------------------------


def _latinos(n: int):
    perms = list(permutations(range(1, n + 1)))

    def rec(filas: list[tuple[int, ...]]):
        if len(filas) == n:
            yield tuple(filas)
            return
        for p in perms:
            if all(p[c] != f[c] for f in filas for c in range(n)):
                yield from rec(filas + [p])

    yield from rec([])


def _cumple_jaula(rejilla, cage) -> bool:
    v = [rejilla[r][c] for r, c in cage.cells]
    if cage.op == "=":
        return len(v) == 1 and v[0] == cage.target
    if cage.op == "+":
        return sum(v) == cage.target
    if cage.op == "*":
        return prod(v) == cage.target
    if cage.op == "-":
        return len(v) == 2 and abs(v[0] - v[1]) == cage.target
    if cage.op == "/":
        if len(v) != 2:
            return False
        may, men = max(v), min(v)
        return may % men == 0 and may // men == cage.target
    return False


def _soluciones(instancia: Instance) -> list:
    return [
        r for r in _latinos(instancia.size) if all(_cumple_jaula(r, c) for c in instancia.cages)
    ]


def _es_cuadrado_latino(rejilla, n: int) -> bool:
    esperado = set(range(1, n + 1))
    filas_ok = all(set(fila) == esperado for fila in rejilla)
    columnas_ok = all({rejilla[r][c] for r in range(n)} == esperado for c in range(n))
    return filas_ok and columnas_ok


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

# Buscado por enumeración hasta dar con uno que usa las cinco operaciones,
# regala una sola celda y tiene solución única.
UNICO = Instance.from_dict(
    {
        "size": 4,
        "cages": [
            {"cells": [[0, 0], [0, 1], [1, 1]], "op": "*", "target": 2},
            {"cells": [[0, 2]], "op": "=", "target": 3},
            {"cells": [[0, 3], [1, 2], [1, 3]], "op": "+", "target": 11},
            {"cells": [[1, 0], [2, 0], [3, 0]], "op": "*", "target": 24},
            {"cells": [[2, 1], [2, 2]], "op": "-", "target": 3},
            {"cells": [[2, 3], [3, 3]], "op": "/", "target": 2},
            {"cells": [[3, 1], [3, 2]], "op": "*", "target": 6},
        ],
    }
)

SOLUCION_UNICO = ((1, 2, 3, 4), (2, 1, 4, 3), (3, 4, 1, 2), (4, 3, 2, 1))

# Cada fila suma 10, que es lo que suma 1+2+3+4: no restringe nada. Los 576
# cuadrados latinos lo cumplen.
AMBIGUO = Instance.from_dict(
    {
        "size": 4,
        "cages": [
            {"cells": [[r, c] for c in range(4)], "op": "+", "target": 10} for r in range(4)
        ],
    }
)

# Las dieciséis celdas valen 1. Bien formado según validate(), y sin solución.
IMPOSIBLE = Instance.from_dict(
    {
        "size": 4,
        "cages": [
            {"cells": [[r, c]], "op": "=", "target": 1} for r in range(4) for c in range(4)
        ],
    }
)


def _tablero_6x6() -> tuple[Instance, tuple]:
    """Un 6x6 cíclico troceado en parejas horizontales. Comprueba que el modelo
    no está atado a n=4 y que aguanta un tablero del tamaño que usa el TB1."""
    sol = tuple(tuple((r + c) % 6 + 1 for c in range(6)) for r in range(6))
    jaulas, i = [], 0
    for r in range(6):
        for c in (0, 2, 4):
            a, b = sol[r][c], sol[r][c + 1]
            op = ("+", "*", "-")[i % 3]
            objetivo = {"+": a + b, "*": a * b, "-": abs(a - b)}[op]
            jaulas.append({"cells": [[r, c], [r, c + 1]], "op": op, "target": objetivo})
            i += 1
    return Instance.from_dict({"size": 6, "cages": jaulas}), sol


# --------------------------------------------------------------------------
# Los fixtures son lo que decimos que son (esto no necesita el modelo)
# --------------------------------------------------------------------------


def test_los_fixtures_estan_bien_formados():
    for instancia in (UNICO, AMBIGUO, IMPOSIBLE, _tablero_6x6()[0]):
        instancia.validate()


def test_el_fixture_unico_tiene_exactamente_una_solucion():
    assert _soluciones(UNICO) == [SOLUCION_UNICO]


def test_el_fixture_ambiguo_tiene_muchas():
    assert len(_soluciones(AMBIGUO)) == 576


def test_el_fixture_imposible_no_tiene_ninguna():
    assert _soluciones(IMPOSIBLE) == []


# --------------------------------------------------------------------------
# El modelo
# --------------------------------------------------------------------------


def test_resuelve_el_tablero_de_solucion_unica():
    assert resolver(UNICO) == SOLUCION_UNICO


def test_la_solucion_es_un_cuadrado_latino():
    assert _es_cuadrado_latino(resolver(UNICO), 4)


def test_la_solucion_cumple_todas_las_jaulas():
    rejilla = resolver(UNICO)
    for cage in UNICO.cages:
        assert _cumple_jaula(rejilla, cage), f"incumple {cage}"


def test_la_jaula_unaria_fija_su_celda():
    assert resolver(UNICO)[0][2] == 3


@pytest.mark.parametrize("op,objetivo,valores", [("-", 3, {1, 4}), ("/", 2, {2, 4})])
def test_resta_y_division_no_dependen_del_orden_de_las_celdas(op, objetivo, valores):
    """La visión lista las dos celdas en el orden en que recorre el tablero.

    El modelo no puede dar por hecho que la primera es la mayor: `|a-b|` y
    `max/min` son simétricas y así hay que escribirlas.
    """
    # Fila 0 con la jaula bajo prueba; el resto del tablero, libre.
    jaulas = [
        {"cells": [[0, 0], [0, 1]], "op": op, "target": objetivo},
        {"cells": [[0, 2], [0, 3]], "op": "+", "target": 10 - sum(valores)},
    ]
    for r in (1, 2, 3):
        jaulas.append({"cells": [[r, c] for c in range(4)], "op": "+", "target": 10})
    instancia = Instance.from_dict({"size": 4, "cages": jaulas})
    instancia.validate()
    rejilla = resolver(instancia)
    assert rejilla is not None
    assert {rejilla[0][0], rejilla[0][1]} == valores


def test_devuelve_None_cuando_no_hay_solucion():
    assert resolver(IMPOSIBLE) is None


def test_resuelve_un_tablero_6x6():
    instancia, _ = _tablero_6x6()
    rejilla = resolver(instancia)
    assert rejilla is not None
    assert _es_cuadrado_latino(rejilla, 6)
    for cage in instancia.cages:
        assert _cumple_jaula(rejilla, cage), f"incumple {cage}"


def test_resuelve_lo_que_llega_por_el_json_del_contrato():
    """La Fase 3 se reduce a leer un JSON: el modelo entra por ahí."""
    assert resolver(Instance.from_json(UNICO.to_json())) == SOLUCION_UNICO


# --------------------------------------------------------------------------
# Contar soluciones — lo que necesita la reparación guiada por el solver
# --------------------------------------------------------------------------


def test_cuenta_una_sola_en_el_puzzle_bien_planteado():
    assert contar_soluciones(UNICO) == 1


def test_cuenta_ninguna_en_el_imposible():
    assert contar_soluciones(IMPOSIBLE) == 0


def test_detecta_que_el_ambiguo_tiene_mas_de_una():
    assert contar_soluciones(AMBIGUO) >= 2


def test_el_tope_corta_el_recuento():
    """Con 576 soluciones, enumerarlas todas para responder 'más de una' sobra."""
    assert contar_soluciones(AMBIGUO, tope=2) == 2
    assert contar_soluciones(AMBIGUO, tope=5) == 5
