"""Genera la mitad digital del dataset que pide el entregable.

El enunciado exige >=10 imágenes "en distintas condiciones (diferente
iluminación, ángulos ligeros, versiones digitales e impresas)". Este script
cubre las **digitales**: varía tamaño de tablero, tipografía y grado de
degradación, y deja junto a cada imagen su ground truth en JSON.

Las **impresas** hay que hacerlas a mano: imprimir `limpio/*.png`, fotografiar
con el móvil y guardar en `dataset/impresas/` con su JSON copiado del sintético
correspondiente. Sin ese tramo, la métrica de robustez no dice nada sobre papel
real, que es justo lo que el profesor va a probar.

Uso: ``PYTHONPATH=. uv run python scripts/generar_dataset.py [n] [destino]``
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

from kenken_cv.render import FUENTES, degradar, guardar, random_instance, render

# Cada receta es una condición distinta, no una repetición con otra semilla.
RECETAS = (
    ("limpio",            dict()),
    ("perspectiva_suave", dict(perspectiva=0.03, rotacion=2, desenfoque=0.6, ruido=4, iluminacion=0.15)),
    ("perspectiva_fuerte",dict(perspectiva=0.09, rotacion=8, desenfoque=1.0, ruido=6, iluminacion=0.25)),
    ("luz_desigual",      dict(perspectiva=0.03, rotacion=3, desenfoque=0.8, ruido=5, iluminacion=0.55)),
    ("desenfocado",       dict(perspectiva=0.04, rotacion=3, desenfoque=2.2, ruido=6, iluminacion=0.2)),
    ("ruido_alto",        dict(perspectiva=0.04, rotacion=3, desenfoque=0.8, ruido=18, iluminacion=0.2)),
)


def generar(cantidad: int = 12, destino: str = "dataset", semilla: int = 2026) -> None:
    raiz = Path(destino)
    rng = random.Random(semilla)
    for i in range(cantidad):
        nombre, ajustes = RECETAS[i % len(RECETAS)]
        n = (4, 5, 6, 7, 9)[i % 5]
        fuente = FUENTES[i % len(FUENTES)]
        instancia, _ = random_instance(n, rng)
        imagen = render(instancia, fuente=fuente)
        if ajustes:
            imagen = degradar(imagen, rng, **ajustes)

        base = raiz / f"{i:02d}_{nombre}_n{n}"
        guardar(imagen, base.with_suffix(".png"))
        base.with_suffix(".json").write_text(instancia.to_json(), encoding="utf-8")
        print(f"  {base.with_suffix('.png')}  n={n}  {Path(fuente).stem}")

    (raiz / "impresas").mkdir(parents=True, exist_ok=True)
    print(f"\n{cantidad} imágenes digitales en {raiz}/")
    print(f"Falta la parte impresa: fotografía tableros en papel y déjalos en {raiz}/impresas/")


if __name__ == "__main__":
    generar(
        int(sys.argv[1]) if len(sys.argv) > 1 else 12,
        sys.argv[2] if len(sys.argv) > 2 else "dataset",
    )
