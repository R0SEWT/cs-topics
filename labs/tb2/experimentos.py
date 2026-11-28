"""
experimentos.py — los experimentos "con y sin" que pide el informe, una pieza por sesión.

Cada variante juega las mismas semillas desde la esquina A contra tres equipos base. La variante
`completo` es el equipo tal como se entrega; las demás apagan o cambian UNA cosa.

    uv run --no-project --with pygame python experimentos.py [--semillas 1-10] [--procesos 4]

Escribe reports/experimentos.json (todo) y reports/experimentos.md (tablas para el informe).
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import shutil
import statistics as st
from typing import Any, Dict, List, Tuple

import arena

NUESTRO = "equipoA.py"

# nombre -> (sesión, qué prueba, ajustes de constantes, tormentas extra)
VARIANTES: Dict[str, Tuple[str, str, Dict[str, str], int]] = {
    "completo": ("—", "Equipo tal como se entrega", {}, 0),
    "s1_un_solo_gajo": ("S1", "Todos los exploradores patrullan la misma franja", {"GAJOS": "1"}, 0),
    "s1_sin_olvido": ("S1", "Una veta agotada solo se borra al pararse encima", {"EXP_OLVIDO": "False"}, 0),
    "s2_sin_evasion": ("S2", "Sin esperar, rodear ni esquivar tormentas", {"EXP_EVITAR_TORMENTAS": "False"}, 0),
    "s2_w2_mitad": ("S2", "Costo de desplazamiento a la mitad (w2 x0.5)", {"EXP_PESOS": "(1.0, 0.5, 1.0, 1.0)"}, 0),
    "s2_w2_doble": ("S2", "Costo de desplazamiento al doble (w2 x2)", {"EXP_PESOS": "(1.0, 2.0, 1.0, 1.0)"}, 0),
    "s2_w4_tercio": ("S2", "Tormenta pesa un tercio (w4 x1/3)", {"EXP_PESOS": "(1.0, 1.0, 1.0, 0.3333)"}, 0),
    "s2_w4_cero": ("S2", "Sin penalizar tormenta en la utilidad (w4 x0)", {"EXP_PESOS": "(1.0, 1.0, 1.0, 0.0)"}, 0),
    "s2_w4_triple": ("S2", "Tormenta pesa el triple (w4 x3)", {"EXP_PESOS": "(1.0, 1.0, 1.0, 3.0)"}, 0),
    "s2_pesos_iniciales": ("S2", "Pesos antes de calibrar (w2 x2, w4 x1/3)",
                           {"EXP_PESOS": "(1.0, 2.0, 1.0, 0.3333)"}, 0),
    "s3_sin_filtros": ("S3", "Reportes sin deduplicar, sin enfriamiento ni umbral de valor", {"EXP_FILTROS_MENSAJES": "False"}, 0),
    "s4_sin_subastas": ("S4", "Sin subasta implícita ni CNP: cada rover va a lo que ve",
                        {"EXP_SUBASTA_IMPLICITA": "False", "EXP_CNP": "False"}, 0),
    "s4_sin_implicita": ("S4", "Sin subasta implícita (queda el CNP explícito)",
                         {"EXP_SUBASTA_IMPLICITA": "False"}, 0),
    "s4_sin_cnp": ("S4", "Sin CNP explícito (queda la subasta implícita; avisos por INFORM)",
                   {"EXP_CNP": "False"}, 0),
    "s5_tormenta_votando": ("S5", "Alta tormenta (+3): con votación", {}, 3),
    "s5_tormenta_fija_ahorro": ("S5", "Alta tormenta (+3): política fija AHORRO", {"EXP_VOTACION": "False"}, 3),
    "s5_tormenta_fija_expansion": ("S5", "Alta tormenta (+3): política fija EXPANSION",
                                   {"EXP_VOTACION": "False", "POLITICA_INICIAL": '"EXPANSION"'}, 3),
    "s5_normal_fija_ahorro": ("S5", "Escenario normal: política fija AHORRO", {"EXP_VOTACION": "False"}, 0),
}


def _una(tarea: Tuple[str, int]) -> Dict[str, Any]:
    nombre, semilla = tarea
    _, _, ajustes, extra = VARIANTES[nombre]
    tmp = arena.preparar({"A": NUESTRO, "B": "base", "C": "base", "D": "base"}, ajustes)
    try:
        r = arena.partida(tmp, semilla, tormentas_extra=extra, cobertura_de="A")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    e = r["equipos"]["A"]
    g = e["gasto"]
    c = e["interno"]["contadores"]
    return {
        "variante": nombre, "semilla": semilla, "ticks": r["ticks"], "terminada": r["terminada"],
        "puesto": e["puesto"], "ratio": e["ratio"], "recursos": e["recursos"], "bateria": e["bateria"],
        "vivas": e["vivas"], "mensajes": e["mensajes"],
        "bat_mensajes": sum(v for k, v in g.items() if "mensajes" in k),
        "bat_tormenta": sum(v for k, v in g.items() if "tormenta" in k),
        "bat_pasos": sum(v for k, v in g.items() if k.endswith(":paso")),
        "viajes_en_vano": c.get("viajes_en_vano", 0),
        "depositos": c.get("depositos", 0),
        "subastas": c.get("subastas_adjudicadas", 0),
        "cedidas_sin_mensaje": c.get("cedidas_sin_mensaje", 0),
        "reportes_filtrados": c.get("reportes_filtrados", 0),
        "errores": c.get("errores", 0),
        "cambios_de_politica": e["interno"]["cambios_de_politica"],
        "desempates": e["interno"].get("desempates", {}),
        "ticks_por_politica": e["interno"].get("ticks_por_politica", {}),
        "votos": e["interno"].get("votos", []) if semilla <= 2 else [],
        "ms": e["interno"]["ms"],
        "cobertura": r["cobertura"],
        "cobertura_mapa": r["cobertura_mapa"],
        "histograma_ms": e["interno"].get("histograma_ms", []),
        "contadores": c,
    }


def _ms(xs: List[float]) -> str:
    return "%.4f ± %.4f" % (st.mean(xs), st.pstdev(xs)) if len(xs) > 1 else "%.4f" % xs[0]


def _cobertura_en(filas: List[Dict[str, Any]], tick: int) -> float:
    vals = []
    for f in filas:
        previos = [c for t, c in f["cobertura"] if t <= tick]
        if previos:
            vals.append(previos[-1])
    return st.mean(vals) if vals else 0.0


def tabla(resultados: List[Dict[str, Any]]) -> str:
    por: Dict[str, List[Dict[str, Any]]] = {}
    for r in resultados:
        por.setdefault(r["variante"], []).append(r)
    base = {r["semilla"]: r for r in por.get("completo", [])}
    lineas = [
        "# Experimentos con y sin cada pieza",
        "",
        "Nuestro equipo en la esquina A contra tres equipos base, mismas semillas en todas las variantes.",
        "Δ ratio es la diferencia media, semilla a semilla, contra `completo`.",
        "",
        "| Sesión | Variante | Qué cambia | n | Ratio (media ± desv.) | Δ ratio | Hielo | Batería | Bat. mensajes | Bat. tormentas | Viajes en vano | Puesto medio |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for nombre, (sesion, que, _, _) in VARIANTES.items():
        fs = por.get(nombre)
        if not fs:
            continue
        deltas = [f["ratio"] - base[f["semilla"]]["ratio"] for f in fs if f["semilla"] in base]
        delta = "%+.4f" % st.mean(deltas) if deltas and nombre != "completo" else "—"
        lineas.append("| %s | `%s` | %s | %d | %s | %s | %.0f | %.0f | %.0f | %.0f | %.1f | %.2f |" % (
            sesion, nombre, que, len(fs), _ms([f["ratio"] for f in fs]), delta,
            st.mean(f["recursos"] for f in fs), st.mean(f["bateria"] for f in fs),
            st.mean(f["bat_mensajes"] for f in fs), st.mean(f["bat_tormenta"] for f in fs),
            st.mean(f["viajes_en_vano"] for f in fs), st.mean(f["puesto"] for f in fs),
        ))
    lineas += ["", "## S1 · Cobertura del cuadrante propio (fracción de celdas vistas)", "",
               "| Variante | tick 100 | tick 200 | tick 400 | tick 600 |", "|---|---:|---:|---:|---:|"]
    for nombre in ("completo", "s1_un_solo_gajo"):
        if nombre in por:
            lineas.append("| `%s` | %s |" % (nombre, " | ".join("%.0f %%" % (100 * _cobertura_en(por[nombre], t)) for t in (100, 200, 400, 600))))
    if "completo" in por:
        fs = por["completo"]
        lineas += ["", "## S6 · Latencia por turno del equipo completo (ms)", "",
                   "| media | p95 | p99 | máximo |", "|---:|---:|---:|---:|",
                   "| %.2f | %.2f | %.2f | %.2f |" % (
                       st.mean(f["ms"]["media"] for f in fs), max(f["ms"]["p95"] for f in fs),
                       max(f["ms"]["p99"] for f in fs), max(f["ms"]["max"] for f in fs)),
                   "", "Ojo: estos tiempos se midieron con otras partidas corriendo en paralelo. Para el informe,",
                   "repetir con `latencia.py` y la máquina libre."]
        errores = sum(f["errores"] for f in resultados)
        lineas += ["", "Errores atrapados por la red de seguridad en todas las partidas: **%d**." % errores]
    return "\n".join(lineas) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--semillas", default="1-10")
    ap.add_argument("--procesos", type=int, default=4)
    ap.add_argument("--solo", nargs="*", help="nombres de variantes a correr")
    args = ap.parse_args()
    nombres = args.solo or list(VARIANTES)
    tareas = [(n, s) for n in nombres for s in arena._rango(args.semillas)]
    with mp.get_context("spawn").Pool(args.procesos) as pool:
        resultados = []
        for i, r in enumerate(pool.imap_unordered(_una, tareas), start=1):
            resultados.append(r)
            if i % 10 == 0:
                print(f"{i}/{len(tareas)}", flush=True)
    resultados.sort(key=lambda r: (list(VARIANTES).index(r["variante"]), r["semilla"]))
    destino = arena.AQUI / "reports"
    destino.mkdir(exist_ok=True)
    (destino / "experimentos.json").write_text(json.dumps(resultados, ensure_ascii=False))
    texto = tabla(resultados)
    (destino / "experimentos.md").write_text(texto)
    print(texto)


if __name__ == "__main__":
    main()
