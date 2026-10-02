"""Las fuentes se resuelven por nombre, no por ruta fija de una distro."""

from pathlib import Path

import pytest

from kenken_cv.fuentes import FuenteAusente, resolver, resolver_todas


def test_resuelve_una_fuente_que_el_sistema_tiene():
    ruta = Path(resolver("DejaVuSans.ttf"))
    assert ruta.is_absolute()
    assert ruta.exists()
    assert ruta.name == "DejaVuSans.ttf"


def test_la_fuente_que_falta_se_nombra_en_el_error():
    with pytest.raises(FuenteAusente) as err:
        resolver("NoExisteEstaTipografia-Regular.ttf")
    assert "NoExisteEstaTipografia-Regular.ttf" in str(err.value)


def test_el_error_sugiere_el_paquete_que_la_trae():
    with pytest.raises(FuenteAusente) as err:
        resolver_todas(("DejaVuSans.ttf", "DejaVuNoExisteEstaVariante.ttf"))
    mensaje = str(err.value)
    # Se queja de la que falta y no de la que está.
    assert "DejaVuNoExisteEstaVariante.ttf" in mensaje
    assert "DejaVuSans.ttf" not in mensaje
    assert "dnf" in mensaje and "apt" in mensaje


def test_resolver_todas_conserva_el_orden():
    nombres = ("LiberationSans-Regular.ttf", "DejaVuSans.ttf")
    assert tuple(Path(r).name for r in resolver_todas(nombres)) == nombres


def test_el_banco_y_las_fuentes_de_render_son_rutas_reales():
    """Regresión: estaban fijadas a /usr/share/fonts/truetype/... (Debian)."""
    from kenken_cv.glyphs import BANCO
    from kenken_cv.render import FUENTES

    for ruta in (*BANCO, *FUENTES):
        assert Path(ruta).exists(), ruta


def test_render_usa_tipografias_fuera_del_banco():
    """`scripts/evaluar.py` separa 'plantilla' de 'holdout' comparando rutas.

    Si la resolución dejara las dos listas en formas distintas de la misma
    ruta, o si el banco se comiera todas las fuentes, esa medida de
    generalización se quedaría sin holdout y nadie se enteraría.
    """
    from kenken_cv.glyphs import BANCO
    from kenken_cv.render import FUENTES

    assert set(FUENTES) - set(BANCO), "no queda ninguna fuente nunca vista"
    assert set(FUENTES) & set(BANCO), "ninguna fuente comparte forma con el banco"
