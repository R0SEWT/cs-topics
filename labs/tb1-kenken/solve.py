"""Script unificado para resolver un tablero KenKen (Fase 1 + Fase 2 + Fase 3)."""

import argparse
from pathlib import Path
import cv2

from kenken_cv.pipeline import leer
from kenken_cp.solver import resolver, contar_soluciones
from kenken_cv.render import render, guardar

def main():
    parser = argparse.ArgumentParser(description="Resuelve un tablero KenKen End-to-End.")
    parser.add_argument("imagen", type=str, help="Ruta de la imagen de entrada (jpg, png).")
    parser.add_argument("--out", type=str, default="resultado.png", help="Ruta para guardar la imagen con el tablero resuelto.")
    args = parser.parse_args()

    imagen_path = Path(args.imagen)
    if not imagen_path.exists():
        print(f"Error: No se encontró el archivo '{args.imagen}'")
        return

    print("--- Fase 1: Extrayendo tablero (Visión Computacional) ---")
    try:
        lectura = leer(imagen_path)
        print(f"Tablero detectado: {lectura.instancia.size}x{lectura.instancia.size} con {len(lectura.instancia.cages)} jaulas.")
        print(f"Confianza de OCR: {lectura.confianza:.2f}")
        for aviso in lectura.avisos:
            print(f"Aviso: {aviso}")
    except Exception as e:
        print(f"Error en Fase 1: {e}")
        return

    print("\n--- Fase 2: Resolviendo (Constraint Programming) ---")
    
    solucion = resolver(lectura.instancia)
    
    if solucion is None:
        print("El solver no encontró solución. Es probable que el OCR haya fallado en leer alguna etiqueta.")
        # Aquí se podría añadir el jurado de OCR o reparación guiada.
        # Por ahora se reporta y dibuja sin solución.
    else:
        print("¡Solución encontrada!")
        for fila in solucion:
            print("  " + " ".join(str(c) for c in fila))

    print(f"\n--- Fase 3: Renderizando solución en {args.out} ---")
    img_render = render(lectura.instancia, solucion=solucion)
    guardar(img_render, args.out)
    print("Completado.")

if __name__ == "__main__":
    main()
