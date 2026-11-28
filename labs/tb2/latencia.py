"""
latencia.py — S6: tiempo de decisión por turno de nuestro equipo, en un solo proceso.

Correr con la máquina libre (sin otras partidas ni compilaciones), porque mide tiempo de pared:

    uv run --no-project --with pygame python latencia.py [--semillas 1-5]

Escribe reports/latencia.json con el resumen por semilla (media, p95, p99, máximo). El umbral del
enunciado es 40 ms por turno para todo el equipo.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics as st

import arena

UMBRAL_MS = 40.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--semillas", default="1-5")
    ap.add_argument("--copias", type=int, default=1, help="cuántos de los 4 equipos son el nuestro (1 o 4)")
    args = ap.parse_args()

    asignacion = {k: ("equipoA.py" if (i < args.copias) else "base") for i, k in enumerate(arena.LETRAS)}
    tmp = arena.preparar(asignacion)
    turnos = []
    try:
        for s in arena._rango(args.semillas):
            r = arena.partida(tmp, s)   # se usa la medición interna del propio equipo (perf_counter)
            turnos.append((s, r["equipos"]["A"]["interno"]["ms"], r["ticks"]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    carga = os.getloadavg()[0]
    print(f"carga de la máquina (1 min): {carga:.1f}  -> {'OK' if carga < 2 else 'ALTA: repetir con la máquina libre'}")
    print(f"{'semilla':>8}{'ticks':>7}{'media':>8}{'p95':>8}{'p99':>8}{'max':>8}")
    for s, ms, ticks in turnos:
        print(f"{s:>8}{ticks:>7}{ms['media']:>8.2f}{ms['p95']:>8.2f}{ms['p99']:>8.2f}{ms['max']:>8.2f}")
    peor = max(ms["max"] for _, ms, _ in turnos)
    print(f"peor turno: {peor:.2f} ms ({'cumple' if peor < UMBRAL_MS else 'NO cumple'} el umbral de {UMBRAL_MS:.0f} ms)")
    destino = arena.AQUI / "reports" / "latencia.json"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(json.dumps({
        "carga_1min": carga, "copias": args.copias,
        "por_semilla": [{"semilla": s, "ticks": t, **ms} for s, ms, t in turnos],
        "resumen": {
            "media": st.mean(ms["media"] for _, ms, _ in turnos),
            "p95": max(ms["p95"] for _, ms, _ in turnos),
            "p99": max(ms["p99"] for _, ms, _ in turnos),
            "max": peor,
        },
    }, indent=1))
    print(f"guardado en {destino}")


if __name__ == "__main__":
    main()
