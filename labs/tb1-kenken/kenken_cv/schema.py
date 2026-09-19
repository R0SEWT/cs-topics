"""Contrato entre la Fase 1 (visión) y la Fase 2 (Constraint Programming).

La visión produce una `Instancia`; el modelo CP la consume. Nada más cruza esa
frontera. Así ambas fases avanzan en paralelo y la Fase 3 (integración) se
reduce a leer un JSON.

Formato en disco::

    {
      "size": 4,
      "cages": [
        {"cells": [[0, 0], [1, 0]], "op": "-", "target": 3},
        {"cells": [[0, 1]],         "op": "=", "target": 2}
      ]
    }

Las celdas son `[fila, columna]` con origen 0 en la esquina superior izquierda.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal

Op = Literal["+", "-", "*", "/", "="]
OPS: tuple[Op, ...] = ("+", "-", "*", "/", "=")

Cell = tuple[int, int]


class InstanciaInvalida(ValueError):
    """La instancia no describe un KenKen bien formado."""


@dataclass(frozen=True)
class Cage:
    """Una jaula: celdas, operación y número objetivo."""

    cells: tuple[Cell, ...]
    op: Op
    target: int


@dataclass(frozen=True)
class Instance:
    """Un tablero KenKen n x n completo."""

    size: int
    cages: tuple[Cage, ...]

    # -- orden canónico -------------------------------------------------

    def canonical(self) -> "Instance":
        """Misma instancia con jaulas y celdas en orden fijo.

        La visión descubre las jaulas en el orden en que recorre el tablero,
        que no tiene por qué coincidir con el de nadie. Comparar o serializar
        sin canonizar primero produce falsos negativos.
        """
        jaulas = tuple(
            sorted(
                (Cage(cells=tuple(sorted(c.cells)), op=c.op, target=c.target) for c in self.cages),
                key=lambda c: c.cells[0],
            )
        )
        return Instance(size=self.size, cages=jaulas)

    # -- serialización --------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "size": self.size,
            "cages": [
                {"cells": [list(c) for c in cage.cells], "op": cage.op, "target": cage.target}
                for cage in self.cages
            ],
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.canonical().to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict) -> Instance:
        cages = tuple(
            Cage(
                cells=tuple((int(r), int(c)) for r, c in cage["cells"]),
                op=cage["op"],
                target=int(cage["target"]),
            )
            for cage in data["cages"]
        )
        return cls(size=int(data["size"]), cages=cages)

    @classmethod
    def from_json(cls, text: str) -> Instance:
        return cls.from_dict(json.loads(text))

    # -- validación -----------------------------------------------------

    def validate(self) -> None:
        """Comprueba que la instancia sea un KenKen bien formado.

        Es la red de seguridad entre visión y solver: si la Fase 1 se equivoca
        leyendo el tablero, casi siempre rompe una de estas invariantes y el
        fallo se ve aquí, con un mensaje claro, en vez de como un `INFEASIBLE`
        mudo del solver.
        """
        n = self.size
        if n < 1:
            raise InstanciaInvalida(f"tamaño inválido: {n}")

        vistas: dict[Cell, int] = {}
        for i, cage in enumerate(self.cages):
            if cage.op not in OPS:
                raise InstanciaInvalida(f"jaula {i}: operación desconocida {cage.op!r}")
            if not cage.cells:
                raise InstanciaInvalida(f"jaula {i}: sin celdas")

            for cell in cage.cells:
                r, c = cell
                if not (0 <= r < n and 0 <= c < n):
                    raise InstanciaInvalida(f"jaula {i}: celda fuera del tablero {cell}")
                if cell in vistas:
                    raise InstanciaInvalida(
                        f"celda {cell} aparece en las jaulas {vistas[cell]} y {i}"
                    )
                vistas[cell] = i

            if not _es_conexa(cage.cells):
                raise InstanciaInvalida(f"jaula {i}: sus celdas no son contiguas")

            if (cage.op == "=") != (len(cage.cells) == 1):
                raise InstanciaInvalida(
                    f"jaula {i}: '=' corresponde solo a jaulas de una celda"
                )
            if cage.op in ("-", "/") and len(cage.cells) != 2:
                raise InstanciaInvalida(
                    f"jaula {i}: '{cage.op}' solo se define sobre dos celdas"
                )
            if cage.target < 1:
                raise InstanciaInvalida(f"jaula {i}: objetivo inválido {cage.target}")
            if cage.op in ("=", "-") and cage.target > n:
                raise InstanciaInvalida(
                    f"jaula {i}: objetivo {cage.target} inalcanzable con dominio 1..{n}"
                )

        faltan = {(r, c) for r in range(n) for c in range(n)} - set(vistas)
        if faltan:
            raise InstanciaInvalida(
                f"{len(faltan)} celdas sin jaula, p. ej. {sorted(faltan)[0]}"
            )


def _es_conexa(cells: tuple[Cell, ...]) -> bool:
    """¿Las celdas forman una región ortogonalmente contigua?"""
    pendientes = set(cells)
    frontera = [next(iter(pendientes))]
    pendientes.discard(frontera[0])
    while frontera:
        r, c = frontera.pop()
        for vecino in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if vecino in pendientes:
                pendientes.discard(vecino)
                frontera.append(vecino)
    return not pendientes
