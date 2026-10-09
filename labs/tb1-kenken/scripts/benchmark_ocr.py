"""EvalAa el OCR de etiquetas con mAtricas de acuerdo no paramAtricas (Cohen's Kappa).

Calcula el Kappa de Cohen para medir el acuerdo real entre el Ground Truth
y las predicciones del OCR, reduciendo la influencia del azar.
Imprime tambiAn un resumen de los casos problemAticos a revisar.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import cv2
from sklearn.metrics import cohen_kappa_score

from kenken_cv.glyphs import EtiquetaIlegible, leer_recorte

SUFIJO = {"eq": "=", "plus": "+", "minus": "-", "times": "*", "div": "/"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark del OCR usando Kappa de Cohen")
    parser.add_argument(
        "--etiquetas",
        type=str,
        default="data_scraped/extraidos",
        help="Directorio raA-z que contiene subcarpetas por tamaAo con las etiquetas (ej. data_scraped/extraidos)",
    )
    args = parser.parse_args()

    raiz = Path(args.etiquetas)
    if not raiz.exists():
        sys.exit(f"Error: el directorio '{raiz}' no existe.")

    # Buscar todas las imAgenes .png en las subcarpetas etiquetas/
    archivos = sorted(raiz.glob("*/etiquetas/*.png"))
    
    if not archivos:
        sys.exit(f"No se encontraron etiquetas en los subdirectorios de {raiz}.")

    y_true = []
    y_pred = []
    
    ok = 0
    fallos: Counter = Counter()

    print(f"Evaluando {len(archivos)} etiquetas desde {raiz}...\n")

    for f in archivos:
        cola = f.stem.split("_")[-1]
        
        # Extraer GT (Target y Operador)
        try:
            op_str, objetivo_str = next(
                (k, cola[: -len(k)]) for k in SUFIJO.keys() if cola.endswith(k)
            )
            op = SUFIJO[op_str]
            objetivo = int(objetivo_str)
        except StopIteration:
            print(f"Advertencia: No se pudo parsear el GT de {f.name}")
            continue

        gt_label = f"{objetivo}{op}"
        y_true.append(gt_label)

        # Predecir con el OCR actual
        try:
            img = cv2.imread(str(f), cv2.IMREAD_GRAYSCALE)
            if img is None:
                raise EtiquetaIlegible("No se pudo leer la imagen")
                
            leido_op, leido_num, _ = leer_recorte(img, unaria=(op == "="))
            pred_label = f"{leido_num}{leido_op}"
        except EtiquetaIlegible:
            leido_op, leido_num = "?", -1
            pred_label = "??"
            
        y_pred.append(pred_label)

        if gt_label == pred_label:
            ok += 1
        else:
            fallos[(gt_label, pred_label)] += 1

    n = len(y_true)
    accuracy = ok / n if n > 0 else 0.0
    
    # Calcular Kappa de Cohen
    kappa = cohen_kappa_score(y_true, y_pred)

    print("-" * 50)
    print("RESUMEN DE RESULTADOS (MÉTRICAS)")
    print("-" * 50)
    print(f"Total evaluadas : {n}")
    print(f"Accuracy Exacta : {accuracy * 100:.2f}%")
    print(f"Cohen's Kappa   : {kappa:.4f}")
    
    if kappa < 0:
         interpretacion = "Pobre (menor que por azar)"
    elif kappa <= 0.20:
         interpretacion = "Leve"
    elif kappa <= 0.40:
         interpretacion = "Aceptable / Justo"
    elif kappa <= 0.60:
         interpretacion = "Moderado"
    elif kappa <= 0.80:
         interpretacion = "Sustancial / Bueno"
    else:
         interpretacion = "Casi perfecto"
         
    print(f"Acuerdo (Kappa) : {interpretacion}")

    print("\n" + "-" * 50)
    print("PRINCIPALES CONFUSIONES (TOP FALLOS)")
    print("-" * 50)
    
    if not fallos:
        print("¡NingAn fallo detectado!")
    else:
        for (verdadero, leido), cantidad in fallos.most_common(15):
            print(f"  GT: {verdadero:7s} | LeA-do: {leido:7s} | Cantidad: {cantidad}")

if __name__ == "__main__":
    main()
