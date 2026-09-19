"""Modelo CP-SAT de KenKen. **Los cuerpos los escribe el equipo, no la IA.**

El README de este lab declara que el andamiaje de visión se hizo con asistencia
de IA y que el modelo de Constraint Programming no. Aquí están las firmas que
fijan los tests (`tests/test_kenken_cp.py`) y nada más: rellenarlas es el
trabajo de la Fase 2.

Lo que hay que modelar, sobre `Instance` (ver `kenken_cv/schema.py`):

* Una variable entera por celda con dominio ``1..n``.
* Cuadrado latino: `AllDifferent` por cada fila y por cada columna.
* Una restricción por jaula, según `cage.op`:
    - ``=``  jaula de una celda: la celda vale `target`.
    - ``+``  la suma de sus celdas es `target`.
    - ``*``  el producto de sus celdas es `target`.
    - ``-``  exactamente dos celdas, ``|a - b| == target``.
    - ``/``  exactamente dos celdas, ``max/min == target`` y la división exacta.

`-` y `/` son simétricas: el orden en que la visión listó las dos celdas no
significa nada, así que el modelo no puede suponer que la primera es la mayor.

`models/nqueens.py` de `labs/cp` es la referencia de estilo del repo:
modelo -> restricciones -> solver -> solución.
"""

from __future__ import annotations

from kenken_cv.schema import Instance

# Una rejilla resuelta: `rejilla[fila][columna]` es el valor de esa celda.
Rejilla = tuple[tuple[int, ...], ...]


def resolver(instancia: Instance) -> Rejilla | None:
    """Resuelve el tablero. Devuelve la rejilla, o None si no tiene solución."""
    raise NotImplementedError("Fase 2: lo escribe el equipo")


def contar_soluciones(instancia: Instance, tope: int = 2) -> int:
    """Cuántas soluciones tiene, dejando de contar al llegar a `tope`.

    El tope no es una optimización menor: un tablero poco restringido tiene
    cientos de soluciones y enumerarlas todas no aporta nada. Lo que interesa
    casi siempre es distinguir "una" de "más de una" — que es lo que necesita
    la reparación guiada por el solver de cst-7p6, donde entre los candidatos
    que proponen los motores de OCR se elige el que deja el puzzle con
    solución única.
    """
    raise NotImplementedError("Fase 2: lo escribe el equipo")
