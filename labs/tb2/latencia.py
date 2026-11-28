"""
latencia.py — S6: tiempo de decisión por turno de nuestro equipo, en un solo proceso.

Correr con la máquina libre (sin otras partidas ni compilaciones), porque mide tiempo de pared:

    uv run --no-project --with pygame python latencia.py [--semillas 1-5]

Cada semilla se corre REPETICIONES veces. La simulación es determinista, así que el trabajo del
equipo es idéntico en las repeticiones: lo que cambia entre ellas es el ruido del sistema operativo
(otros procesos que le quitan la CPU a mitad de un turno). Por semilla se reporta la repetición
mediana (según su turno más lento) y se guardan los máximos de todas, sin descartar ninguno.

Escribe reports/latencia.json. El umbral del enunciado es 40 ms por turno para todo el equipo.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics as st

import arena

UMBRAL_MS = 40.0
REPETICIONES = 3


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
            corridas = []
            for _ in range(REPETICIONES):
                r = arena.partida(tmp, s)   # medición interna del propio equipo (perf_counter)
                corridas.append((r["equipos"]["A"]["interno"]["ms"], r["ticks"]))
            corridas.sort(key=lambda c: c[0]["max"])
            ms, ticks = corridas[len(corridas) // 2]
            ms = dict(ms, maximos=[c[0]["max"] for c in corridas])
            turnos.append((s, ms, ticks))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    carga = os.getloadavg()[0]
    print(f"carga de la máquina (1 min): {carga:.1f}  -> {'OK' if carga < 2 else 'ALTA: repetir con la máquina libre'}")
    print(f"{'semilla':>8}{'ticks':>7}{'media':>8}{'p95':>8}{'p99':>8}{'max':>8}")
    for s, ms, ticks in turnos:
        print(f"{s:>8}{ticks:>7}{ms['media']:>8.2f}{ms['p95']:>8.2f}{ms['p99']:>8.2f}{ms['max']:>8.2f}")
    peor = max(ms["max"] for _, ms, _ in turnos)
    peor_bruto = max(max(ms["maximos"]) for _, ms, _ in turnos)
    print(f"peor turno (repetición mediana): {peor:.2f} ms "
          f"({'cumple' if peor < UMBRAL_MS else 'NO cumple'} el umbral de {UMBRAL_MS:.0f} ms)")
    print(f"peor turno entre todas las repeticiones: {peor_bruto:.2f} ms; máximos por semilla: "
          + "; ".join(f"{s}: {ms['maximos']}" for s, ms, _ in turnos))
    destino = arena.AQUI / "reports" / "latencia.json"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(json.dumps({
        "carga_1min": carga, "copias": args.copias, "repeticiones": REPETICIONES,
        "por_semilla": [{"semilla": s, "ticks": t, **ms} for s, ms, t in turnos],
        "resumen": {
            "media": st.mean(ms["media"] for _, ms, _ in turnos),
            "p95": max(ms["p95"] for _, ms, _ in turnos),
            "p99": max(ms["p99"] for _, ms, _ in turnos),
            "max": peor,
            "max_bruto": peor_bruto,
        },
    }, indent=1))
    print(f"guardado en {destino}")


if __name__ == "__main__":
    main()
