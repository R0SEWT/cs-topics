"""Tests para el extractor de etiquetas y división de páginas 4pp.

Prueba la lógica de división de cuadrantes, proyección de palabras a celdas
y nomenclatura de archivos de ground truth sin requerir ejecución externa.
"""

from __future__ import annotations

import numpy as np
import pytest

from kenken_cv.extractor import (
    NOMBRE_OP,
    OPERADORES,
    dividir_cuadrantes,
    filtrar_palabras_cuadrante,
    formatear_nombre_etiqueta,
)


def test_dividir_cuadrantes_genera_cuatro_subimagenes_correctas():
    # Imagen de 1000x800 (alto x ancho)
    imagen = np.zeros((1000, 800), dtype=np.uint8)
    cuadrantes = dividir_cuadrantes(imagen)

    assert len(cuadrantes) == 4
    nombres = [c[0] for c in cuadrantes]
    assert nombres == ["q1_tl", "q2_tr", "q3_bl", "q4_br"]

    for nombre, sub_img, (y1, y2, x1, x2) in cuadrantes:
        assert sub_img.shape == (500, 400)
        assert y2 - y1 == 500
        assert x2 - x1 == 400


def test_dividir_cuadrantes_preserva_contenido():
    imagen = np.arange(100, dtype=np.uint8).reshape(10, 10)
    cuadrantes = dividir_cuadrantes(imagen)
    _, tl, _ = cuadrantes[0]
    assert np.array_equal(tl, imagen[:5, :5])


def test_filtrar_palabras_cuadrante_desplaza_coordenadas():
    # Palabras en formato (xMin, yMin, xMax, yMax, texto) en puntos
    # Supongamos escala 1 punto = 1 px para simplicidad
    palabras = [
        (10.0, 10.0, 30.0, 20.0, "12+"),   # en Q1 (x: 0..400, y: 0..500)
        (500.0, 10.0, 520.0, 20.0, "3-"),   # en Q2 (x: 400..800, y: 0..500)
        (10.0, 600.0, 30.0, 620.0, "4/"),   # en Q3 (x: 0..400, y: 500..1000)
    ]
    # Cuadrante Q2: x de 400 a 800, y de 0 a 500
    bbox_q2_px = (0, 500, 400, 800)  # y1, y2, x1, x2
    filtradas = filtrar_palabras_cuadrante(palabras, bbox_q2_px, punto_a_pixel=1.0)

    assert len(filtradas) == 1
    x1, y1, x2, y2, texto = filtradas[0]
    assert texto == "3-"
    # Desplazado respecto al origen de Q2 (x1=400, y1=0)
    assert x1 == 100.0
    assert y1 == 10.0


def test_formatear_nombre_etiqueta_genera_convencion_del_repo():
    nombre = formatear_nombre_etiqueta(
        prefijo="INKY_6H_b001_p1",
        ancla=(0, 2),
        objetivo=12,
        op="+",
    )
    assert nombre == "INKY_6H_b001_p1_02_12plus.png"


def test_formatear_nombre_etiqueta_multiplicacion():
    nombre = formatear_nombre_etiqueta(
        prefijo="INKY_9H_b001_p1_q1",
        ancla=(3, 5),
        objetivo=2400,
        op="*",
    )
    assert nombre == "INKY_9H_b001_p1_q1_35_2400times.png"


def test_operadores_cubren_simbolos_estandar_y_unicode():
    assert OPERADORES["+"] == "+"
    assert OPERADORES["-"] == "-"
    assert OPERADORES["−"] == "-"
    assert OPERADORES["×"] == "*"
    assert OPERADORES["x"] == "*"
    assert OPERADORES["/"] == "/"
    assert OPERADORES["÷"] == "/"
    assert NOMBRE_OP["*"] == "times"
    assert NOMBRE_OP["="] == "eq"


def test_asociar_etiquetas_celdas_asocia_correctamente():
    from unittest.mock import MagicMock
    from kenken_cv.extractor import asociar_etiquetas_celdas

    # Rejilla simulada de 1000x1000 con matriz identidad
    rejilla = MagicMock()
    rejilla.warp = np.zeros((1000, 1000), dtype=np.uint8)
    rejilla.homografia = np.eye(3, dtype=np.float32)

    # En un tablero 4x4 (celda = 250 px = 120 puntos a escala 150/72):
    # Celda (0, 0) va de (0, 0) a (120, 120) puntos
    # Ponemos la palabra "12" y "+" en la esquina superior izquierda de (0, 0):
    palabras = [
        (10.0, 10.0, 30.0, 20.0, "12"),
        (32.0, 10.0, 40.0, 20.0, "+"),
        # Celda (1, 1) va de (120, 120) a (240, 240) puntos
        (130.0, 130.0, 140.0, 140.0, "3"),
        (142.0, 130.0, 150.0, 140.0, "-"),
    ]

    verdad = asociar_etiquetas_celdas(palabras, rejilla, n=4, punto_a_pixel=150.0 / 72.0)

    assert verdad[(0, 0)] == ("+", 12)
    assert verdad[(1, 1)] == ("-", 3)
