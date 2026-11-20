"""Figuras de la portada del repo (README raíz), con los mismos datos que dibujan las
diapositivas: ninguna cifra ni ninguna jaula está a mano.

Escribe en .github/portada/, cada SVG en variante clara y oscura para <picture>:

* heroe-*.svg: la reparación de la foto real, animada. Las jaulas son las que leyó la
  Fase 1, con los dos 3+ que eran 3÷, y la solución es la que devolvió el solver
  (presentacion/datos/foto.json).
* cifras-*.svg: las cuatro cifras de la portada (etiquetas.json, tableros.json).
* tableros-*.svg: qué hizo el sistema con cada uno de los 70 tableros de KrazyDad
  (presentacion/datos/tableros.json).
* arquitectura-*.svg: las dos fases, el contrato entre ellas y las cuatro salidas: la de la
  Fase 1, cuando no puede leer, y las tres del solver.
* telefono.png: la captura del Pixel sin el marco del teléfono.
* app-reparada.png y app-sin-tablero.png: las pantallas (c) y (d) de la app, sueltas.

Con --gif, además, demo.gif: tres tramos de presentacion/video/demo.mp4 (pide
imageio-ffmpeg, que trae su propio ffmpeg).

Los SVG no incrustan imágenes ni tipografías: GitHub los sirve con una CSP que solo deja
pasar estilos en línea. Las animaciones son CSS y respetan prefers-reduced-motion: sin
movimiento se ve el estado final.

Uso:  uv run python scripts/figuras_portada.py
      uv run --with imageio-ffmpeg python scripts/figuras_portada.py --gif
"""
from __future__ import annotations

import json
import subprocess
import sys
from html import escape
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
DATOS = RAIZ / "presentacion" / "datos"
VIDEO = RAIZ / "presentacion" / "video" / "demo.mp4"
SALIDA = RAIZ / ".github" / "portada"

# La paleta de las diapositivas (presentacion/tema.scss): índigo para lo que el sistema
# decide bien, naranja para la lectura equivocada y su reparación.
TEMAS = {
    "claro": dict(
        fondo="#F5F3EE", tarjeta="#FCFBF7", tinta="#15161D", suave="#4A4D5A",
        nota="#6B6E7B", borde="#DEDBD2", rejilla="#D3CFC4", indigo="#4B45C9",
        indigo_palido="#E4E1F7", naranja="#D96A2B", naranja_texto="#B4501A",
        naranja_palido="#F8E3D3", neutro="#B9B6AC", sobre="#FFFFFF",
    ),
    "oscuro": dict(
        fondo="#15161D", tarjeta="#1F2029", tinta="#EDEBF5", suave="#B9B8CC",
        nota="#9A99AD", borde="#2E3040", rejilla="#353746", indigo="#857FEE",
        indigo_palido="#2A2950", naranja="#DD7436", naranja_texto="#F2A65A",
        naranja_palido="#3A2A22", neutro="#5C5E6B", sobre="#15161D",
    ),
}
LETRA = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"
OP = {"+": "+", "*": "×", "-": "−", "/": "÷", "=": ""}


def ms(x: float) -> str:
    return f"{x:.1f}"


def svg(ancho: int, alto: int, titulo: str, desc: str, estilo: str, cuerpo: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho} {alto}" '
        f'width="{ancho}" height="{alto}" role="img" aria-labelledby="t d" '
        f'font-family="{LETRA}">\n'
        f"<title id=\"t\">{escape(titulo)}</title>\n<desc id=\"d\">{escape(desc)}</desc>\n"
        f"<style>{estilo}</style>\n{cuerpo}\n</svg>\n"
    )


def texto(x: float, y: float, s: str, tam: float, color: str, peso: int = 400,
          ancla: str = "start", extra: str = "") -> str:
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{tam}" font-weight="{peso}" '
            f'fill="{color}" text-anchor="{ancla}"{extra}>{escape(s)}</text>')


# --------------------------------------------------------------------------- héroe

def heroe(t: dict, foto: dict) -> str:
    """El tablero de la foto real: se lee, el solver dice que así no tiene solución,
    repara las dos jaulas y lo resuelve. Un ciclo de 14 s; sin movimiento, el final."""
    n = foto["n"]
    jaulas = foto["jaulas"]
    sol = foto["solucion"]
    corr = {tuple(c["celda"]): c for c in foto["correcciones"]}
    primera = next(iter(corr.values()))
    leido, corregido, malos = primera["leido"], primera["corregido"], len(corr)
    W, H = 880, 512
    x0, y0, lado = 36, 36, 440
    c = lado / n

    dueño = {}
    for k, j in enumerate(jaulas):
        for r, q in j["celdas"]:
            dueño[(r, q)] = k

    partes = [f'<rect width="{W}" height="{H}" rx="28" fill="{t["fondo"]}"/>',
              f'<rect x="{x0}" y="{y0}" width="{lado}" height="{lado}" fill="{t["tarjeta"]}"/>']

    # Las jaulas que se corrigen quedan marcadas, como en la app.
    marcas = []
    for j in jaulas:
        if tuple(min(j["celdas"])) in corr:
            for r, q in j["celdas"]:
                marcas.append(f'<rect x="{x0 + q * c:.1f}" y="{y0 + r * c:.1f}" '
                              f'width="{c:.1f}" height="{c:.1f}" fill="{t["naranja_palido"]}"/>')
    partes.append(f'<g class="a marca">{"".join(marcas)}</g>')

    finas = []
    for i in range(1, n):
        finas.append(f'<line x1="{x0 + i * c:.1f}" y1="{y0}" x2="{x0 + i * c:.1f}" y2="{y0 + lado}"/>')
        finas.append(f'<line x1="{x0}" y1="{y0 + i * c:.1f}" x2="{x0 + lado}" y2="{y0 + i * c:.1f}"/>')
    partes.append(f'<g stroke="{t["rejilla"]}" stroke-width="1.6">{"".join(finas)}</g>')

    gruesas = []
    for r in range(n):
        for q in range(n):
            if q + 1 < n and dueño[(r, q)] != dueño[(r, q + 1)]:
                x = x0 + (q + 1) * c
                gruesas.append(f'<line x1="{x:.1f}" y1="{y0 + r * c:.1f}" x2="{x:.1f}" y2="{y0 + (r + 1) * c:.1f}"/>')
            if r + 1 < n and dueño[(r, q)] != dueño[(r + 1, q)]:
                y = y0 + (r + 1) * c
                gruesas.append(f'<line x1="{x0 + q * c:.1f}" y1="{y:.1f}" x2="{x0 + (q + 1) * c:.1f}" y2="{y:.1f}"/>')
    partes.append(f'<g class="a jaulas" stroke="{t["tinta"]}" stroke-width="5" '
                  f'stroke-linecap="square">{"".join(gruesas)}</g>')

    etiquetas, malas, buenas = [], [], []
    for j in jaulas:
        r, q = min(j["celdas"])
        x, y = x0 + q * c + 7, y0 + r * c + 25
        if (r, q) in corr:
            malas.append(texto(x, y + 2, leido, 28, t["naranja_texto"], 700))
            buenas.append(texto(x, y + 2, corregido, 28, t["naranja_texto"], 700))
        else:
            etiquetas.append(texto(x, y, j["etiqueta"], 21, t["suave"], 600))
    partes.append(f'<g class="a etiq">{"".join(etiquetas)}</g>')
    partes.append(f'<g class="a malo">{"".join(malas)}</g>')
    partes.append(f'<g class="a bueno">{"".join(buenas)}</g>')

    digitos = []
    for r in range(n):
        for q in range(n):
            digitos.append(
                f'<text class="a dig" style="animation-delay:{(r + q) * 0.07:.2f}s" '
                f'x="{x0 + (q + 0.5) * c:.1f}" y="{y0 + (r + 0.83) * c:.1f}" font-size="42" '
                f'font-weight="500" fill="{t["indigo"]}" text-anchor="middle">{sol[r][q]}</text>')
    partes.append("".join(digitos))

    partes.append(f'<rect class="a marco" x="{x0}" y="{y0}" width="{lado}" height="{lado}" '
                  f'fill="none" stroke="{t["tinta"]}" stroke-width="6"/>')
    partes.append(f'<rect class="a escaneo" x="{x0}" y="{y0 - 2}" width="{lado}" height="4" '
                  f'fill="{t["indigo"]}"/>')

    # Mientras se verifica, un sello sobre el tablero: así leído no tiene solución.
    sx, sy, sw, sh = x0 + lado / 2 - 150, y0 + lado / 2 - 40, 300, 80
    partes.append(f'<g class="a sello"><rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="16" '
                  f'fill="{t["naranja_palido"]}" stroke="{t["naranja"]}" stroke-width="4"/>'
                  + texto(x0 + lado / 2, sy + 53, "0 soluciones", 36, t["naranja_texto"], 700, "middle")
                  + "</g>")

    # A la derecha, los cuatro pasos: título y estado, que se encienden con el tablero.
    pasos = [
        ("Leer", f"lee {leido} donde dice {corregido}", t["indigo"], t["naranja_texto"]),
        ("Verificar", "0 soluciones", t["naranja"], t["naranja_texto"]),
        ("Reparar", f"única corrección: {corregido}", t["naranja"], t["naranja_texto"]),
        ("Resolver", "solución única", t["indigo"], t["indigo"]),
    ]
    px, py, paso_y = 524, 84, 114
    for i, (titulo, estado, color, color_texto) in enumerate(pasos):
        y = py + i * paso_y
        if i < len(pasos) - 1:
            partes.append(f'<line x1="{px}" y1="{y + 25}" x2="{px}" y2="{y + paso_y - 25}" '
                          f'stroke="{t["borde"]}" stroke-width="4" stroke-linecap="round"/>')
            partes.append(f'<line class="a riel{i + 1}" x1="{px}" y1="{y + 25}" x2="{px}" '
                          f'y2="{y + paso_y - 25}" stroke="{pasos[i + 1][2]}" stroke-width="4" '
                          f'stroke-linecap="round"/>')
        partes.append(
            f'<g class="a paso{i + 1}">'
            f'<circle cx="{px}" cy="{y}" r="21" fill="{color}"/>'
            + texto(px, y + 8, str(i + 1), 23, t["sobre"], 700, "middle")
            + texto(px + 38, y + 12, titulo, 36, t["tinta"], 700)
            + texto(px + 38, y + 53, estado, 28, color_texto, 500)
            + "</g>")

    T = 14
    cuadros = f"""
.a {{ animation-duration: {T}s; animation-iteration-count: infinite; animation-fill-mode: both;
      animation-timing-function: ease-in-out; }}
.escaneo {{ opacity: 0; animation-name: escaneo; animation-timing-function: linear; }}
@keyframes escaneo {{ 0% {{ transform: translateY(0); opacity: 0 }} 1% {{ opacity: .85 }}
  11% {{ transform: translateY({lado}px); opacity: .85 }} 12%, 100% {{ transform: translateY({lado}px); opacity: 0 }} }}
.jaulas {{ animation-name: jaulas }}
@keyframes jaulas {{ 0%, 2% {{ opacity: 0 }} 10% {{ opacity: 1 }} 93% {{ opacity: 1 }} 98%, 100% {{ opacity: 0 }} }}
.etiq {{ animation-name: etiq }}
@keyframes etiq {{ 0%, 4% {{ opacity: 0 }} 12% {{ opacity: 1 }} 93% {{ opacity: 1 }} 98%, 100% {{ opacity: 0 }} }}
.marca {{ animation-name: marca }}
@keyframes marca {{ 0%, 12% {{ opacity: 0 }} 15% {{ opacity: 1 }} 18% {{ opacity: .35 }} 21% {{ opacity: 1 }}
  93% {{ opacity: 1 }} 98%, 100% {{ opacity: 0 }} }}
.malo {{ opacity: 0; animation-name: malo }}
@keyframes malo {{ 0%, 4% {{ opacity: 0 }} 12% {{ opacity: 1 }} 42% {{ opacity: 1 }} 45%, 100% {{ opacity: 0 }} }}
.bueno {{ animation-name: bueno }}
@keyframes bueno {{ 0%, 44% {{ opacity: 0 }} 48% {{ opacity: 1 }} 93% {{ opacity: 1 }} 98%, 100% {{ opacity: 0 }} }}
.marco {{ animation-name: marco }}
@keyframes marco {{ 0%, 21% {{ stroke: {t["tinta"]} }} 24%, 40% {{ stroke: {t["naranja"]} }} 44%, 100% {{ stroke: {t["tinta"]} }} }}
.sello {{ opacity: 0; animation-name: sello }}
@keyframes sello {{ 0%, 23% {{ opacity: 0; transform: scale(.9) }} 26% {{ opacity: 1; transform: scale(1) }}
  39% {{ opacity: 1; transform: scale(1) }} 42%, 100% {{ opacity: 0; transform: scale(1) }} }}
.sello {{ transform-box: fill-box; transform-origin: center; }}
.dig {{ animation-name: dig }}
@keyframes dig {{ 0%, 58% {{ opacity: 0; transform: translateY(10px) }} 63% {{ opacity: 1; transform: translateY(0) }}
  93% {{ opacity: 1 }} 98%, 100% {{ opacity: 0 }} }}
.paso2 {{ animation-name: paso2 }} .paso3 {{ animation-name: paso3 }} .paso4 {{ animation-name: paso4 }}
@keyframes paso2 {{ 0%, 21% {{ opacity: .25 }} 24%, 94% {{ opacity: 1 }} 98%, 100% {{ opacity: .25 }} }}
@keyframes paso3 {{ 0%, 41% {{ opacity: .25 }} 44%, 94% {{ opacity: 1 }} 98%, 100% {{ opacity: .25 }} }}
@keyframes paso4 {{ 0%, 57% {{ opacity: .25 }} 60%, 94% {{ opacity: 1 }} 98%, 100% {{ opacity: .25 }} }}
.riel1, .riel2, .riel3 {{ transform-box: fill-box; transform-origin: top; }}
.riel1 {{ animation-name: riel1 }} .riel2 {{ animation-name: riel2 }} .riel3 {{ animation-name: riel3 }}
@keyframes riel1 {{ 0%, 12% {{ transform: scaleY(0) }} 22%, 94% {{ transform: scaleY(1) }} 98%, 100% {{ transform: scaleY(0) }} }}
@keyframes riel2 {{ 0%, 32% {{ transform: scaleY(0) }} 42%, 94% {{ transform: scaleY(1) }} 98%, 100% {{ transform: scaleY(0) }} }}
@keyframes riel3 {{ 0%, 49% {{ transform: scaleY(0) }} 58%, 94% {{ transform: scaleY(1) }} 98%, 100% {{ transform: scaleY(0) }} }}
@media (prefers-reduced-motion: reduce) {{ .a {{ animation: none !important }} }}
"""
    titulo = "El solver repara una lectura equivocada"
    desc = (f"Un KenKen de {n}×{n} leído de una foto real. La visión lee {leido} en {malos} "
            f"jaulas que dicen {corregido}; CP-SAT demuestra que así no tiene solución, prueba "
            f"lecturas vecinas, corrige esas jaulas y resuelve el tablero.")
    return svg(W, H, titulo, desc, cuadros, "\n".join(partes))


# ------------------------------------------------------------------------ cifras

def cifras(t: dict, filas: list[dict], etiq: dict) -> str:
    """Las cuatro cifras de la portada, de la etiqueta al tablero: cuánto se lee bien,
    cuántos tableros salen enteros, cuántas lecturas repara el solver y cuántas terminan
    en una solución errónea. En 2×2 para que el pie se lea en un celular."""
    n = sum(g["n"] for g in etiq.values())
    bien = sum(g["bien"] for g in etiq.values())
    enteros = sum(f["lectura"] == "bien" for f in filas)
    mal = [f for f in filas if f["lectura"] != "bien"]
    sin_sol = [f for f in mal if f["lectura"] == "sin_solucion"]
    reparadas = sum(f.get("reparacion") == "bien" for f in sin_sol)
    erroneas = sum(f.get("reparacion") not in (None, "bien", "abstiene") for f in mal)
    celdas = [
        (f"{100 * bien / n:.2f}%", t["indigo"], [f"de {n} etiquetas en PDF,", "leídas sin error"]),
        (f"{enteros} de {len(filas)}", t["indigo"], ["tableros en PDF leídos", "sin un solo error"]),
        (f"{reparadas} de {len(sin_sol)}", t["naranja_texto"], ["lecturas sin solución,", "reparadas por el solver"]),
        (f"{erroneas} de {len(mal)}", t["indigo"], ["mal leídos que terminan", "en una solución errónea"]),
    ]
    W, H, cw, ch = 760, 300, 380, 150
    p = [f'<rect width="{W}" height="{H}" rx="24" fill="{t["fondo"]}"/>',
         f'<line x1="{cw}" y1="26" x2="{cw}" y2="{H - 26}" stroke="{t["borde"]}" stroke-width="2"/>',
         f'<line x1="26" y1="{ch}" x2="{W - 26}" y2="{ch}" stroke="{t["borde"]}" stroke-width="2"/>']
    for i, (cifra, color, pie) in enumerate(celdas):
        cx, y = cw * (i % 2) + cw / 2, ch * (i // 2)
        p.append(texto(cx, y + 66, cifra, 54, color, 700, "middle", ' letter-spacing="-1"'))
        for k, linea in enumerate(pie):
            p.append(texto(cx, y + 100 + k * 28, linea, 23, t["suave"], 400, "middle"))
    desc = "; ".join(f"{c}: {' '.join(pie)}" for c, _, pie in celdas)
    return svg(W, H, "El TB1 en cuatro cifras", desc, "", "\n".join(p))


# ------------------------------------------------------------------- 70 tableros

def tableros(t: dict, filas: list[dict]) -> str:
    """Cada tablero real es un cuadrado con su rejilla de n×n, agrupado por lo que hizo
    el sistema con él."""
    def clase(f: dict) -> str:
        if f["lectura"] == "bien":
            return "bien"
        if f["lectura"] == "rechazado":
            return "rechazado"
        return "reparado" if f.get("reparacion") == "bien" else "abstiene"

    grupos: dict[str, list[dict]] = {"bien": [], "reparado": [], "abstiene": [], "rechazado": []}
    for f in sorted(filas, key=lambda f: f["n"]):
        grupos[clase(f)].append(f)
    total = len(filas)
    mal = total - len(grupos["bien"])

    W, H = 900, 410
    u, g = 32, 7  # lado de cada tablero y separación

    def mini(x: float, y: float, n: int, relleno: str, trazo: str, rayas: str) -> str:
        paso = u / n
        lineas = "".join(
            f'<line x1="{x + i * paso:.1f}" y1="{y:.1f}" x2="{x + i * paso:.1f}" y2="{y + u:.1f}"/>'
            f'<line x1="{x:.1f}" y1="{y + i * paso:.1f}" x2="{x + u:.1f}" y2="{y + i * paso:.1f}"/>'
            for i in range(1, n))
        return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{u}" height="{u}" rx="3" fill="{relleno}" '
                f'stroke="{trazo}" stroke-width="2"/>'
                f'<g stroke="{rayas}" stroke-width="1" opacity=".55">{lineas}</g>')

    estilo_de = {
        "bien": (t["indigo"], t["indigo"], t["sobre"]),
        "reparado": (t["naranja"], t["naranja"], t["sobre"]),
        "abstiene": (t["tarjeta"], t["naranja"], t["naranja"]),
        "rechazado": (t["neutro"], t["neutro"], t["sobre"]),
    }
    partes = [f'<rect width="{W}" height="{H}" rx="24" fill="{t["fondo"]}"/>']

    # Izquierda: los bien leídos.
    ax, ay, cols_a = 40, 96, 8
    partes.append(texto(ax, 52, f"{len(grupos['bien'])} leídos sin error", 30, t["indigo"], 700))
    partes.append(texto(ax, 80, "y resueltos sin intervención", 19, t["nota"]))
    for i, f in enumerate(grupos["bien"]):
        partes.append(mini(ax + (i % cols_a) * (u + g), ay + (i // cols_a) * (u + g), f["n"],
                           *estilo_de["bien"]))

    # Derecha: los mal leídos, y qué pasó con cada uno.
    bx, by, cols_b = 420, 96, 6
    partes.append(texto(bx, 52, f"{mal} con algún error", 30, t["naranja_texto"], 700))
    partes.append(texto(bx, 80, "ninguno termina en una solución errónea", 19, t["nota"]))
    i = 0
    for clave in ("reparado", "abstiene", "rechazado"):
        for f in grupos[clave]:
            partes.append(mini(bx + (i % cols_b) * (u + g), by + (i // cols_b) * (u + g), f["n"],
                               *estilo_de[clave]))
            i += 1
    leyenda = [
        ("reparado", f"{len(grupos['reparado'])}", "el solver lo nota y lo repara"),
        ("abstiene", f"{len(grupos['abstiene'])}", "el solver lo nota y pide otra foto"),
        ("rechazado", f"{len(grupos['rechazado'])}", "etiqueta ilegible: se rechaza"),
    ]
    lx, ly = bx, by + 4 * (u + g) + 26
    for k, (clave, cuenta, frase) in enumerate(leyenda):
        y = ly + k * 34
        relleno, trazo, _ = estilo_de[clave]
        partes.append(f'<rect x="{lx}" y="{y - 17}" width="20" height="20" rx="3" fill="{relleno}" '
                      f'stroke="{trazo}" stroke-width="2"/>')
        partes.append(texto(lx + 32, y, cuenta, 21, t["tinta"], 700))
        partes.append(texto(lx + 62, y, frase, 21, t["suave"]))

    tamaños = sorted({f["n"] for f in filas})
    partes.append(texto(ax, H - 24, "Cada cuadro es un tablero de KrazyDad (PDF), con su rejilla de "
                        + ", ".join(f"{n}×{n}" for n in tamaños[:-1]) + f" o {tamaños[-1]}×{tamaños[-1]}.",
                        17, t["nota"]))

    titulo = f"Qué hizo el sistema con los {total} tableros de KrazyDad"
    desc = (f"{len(grupos['bien'])} de {total} tableros se leen bien y se resuelven. De los "
            f"{mal} mal leídos, ninguno llega a una solución errónea: el solver repara "
            f"{len(grupos['reparado'])}, se abstiene en {len(grupos['abstiene'])} y "
            f"{len(grupos['rechazado'])} se rechazan por una etiqueta ilegible.")
    return svg(W, H, titulo, desc, "", "\n".join(partes))


# ----------------------------------------------------------------- arquitectura

def arquitectura(t: dict) -> str:
    W, H = 1000, 446

    def caja(x, y, w, h, titulo, sub, borde, fondo, tit_color, punteada=False):
        dash = ' stroke-dasharray="7 6"' if punteada else ""
        out = [(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{fondo}" '
                f'stroke="{borde}" stroke-width="2.5"{dash}/>'),
               texto(x + w / 2, y + 40, titulo, 25, tit_color, 700, "middle")]
        for k, linea in enumerate(sub):
            out.append(texto(x + w / 2, y + 70 + k * 24, linea, 18, t["suave"], 400, "middle"))
        return "".join(out)

    def flecha(x1, y1, x2, y2, color, rotulo=""):
        out = [(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="3" '
                f'marker-end="url(#punta-{color[1:]})"/>')]
        if rotulo:
            out.append(texto((x1 + x2) / 2, min(y1, y2) - 10, rotulo, 16, t["nota"], 400, "middle"))
        return "".join(out)

    colores = dict.fromkeys([t["nota"], t["indigo"], t["naranja"], t["neutro"]])  # orden fijo
    defs = "".join(
        f'<marker id="punta-{c[1:]}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" '
        f'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
        for c in colores)
    p = [f'<defs>{defs}</defs>', f'<rect width="{W}" height="{H}" rx="24" fill="{t["fondo"]}"/>']

    # El nodo (la PC) envuelve las dos fases; la app solo le habla por HTTP.
    p.append(f'<rect x="206" y="22" width="772" height="214" rx="20" fill="none" '
             f'stroke="{t["nota"]}" stroke-width="2" stroke-dasharray="3 7" stroke-linecap="round"/>')
    p.append(texto(228, 50, "Nodo · FastAPI en la PC", 17, t["nota"], 600))
    p.append(texto(958, 50, "POST /resolver", 16, t["nota"], 400, "end",
                   f' font-family="{MONO}"'))

    y, h = 68, 148
    p.append(caja(22, y, 156, h, "App", ["Android", "toma la foto"],
                  t["borde"], t["tarjeta"], t["tinta"]))
    p.append(flecha(178, y + 74, 222, y + 74, t["nota"]))
    p.append(caja(226, y, 224, h, "Fase 1 · visión", ["sin aprendizaje:", "rejilla, jaulas",
                                                      "y etiquetas"],
                  t["borde"], t["tarjeta"], t["tinta"]))
    p.append(flecha(450, y + 74, 490, y + 74, t["nota"]))
    p.append(caja(494, y, 196, h, "Instancia", ["tamaño y jaulas:", "el contrato"],
                  t["indigo"], t["indigo_palido"], t["indigo"], punteada=True))
    p.append(flecha(690, y + 74, 730, y + 74, t["nota"]))
    p.append(caja(734, y, 224, h, "Fase 2 · CP-SAT", ["resuelve y cuenta", "hasta 2 soluciones"],
                  t["borde"], t["tarjeta"], t["tinta"]))

    # Abajo, las cuatro salidas. La primera es de la Fase 1: lo que no se pudo leer no
    # llega al solver. Las otras tres son de CP-SAT, por un bus ortogonal.
    oy, oh = 300, 124
    temprana = (22, 222, "Sin lectura", ["etiqueta ilegible o", "jaulas inválidas:", "pide otra foto"],
                t["neutro"], t["tarjeta"], t["suave"])
    salidas = [
        (264, 214, "1 solución", ["se devuelve"], t["indigo"], t["indigo_palido"], t["indigo"]),
        (500, 236, "0 soluciones", ["repara con la única", "corrección posible,", "o pide otra foto"],
         t["naranja"], t["naranja_palido"], t["naranja_texto"]),
        (758, 220, "2 o más", ["se rechaza con", "un mensaje claro"], t["neutro"], t["tarjeta"], t["suave"]),
    ]
    x1c, bajada = 226 + 112, 250
    tx = temprana[0] + temprana[1] / 2
    p.append(f'<path d="M{x1c},{y + h} V{bajada} H{tx} V{oy - 6}" fill="none" stroke="{t["neutro"]}" '
             f'stroke-width="3" marker-end="url(#punta-{t["neutro"][1:]})"/>')
    p.append(caja(temprana[0], oy, temprana[1], oh, *temprana[2:]))
    fx, bus = 734 + 112, 270
    centros = [x + w / 2 for x, w, *_ in salidas]
    p.append(f'<path d="M{fx},{y + h} V{bus} M{min(centros)},{bus} H{max(centros)}" fill="none" '
             f'stroke="{t["nota"]}" stroke-width="3" stroke-linecap="round"/>')
    for (x, w, tit, sub, borde, fondo, color), cx in zip(salidas, centros):
        p.append(flecha(cx, bus, cx, oy - 4, borde))
        p.append(caja(x, oy, w, oh, tit, sub, borde, fondo, color))

    titulo = "Arquitectura: la visión y el solver solo se hablan por la instancia"
    desc = ("La app manda la foto al nodo; la Fase 1 la convierte en una instancia (tamaño y "
            "jaulas), que es lo único que ve la Fase 2. Si una etiqueta es ilegible o las jaulas "
            "no son válidas, pide otra foto antes del solver. CP-SAT resuelve y cuenta hasta dos "
            "soluciones: con una se devuelve, con ninguna intenta reparar la lectura, con "
            "varias rechaza.")
    return svg(W, H, titulo, desc, "", "\n".join(p))


# -------------------------------------------------------------------- teléfono

def telefono(destino: Path, bisel: int = 16) -> None:
    """La captura del Pixel (presentacion/img/telefono.png) sin el marco del teléfono: el
    marco deja esquinas blancas sobre fondo oscuro y el GIF de la demo no lo tiene."""
    from PIL import Image, ImageDraw

    im = Image.open(RAIZ / "presentacion" / "img" / "telefono.png").convert("RGB")
    w, h = im.size
    im = im.crop((bisel, bisel, w - bisel, h - bisel))
    # El marco es redondeado: en las esquinas queda el blanco de fondo. Se pinta del color
    # del marco, que se funde con la interfaz oscura de la app.
    marco = im.getpixel((im.width // 2, 2))
    for esquina in ((0, 0), (im.width - 1, 0), (0, im.height - 1), (im.width - 1, im.height - 1)):
        if min(im.getpixel(esquina)) > 200:
            ImageDraw.floodfill(im, esquina, marco, thresh=60)
    im.save(destino, optimize=True)


# ------------------------------------------------------------------- pantallas

def pantallas(destinos: dict[str, Path]) -> None:
    """Las pantallas (c) y (d) de presentacion/img/app.png, sueltas: la lectura reparada y la
    foto sin tablero. Juntas, las cuatro no se leen en un celular."""
    import numpy as np
    from PIL import Image

    im = Image.open(RAIZ / "presentacion" / "img" / "app.png").convert("RGB")
    gris = np.asarray(im.convert("L"))
    # Los paneles son los tramos de columnas que no son blanco puro.
    tinta = ~(gris > 250).all(axis=0)
    bordes = np.flatnonzero(np.diff(np.r_[False, tinta, False].astype(int)))
    paneles = [(a, b) for a, b in zip(bordes[::2], bordes[1::2]) if b - a > 100]
    for letra, destino in destinos.items():
        x0, x1 = paneles["abcd".index(letra)]
        # Bajo la letra del panel empieza el marco: la primera fila larga con tinta.
        filas = (gris[:, x0:x1] < 250).sum(axis=1)
        y0 = next(y for y in range(48, gris.shape[0]) if filas[y] > (x1 - x0) * 0.9)
        im.crop((int(x0), int(y0), int(x1), im.height)).save(destino, optimize=True)


# ------------------------------------------------------------------------- GIF

# Tramos de demo.mp4 (inicio, fin, velocidad): la foto en Modo Rápido y su solución,
# el cambio a tablero limpio, y el Modo Asistencia revelando casillas.
TRAMOS = ((7.5, 13.5, 1.0), (57.0, 61.8, 1.0), (68.0, 84.5, 3.0))


def gif(destino: Path, ancho: int = 300, fps: int = 12) -> None:
    import imageio_ffmpeg  # solo para --gif

    ff = imageio_ffmpeg.get_ffmpeg_exe()
    trozos, etiquetas = [], []
    for k, (a, b, v) in enumerate(TRAMOS):
        trozos.append(f"[0:v]trim={a}:{b},setpts=(PTS-STARTPTS)/{v}[t{k}]")
        etiquetas.append(f"[t{k}]")
    filtro = (";".join(trozos) + f";{''.join(etiquetas)}concat=n={len(TRAMOS)}:v=1:a=0,"
              f"tpad=stop_mode=clone:stop_duration=1.5,fps={fps},scale={ancho}:-2:flags=lanczos,"
              "split[s0][s1];[s0]palettegen=max_colors=96:stats_mode=diff[p];"
              "[s1][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle")
    subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-i", str(VIDEO),
                    "-filter_complex", filtro, "-loop", "0", str(destino)], check=True)


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    foto = json.loads((DATOS / "foto.json").read_text())
    filas = json.loads((DATOS / "tableros.json").read_text())
    etiq = json.loads((DATOS / "etiquetas.json").read_text())
    for nombre, t in TEMAS.items():
        for base, contenido in (("heroe", heroe(t, foto)), ("cifras", cifras(t, filas, etiq)),
                                ("tableros", tableros(t, filas)), ("arquitectura", arquitectura(t))):
            ruta = SALIDA / f"{base}-{nombre}.svg"
            ruta.write_text(contenido)
            print(f"{ruta.relative_to(RAIZ)}  {len(contenido.encode()) / 1024:.1f} kB")
    ruta = SALIDA / "telefono.png"
    telefono(ruta)
    print(f"{ruta.relative_to(RAIZ)}  {ruta.stat().st_size / 1024:.0f} kB")
    rutas = {"c": SALIDA / "app-reparada.png", "d": SALIDA / "app-sin-tablero.png"}
    pantallas(rutas)
    for ruta in rutas.values():
        print(f"{ruta.relative_to(RAIZ)}  {ruta.stat().st_size / 1024:.0f} kB")
    if "--gif" in sys.argv:
        ruta = SALIDA / "demo.gif"
        gif(ruta)
        print(f"{ruta.relative_to(RAIZ)}  {ruta.stat().st_size / 1024:.0f} kB")


if __name__ == "__main__":
    main()
