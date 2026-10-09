"""Extrae tableros KenKen individuales y recortes de etiquetas a partir de cuadernillos PDF.

Soporta formatos 1pp (1 por página) y 4pp (4 por página), organizando
automáticamente los resultados separados por tamaño (ej. extraidos/4x4, 6x6, 9x9).

Para cada tablero se guarda:
- Imagen individual rectificada (1000x1000): 'tableros/<nombre>.png'
- Contrato formal con ground truth: 'tableros/<nombre>.json'
- Recortes de etiquetas para OCR: 'etiquetas/<nombre_ancla_objetivo>.png'

Uso:
    PYTHONPATH=. uv run python scripts/extraer_dataset.py --origen data_scraped --destino data_scraped/extraidos
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

from kenken_cv.extractor import procesar_cuadernillo, ruta_por_tamano


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extrae tableros individuales y etiquetas desde cuadernillos PDF, organizados por tamaño."
    )
    parser.add_argument(
        "--origen",
        type=str,
        default="data_scraped",
        help="Directorio con los archivos PDF a procesar.",
    )
    parser.add_argument(
        "--destino",
        type=str,
        default="data_scraped/extraidos",
        help="Directorio raíz de salida para los tableros organizados por tamaño.",
    )
    parser.add_argument(
        "--tamano",
        type=str,
        default="",
        help="Filtro opcional de tamaños separados por comas (ej. 4,6,9). Si no se especifica, procesa todos.",
    )
    parser.add_argument(
        "--paginas",
        type=int,
        default=0,
        help="Cantidad de páginas a procesar (por defecto 0 = automático, excluye el solucionario).",
    )
    args = parser.parse_args()

    origen = Path(args.origen)
    destino = Path(args.destino)

    if not origen.exists():
        print(f"Error: el directorio de origen '{origen}' no existe.")
        return

    filtro_tamanos = (
        {int(t.strip()) for t in args.tamano.split(",") if t.strip().isdigit()}
        if args.tamano
        else None
    )

    pdfs = sorted(origen.glob("*.pdf"))
    if not pdfs:
        print(f"No se encontraron archivos PDF en '{origen}'.")
        return

    print("=== Extractor de Tableros KenKen Individuales ===")
    print(f"Origen:  {origen.resolve()}")
    print(f"Destino: {destino.resolve()}")
    if filtro_tamanos:
        print(f"Filtro de tamaños: {sorted(filtro_tamanos)}")
    print("-" * 55)

    resumen: dict[int, dict[str, int]] = defaultdict(lambda: {"tableros": 0, "etiquetas": 0})

    for pdf in pdfs:
        match = re.search(r"INKY_(\d+)", pdf.name)
        n = int(match.group(1)) if match else None

        if filtro_tamanos and n not in filtro_tamanos:
            continue

        print(f"Procesando: {pdf.name} (n={n or '?'})...")
        rango_paginas = range(1, args.paginas + 1) if args.paginas > 0 else None
        stats = procesar_cuadernillo(
            pdf_path=pdf,
            destino_raiz=destino,
            paginas=rango_paginas,
        )

        n_res = stats["n"]
        resumen[n_res]["tableros"] += stats["tableros"]
        resumen[n_res]["etiquetas"] += stats["etiquetas"]
        print(
            f"  -> {stats['tableros']} tableros y {stats['etiquetas']} etiquetas "
            f"guardados en {ruta_por_tamano(destino, n_res)}/"
        )

    print("\n" + "=" * 55)
    print("Resumen de extracción por tamaño:")
    for tam in sorted(resumen.keys()):
        d = resumen[tam]
        print(f"  [{tam}x{tam}]: {d['tableros']} tableros individuales | {d['etiquetas']} recortes de etiquetas")
    print("=" * 55)


if __name__ == "__main__":
    main()
