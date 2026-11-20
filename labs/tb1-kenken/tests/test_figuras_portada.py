"""Las figuras de la portada no pueden esconder una solución errónea.

Hoy ningún tablero termina en una (es la cifra «0 de 22»), pero las figuras se regeneran
desde los datos: si un día aparece una, tiene que cortar la generación, nunca dibujarse
como «pide otra foto».
"""
from __future__ import annotations

import pytest

from scripts.figuras_portada import TEMAS, destino, tableros


def fila(lectura: str, reparacion: str | None = None) -> dict:
    f = {"id": f"{lectura}-{reparacion}", "n": 4, "lectura": lectura}
    if reparacion is not None:
        f["reparacion"] = reparacion
    return f


@pytest.mark.parametrize(("f", "esperado"), [
    (fila("bien"), "bien"),
    (fila("rechazado"), "rechazado"),
    (fila("sin_solucion", "bien"), "reparado"),
    (fila("sin_solucion", "abstiene"), "abstiene"),
    (fila("sin_solucion", "error"), "erroneo"),
    (fila("error_silencioso"), "erroneo"),
    (fila("varias"), "varias"),
])
def test_destino_de_cada_tablero(f, esperado):
    assert destino(f) == esperado


def test_un_estado_desconocido_no_se_adivina():
    with pytest.raises(KeyError):
        destino(fila("otro"))


@pytest.mark.parametrize("mala", [fila("error_silencioso"), fila("sin_solucion", "error")])
def test_la_figura_de_tableros_no_dibuja_un_error_como_abstencion(mala):
    with pytest.raises(SystemExit, match="errónea"):
        tableros(TEMAS["claro"], [fila("bien"), mala])
