"""Scraper de tableros KenKen (Inkies de KrazyDad).

Descarga cuadernillos PDF clasificados por tamaño (3x3 a 9x9), permitiendo
aumentar el dataset de evaluación y entrenamiento del OCR con ground truth exacto.

Convenciones de formato de KrazyDad:
- n <= 5 (3x3, 4x4, 5x5): formateados como 4 acertijos por página ('_4pp.pdf').
- n >= 6 (6x6, 7x7, 8x8, 9x9): formateados como 1 acertijo por página ('_1pp.pdf').

Uso:
    PYTHONPATH=. uv run python scripts/scrapear_kenken.py --tamano 4,6,9 --libros 1
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path

BASE_SFILES = "https://krazydad.com/inkies/sfiles/"
USER_AGENT = "Mozilla/5.0 (tb1-kenken; uso académico)"


@dataclass(frozen=True)
class EntradaCatalogo:
    n: int
    slug: str
    dificultad: str
    prefijo: str
    formato: str = "1pp"


CATALOGO: tuple[EntradaCatalogo, ...] = (
    EntradaCatalogo(n=3, slug="3x3_easy", dificultad="E", prefijo="INKY_3E", formato="4pp"),
    EntradaCatalogo(n=4, slug="4x4_easy", dificultad="E", prefijo="INKY_4E", formato="4pp"),
    EntradaCatalogo(n=4, slug="4x4_hard", dificultad="H", prefijo="INKY_4H", formato="4pp"),
    EntradaCatalogo(n=5, slug="5x5_easy", dificultad="E", prefijo="INKY_5E", formato="4pp"),
    EntradaCatalogo(n=5, slug="5x5_hard", dificultad="H", prefijo="INKY_5H", formato="4pp"),
    EntradaCatalogo(n=6, slug="6x6_easy", dificultad="E", prefijo="INKY_6E", formato="1pp"),
    EntradaCatalogo(n=6, slug="6x6_hard", dificultad="H", prefijo="INKY_6H", formato="1pp"),
    EntradaCatalogo(n=7, slug="7x7_hard", dificultad="H", prefijo="INKY_7H", formato="1pp"),
    EntradaCatalogo(n=8, slug="8x8_hard", dificultad="H", prefijo="INKY_8H", formato="1pp"),
    EntradaCatalogo(n=9, slug="9x9_hard", dificultad="H", prefijo="INKY_9H", formato="1pp"),
)


@dataclass(frozen=True)
class Cuadernillo:
    archivo: str

    def tamano(self) -> int | None:
        """Extrae el tamaño del tablero a partir del nombre del archivo."""
        match = re.search(r"INKY_(\d+)", self.archivo)
        return int(match.group(1)) if match else None


def url_pdf(entrada: EntradaCatalogo, libro: int = 1) -> str:
    """Genera la URL canónica de un cuadernillo PDF en KrazyDad."""
    return f"{BASE_SFILES}{entrada.prefijo}_b{libro:03d}_{entrada.formato}.pdf"


def descubrir_cuadernillos(html: str) -> list[Cuadernillo]:
    """Extrae enlaces a cuadernillos PDF desde el HTML de una página."""
    patron = re.compile(r'href=["\'](?:[^"\']*/)?(INKY_\w+\.pdf)["\']')
    encontrados = patron.findall(html)
    return [Cuadernillo(archivo=nombre) for nombre in encontrados]


def descargar_pdf(url: str, destino: Path, pausa: float = 1.0) -> bool:
    """Descarga un PDF si no existe localmente, respetando un delay de cortesía."""
    if destino.exists():
        print(f"  ya existe: {destino.name}")
        return True
    destino.parent.mkdir(parents=True, exist_ok=True)
    peticion = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(peticion) as resp:
            destino.write_bytes(resp.read())
        print(f"  descargado: {destino.name} ({destino.stat().st_size} bytes)")
        if pausa > 0:
            time.sleep(pausa)
        return True
    except Exception as e:
        print(f"  error al descargar {url}: {e}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scraper de cuadernillos KenKen de KrazyDad con ground truth."
    )
    parser.add_argument(
        "--tamano",
        type=str,
        default="4,6,9",
        help="Tamaños a descargar separados por comas (ej. 4,6,9).",
    )
    parser.add_argument(
        "--libros",
        type=int,
        default=1,
        help="Cantidad de libros por cada tamaño a descargar (por defecto: 1).",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="data_scraped",
        help="Directorio de destino para los archivos PDF descargados.",
    )
    parser.add_argument(
        "--solo-urls",
        action="store_true",
        help="Solo lista las URLs sin descargar los archivos.",
    )
    args = parser.parse_args()

    tamanos = {int(t.strip()) for t in args.tamano.split(",") if t.strip().isdigit()}
    entradas = [e for e in CATALOGO if e.n in tamanos]

    if not entradas:
        print(f"No hay entradas en el catálogo para los tamaños: {args.tamano}")
        return

    destino = Path(args.out)
    print(f"=== KenKen Scraper (KrazyDad Inkies) ===")
    print(f"Tamaños seleccionados: {sorted(tamanos)}")
    print(f"Libros por tamaño: {args.libros}")
    print(f"Destino: {destino.resolve()}\n")

    total = 0
    descargados = 0
    for entrada in entradas:
        print(f"[{entrada.slug}] n={entrada.n} (Dificultad: {entrada.dificultad}, Formato: {entrada.formato}):")
        for libro in range(1, args.libros + 1):
            url = url_pdf(entrada, libro=libro)
            nombre_archivo = f"{entrada.prefijo}_b{libro:03d}_{entrada.formato}.pdf"
            total += 1
            if args.solo_urls:
                print(f"  URL: {url}")
            else:
                ok = descargar_pdf(url, destino / nombre_archivo)
                if ok:
                    descargados += 1

    if not args.solo_urls:
        print(f"\nFinalizado: {descargados}/{total} archivos listos en {destino}/")


if __name__ == "__main__":
    main()
