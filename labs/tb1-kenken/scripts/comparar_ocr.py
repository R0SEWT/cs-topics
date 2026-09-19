"""Compara motores de OCR sobre las etiquetas REALES del dataset de KrazyDad.

Requiere haber ejecutado antes ``scripts/dataset_real.py``.

Cada motor es opcional: si le falta su dependencia se salta con un aviso, así
que el script corre igual en una máquina pelada que en una con GPU. Añadir un
motor nuevo es registrar una función en `MOTORES`.

Lo que se mide es la etiqueta COMPLETA ('40×' = operación y objetivo), que es la
unidad que consume el modelo CP. Al final se calcula el acuerdo entre motores:
es ahí donde está el margen real, no en el ranking.

Uso::

    PYTHONPATH=. uv run python scripts/comparar_ocr.py
    PYTHONPATH=. uv run python scripts/comparar_ocr.py --motores plantillas,trocr
"""

from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys
import tempfile
from collections import Counter
from math import comb
from pathlib import Path

import cv2
import numpy as np

from kenken_cv.glyphs import EtiquetaIlegible, leer_recorte

SUFIJO = {"eq": "=", "plus": "+", "minus": "-", "times": "*", "div": "/"}
SIMBOLO = {"+": "+", "-": "-", "−": "-", "x": "*", "X": "*", "×": "*",
           "/": "/", "÷": "/", "\\": "/"}


def cargar(raiz: Path) -> list[tuple[np.ndarray, str, int]]:
    datos = []
    for f in sorted(glob.glob(str(raiz / "etiquetas/*.png"))):
        cola = Path(f).stem.split("_")[-1]
        for k, op in SUFIJO.items():
            if cola.endswith(k):
                datos.append((cv2.imread(f, cv2.IMREAD_GRAYSCALE), op, int(cola[: -len(k)])))
                break
    return datos


def _interpretar(texto: str) -> tuple[str, int]:
    """'40 ×' -> ('*', 40). Devuelve ('?', -1) si no hay nada legible."""
    digitos = "".join(c for c in texto if c.isdigit())
    simbolos = [SIMBOLO[c] for c in texto if c in SIMBOLO]
    if not digitos:
        return "?", -1
    return (simbolos[-1] if simbolos else "="), int(digitos)


# ------------------------------------------------------------------ motores

def motor_plantillas(datos):
    """El del propio pipeline: segmentación + correlación con plantillas."""
    salida = []
    for img, op, _ in datos:
        try:
            o, t, _ = leer_recorte(img, unaria=(op == "="))
            salida.append((o, t))
        except EtiquetaIlegible:
            salida.append(("?", -1))
    return salida


def motor_tesseract(datos):
    """Tesseract en modo línea suelta (PSM 7). Necesita el binario del sistema."""
    binario = os.environ.get("TESSERACT_BIN", "tesseract")
    if subprocess.run(["which", binario], capture_output=True).returncode != 0:
        raise RuntimeError(f"no encuentro el binario '{binario}' (apt install tesseract-ocr)")
    salida = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, (img, _, _) in enumerate(datos):
            # Tesseract necesita escala y margen: con el recorte pelado devuelve vacío.
            a = cv2.resize(img, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
            a = cv2.copyMakeBorder(a, 30, 30, 30, 30, cv2.BORDER_CONSTANT, value=255)
            ruta = f"{tmp}/e{i}.png"
            cv2.imwrite(ruta, a)
            r = subprocess.run(
                [binario, ruta, "-", "--psm", "7", "-c",
                 "tessedit_char_whitelist=0123456789+-xX/"],
                capture_output=True, text=True,
            )
            salida.append(_interpretar("".join(r.stdout.split())))
    return salida


def motor_trocr(datos, modelo: str = "microsoft/trocr-base-printed"):
    """TrOCR: transformer de línea impresa. Aprovecha GPU si la hay."""
    import torch
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel

    disp = "cuda" if torch.cuda.is_available() else "cpu"
    proc = TrOCRProcessor.from_pretrained(modelo)
    red = VisionEncoderDecoderModel.from_pretrained(modelo).to(disp).eval()
    print(f"    TrOCR en {disp}")
    salida = []
    lote = 16 if disp == "cuda" else 4
    for i in range(0, len(datos), lote):
        imgs = []
        for img, _, _ in datos[i : i + lote]:
            a = cv2.copyMakeBorder(img, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)
            imgs.append(cv2.cvtColor(a, cv2.COLOR_GRAY2RGB))
        px = proc(images=imgs, return_tensors="pt").pixel_values.to(disp)
        with torch.no_grad():
            ids = red.generate(px, max_new_tokens=12)
        for texto in proc.batch_decode(ids, skip_special_tokens=True):
            salida.append(_interpretar(texto))
    return salida


def motor_rapidocr(datos):
    """PP-OCR vía onnxruntime: reconocedor de línea, ligero y en CPU."""
    from rapidocr_onnxruntime import RapidOCR

    ocr = RapidOCR()
    salida = []
    for img, _, _ in datos:
        a = cv2.copyMakeBorder(img, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)
        res, _ = ocr(cv2.cvtColor(a, cv2.COLOR_GRAY2RGB))
        salida.append(_interpretar("".join(r[1] for r in res) if res else ""))
    return salida


MOTORES = {
    "plantillas": motor_plantillas,
    "tesseract": motor_tesseract,
    "rapidocr": motor_rapidocr,
    "trocr": motor_trocr,
}


def mcnemar(a: list[bool], b: list[bool]) -> tuple[int, int, float]:
    """p exacta de que la diferencia entre dos motores sea azar."""
    solo_b = sum(1 for x, y in zip(a, b) if not x and y)
    solo_a = sum(1 for x, y in zip(a, b) if x and not y)
    m, k = solo_a + solo_b, min(solo_a, solo_b)
    p = (sum(comb(m, i) for i in range(k + 1)) / 2**m * 2) if m else 1.0
    return solo_a, solo_b, min(p, 1.0)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="dataset_real")
    ap.add_argument("--motores", default=",".join(MOTORES))
    args = ap.parse_args()

    datos = cargar(Path(args.dataset))
    if not datos:
        sys.exit(f"no hay etiquetas en {args.dataset}; ejecuta antes scripts/dataset_real.py")
    verdad = [(op, obj) for _, op, obj in datos]
    print(f"etiquetas reales: {len(datos)}\n")

    resultados: dict[str, list[bool]] = {}
    print(f"{'motor':14s} {'etiqueta':>10s} {'operación':>11s} {'número':>9s}")
    print("-" * 48)
    for nombre in args.motores.split(","):
        nombre = nombre.strip()
        if nombre not in MOTORES:
            print(f"{nombre:14s} (desconocido)")
            continue
        try:
            pred = MOTORES[nombre](datos)
        except Exception as e:  # noqa: BLE001
            print(f"{nombre:14s} no disponible: {type(e).__name__}: {str(e)[:40]}")
            continue
        acierto = [p == v for p, v in zip(pred, verdad)]
        op_ok = sum(p[0] == v[0] for p, v in zip(pred, verdad))
        num_ok = sum(p[1] == v[1] for p, v in zip(pred, verdad))
        n = len(datos)
        print(f"{nombre:14s} {100*sum(acierto)/n:9.1f}% {100*op_ok/n:10.1f}% {100*num_ok/n:8.1f}%")
        resultados[nombre] = acierto

    if len(resultados) < 2:
        return

    print("\n¿son distinguibles entre sí? (McNemar exacta)")
    nombres = list(resultados)
    for i, a in enumerate(nombres):
        for b in nombres[i + 1 :]:
            ga, gb, p = mcnemar(resultados[a], resultados[b])
            juicio = "diferencia real" if p <= 0.05 else "indistinguible del azar"
            print(f"  {a} vs {b}: gana {a} en {ga}, gana {b} en {gb}, p={p:.3f} -> {juicio}")

    n = len(datos)
    alguno = sum(any(r[i] for r in resultados.values()) for i in range(n))
    todos = sum(all(r[i] for r in resultados.values()) for i in range(n))
    print(f"\nal menos un motor acierta   {100*alguno/n:5.1f}%  (techo de un jurado)")
    print(f"aciertan todos a la vez     {100*todos/n:5.1f}%")


if __name__ == "__main__":
    main()
