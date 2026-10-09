"""Figura del informe: una foto simulada de un tablero sintético y lo que el sistema devuelve.

Se usa un tablero sintético, no uno de KrazyDad, porque el informe se publica y sus
puzzles no se pueden redistribuir. Se busca la primera semilla cuya lectura coincide con
la verdad y cuya solución es única, para mostrar el camino feliz completo.

Uso: PYTHONPATH=. uv run python scripts/figura_informe.py ../../informe/fig/pipeline.png
"""
from __future__ import annotations

import random, sys, tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from kenken_cp.solver import contar_soluciones, resolver
from kenken_cv.pipeline import leer
from kenken_cv.render import degradar, guardar, random_instance, render


def main() -> None:
    destino = Path(sys.argv[1] if len(sys.argv) > 1 else "pipeline.png")
    for semilla in range(2026, 2126):
        rng = random.Random(semilla)
        verdad, _ = random_instance(6, rng)
        if contar_soluciones(verdad, tope=2) != 1:
            continue
        foto = degradar(render(verdad).convert("RGB"), rng).convert("L")
        with tempfile.TemporaryDirectory() as d:
            ruta = guardar(foto, Path(d) / "foto.png")
            try:
                leida = leer(ruta).instancia
            except Exception:
                continue
        if leida.canonical() != verdad.canonical():
            continue
        resuelto = render(leida, solucion=resolver(leida))
        break
    else:
        sys.exit("ninguna semilla dio una lectura perfecta")
    alto = 600
    a = foto.resize((round(foto.width * alto / foto.height), alto))
    b = resuelto.resize((round(resuelto.width * alto / resuelto.height), alto))
    lienzo = Image.new("L", (a.width + b.width + 60, alto + 60), 255)
    lienzo.paste(a, (0, 60)); lienzo.paste(b, (a.width + 60, 60))
    dib = ImageDraw.Draw(lienzo)
    try:
        f = ImageFont.truetype("DejaVuSans.ttf", 34)
    except OSError:
        f = ImageFont.load_default()
    dib.text((a.width // 2, 28), "(a) entrada", fill=0, font=f, anchor="mm")
    dib.text((a.width + 60 + b.width // 2, 28), "(b) salida", fill=0, font=f, anchor="mm")
    lienzo.save(destino)
    print(f"semilla {semilla} · {len(leida.cages)} jaulas · {destino}")


if __name__ == "__main__":
    main()
