"""
arena.py — corre partidas del TB2 sin ventana y mide.

No modifica el simulador del profesor: lo importa tal cual desde
materials/evaluaciones/tb2/ y arma en una carpeta temporal los equipoA..D.py
que se le pidan.

Uso (desde labs/tb2):
    uv run --no-project --with pygame python arena.py                    # nuestro equipo en A, base en B, C, D
    uv run --no-project --with pygame python arena.py --rotar            # nuestro equipo pasa por las 4 esquinas
    uv run --no-project --with pygame python arena.py A=equipoA.py B=equipoA.py --semillas 1-20
    uv run --no-project --with pygame python arena.py --json reports/base.json

Cada equipo se indica como LETRA=archivo.py (o LETRA=base). Lo que no se indique es la base.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import shutil
import statistics
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

AQUI = Path(__file__).resolve().parent
MOTOR = AQUI.parent.parent / "materials" / "evaluaciones" / "tb2"
LETRAS = ("A", "B", "C", "D")
LIMITE_SIM_S = 360.0   # si nadie recoge el hielo que queda la partida no termina: se corta a los 6 minutos


def _rango(texto: str) -> List[int]:
    if "-" in texto:
        a, b = texto.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(x) for x in texto.split(",")]


def _percentil(orden: List[float], p: float) -> float:
    if not orden:
        return 0.0
    return orden[min(len(orden) - 1, int(p * len(orden)))]


def preparar(asignacion: Dict[str, str], ajustes: Optional[Dict[str, str]] = None) -> Path:
    """Carpeta temporal con el motor y un equipoX.py por letra asignada.

    `ajustes` reescribe constantes de módulo (líneas `NOMBRE = valor`) en la copia de nuestros
    equipos: así se prueba una variante sin tocar el archivo de la entrega.
    """
    tmp = Path(tempfile.mkdtemp(prefix="tb2-arena-"))
    for nombre in ("simulador.py", "equipo_base.py"):
        shutil.copy(MOTOR / nombre, tmp / nombre)
    for letra, origen in asignacion.items():
        if origen == "base":
            continue
        texto = (AQUI / origen).read_text()
        for nombre, valor in (ajustes or {}).items():
            texto, n = re.subn(r"(?m)^%s = [^#\n]*" % re.escape(nombre), "%s = %s  " % (nombre, valor), texto)
            if n != 1:
                raise SystemExit(f"ajuste {nombre}: se esperaba 1 línea en {origen}, hay {n}")
        (tmp / f"equipo{letra}.py").write_text(texto)
    return tmp


def partida(tmp: Path, semilla: int, tormentas_extra: int = 0, cobertura_de: str = "",
            flota_doble: bool = False) -> Dict[str, Any]:
    """Una partida completa. Devuelve una fila de métricas por equipo.

    tormentas_extra  escenario de alta tormenta: suma N tormentas de movimiento libre desde el inicio.
    cobertura_de     letra del equipo al que se le mide qué fracción de su cuadrante ha visto.
    flota_doble      100 unidades por equipo (60/30/10), como dice el enunciado: se suman a las 50
                     que crea el simulador otras 50 con los mismos tipos, proporción y zona de
                     aparición. Sirve para medir la latencia con 400 unidades.
    """
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    for mod in [m for m in sys.modules if m.startswith("equipo") or m == "simulador"]:
        del sys.modules[mod]
    if str(tmp) not in sys.path:
        sys.path.insert(0, str(tmp))
    random.seed(semilla)
    import simulador as S  # noqa: PLC0415

    sim = S.SimuladorMarte()
    if flota_doble:
        for letra in LETRAS:
            bx, by = S.BASES_EQUIPO[letra]
            for tipo, prefijo, n, radio in (("rover", "rover", 30, 4), ("dron_explorador", "expl", 15, 3),
                                            ("dron_recarga", "rec", 5, 1)):
                for i in range(n, 2 * n):
                    pos = (int(S.clamp(bx + random.randint(-radio, radio), 0, S.GRID_W - 1)),
                           int(S.clamp(by + random.randint(-radio, radio), 0, S.GRID_H - 1)))
                    paso = S.TICK_DT * (2.0 if tipo == "rover" else 1.0)
                    u = S.UnidadSim(
                        id=f"{letra}_{prefijo}_{i}", equipo=letra, tipo=tipo, pos=pos, prev_pos=pos,
                        capacidad=S.CAPACIDAD_ROVER if tipo == "rover" else 0,
                        carga_recarga=1 if tipo == "dron_recarga" else 0,
                        move_interval=paso, interp_dur=paso,
                    )
                    sim.unidades.append(u)
                    sim.unidades_por_id[u.id] = u
    for i in range(tormentas_extra):
        ang = random.uniform(0, math.tau)
        sim.tormentas.append(S.TormentaSim(
            id=f"X{i}", modo="aleatorio", fx=random.uniform(8, S.GRID_W - 8), fy=random.uniform(8, S.GRID_H - 8),
            vx=math.cos(ang) * 4.5, vy=math.sin(ang) * 4.5,
        ))
    visto = set()
    visto_mapa = set()
    curva: List[List[float]] = []
    curva_mapa: List[List[float]] = []
    if cobertura_de:
        bx, by = S.BASES_EQUIPO[cobertura_de]
        x0, x1 = (0, S.GRID_W // 2) if bx == 0 else (S.GRID_W // 2, S.GRID_W)
        y0, y1 = (0, S.GRID_H // 2) if by == 0 else (S.GRID_H // 2, S.GRID_H)
        area = (x1 - x0) * (y1 - y0)
        radios = {"rover": 5, "dron_explorador": 9, "dron_recarga": 7}
    acumulado = {k: 0.0 for k in LETRAS}
    por_tick: Dict[str, List[float]] = {k: [] for k in LETRAS}
    mensajes = {k: 0 for k in LETRAS}

    for letra, eq in sim.equipos.items():
        original = eq.decidir_unidad

        def envuelto(u, p, a, _o=original, _l=letra):
            t0 = time.perf_counter()
            r = _o(u, p, a)
            acumulado[_l] += time.perf_counter() - t0
            return r

        eq.decidir_unidad = envuelto

    enviar_original = sim.enviar_mensaje_unidad

    def enviar(emisor, dest_id, asunto, datos):
        ok = enviar_original(emisor, dest_id, asunto, datos)
        if ok:
            mensajes[emisor.equipo] += 1
        return ok

    sim.enviar_mensaje_unidad = enviar

    gasto: Dict[str, Dict[str, float]] = {k: {} for k in LETRAS}
    consumir_original = sim._consumir_bateria

    def consumir(u, cantidad):
        antes = u.bateria
        consumir_original(u, cantidad)
        causa = {0.5: "mensajes", 1.0: "paso", 5.0: "paso_tormenta", 3.0: "pulso_tormenta"}.get(cantidad, "otro")
        clave = u.tipo.replace("dron_", "") + ":" + causa
        gasto[u.equipo][clave] = gasto[u.equipo].get(clave, 0.0) + (antes - u.bateria)

    sim._consumir_bateria = consumir

    tick_original = sim._tick_logico

    def tick():
        for k in acumulado:
            acumulado[k] = 0.0
        tick_original()
        for k in acumulado:
            por_tick[k].append(acumulado[k] * 1000.0)
        if cobertura_de and sim.tick_count % 5 == 0:
            for u in sim.unidades:
                if u.equipo == cobertura_de and u.estado != "muerto":
                    r = radios[u.tipo]
                    for x in range(max(0, u.pos[0] - r), min(S.GRID_W, u.pos[0] + r + 1)):
                        for y in range(max(0, u.pos[1] - r), min(S.GRID_H, u.pos[1] + r + 1)):
                            visto_mapa.add((x, y))
                            if x0 <= x < x1 and y0 <= y < y1:
                                visto.add((x, y))
            if sim.tick_count % 25 == 0:
                curva.append([sim.tick_count, round(len(visto) / area, 4)])
                curva_mapa.append([sim.tick_count, round(len(visto_mapa) / (S.GRID_W * S.GRID_H), 4)])

    sim._tick_logico = tick

    sim_s = 0.0
    while not sim.simulacion_terminada and sim_s < LIMITE_SIM_S:
        sim.actualizar(S.TICK_DT)
        sim_s += S.TICK_DT

    filas = {}
    for puesto, f in enumerate(sim.obtener_ranking(), start=1):
        letra = f["letra"]
        orden = sorted(por_tick[letra])
        unidades = [u for u in sim.unidades if u.equipo == letra]
        fila = {
            "puesto": puesto,
            "nombre": f["nombre"],
            "recursos": f["recursos"],
            "bateria": round(f["bateria"], 1),
            "ratio": round(f["ratio"], 5),
            "vivas": sum(1 for u in unidades if u.estado != "muerto"),
            "unidades": len(unidades),
            "mensajes": mensajes[letra],
            "gasto": {k: round(v) for k, v in sorted(gasto[letra].items())},
            "ms_media": round(statistics.mean(orden), 3) if orden else 0.0,
            "ms_p95": round(_percentil(orden, 0.95), 3),
            "ms_p99": round(_percentil(orden, 0.99), 3),
            "ms_max": round(orden[-1], 3) if orden else 0.0,
        }
        extra = getattr(sim.equipos[letra], "estadisticas", None)
        if callable(extra):
            fila["interno"] = extra()
        filas[letra] = fila
    return {
        "semilla": semilla,
        "sim_s": round(sim_s, 1),
        "ticks": sim.tick_count,
        "terminada": sim.simulacion_terminada,
        "hielo_inicial": sim.hielo_inicial,
        "cobertura": curva,
        "cobertura_mapa": curva_mapa,
        "equipos": filas,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("equipos", nargs="*", help="LETRA=archivo.py o LETRA=base")
    ap.add_argument("--semillas", default="1-5")
    ap.add_argument("--rotar", action="store_true", help="pasa el primer equipo no-base por las 4 esquinas")
    ap.add_argument("--json", help="guarda todas las partidas en este archivo")
    ap.add_argument("--detalle", action="store_true", help="imprime cada partida")
    args = ap.parse_args()

    asignacion = {k: "base" for k in LETRAS}
    if not args.equipos:
        asignacion["A"] = "equipoA.py"
    for par in args.equipos:
        letra, origen = par.split("=")
        asignacion[letra.upper()] = origen

    configuraciones = [asignacion]
    if args.rotar:
        nuestro = next(v for v in asignacion.values() if v != "base")
        configuraciones = [{k: (nuestro if k == l else "base") for k in LETRAS} for l in LETRAS]

    todas = []
    for conf in configuraciones:
        tmp = preparar(conf)
        try:
            for s in _rango(args.semillas):
                r = partida(tmp, s)
                r["asignacion"] = conf
                todas.append(r)
                if args.detalle:
                    print(f"semilla={s} ticks={r['ticks']} sim={r['sim_s']}s hielo={r['hielo_inicial']}")
                    for letra, f in sorted(r["equipos"].items(), key=lambda kv: kv[1]["puesto"]):
                        print(
                            f"  {f['puesto']}º {letra} {conf[letra]:<14} rec={f['recursos']:4d} "
                            f"bat={f['bateria']:8.0f} ratio={f['ratio']:.4f} vivas={f['vivas']:2d}/{f['unidades']} "
                            f"msg={f['mensajes']:4d} ms p99={f['ms_p99']:.2f} max={f['ms_max']:.2f}"
                        )
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
            if str(tmp) in sys.path:
                sys.path.remove(str(tmp))

    # Resumen por archivo de equipo (junta todas las letras y semillas donde jugó)
    por_origen: Dict[str, List[Dict[str, Any]]] = {}
    for r in todas:
        for letra, f in r["equipos"].items():
            por_origen.setdefault(r["asignacion"][letra], []).append(f)

    print(f"\n{len(todas)} partidas ({sum(1 for r in todas if not r['terminada'])} cortadas por tiempo)")
    print(f"{'equipo':<16}{'n':>4}{'ratio':>9}{'mediana':>9}{'min':>8}{'max':>8}{'puesto':>8}{'rec':>7}{'bat':>8}{'vivas':>7}{'msg':>6}{'p99ms':>8}{'maxms':>8}")
    for origen, fs in sorted(por_origen.items(), key=lambda kv: -statistics.mean(f["ratio"] for f in kv[1])):
        ratios = [f["ratio"] for f in fs]
        print(
            f"{origen:<16}{len(fs):>4}{statistics.mean(ratios):>9.4f}{statistics.median(ratios):>9.4f}{min(ratios):>8.4f}{max(ratios):>8.4f}"
            f"{statistics.mean(f['puesto'] for f in fs):>8.2f}{statistics.mean(f['recursos'] for f in fs):>7.0f}"
            f"{statistics.mean(f['bateria'] for f in fs):>8.0f}{statistics.mean(f['vivas'] for f in fs):>7.1f}"
            f"{statistics.mean(f['mensajes'] for f in fs):>6.0f}{max(f['ms_p99'] for f in fs):>8.2f}{max(f['ms_max'] for f in fs):>8.2f}"
        )

    if args.json:
        destino = AQUI / args.json
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps(todas, ensure_ascii=False, indent=1))
        print(f"guardado en {destino}")


if __name__ == "__main__":
    main()
