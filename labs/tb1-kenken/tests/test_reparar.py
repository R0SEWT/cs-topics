"""Reparación guiada por el solver: si lo leído no tiene solución, probar las confusiones
típicas de la visión y quedarse con la corrección mínima que deja una solución única."""

from __future__ import annotations

import random
from dataclasses import replace

from kenken_cp.reparar import reparar
from kenken_cp.solver import contar_soluciones, resolver
from kenken_cv.render import random_instance
from kenken_cv.schema import Instance


def _unica(n: int, semilla: int) -> Instance:
    rng = random.Random(semilla)
    while True:
        inst, _ = random_instance(n, rng)
        if contar_soluciones(inst, tope=2) == 1:
            return inst


def _cambiar(inst: Instance, cambios: dict) -> Instance:
    """cambios: celda ancla -> (op, objetivo) leído mal."""
    jaulas = []
    for c in inst.cages:
        if min(c.cells) in cambios:
            op, t = cambios[min(c.cells)]
            c = replace(c, op=op, target=t)
        jaulas.append(c)
    return Instance(size=inst.size, cages=tuple(jaulas))


def test_dos_divisiones_leidas_como_suma():
    # El tablero de la Fig. 1 del informe: la foto leyó los dos 3÷ como 3+.
    verdad, _ = random_instance(6, random.Random(2026))
    leida = _cambiar(verdad, {(1, 3): ("+", 3), (1, 5): ("+", 3)})
    assert resolver(leida) is None
    r = reparar(leida)
    assert r is not None
    assert r.instancia.canonical() == verdad.canonical()
    assert sorted(c.celda for c in r.correcciones) == [(1, 3), (1, 5)]
    assert r.solucion == resolver(verdad)


def test_un_cinco_leido_como_seis():
    for semilla in range(50):
        verdad = _unica(5, semilla)
        sumas = [c for c in verdad.cages if c.op == "+" and "5" in str(c.target)]
        if not sumas:
            continue
        jaula = sumas[0]
        leida = _cambiar(verdad, {min(jaula.cells): ("+", int(str(jaula.target).replace("5", "6", 1)))})
        if resolver(leida) is not None:
            continue  # el error no rompe el tablero: no hay nada que reparar
        r = reparar(leida)
        assert r is not None and r.instancia.canonical() == verdad.canonical()
        assert len(r.correcciones) == 1
        return
    raise AssertionError("no se encontró un caso de prueba")


def test_no_toca_una_lectura_que_ya_tiene_solucion():
    verdad = _unica(5, 1)
    assert reparar(verdad) is None


def test_no_inventa_si_hace_falta_cambiar_demasiado():
    verdad = _unica(4, 2)
    sumas = [c for c in verdad.cages if c.op == "+"]
    # Objetivos imposibles en todas las jaulas de suma: ninguna confusión plausible lo arregla.
    leida = _cambiar(verdad, {min(c.cells): ("+", 1) for c in sumas})
    assert reparar(leida, max_cambios=1) is None
