"""Exporta los datos que dibujan las diapositivas (presentacion/), para que ninguna cifra
de la exposición se escriba a mano.

Produce, en el directorio de salida:
* foto.json y img/: la Fase 1 paso a paso sobre una foto real tomada con el celular
  (umbral, cuadrilátero, perfiles de la rejilla, grosor de aristas, etiquetas, reparación).
* tableros.json: por cada tablero real, su lectura, la reparación y las dos formulaciones.
* reparacion.json: la reparación de las 19 lecturas sin solución con distintos parámetros.
* etiquetas.json: aciertos y confusiones de la lectura de etiquetas, por conjunto.
* datos.js: todo lo anterior como `window.DATOS`, para que el deck abra sin servidor.

Los tableros de KrazyDad no se redistribuyen: de ellos solo salen identificadores y cifras.

Uso: PYTHONPATH=. uv run python scripts/datos_diapos.py FOTO [data_scraped/extraidos] [salida]
"""
from __future__ import annotations

import base64, json, sys, time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from comparar_formulaciones import medir  # noqa: E402

from kenken_cp.reparar import candidatas, reparar  # noqa: E402
from kenken_cp.solver import contar_soluciones, resolver  # noqa: E402
from kenken_cv.cages import _otsu_1d, medir_aristas  # noqa: E402
import kenken_cv.glyphs as G  # noqa: E402
from kenken_cv.glyphs import EtiquetaIlegible, leer_recorte, recortar_etiqueta  # noqa: E402
from kenken_cv.grid import LADO, _binarizar, _perfil, _puntuar, rectificar  # noqa: E402
from kenken_cv.pipeline import leer  # noqa: E402
from kenken_cv.schema import Instance  # noqa: E402

OP = {"+": "+", "*": "×", "-": "−", "/": "÷", "=": ""}


def etiqueta(op: str, t: int) -> str:
    return f"{t}{OP[op]}"


def _png(img: np.ndarray) -> str:
    return "data:image/png;base64," + base64.b64encode(cv2.imencode(".png", img)[1]).decode()


def glifos(rejilla, ancla: tuple[int, int]) -> dict:
    """Cómo se leyó una etiqueta: componentes, glifos normalizados y la correlación de
    cada uno con las plantillas. Espía a `glyphs` en vez de copiar su lógica."""
    cajas, grupos, parches = [], [], []
    agrupar, clasificar = G._agrupar, G.clasificar

    def _agrupar(c):
        cajas.extend(c)
        g = agrupar(c)
        grupos.extend(g)
        return g

    def _clasificar(patch, fuentes):
        parches.append(patch.copy())
        return clasificar(patch, fuentes)

    G._agrupar, G.clasificar = _agrupar, _clasificar
    try:
        recorte = recortar_etiqueta(rejilla, ancla)
        op, objetivo, _ = leer_recorte(recorte)
    finally:
        G._agrupar, G.clasificar = agrupar, clasificar
    banco = G._plantillas(G.BANCO)
    salida = []
    for grupo, patch in zip(grupos, parches):
        normal = G._normalizar(patch)
        puntos = []
        for ch, plantillas in banco.items():
            s, mejor = max((G._correlacion(normal, t), t) for t in plantillas)
            puntos.append({"ch": ch, "s": round(s, 3), "img": _png((255 - mejor * 255).astype(np.uint8))})
        puntos.sort(key=lambda d: -d["s"])
        caja = [min(cajas[j][0] for j in grupo), min(cajas[j][1] for j in grupo),
                max(cajas[j][0] + cajas[j][2] for j in grupo), max(cajas[j][1] + cajas[j][3] for j in grupo)]
        salida.append({"caja": [int(v) for v in caja], "componentes": [[int(v) for v in cajas[j]] for j in grupo],
                       "normal": _png((255 - normal * 255).astype(np.uint8)), "puntos": puntos[:5]})
    return {"ancla": list(ancla), "alto": int(recorte.shape[0]), "ancho": int(recorte.shape[1]),
            "recorte": _png(recorte),
            "leido": etiqueta(op, objetivo), "glifos": salida, "fuentes": len(G.BANCO)}


def fase1(foto: Path, salida: Path) -> dict:
    img_dir = salida / "img"
    img_dir.mkdir(parents=True, exist_ok=True)
    gris = cv2.imread(str(foto), cv2.IMREAD_GRAYSCALE)
    alto, ancho = gris.shape
    escala = 1200 / alto
    chica = cv2.resize(gris, (round(ancho * escala), 1200), interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(img_dir / "f1_foto.jpg"), chica, [cv2.IMWRITE_JPEG_QUALITY, 85])
    cv2.imwrite(str(img_dir / "f1_binaria.png"), 255 - _binarizar(chica))

    warp, h = rectificar(gris)
    cv2.imwrite(str(img_dir / "f1_warp.jpg"), warp, [cv2.IMWRITE_JPEG_QUALITY, 88])
    inv = np.linalg.inv(h)
    marco = np.float32([[0, 0], [LADO, 0], [LADO, LADO], [0, LADO]]).reshape(-1, 1, 2)
    esquinas = cv2.perspectiveTransform(marco, inv).reshape(-1, 2) / [ancho, alto]

    # Perfiles de tinta de los trazos largos (lo mismo que hace encontrar_rejilla).
    binaria = _binarizar(warp)
    largo = max(12, LADO // 15)
    vert = cv2.morphologyEx(binaria, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, largo)))
    hori = cv2.morphologyEx(binaria, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (largo, 1)))
    px, py = _perfil(vert, 0), _perfil(hori, 1)
    puntajes = [
        {"n": n, "x": _puntuar(px, n, LADO) / LADO, "y": _puntuar(py, n, LADO) / LADO}
        for n in range(3, 13)
    ]

    lect = leer(gris)
    rej, inst = lect.rejilla, lect.instancia
    aristas, grosor_marco = medir_aristas(rej)
    valores = np.array(list(aristas.values()), dtype=np.float32)
    umbral = _otsu_1d(valores)

    jaulas = []
    for k, cage in enumerate(inst.cages):
        ancla = min(cage.cells)
        recorte = recortar_etiqueta(rej, ancla)
        cv2.imwrite(str(img_dir / f"f1_etiqueta_{k:02d}.png"), recorte)
        jaulas.append({
            "celdas": [list(c) for c in cage.cells], "op": cage.op, "objetivo": cage.target,
            "etiqueta": etiqueta(cage.op, cage.target),
            "candidatas": [{"etiqueta": etiqueta(o, t), "op": o, "objetivo": t, "peso": w}
                           for o, t, w in candidatas(cage, inst.size)],
        })

    t0 = time.perf_counter(); sin = resolver(inst); t_res = 1000 * (time.perf_counter() - t0)
    t0 = time.perf_counter(); rep = reparar(inst); t_rep = 1000 * (time.perf_counter() - t0)
    n = inst.size
    centros = np.float32([[((rej.xs[c] + rej.xs[c + 1]) / 2, (rej.ys[r] + rej.ys[r + 1]) / 2)
                           for c in range(n)] for r in range(n)]).reshape(-1, 1, 2)
    en_foto = (cv2.perspectiveTransform(centros, inv).reshape(n, n, 2) / [ancho, alto]).round(4)
    return {
        "foto": {"ancho": ancho, "alto": alto, "esquinas": esquinas.round(4).tolist(),
                 "en_foto": en_foto.tolist()},
        "lado": LADO, "n": n, "xs": list(rej.xs), "ys": list(rej.ys),
        "perfil": {"x": (px / LADO).round(4).tolist(), "y": (py / LADO).round(4).tolist()},
        "puntajes": puntajes, "minimo_linea": 0.12,
        "aristas": [{"a": list(a), "b": list(b), "grosor": round(float(g), 2), "gruesa": bool(g > umbral)}
                    for (a, b), g in aristas.items()],
        "umbral": round(float(umbral), 2), "marco": round(float(grosor_marco), 2),
        "jaulas": jaulas,
        "sin_solucion": sin is None, "ms_resolver": round(t_res, 1), "ms_reparar": round(t_rep, 1),
        "correcciones": [{"celda": list(c.celda), "leido": etiqueta(c.leido[0], c.leido[1]),
                          "corregido": etiqueta(c.corregido[0], c.corregido[1])}
                         for c in (rep.correcciones if rep else ())],
        "solucion": [list(f) for f in rep.solucion] if rep else None,
        "plantillas": glifos(rej, tuple(rep.correcciones[0].celda)) if rep else None,
    }


def tableros(raiz: Path) -> tuple[list[dict], dict]:
    filas, sin_sol = [], []
    for js in sorted(raiz.glob("*/tableros/*.json")):
        verdad = Instance.from_json(js.read_text()).canonical()
        sol_verdad = resolver(verdad)
        fila = {"id": js.stem, "cuadernillo": js.parent.parent.name, "n": verdad.size,
                "etiquetas": len(verdad.cages)}
        for variante in ("global", "binaria"):
            ms, ramas, _, _ = medir(verdad, variante)
            fila[variante] = {"ms": round(ms, 2), "ramas": ramas}
        try:
            leida = leer(js.with_suffix(".png")).instancia.canonical()
        except Exception:
            fila["lectura"] = "rechazado"
            filas.append(fila)
            continue
        sol = resolver(leida)
        if leida == verdad:
            fila["lectura"] = "bien"
        elif sol is not None and contar_soluciones(leida, 2) == 1 and sol_verdad is None:
            fila["lectura"] = "bien"  # la verdad extraída del PDF estaba mal (ver informe)
            fila["verdad_erronea"] = True
        elif sol is None:
            fila["lectura"] = "sin_solucion"
            sin_sol.append((fila, leida, sol_verdad))
        else:
            fila["lectura"] = "varias" if contar_soluciones(leida, 2) > 1 else "error_silencioso"
        filas.append(fila)

    rejilla = {}
    for k in (1, 2, 3):
        for margen in (0, 1):
            res = []
            for fila, leida, sol_verdad in sin_sol:
                r = reparar(leida, max_cambios=k, margen=margen)
                res.append("abstiene" if r is None else ("bien" if r.solucion == sol_verdad else "error"))
            rejilla[f"{k}-{margen}"] = res
    for i, (fila, leida, sol_verdad) in enumerate(sin_sol):
        fila["reparacion"] = rejilla["3-1"][i]
    return filas, {"ids": [f["id"] for f, _, _ in sin_sol], "n": [f["n"] for f, _, _ in sin_sol],
                   "resultados": rejilla}


SUFIJO = {"eq": "=", "plus": "+", "minus": "-", "times": "*", "div": "/"}
DESARROLLO = {"INKY_6H", "INKY_9H"}  # los cuadernillos con que se ajustó la Fase 1


def etiquetas(raiz: Path) -> dict:
    """Misma lectura que scripts/etiquetas_por_split.py, con las confusiones como lista."""
    salida = {c: {"n": 0, "bien": 0, "fallos": {}} for c in ("desarrollo", "no_usados")}
    for f in sorted(raiz.glob("*/etiquetas/*.png")):
        cuad = "_".join(f.stem.split("_")[:2])
        cola = f.stem.split("_")[-1]
        k = next(k for k in SUFIJO if cola.endswith(k))
        op, obj = SUFIJO[k], int(cola[: -len(k)])
        try:
            lo, ln, _ = leer_recorte(cv2.imread(str(f), cv2.IMREAD_GRAYSCALE), unaria=(op == "="))
            leido = etiqueta(lo, ln)
        except EtiquetaIlegible:
            leido = "ilegible"
        g = salida["desarrollo" if cuad in DESARROLLO else "no_usados"]
        g["n"] += 1
        verdad = etiqueta(op, obj)
        if leido == verdad:
            g["bien"] += 1
        else:
            par = f"{verdad} → {leido}"
            g["fallos"][par] = g["fallos"].get(par, 0) + 1
    return salida


def main() -> None:
    foto = Path(sys.argv[1])
    raiz = Path(sys.argv[2] if len(sys.argv) > 2 else "data_scraped/extraidos")
    salida = Path(sys.argv[3] if len(sys.argv) > 3 else "../../presentacion/datos")
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "foto.json").write_text(json.dumps(fase1(foto, salida), ensure_ascii=False))
    filas, rep = tableros(raiz)
    (salida / "tableros.json").write_text(json.dumps(filas, ensure_ascii=False, indent=0))
    (salida / "reparacion.json").write_text(json.dumps(rep, ensure_ascii=False))
    (salida / "etiquetas.json").write_text(json.dumps(etiquetas(raiz), ensure_ascii=False))
    todo = {p.stem: json.loads(p.read_text()) for p in sorted(salida.glob("*.json"))}
    (salida / "datos.js").write_text("window.DATOS = " + json.dumps(todo, ensure_ascii=False) + ";\n")
    from collections import Counter
    print(Counter(f["lectura"] for f in filas), Counter(f.get("reparacion") for f in filas))
    print({k: Counter(v) for k, v in rep["resultados"].items()})


if __name__ == "__main__":
    main()
