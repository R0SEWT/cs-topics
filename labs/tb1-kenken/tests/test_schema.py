import pytest

from kenken_cv.schema import Cage, Instance, InstanciaInvalida


def instancia_2x2() -> Instance:
    """El KenKen válido más pequeño que ejercita jaulas de 1 y de 2 celdas."""
    return Instance(
        size=2,
        cages=(
            Cage(cells=((0, 0), (1, 0)), op="-", target=1),
            Cage(cells=((0, 1),), op="=", target=1),
            Cage(cells=((1, 1),), op="=", target=2),
        ),
    )


def test_instancia_valida_pasa():
    instancia_2x2().validate()


def test_ida_y_vuelta_por_json_conserva_la_instancia():
    original = instancia_2x2()
    assert Instance.from_json(original.to_json()) == original


def test_celda_repetida_en_dos_jaulas():
    mala = Instance(
        size=2,
        cages=(
            Cage(cells=((0, 0), (1, 0)), op="-", target=1),
            Cage(cells=((0, 0),), op="=", target=1),
            Cage(cells=((0, 1),), op="=", target=1),
            Cage(cells=((1, 1),), op="=", target=2),
        ),
    )
    with pytest.raises(InstanciaInvalida, match="aparece en las jaulas"):
        mala.validate()


def test_celda_sin_jaula():
    mala = Instance(size=2, cages=(Cage(cells=((0, 0),), op="=", target=1),))
    with pytest.raises(InstanciaInvalida, match="sin jaula"):
        mala.validate()


def test_jaula_no_contigua():
    """Dos celdas en diagonal no forman jaula: es el error típico cuando la
    detección de bordes gruesos une regiones que solo se tocan por la esquina."""
    mala = Instance(
        size=2,
        cages=(
            Cage(cells=((0, 0), (1, 1)), op="+", target=3),
            Cage(cells=((0, 1),), op="=", target=1),
            Cage(cells=((1, 0),), op="=", target=2),
        ),
    )
    with pytest.raises(InstanciaInvalida, match="no son contiguas"):
        mala.validate()


def test_resta_sobre_tres_celdas_es_invalida():
    mala = Instance(
        size=2,
        cages=(
            Cage(cells=((0, 0), (0, 1), (1, 0)), op="-", target=1),
            Cage(cells=((1, 1),), op="=", target=2),
        ),
    )
    with pytest.raises(InstanciaInvalida, match="solo se define sobre dos celdas"):
        mala.validate()


def test_jaula_de_una_celda_debe_usar_igual():
    mala = Instance(
        size=2,
        cages=(
            Cage(cells=((0, 0),), op="+", target=1),
            Cage(cells=((0, 1),), op="=", target=2),
            Cage(cells=((1, 0), (1, 1)), op="+", target=3),
        ),
    )
    with pytest.raises(InstanciaInvalida, match="una celda"):
        mala.validate()


def test_objetivo_inalcanzable_en_jaula_de_una_celda():
    """Un 8 leído en un tablero 4x4 es un error de OCR, no un tablero raro."""
    mala = Instance(
        size=2,
        cages=(
            Cage(cells=((0, 0),), op="=", target=8),
            Cage(cells=((0, 1),), op="=", target=1),
            Cage(cells=((1, 0), (1, 1)), op="+", target=3),
        ),
    )
    with pytest.raises(InstanciaInvalida, match="inalcanzable"):
        mala.validate()


def test_celda_fuera_del_tablero():
    mala = Instance(size=2, cages=(Cage(cells=((0, 5),), op="=", target=1),))
    with pytest.raises(InstanciaInvalida, match="fuera del tablero"):
        mala.validate()


def test_canonical_iguala_instancias_que_solo_difieren_en_el_orden():
    """La visión descubre las jaulas en otro orden que el generador; sin
    canonizar, dos descripciones del mismo tablero no se reconocen iguales."""
    a = instancia_2x2()
    b = Instance(size=2, cages=tuple(reversed(a.cages)))
    assert a != b
    assert a.canonical() == b.canonical()


def test_canonical_ordena_tambien_las_celdas_dentro_de_la_jaula():
    desordenada = Instance(
        size=2,
        cages=(
            Cage(cells=((1, 0), (0, 0)), op="-", target=1),
            Cage(cells=((0, 1),), op="=", target=1),
            Cage(cells=((1, 1),), op="=", target=2),
        ),
    )
    assert desordenada.canonical() == instancia_2x2().canonical()
