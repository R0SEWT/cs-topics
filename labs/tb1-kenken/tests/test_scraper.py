"""Tests del scraper de KenKen — offline, sin conexión a red.

Cada test usa fixtures HTML locales que simulan las páginas de KrazyDad,
para que la CI corra sin dependencias externas ni pausas de cortesía.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.scrapear_kenken import (
    CATALOGO,
    Cuadernillo,
    descubrir_cuadernillos,
    url_pdf,
)

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Catálogo estático
# ---------------------------------------------------------------------------

def test_el_catalogo_cubre_los_tamanos_del_proyecto():
    """El repo trabaja con 4x4, 5x5, 6x6, 7x7, 8x8 y 9x9."""
    tamanos = {entrada.n for entrada in CATALOGO}
    assert {4, 5, 6, 7, 8, 9} <= tamanos


def test_cada_entrada_del_catalogo_tiene_url_y_tamano_validos():
    for entrada in CATALOGO:
        assert entrada.n >= 3
        assert entrada.slug, "slug vacío"
        assert url_pdf(entrada, libro=1).startswith("https://")


# ---------------------------------------------------------------------------
# Descubrimiento de cuadernillos desde HTML (offline)
# ---------------------------------------------------------------------------

def test_descubre_tres_cuadernillos_6x6():
    html = (FIXTURES / "krazydad_index_6x6.html").read_text(encoding="utf-8")
    libros = descubrir_cuadernillos(html)
    assert len(libros) == 3
    assert all(isinstance(c, Cuadernillo) for c in libros)


def test_los_cuadernillos_descubiertos_conservan_el_orden():
    html = (FIXTURES / "krazydad_index_6x6.html").read_text(encoding="utf-8")
    libros = descubrir_cuadernillos(html)
    nombres = [c.archivo for c in libros]
    assert nombres == [
        "INKY_6H_b001_1pp.pdf",
        "INKY_6H_b002_1pp.pdf",
        "INKY_6H_b003_1pp.pdf",
    ]


def test_descubre_cuadernillos_9x9():
    html = (FIXTURES / "krazydad_index_9x9.html").read_text(encoding="utf-8")
    libros = descubrir_cuadernillos(html)
    assert len(libros) == 2
    assert libros[0].archivo == "INKY_9H_b001_1pp.pdf"


def test_html_sin_enlaces_devuelve_lista_vacia():
    libros = descubrir_cuadernillos("<html><body>nada</body></html>")
    assert libros == []


# ---------------------------------------------------------------------------
# Generación de URLs
# ---------------------------------------------------------------------------

def test_url_pdf_usa_la_base_de_krazydad():
    entrada = CATALOGO[0]
    url = url_pdf(entrada, libro=1)
    assert "krazydad.com/inkies/sfiles/" in url
    assert url.endswith(".pdf")


def test_url_pdf_formatea_el_numero_de_libro_con_tres_digitos():
    entrada = CATALOGO[0]
    assert "b001" in url_pdf(entrada, libro=1)
    assert "b012" in url_pdf(entrada, libro=12)


# ---------------------------------------------------------------------------
# Extracción de tamaño desde el nombre del archivo
# ---------------------------------------------------------------------------

def test_cuadernillo_extrae_tamano_del_nombre():
    c = Cuadernillo(archivo="INKY_6H_b001_1pp.pdf")
    assert c.tamano() == 6


def test_cuadernillo_extrae_tamano_9x9():
    c = Cuadernillo(archivo="INKY_9H_b002_1pp.pdf")
    assert c.tamano() == 9


def test_cuadernillo_extrae_tamano_4x4():
    c = Cuadernillo(archivo="INKY_4H_b001_1pp.pdf")
    assert c.tamano() == 4


def test_cuadernillo_sin_tamano_devuelve_none():
    c = Cuadernillo(archivo="algo_raro.pdf")
    assert c.tamano() is None
