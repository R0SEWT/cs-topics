"""El nodo de cómputo: la API HTTP que la app del celular usa para resolver una foto."""

from __future__ import annotations

import base64
import io
import random

from fastapi.testclient import TestClient

from kenken_cp.solver import contar_soluciones, resolver
from kenken_cv.render import random_instance, render
from kenken_nodo.servidor import app

cliente = TestClient(app)


def _png_b64(img) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _instancia_unica(n: int):
    """Las instancias aleatorias no garantizan unicidad; un puzzle publicado sí."""
    rng = random.Random(n)
    while True:
        instancia, _ = random_instance(n, rng)
        if contar_soluciones(instancia, tope=2) == 1:
            return instancia


def test_salud_identifica_al_nodo():
    r = cliente.get("/salud")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["ok"] is True and cuerpo["nodo"]


def test_resuelve_un_tablero_limpio():
    instancia = _instancia_unica(5)
    r = cliente.post("/resolver", json={"imagen": _png_b64(render(instancia))})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["estado"] == "resuelto"
    assert cuerpo["n"] == 5
    assert len(cuerpo["jaulas"]) == len(instancia.cages)
    assert [tuple(f) for f in cuerpo["solucion"]] == list(resolver(instancia))
    assert cuerpo["ms"]["vision"] > 0 and cuerpo["ms"]["solver"] >= 0


def test_acepta_data_url():
    instancia = _instancia_unica(4)
    r = cliente.post("/resolver", json={"imagen": "data:image/png;base64," + _png_b64(render(instancia))})
    assert r.json()["estado"] == "resuelto"


def test_una_lectura_con_varias_soluciones_no_se_entrega():
    rng = random.Random(3)
    while True:
        instancia, _ = random_instance(4, rng)
        if contar_soluciones(instancia, tope=2) == 2:
            break
    cuerpo = cliente.post("/resolver", json={"imagen": _png_b64(render(instancia))}).json()
    assert cuerpo["estado"] == "varias"
    assert cuerpo["solucion"] is None and len(cuerpo["jaulas"]) == len(instancia.cages)


def test_una_foto_sin_tablero_lo_dice_en_llano():
    from PIL import Image

    r = cliente.post("/resolver", json={"imagen": _png_b64(Image.new("L", (400, 300), 255))})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["estado"] == "sin_tablero"
    assert cuerpo["solucion"] is None and cuerpo["jaulas"] == []
    assert "tablero" in cuerpo["mensaje"].lower()


def test_imagen_corrupta_es_error_del_cliente():
    r = cliente.post("/resolver", json={"imagen": "esto no es base64 de una imagen"})
    assert r.status_code == 400


def test_una_lectura_sin_solucion_se_repara_si_es_inequivoco(monkeypatch):
    # El caso de la foto de la Fig. 1: los dos 3÷ se leyeron 3+.
    from dataclasses import replace

    import kenken_nodo.servidor as servidor
    from kenken_cv.schema import Instance

    verdad, _ = random_instance(6, random.Random(2026))
    jaulas = tuple(
        replace(c, op="+") if min(c.cells) in {(1, 3), (1, 5)} else c for c in verdad.cages
    )
    leida = Instance(size=6, cages=jaulas)
    real = servidor.leer
    monkeypatch.setattr(servidor, "leer", lambda gris: replace(real(gris), instancia=leida))
    cuerpo = cliente.post("/resolver", json={"imagen": _png_b64(render(verdad))}).json()
    assert cuerpo["estado"] == "reparado"
    assert sorted(tuple(c["celda"]) for c in cuerpo["correcciones"]) == [(1, 3), (1, 5)]
    assert all(c["corregido"]["op"] == "/" for c in cuerpo["correcciones"])
    assert [tuple(f) for f in cuerpo["solucion"]] == list(resolver(verdad))
