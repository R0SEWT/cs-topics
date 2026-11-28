"""
figuras.py — genera TODO lo que el informe toma de los datos: figuras, tablas y valores sueltos.

Lee ../reports/afinado-v2.json (torneo), ../reports/experimentos.json (variantes "con y sin") y
../reports/latencia.json (perfilado), más las constantes de ../equipoA.py, y escribe:

    figs/*.svg        figuras (matplotlib + seaborn, paleta tab10)
    tablas/*.typ      tablas en Typst que informe.qmd incluye
    valores.json      números sueltos que el texto cita (ya formateados)
    _estado.yml       qué bloques de datos existen (exp_ok, lat_ok), para el contenido condicional

No corre partidas. Si un JSON falta, su figura y su tabla no se generan y el informe omite el bloque.

    uv run --no-project --with matplotlib --with seaborn python figuras.py
"""

from __future__ import annotations

import json
import statistics as st
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import seaborn as sns  # noqa: E402

AQUI = Path(__file__).resolve().parent
TB2 = AQUI.parent
REPORTS = TB2 / "reports"
MOTOR = TB2.parent.parent / "materials" / "evaluaciones" / "tb2"
FIGS = AQUI / "figs"
TABLAS = AQUI / "tablas"
FIGS.mkdir(exist_ok=True)
TABLAS.mkdir(exist_ok=True)

sys.path.insert(0, str(MOTOR))
sys.path.insert(0, str(TB2))
import equipoA as E  # noqa: E402
import equipo_base as _EB  # noqa: E402

# La clase del equipo se localiza por herencia: su nombre puede cambiar.
Clase = next(v for v in vars(E).values()
             if isinstance(v, type) and issubclass(v, _EB.EquipoBase) and v is not _EB.EquipoBase)

sns.set_theme(style="whitegrid", palette="tab10", font="DejaVu Sans", rc={
    "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5, "axes.linewidth": 0.6, "grid.linewidth": 0.4, "grid.color": "#dddddd",
    "axes.edgecolor": "#555555", "svg.fonttype": "path", "legend.frameon": False,
})
C = sns.color_palette("tab10")
UMBRAL_MS = 40.0


def es(x: float, d: int = 4) -> str:
    """Número con coma decimal."""
    return ("%.*f" % (d, x)).replace(".", ",")


def sg(x: float, d: int = 4) -> str:
    if round(x, d) == 0:
        return ("%.*f" % (d, 0.0)).replace(".", ",")
    return ("%+.*f" % (d, x)).replace(".", ",").replace("-", "−")


def guardar(fig, nombre: str) -> None:
    fig.savefig(FIGS / nombre, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def cargar(nombre: str):
    ruta = REPORTS / nombre
    return json.loads(ruta.read_text()) if ruta.exists() else None


def tabla_typ(nombre: str, columnas: str, alineacion: str, cabecera: list, filas: list, grosor_cab: bool = True) -> None:
    """Escribe una tabla Typst. Las celdas ya vienen como marcado Typst."""
    lineas = [
        "#table(",
        "  columns: %s," % columnas,
        "  align: %s," % alineacion,
        "  stroke: none, inset: (x: 3pt, y: 2.6pt),",
        "  table.hline(stroke: 0.6pt),",
        "  table.header(%s)," % ", ".join(("[*%s*]" % c) if c else "[]" for c in cabecera),
        "  table.hline(stroke: 0.4pt),",
    ]
    for fila in filas:
        lineas.append("  " + ", ".join("[%s]" % c for c in fila) + ",")
    lineas += ["  table.hline(stroke: 0.6pt),", ")"]
    (TABLAS / nombre).write_text("\n".join(lineas) + "\n")


V: dict = {}

# ----------------------------------------------------------------------------------------------
# Constantes y políticas, leídas del código que se entrega
# ----------------------------------------------------------------------------------------------
V["c"] = {
    k: (es(v, 1) if isinstance(v, float) else str(v))
    for k, v in vars(E).items()
    if k.isupper() and isinstance(v, (int, float)) and not isinstance(v, bool)
}
V["c"]["VISION_ROVER"] = str(E.VISION["rover"])
V["c"]["VISION_EXPL"] = str(E.VISION["dron_explorador"])
V["c"]["VISION_REC"] = str(E.VISION["dron_recarga"])
V["c"]["POLITICA_INICIAL"] = E.POLITICA_INICIAL
V["c"]["ORDEN"] = " ≻ ".join(E.ORDEN_POLITICAS)
V["c"]["MARGEN_INERCIA_PCT"] = "%d" % round(100 * E.MARGEN_INERCIA)
V["c"]["CLASE"] = Clase.__name__
import math as _m
_gajos = getattr(E, "GAJOS", 1)
_rp = getattr(E, "RADIO_PATRULLA", 0)
V["c"]["ANG_GAJO"] = es(90.0 / _gajos, 0)
V["c"]["ARCO_GAJO"] = es(_rp * (_m.pi / 2) / _gajos, 1)
_ex = [p.get("exploradores", 0) for p in E.POLITICAS.values()]
V["c"]["EXPL_MIN"], V["c"]["EXPL_MAX"] = str(min(_ex)), str(max(_ex))
V["c"]["EXPL_POR_POLITICA"] = ", ".join("%s con %s" % (p["exploradores"], k) for k, p in E.POLITICAS.items())
_k = [p.get("k_cnp", 0) for p in E.POLITICAS.values()]
V["c"]["K_MIN"], V["c"]["K_MAX"] = str(min(_k)), str(max(_k))
if hasattr(E, "RADIO_BUSQUEDA"):
    V["c"]["RADIOS_BUSQUEDA"] = ", ".join(str(E.RADIO_BUSQUEDA + E.PASO_BUSQUEDA * i) for i in range(E.TRAMOS_BUSQUEDA))


def _inf(x) -> str:
    return "∞" if isinstance(x, (int, float)) and x >= 10 ** 6 else (es(x, 2) if isinstance(x, float) and x != int(x) else str(int(x) if isinstance(x, float) else x))


CLAVES = {  # clave de POLITICAS -> (cabecera Typst, descripción para el pie de tabla)
    "umbral_u": ("$u_min$", "$u_min$, utilidad de reserva (lo que vale volver a la base)"),
    "radio_max": ("$r_max$", "$r_max$, distancia máxima a la base a la que se trabaja o patrulla"),
    "valor_min": ("$v_min$", "$v_min$, hielo mínimo de una zona para que valga un mensaje"),
    "enfriamiento": ("enfr.", "enfr., ticks antes de repetir un reporte de la misma zona"),
    "k_cnp": ("$k$", "$k$, invitados a una subasta"),
    "exploradores": ("expl.", "expl., exploradores de turno a la vez"),
    "cadencia": ("cad.", "cad., un explorador de turno avanza uno de cada «cad.» ticks"),
    "pausa": ("pausa", "pausa, ticks entre patrullas"),
    "bat_pit": ("bat. pit", "bat. pit, batería bajo la cual un rover vacío pide recarga preventiva en la base"),
}
claves = [k for k in next(iter(E.POLITICAS.values())) if k != "w"]
filas = []
for nombre in E.POLITICAS:
    p = E.POLITICAS[nombre]
    filas.append(["`%s`" % nombre] + [es(w, 1) for w in p["w"]] + [
        es(p[k], 2) if k == "umbral_u" else _inf(p[k]) for k in claves])
n_col = 4 + len(claves)
tabla_typ("politicas.typ", "(auto,) + (1fr,) * %d" % n_col, "(left,) + (right,) * %d" % n_col,
          ["Política", "$w_1$", "$w_2$", "$w_3$", "$w_4$"] + [CLAVES.get(k, (k, k))[0] for k in claves], filas)
V["c"]["LEYENDA_POLITICAS"] = "; ".join(CLAVES.get(k, (k, k))[1] for k in claves)

# ----------------------------------------------------------------------------------------------
# S5 · Ejemplo trabajado de Copeland con las funciones reales del equipo
# ----------------------------------------------------------------------------------------------
PERFILES = [
    # (n, batería, ve tormenta, vetas ricas recordadas, restos recordados, descripción)
    (18, 100.0, True, 0, 0, "en base, batería llena, tormenta a la vista"),
    (12, 80.0, False, 4, 0, "en campo, sin tormenta, 4 vetas ricas en memoria"),
    (8, 60.0, True, 2, 0, "en campo, tormenta a la vista, 2 vetas ricas"),
    (7, 45.0, False, 0, 2, "batería bajo 50 %, 2 restos en memoria"),
    (5, 90.0, False, 0, 0, "en base, sin tormenta ni hallazgos"),
]
papeletas = []
filas = []
for n, bat, torm, ricas, restos, desc in PERFILES:
    yo = SimpleNamespace(ultima_eleccion=-10 ** 6, urna={})
    u = SimpleNamespace(id="x", bateria=bat, en_tormenta=False)
    p = SimpleNamespace(tick=0, fase_final=False)
    m = {"tormentas": [(0, 0, 5, 0)] if torm else [],
         "hielo": {(i, 0): (4, 0) for i in range(ricas)},
         "restos": {i: None for i in range(restos)}, "ultimo_hielo": 0}
    Clase._depositar_papeleta(yo, u, p, m)
    orden = yo.urna["x"]
    papeletas += [orden] * n
    filas.append([str(n), desc, " ≻ ".join("`%s`" % o[:3] for o in orden)])
tabla_typ("papeletas.typ", "(1fr, auto)", "(left, left)", ["Estado local del votante", "Papeleta que produce"], [f_[1:] for f_ in filas])


# ----------------------------------------------------------------------------------------------
# Torneo (afinado-v2.json)
# ----------------------------------------------------------------------------------------------
torneo = cargar("torneo.json")


def _es_version_actual(contadores: dict) -> bool:
    """Los datos son de la versión entregada si traen contadores que solo ella produce."""
    return any(k.startswith("msg_ont_") or k == "rondas_de_busqueda" for k in contadores)


# Dato histórico: la versión anterior del equipo (archivada en reports/v-anterior/).
_ant = REPORTS / "v-anterior" / "experimentos.json"
if _ant.exists():
    _c = [r for r in json.loads(_ant.read_text()) if r["variante"] == "completo"]
    if _c:
        V["ant"] = {"n": str(len(_c)), "ratio": es(st.mean(r["ratio"] for r in _c)),
                    "hielo": es(st.mean(r["recursos"] for r in _c), 0), "bat": es(st.mean(r["bateria"] for r in _c), 0)}
_ens = AQUI / "datos" / "ensayo-calibracion.json"
_bar = AQUI / "datos" / "barrido-previo.json"
if _ens.exists() and _bar.exists():
    _e = json.loads(_ens.read_text())
    _c = {r["semilla"]: r for r in _e if r["variante"] == "completo"}
    _t = [r for r in _e if r["variante"] == "s2_w2_mitad_w4_triple"]
    _b = json.loads(_bar.read_text())["x"]
    V["cal"] = {
        "previo_ratio": _b["completo"]["ratio"], "previo_w2_mitad": _b["s2_w2_mitad"]["delta"], "previo_w2_doble": _b["s2_w2_doble"]["delta"],
        "previo_w4_triple": _b["s2_w4_triple"]["delta"], "previo_w4_cero": _b["s2_w4_cero"]["delta"],
        "ens_n": str(len(_t)), "ens_antes": es(st.mean(r["ratio"] for r in _c.values())), "ens_despues": es(st.mean(r["ratio"] for r in _t)),
        "ens_delta": sg(st.mean(r["ratio"] - _c[r["semilla"]]["ratio"] for r in _t)),
        "ens_mejor_en": "%d de %d" % (sum(1 for r in _t if r["ratio"] > _c[r["semilla"]]["ratio"]), len(_t)),
        "ens_primeros": "%d de %d" % (sum(1 for r in _t if r["puesto"] == 1), len(_t)),
    }
if torneo:
    N, B, filas_n = [], [], []
    for r in torneo:
        for letra, f in r["equipos"].items():
            if r["asignacion"][letra] != "base":
                N.append(f)
                filas_n.append((letra, r, f))
            else:
                B.append(f)

    def media(fs, k):
        return st.mean(f[k] for f in fs)

    def gasto(fs):
        g = Counter()
        for f in fs:
            for k, v in f["gasto"].items():
                g[k.split(":")[1]] += v
        return {k: v / len(fs) for k, v in g.items()}

    gn, gb = gasto(N), gasto(B)
    cont = Counter()
    for f in N:
        cont.update(f["interno"]["contadores"])
    cm = {k: v / len(N) for k, v in cont.items()}
    msgs_cnp = sum(cm.get("msg_" + k, 0) for k in ("CFP", "PROPOSE", "ACCEPT_PROPOSAL", "REJECT_PROPOSAL"))
    puestos_n = Counter(f["puesto"] for f in N)
    term = [f for (_, r, f) in filas_n if r["terminada"]]
    cort = [f for (_, r, f) in filas_n if not r["terminada"]]
    V["t"] = {
        "version_actual": _es_version_actual(cont),
        "partidas": str(len(torneo)), "cortadas": str(sum(1 for r in torneo if not r["terminada"])),
        "terminadas": str(sum(1 for r in torneo if r["terminada"])),
        "semillas": str(len({r["semilla"] for r in torneo})),
        "hielo_min": str(min(r["hielo_inicial"] for r in torneo)), "hielo_max": str(max(r["hielo_inicial"] for r in torneo)),
        "ticks_min": str(min(r["ticks"] for r in torneo)), "ticks_max": str(max(r["ticks"] for r in torneo)),
        "ratio_n": es(media(N, "ratio")), "ratio_b": es(media(B, "ratio")),
        "mediana_n": es(st.median(f["ratio"] for f in N)), "errores": str(int(cont.get("errores", 0))),
        "sd_n": es(st.pstdev(f["ratio"] for f in N)), "sd_b": es(st.pstdev(f["ratio"] for f in B)),
        "min_n": es(min(f["ratio"] for f in N)), "max_n": es(max(f["ratio"] for f in N)),
        "veces": es(media(N, "ratio") / media(B, "ratio"), 1),
        "primeros": str(puestos_n[1]), "segundos": str(puestos_n[2]), "terceros": str(puestos_n[3]), "cuartos": str(puestos_n[4]), "peor_puesto": str(max(puestos_n)),
        "puesto_n": es(media(N, "puesto"), 2),
        "rec_n": es(media(N, "recursos"), 0), "rec_b": es(media(B, "recursos"), 0),
        "bat_n": es(media(N, "bateria"), 0), "bat_b": es(media(B, "bateria"), 0),
        "vivas_n": es(media(N, "vivas"), 1), "vivas_b": es(media(B, "vivas"), 1),
        "msg_n": es(media(N, "mensajes"), 0), "msg_b": es(media(B, "mensajes"), 0),
        "batmsg_n": es(gn["mensajes"], 0), "batmsg_b": es(gb["mensajes"], 0),
        "pctmsg_n": es(100 * gn["mensajes"] / media(N, "bateria"), 1), "pctmsg_b": es(100 * gb["mensajes"] / media(B, "bateria"), 1),
        "pcttorm_n": es(100 * (gn.get("paso_tormenta", 0) + gn.get("pulso_tormenta", 0)) / media(N, "bateria"), 1),
        "pcttorm_b": es(100 * (gb.get("paso_tormenta", 0) + gb.get("pulso_tormenta", 0)) / media(B, "bateria"), 1),
        "pasotorm_n": es(gn.get("paso_tormenta", 0), 0), "pasotorm_b": es(gb.get("paso_tormenta", 0), 0),
        "pulso_n": es(gn.get("pulso_tormenta", 0), 0), "pulso_b": es(gb.get("pulso_tormenta", 0), 0),
        "ratio_term": es(st.mean(f["ratio"] for f in term)) if term else "—",
        "ratio_cort": es(st.mean(f["ratio"] for f in cort)) if cort else "—",
        "n_term": str(len(term)), "n_cort": str(len(cort)),
        "sub_abiertas": es(cm.get("subastas_abiertas", 0), 1), "sub_adj": es(cm.get("subastas_adjudicadas", 0), 1),
        "sub_desiertas": es(cm.get("subastas_desiertas", 0), 1),
        "msg_por_subasta": es(msgs_cnp / cm["subastas_abiertas"], 1) if cm.get("subastas_abiertas") else "—",
        "cfp_sin_puja": es(cm.get("cfp_sin_puja", 0), 1),
        "cedidas": es(cm.get("cedidas_sin_mensaje", 0), 0), "filtrados": es(cm.get("reportes_filtrados", 0), 0),
        "esperas": es(cm.get("esperas_por_tormenta", 0), 0), "esquives": es(cm.get("esquives", 0), 0),
        "astar": es(cm.get("astar", 0), 1), "carronas": es(cm.get("carronas", 0), 1),
        "recargas": es(cm.get("recargas", 0), 1), "requests": es(cm.get("msg_REQUEST", 0), 1),
        "agree": es(cm.get("msg_AGREE", 0), 1), "failure": es(cm.get("msg_FAILURE", 0), 1),
        "reenviados": es(cm.get("rescates_reenviados", 0), 1),
        "elecciones": es(cm.get("elecciones", 0), 1),
        "cambios": es(st.mean(len(f["interno"]["cambios_de_politica"]) for f in N), 1),
        "pasos_explorando": es(cm.get("pasos_EXPLORANDO", 0), 0), "pasos_patrullando": es(cm.get("pasos_PATRULLANDO", 0), 0),
        "pasos_recolectando": es(cm.get("pasos_RECOLECTANDO", 0), 0), "pasos_retornando": es(cm.get("pasos_RETORNANDO", 0), 0),
        "ms_max_torneo": es(max(f["interno"]["ms"]["max"] for f in N), 1),
        "ms_max_base": es(max(f["ms_max"] for f in B), 1),
    }

    # Tabla resumen del torneo, por esquina
    filas = []
    for letra in "ABCD":
        fs = [(r, f) for (l, r, f) in filas_n if l == letra]
        if not fs:
            continue
        rivales = [f2 for (r, _) in fs for l2, f2 in r["equipos"].items() if r["asignacion"][l2] == "base"]
        pu = Counter(f["puesto"] for _, f in fs)
        filas.append([
            letra, str(len(fs)), str(sum(1 for r, _ in fs if not r["terminada"])),
            es(st.mean(f["ratio"] for _, f in fs)), es(min(f["ratio"] for _, f in fs)), es(max(f["ratio"] for _, f in fs)),
            " / ".join(str(pu[i]) for i in (1, 2, 3, 4)), es(st.mean(f["recursos"] for _, f in fs), 0), es(st.mean(f["bateria"] for _, f in fs), 0),
            es(st.mean(f["ratio"] for f in rivales)), es(st.mean(f["recursos"] for f in rivales), 0), es(st.mean(f["bateria"] for f in rivales), 0),
        ])
    filas.append(["*Total*", str(len(N)), V["t"]["cortadas"], "*%s*" % V["t"]["ratio_n"], V["t"]["min_n"], V["t"]["max_n"],
                  " / ".join(str(puestos_n[i]) for i in (1, 2, 3, 4)), V["t"]["rec_n"], V["t"]["bat_n"],
                  "*%s*" % V["t"]["ratio_b"], V["t"]["rec_b"], V["t"]["bat_b"]])
    (TABLAS / "torneo.typ").write_text("\n".join([
        "#table(",
        "  columns: (auto, 1fr, 1fr, 1fr, 1fr, 1fr, auto, 1fr, 1fr, 1fr, 1fr, 1fr),",
        "  align: (left,) + (right,) * 11,",
        "  stroke: none, inset: (x: 4pt, y: 2.6pt),",
        "  table.hline(stroke: 0.6pt),",
        "  table.header(table.cell(colspan: 3)[], table.cell(colspan: 6, align: center)[*Nuestro equipo*], table.cell(colspan: 3, align: center)[*Equipos base (media)*],",
        "    table.hline(start: 3, end: 9, stroke: 0.3pt), table.hline(start: 9, end: 12, stroke: 0.3pt),",
        "    " + ", ".join("[*%s*]" % c for c in ["Esquina", "$n$", "cort.", "Ratio", "mín.", "máx.", "puestos 1–4", "hielo", "batería", "Ratio", "hielo", "batería"]) + "),",
        "  table.hline(stroke: 0.4pt),",
    ] + ["  " + ", ".join("[%s]" % c for c in f) + "," for f in filas[:-1]] + [
        "  table.hline(stroke: 0.3pt),",
        "  " + ", ".join("[%s]" % c for c in filas[-1]) + ",",
        "  table.hline(stroke: 0.6pt),", ")",
    ]) + "\n")

    # Tabla de mensajes por performativa
    perfs = [("INFORM", "hielo, restos", "`pos`, `cantidad`, `total` · `agotado` · `id`, `combustible`", "hallazgo, sobrante o veta agotada"),
             ("CFP", "hielo, restos, recarga", "tarea + `vence`", "abre subasta a $<= k$ candidatos"),
             ("PROPOSE", "las tres", "`puja`", "oferta de un candidato"),
             ("ACCEPT_PROPOSAL", "las tres", "tarea adjudicada", "adjudicación a la menor puja"),
             ("REJECT_PROPOSAL", "las tres", "—", "descarte de los demás"),
             ("REQUEST", "recarga", "`rover`, `pos`, `bateria`, `urgente`", "pedido de recarga"),
             ("AGREE", "recarga", "`eta`", "el dron confirma el rescate"),
             ("FAILURE", "las tres", "`motivo`", "sin disponibilidad, aborto u ocupado")]
    total = sum(cm.get("msg_" + k, 0) for k, _, _, _ in perfs)
    filas = [["`%s`" % k, o, cont_, d, es(cm.get("msg_" + k, 0), 1)] for k, o, cont_, d in perfs]
    filas.append(["*Total*", "", "", "cada mensaje cuesta 0,5 % + 0,5 %", "*%s*" % es(total, 1)])
    tabla_typ("mensajes.typ", "(auto, auto, 1fr, auto, auto)", "(left, left, left, left, right)",
              ["Performativa", "Ontología", "Campos de `content`", "Uso", "Por partida"], filas)
    onts = [(o, cm.get("msg_ont_" + o)) for o in ("hielo", "restos", "recarga")]
    V["t"]["msg_por_ont"] = ("Por ontología: " + ", ".join("%s de %s" % (es(n, 1), o) for o, n in onts if n is not None) + ".") if any(n is not None for _, n in onts) else ""
    subs = [(o, cm.get("subastas_" + o)) for o in ("hielo", "restos", "recarga")]
    V["t"]["sub_por_ont"] = (" (" + ", ".join("%s de %s" % (es(n, 1), o) for o, n in subs if n is not None) + ")") if any(n is not None for _, n in subs) else ""
    tp = Counter()
    for f in N:
        tp.update(f["interno"].get("ticks_por_politica", {}))
    V["t"]["pct_politicas"] = ", ".join("`%s` %s %%" % (k, es(100 * tp[k] / sum(tp.values()), 0)) for k in E.POLITICAS) if tp else ""
    veces_pol = Counter()
    for f in N:
        veces_pol.update({E.POLITICA_INICIAL} | {c[1] for c in f["interno"]["cambios_de_politica"]})
    for k in E.POLITICAS:
        V["t"]["partidas_con_" + k] = str(veces_pol.get(k, 0))
    V["t"]["final"] = ", ".join("%s en %d" % (k, n) for k, n in Counter(f["interno"]["politica_final"] for f in N).most_common())

    # Figura: Ratio por partida y esquina
    fig, ax = plt.subplots(figsize=(3.3, 2.1))
    import random as _r
    _r.seed(7)
    for i, letra in enumerate("ABCD"):
        for r in torneo:
            if r["asignacion"][letra] == "base":
                continue
            for l2, f in r["equipos"].items():
                propio = l2 == letra
                x = i + (-0.17 if propio else 0.17) + _r.uniform(-0.09, 0.09)
                col = C[0] if propio else C[1]
                ax.plot(x, f["ratio"], "o", ms=3.6, mew=0.9, mec=col, mfc=col if r["terminada"] else "white", alpha=0.9)
    ax.set_xticks(range(4), ["A", "B", "C", "D"])
    ax.set_xlabel("Esquina asignada a nuestro equipo")
    ax.set_ylabel("Ratio (hielo / batería)")
    ax.set_ylim(0, None)
    ax.grid(axis="x", visible=False)
    from matplotlib.lines import Line2D
    ax.legend(handles=[
        Line2D([], [], marker="o", ls="", ms=4, color=C[0], label="Nuestro equipo"),
        Line2D([], [], marker="o", ls="", ms=4, color=C[1], label="Equipos base"),
        Line2D([], [], marker="o", ls="", ms=4, mfc="white", mec="#555555", label="Partida cortada a 360 s"),
    ], loc="upper center", bbox_to_anchor=(0.5, 1.2), ncol=3, handletextpad=0.1, columnspacing=0.8)
    sns.despine(ax=ax)
    guardar(fig, "torneo.svg")

    # Figura: en qué se va la batería
    causas = [("paso", "Pasos normales", C[2]), ("paso_tormenta", "Pasos en tormenta", C[3]),
              ("pulso_tormenta", "Pulsos de tormenta", C[4]), ("mensajes", "Mensajes", C[5])]
    fig, ax = plt.subplots(figsize=(3.3, 1.5))
    for y, (g, nombre) in enumerate(((gn, "Nuestro\nequipo"), (gb, "Equipos\nbase"))):
        izq = 0.0
        for k, etiqueta, col in causas:
            v = g.get(k, 0.0)
            ax.barh(y, v, left=izq, color=col, edgecolor="white", linewidth=1.0, height=0.55, label=etiqueta if y == 0 else None)
            izq += v
        ax.text(izq + 120, y, es(izq, 0), va="center", fontsize=7.5, color="#333333")
    ax.set_yticks([0, 1], ["Nuestro\nequipo", "Equipos\nbase"])
    ax.invert_yaxis()
    ax.set_xlabel("Batería gastada por partida (puntos porcentuales, media)")
    ax.set_xlim(0, max(sum(gb.values()), sum(gn.values())) * 1.14)
    ax.grid(axis="y", visible=False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.45, 1.42), ncol=2, columnspacing=0.8, handlelength=1.2)
    sns.despine(ax=ax, left=True)
    guardar(fig, "gasto.svg")

    # Figura: política vigente en el tiempo (esquina A)
    col_pol = {"AHORRO": C[0], "EXPANSION": C[1], "CARRONA": C[2], "REPLIEGUE": C[3]}
    juegos = [(r, f) for (l, r, f) in filas_n if l == "A"]
    V["t"]["ticks_max_term"] = str(max((r["ticks"] for r in torneo if r["terminada"]), default=0))
    fig, ax = plt.subplots(figsize=(6.9, 0.2 * len(juegos) + 0.55))
    for y, (r, f) in enumerate(juegos):
        cambios = [(0, E.POLITICA_INICIAL)] + [tuple(c) for c in f["interno"]["cambios_de_politica"]]
        for (t0, pol), (t1, _) in zip(cambios, cambios[1:] + [(r["ticks"], None)]):
            ax.barh(y, t1 - t0, left=t0, color=col_pol[pol], height=0.62, edgecolor="white", linewidth=0.4)
    usadas = [p for p in col_pol if any(p == c[1] for _, f in juegos for c in f["interno"]["cambios_de_politica"]) or p == E.POLITICA_INICIAL]
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=col_pol[p], label=p) for p in usadas], loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=4)
    ax.set_yticks(range(len(juegos)), ["semilla %d" % r["semilla"] for r, _ in juegos])
    ax.invert_yaxis()
    ax.set_xlabel("Tick de la partida")
    ax.grid(axis="y", visible=False)
    sns.despine(ax=ax, left=True)
    guardar(fig, "politicas.svg")

# ----------------------------------------------------------------------------------------------
# Experimentos "con y sin" (experimentos.json)
# ----------------------------------------------------------------------------------------------
ETIQUETAS = {
    "completo": ("—", "Equipo tal como se entrega"),
    "s1_un_solo_gajo": ("S1", "Un solo gajo de patrulla"),
    "s1_sin_olvido": ("S1", "Sin olvido por revisita"),
    "s2_sin_evasion": ("S2", "Sin esperar, rodear ni esquivar tormentas"),
    "s2_w2_mitad": ("S2", "$w_2 times 0,5$"),
    "s2_w2_doble": ("S2", "$w_2 times 2$"),
    "s2_w4_cero": ("S2", "$w_4 times 0$"),
    "s2_w4_tercio": ("S2", "$w_4 times 1\\/3$"),
    "s2_pesos_iniciales": ("S2", "Pesos antes de calibrar ($w_2 times 2$, $w_4 times 1\\/3$)"),
    "s2_w4_triple": ("S2", "$w_4 times 3$"),
    "s3_sin_filtros": ("S3", "Reportes sin filtros"),
    "s4_sin_subastas": ("S4", "Sin subasta implícita ni CNP"),
    "s5_tormenta_votando": ("S5", "Alta tormenta (+3), con votación"),
    "s5_tormenta_fija_ahorro": ("S5", "Alta tormenta (+3), `AHORRO` fija"),
    "s5_tormenta_fija_expansion": ("S5", "Alta tormenta (+3), `EXPANSION` fija"),
    "s5_normal_fija_ahorro": ("S5", "Escenario normal, `AHORRO` fija"),
}
ETIQ_FIG = {
    "s1_un_solo_gajo": "S1 · un solo gajo", "s1_sin_olvido": "S1 · sin olvido por revisita",
    "s2_sin_evasion": "S2 · sin evasión de tormentas", "s2_w2_mitad": "S2 · w2 × 0,5", "s2_w2_doble": "S2 · w2 × 2",
    "s2_w4_cero": "S2 · w4 × 0", "s2_w4_triple": "S2 · w4 × 3", "s2_w4_tercio": "S2 · w4 × 1/3",
    "s2_pesos_iniciales": "S2 · pesos antes de calibrar", "s3_sin_filtros": "S3 · sin filtros de mensajes",
    "s4_sin_subastas": "S4 · sin subastas", "s5_normal_fija_ahorro": "S5 · AHORRO fija (normal)",
    "s5_tormenta_fija_ahorro": "S5 · AHORRO fija (alta tormenta)", "s5_tormenta_fija_expansion": "S5 · EXPANSION fija (alta tormenta)",
}
REFERENCIA = {"s5_tormenta_fija_ahorro": "s5_tormenta_votando", "s5_tormenta_fija_expansion": "s5_tormenta_votando"}

exp = cargar("experimentos.json")
exp_ok = False
if exp:
    por: dict = {}
    for r in exp:
        por.setdefault(r["variante"], []).append(r)
    n_min = min(len(v) for v in por.values())
    exp_ok = n_min >= 10
    for k in por:   # variantes nuevas que este script aún no conoce
        ETIQUETAS.setdefault(k, (k[:2].upper() if k[0] == "s" else "—", "`%s`" % k))
        ETIQ_FIG.setdefault(k, k)
    V["x"] = {"version_actual": all(_es_version_actual(r["contadores"]) for r in exp),
              "n_variantes": str(len(por)), "n_min": str(n_min), "partidas": str(len(exp)),
              "cortadas": str(sum(1 for r in exp if not r["terminada"])),
              "errores": str(sum(r["errores"] for r in exp)), "semillas": str(len({r["semilla"] for r in exp}))}
    filas = []
    deltas_fig = []
    for nombre, fs in por.items():
        sesion, que = ETIQUETAS[nombre]
        ref = {r["semilla"]: r for r in por.get(REFERENCIA.get(nombre, "completo"), [])}
        ds = [f["ratio"] - ref[f["semilla"]]["ratio"] for f in fs if f["semilla"] in ref]
        es_ref = nombre in ("completo", "s5_tormenta_votando")
        if nombre == "s5_tormenta_votando":
            ds = []
        d = st.mean(ds) if ds and not es_ref else None
        gana = sum(1 for x in ds if x < 0)   # semillas en que la variante queda por debajo de su referencia
        ee = st.stdev(ds) / len(ds) ** 0.5 if d is not None and len(ds) > 1 else None
        claro = ee is not None and abs(d) > 2 * ee
        v = {
            "n": str(len(fs)), "ratio": es(st.mean(f["ratio"] for f in fs)), "sd": es(st.pstdev(f["ratio"] for f in fs)) if len(fs) > 1 else "—",
            "delta": sg(d) if d is not None else "—", "delta_tabla": (sg(d) + ("\\*" if claro else "")) if d is not None else "—",
            "efecto": ("fuera del ruido" if claro else "dentro del ruido") if d is not None else "—", "claro": bool(claro), "delta_pct": sg(100 * d / st.mean(r["ratio"] for r in ref.values()), 1) if d is not None else "—",
            "peor_en": "%d de %d" % (gana, len(ds)) if d is not None else "—",
            "hielo": es(st.mean(f["recursos"] for f in fs), 0), "bat": es(st.mean(f["bateria"] for f in fs), 0),
            "bat_msg": es(st.mean(f["bat_mensajes"] for f in fs), 0), "bat_torm": es(st.mean(f["bat_tormenta"] for f in fs), 0),
            "bat_pasos": es(st.mean(f["bat_pasos"] for f in fs), 0),
            "msgs": es(st.mean(f["mensajes"] for f in fs), 0), "viajes": es(st.mean(f["viajes_en_vano"] for f in fs), 1),
            "depositos": es(st.mean(f["depositos"] for f in fs), 1),
            "puesto": es(st.mean(f["puesto"] for f in fs), 2), "vivas": es(st.mean(f["vivas"] for f in fs), 1),
            "cortadas": str(sum(1 for f in fs if not f["terminada"])),
            "hielo_por_bat100": es(100 * st.mean(f["recursos"] for f in fs) / st.mean(f["bateria"] for f in fs), 2),
            "cambios": es(st.mean(len(f["cambios_de_politica"]) for f in fs), 1),
            "filtrados": es(st.mean(f["reportes_filtrados"] for f in fs), 0),
            "cedidas": es(st.mean(f["cedidas_sin_mensaje"] for f in fs), 0),
            "primeros": "%d de %d" % (sum(1 for f in fs if f["puesto"] == 1), len(fs)),
            "reasignados": es(st.mean(f["contadores"].get("contratos_reasignados", 0) for f in fs), 1),
            "subastas": es(st.mean(f["subastas"] for f in fs), 1),
        }
        V["x"][nombre] = v
        filas.append([sesion, que, v["n"], "%s ± %s" % (v["ratio"], v["sd"]), v["delta_tabla"], v["peor_en"], v["hielo"], v["bat"],
                      v["bat_msg"], v["bat_torm"], v["viajes"], v["puesto"]])
        if d is not None:
            deltas_fig.append((nombre, ds))
    tabla_typ("experimentos.typ", "(auto, 1fr, auto, auto, auto, auto, auto, auto, auto, auto, auto, auto)",
              "(left, left) + (right,) * 10",
              ["S.", "Variante", "$n$", "Ratio ± desv.", "Δ Ratio", "Peor en", "Hielo", "Bat.", "Bat. msj.", "Bat. torm.", "V. vano", "Puesto"],
              filas)

    fa, fe = V["x"].get("s5_tormenta_fija_ahorro"), V["x"].get("s5_tormenta_fija_expansion")
    if fa and fe:
        # Δ = fija − votación: positivo y claro significa que la política fija rinde MÁS que votar.
        if not fa["claro"] and not fe["claro"]:
            V["x"]["veredicto_s5"] = "La votación no produce una diferencia medible del Ratio frente a ninguna de las dos políticas fijas"
        else:
            partes = []
            for nombre, v in (("AHORRO", fa), ("EXPANSION", fe)):
                if v["claro"]:
                    partes.append("%s fija rinde %s que la votación (Δ %s)" % (nombre, "menos" if v["delta"].startswith("−") else "más", v["delta"]))
                else:
                    partes.append("frente a %s fija la diferencia está dentro del ruido" % nombre)
            V["x"]["veredicto_s5"] = "Con alta tormenta, " + " y ".join(partes)
    V["x"]["claros"] = ", ".join("`%s` (%s)" % (k, v["delta"]) for k, v in V["x"].items() if isinstance(v, dict) and v.get("claro")) or "ninguna"
    V["x"]["sd_min"] = es(min(st.pstdev(f["ratio"] for f in fs) for fs in por.values()), 3)
    V["x"]["sd_max"] = es(max(st.pstdev(f["ratio"] for f in fs) for fs in por.values()), 3)

    # S2 · Tabla de calibración: pesos efectivos de AHORRO en cada variante del barrido
    MULT = {"s2_pesos_iniciales": (1, 2, 1, 1 / 3), "s2_w2_doble": (1, 2, 1, 1), "s2_w2_mitad": (1, 0.5, 1, 1),
            "s2_w4_cero": (1, 1, 1, 0), "s2_w4_tercio": (1, 1, 1, 1 / 3), "s2_w4_triple": (1, 1, 1, 3), "completo": (1, 1, 1, 1)}
    NOMBRE_CAL = {"s2_pesos_iniciales": "Antes de calibrar", "s2_w2_doble": "$w_2 times 2$", "s2_w2_mitad": "$w_2 times 0,5$",
                  "s2_w4_cero": "$w_4 times 0$", "s2_w4_tercio": "$w_4 times 1\\/3$", "s2_w4_triple": "$w_4 times 3$",
                  "completo": "*Adoptados*"}
    w_ref = E.POLITICAS["AHORRO"]["w"]
    filas_cal = []
    for nombre, mult in MULT.items():
        if nombre not in V["x"]:
            continue
        v = V["x"][nombre]
        filas_cal.append([NOMBRE_CAL[nombre], "(%s)" % "; ".join(es(w * k, 1) for w, k in zip(w_ref, mult)),
                          "%s ± %s" % (v["ratio"], v["sd"]), v["delta_tabla"], v["peor_en"], v["hielo"], v["bat"], v["primeros"]])
    tabla_typ("calibracion.typ", "(auto, auto, auto, 1fr, 1fr, 1fr, 1fr, 1fr)", "(left, left) + (right,) * 6",
              ["Pesos", "$(w_1; w_2; w_3; w_4)$ en `AHORRO`", "Ratio ± desv.", "Δ Ratio", "Peor en", "Hielo", "Bat.", "1.º"], filas_cal)

    # S4 · Tabla con y sin subastas
    if "s4_sin_subastas" in V["x"]:
        a, b = V["x"]["completo"], V["x"]["s4_sin_subastas"]
        tabla_typ("subastas.typ", "(1fr, auto, auto, auto, auto, auto, auto)", "(left,) + (right,) * 6",
                  ["", "Viajes en vano", "Bat. en pasos", "Hielo", "Hielo / 100 bat.", "Mensajes", "Ratio ± desv."],
                  [["Con subastas (entrega)", a["viajes"], a["bat_pasos"], a["hielo"], a["hielo_por_bat100"], a["msgs"], "%s ± %s" % (a["ratio"], a["sd"])],
                   ["Sin subastas", b["viajes"], b["bat_pasos"], b["hielo"], b["hielo_por_bat100"], b["msgs"], "%s ± %s" % (b["ratio"], b["sd"])]])

    # S5 · Elecciones reales: conteo por método y una elección concreta
    con_voto = [r for r in exp if r.get("desempates") and sum(r["desempates"].values())]
    metodos = Counter()
    for r in con_voto:
        metodos.update(r["desempates"])
    if torneo:
        for f_ in N:
            metodos.update(f_["interno"].get("desempates", {}))
    total_el = sum(metodos.values())
    cands = E.ORDEN_POLITICAS

    def condorcet(mat):
        for a_ in cands:
            if all(mat[a_][b_] > mat[b_][a_] for b_ in cands if b_ != a_):
                return a_
        return None

    todas = []   # (variante, semilla, vigente antes, voto)
    for r in exp:
        vigente = E.POLITICA_INICIAL if "expansion" not in r["variante"] else "EXPANSION"
        for voto in r.get("votos") or []:
            todas.append((r["variante"], r["semilla"], vigente, voto))
            vigente = voto["ganadora"]
    sin_cw = [t_ for t_ in todas if condorcet(t_[3]["matriz"]) is None]
    V["x"]["votos"] = {
        "total": str(total_el), "copeland": str(metodos.get("copeland", 0)), "borda": str(metodos.get("borda", 0)),
        "orden_fijo": str(metodos.get("orden_fijo", 0)), "inercia": str(metodos.get("inercia", 0)),
        "exportadas": str(len(todas)), "sin_condorcet": str(len(sin_cw)),
    }
    if todas:
        def interes(t_):
            var, _, vig, voto = t_
            return (var == "completo", voto["desempate"] in ("borda", "orden_fijo"), condorcet(voto["matriz"]) is None,
                    voto["desempate"] == "inercia", voto["cambio"] and voto["ganadora"] != "REPLIEGUE", voto["cambio"])
        var, sem, vig, voto = max(todas, key=interes)
        mat = voto["matriz"]
        filas_v = [["`%s`" % a_] + ["—" if a_ == b_ else str(mat[a_][b_]) for b_ in cands] + [es(voto["copeland"][a_], 1)] for a_ in cands]
        tabla_typ("copeland.typ", "(auto, 1fr, 1fr, 1fr, 1fr, auto)", "(left,) + (right,) * 5",
                  ["$a$ frente a $b$"] + ["`%s`" % c_[:3] for c_ in cands] + ["Copeland"], filas_v)
        cw = condorcet(mat)
        gan = voto["ganadora"]
        # Se rehace el recuento desde la matriz: el conteo de Borda de a es la suma de su fila.
        tope = max(voto["copeland"].values())
        finalistas = [c_ for c_ in cands if voto["copeland"][c_] == tope]
        borda = {c_: sum(mat[c_].values()) for c_ in cands}
        if len(finalistas) > 1:
            mejor_b = max(borda[c_] for c_ in finalistas)
            por_borda = [c_ for c_ in finalistas if borda[c_] == mejor_b]
            top = por_borda[0]
            como = "Borda (%s)" % ", ".join("%s %d" % (c_, borda[c_]) for c_ in finalistas) if len(por_borda) == 1 else "el orden fijo"
            frase = "Empatan en el puntaje de Copeland %s; el desempate por %s da %s" % (" y ".join(finalistas), como, top)
        else:
            top = finalistas[0]
            frase = "El mayor puntaje de Copeland es el de %s" % top
        if top != vig and top != "REPLIEGUE":
            ventaja = mat[top][vig] - mat[vig][top]
            umbral = E.MARGEN_INERCIA * voto["votantes"]
            frase += ". Frente a la vigente %s, su duelo directo queda %d a %d: la ventaja de %d %s el margen de inercia de %s votos" % (
                vig, mat[top][vig], mat[vig][top], ventaja, "supera" if ventaja > umbral else "no supera", es(umbral, 1))
        V["x"]["voto"] = {
            "variante": var, "semilla": str(sem), "tick": str(voto["tick"]), "votantes": str(voto["votantes"]),
            "vigente": vig, "ganadora": gan, "metodo": voto["desempate"], "cambio": "cambia" if voto["cambio"] else "no cambia",
            "condorcet": ("El ganador de Condorcet es %s" % cw) if cw else "No hay ganador de Condorcet", "frase": frase,
        }

    # Figura: Δ Ratio por variante (pareado por semilla)
    if deltas_fig:
        fig, ax = plt.subplots(figsize=(6.9, 0.2 * len(deltas_fig) + 0.6))
        col_ses = {"S1": C[0], "S2": C[1], "S3": C[2], "S4": C[3], "S5": C[4]}
        for y, (nombre, ds) in enumerate(deltas_fig):
            col = col_ses[ETIQUETAS[nombre][0]]
            ax.plot(ds, [y] * len(ds), "o", ms=3, color=col, alpha=0.35, mew=0)
            ax.plot(st.mean(ds), y, "D", ms=5, color=col, mec="white", mew=0.8)
        ax.axvline(0, color="#333333", lw=0.8)
        ax.set_yticks(range(len(deltas_fig)), [ETIQ_FIG[n] for n, _ in deltas_fig])
        ax.invert_yaxis()
        ax.set_xlabel("Δ Ratio frente a su referencia, por semilla (rombo: media). A la izquierda de 0, la variante rinde menos.")
        ax.grid(axis="y", visible=False)
        sns.despine(ax=ax, left=True)
        guardar(fig, "experimentos.svg")

    # Figura: cobertura del cuadrante propio
    curvas = [(n, por[n]) for n in ("completo", "s1_un_solo_gajo") if n in por and any(f["cobertura"] for f in por[n])]
    if curvas:
        fig, ax = plt.subplots(figsize=(3.3, 1.75))
        nombres = {"completo": "Equipo entregado", "s1_un_solo_gajo": "Un solo gajo de patrulla"}
        V["x"]["cob"] = {}
        for i, (nombre, fs) in enumerate(curvas):
            tmax = min(max(t for t, _ in f["cobertura"]) for f in fs)
            ts = [t for t, _ in fs[0]["cobertura"] if t <= min(tmax, 600)]
            ys = [100 * st.mean(dict(map(tuple, f["cobertura"]))[t] for f in fs) for t in ts]
            ax.plot(ts, ys, lw=1.6, color=C[i], label=nombres[nombre], ls="-" if i == 0 else "--")
            V["x"]["cob"][nombre] = {str(t): es(y, 0) for t, y in zip(ts, ys)}
            V["x"]["cob"][nombre]["t100"] = next((es(y, 0) for t, y in zip(ts, ys) if y >= 99.95), "—")
            V["x"]["cob"][nombre]["tick100"] = next((str(t) for t, y in zip(ts, ys) if y >= 99.95), "—")
        ax.set_xlabel("Tick de la partida")
        ax.set_ylabel("Cuadrante propio visto (%)")
        ax.set_ylim(None, 101)
        ax.legend(loc="lower right")
        sns.despine(ax=ax)
        guardar(fig, "cobertura.svg")

# ----------------------------------------------------------------------------------------------
# Latencia (latencia.json)
# ----------------------------------------------------------------------------------------------
import platform  # noqa: E402

_cpu = next((l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name")), "desconocida")
V["maq"] = {"cpu": _cpu, "python": platform.python_version()}
lat_ok = False
flotas = []
for archivo, clave in (("latencia.json", "l"), ("latencia-400.json", "l4")):
    lat = cargar(archivo)
    if not lat:
        continue
    if (REPORTS / archivo).stat().st_mtime < (TB2 / "equipoA.py").stat().st_mtime:
        print("AVISO: %s es ANTERIOR a equipoA.py; hay que repetir latencia.py." % archivo)
    lat_ok = True
    res = lat["resumen"]
    brutos = [m_ for s in lat["por_semilla"] for m_ in s.get("maximos", [s["max"]])]
    V[clave] = {
        "media": es(res["media"], 2), "p95": es(res["p95"], 2), "p99": es(res["p99"], 2), "max": es(res["max"], 2),
        "max_bruto": es(max(brutos), 2), "carga": es(lat.get("carga_1min", 0.0), 1),
        "unidades": str(lat.get("unidades_por_equipo", 50)), "total": str(4 * lat.get("unidades_por_equipo", 50)),
        "repeticiones": str(lat.get("repeticiones", 1)), "semillas": str(len(lat["por_semilla"])),
        "ticks": str(sum(s["ticks"] for s in lat["por_semilla"])),
        "cumple": "sí" if max(brutos) < UMBRAL_MS else "no", "sobre_umbral": str(sum(1 for m_ in brutos if m_ >= UMBRAL_MS)),
        "n_brutos": str(len(brutos)),
    }
    flotas.append((clave, lat, brutos))
if flotas:
    filas = []
    for clave, lat, brutos in flotas:
        v_ = V[clave]
        for s in lat["por_semilla"]:
            filas.append(["%s × 4" % v_["unidades"], str(s["semilla"]), str(s["ticks"]), es(s["media"], 2), es(s["p95"], 2),
                          es(s["p99"], 2), es(s["max"], 2), es(max(s.get("maximos", [s["max"]])), 2)])
        filas.append(["*%s × 4*" % v_["unidades"], "*peor*", v_["ticks"], "*%s*" % v_["media"], "*%s*" % v_["p95"], "*%s*" % v_["p99"],
                      "*%s*" % v_["max"], "*%s*" % v_["max_bruto"]])
    tabla_typ("latencia.typ", "(auto, auto, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr)", "(left,) + (right,) * 7",
              ["Flota", "Sem.", "Turnos", "Media", "p95", "p99", "Máx.", "Máx. rep."], filas)
    fig, ax = plt.subplots(figsize=(3.3, 1.9))
    for i, (clave, lat, brutos) in enumerate(flotas):
        xs, ys = [], []
        for j, s in enumerate(lat["por_semilla"]):
            for m_ in s.get("maximos", [s["max"]]):
                xs.append(j + (i - 0.5 * (len(flotas) - 1)) * 0.3)
                ys.append(m_)
        ax.plot(xs, ys, "os"[i], ms=4, color=C[i], mec="white", mew=0.6, ls="",
                label="%s unidades en total" % V[clave]["total"])
    ax.axhline(UMBRAL_MS, color="#333333", lw=0.9, ls="--")
    n_sem = len(flotas[0][1]["por_semilla"])
    ax.text(n_sem - 0.55, UMBRAL_MS - 1.2, "umbral: 40 ms", ha="right", va="top", fontsize=7.5, color="#333333")
    ax.set_xticks(range(n_sem), [str(s["semilla"]) for s in flotas[0][1]["por_semilla"]])
    ax.set_xlabel("Semilla")
    ax.set_ylabel("Peor turno de cada repetición (ms)")
    ax.set_ylim(0, max(UMBRAL_MS * 1.08, max(max(b_) for _, _, b_ in flotas) * 1.1))
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, 0.9))
    sns.despine(ax=ax)
    guardar(fig, "latencia.svg")

(AQUI / "valores.json").write_text(json.dumps(V, ensure_ascii=False, indent=1))
for nombre, bloque in (("torneo", V.get("t")), ("experimentos", V.get("x"))):
    if bloque is not None and not bloque["version_actual"]:
        print("AVISO: los datos de %s son de una VERSIÓN ANTERIOR del equipo; no sirven para el informe." % nombre)
print("torneo:", bool(torneo), "| experimentos:", "completos" if exp_ok else ("parciales" if exp else "no hay"), "| latencia:", lat_ok)
