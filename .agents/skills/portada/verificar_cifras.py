"""Libro de cifras de la portada: cada número del README tiene que estar en una fuente.

Revisa dos cosas del README, incluidos los textos alternativos de las imágenes y sin bloques
de código, código en línea, URLs ni atributos HTML:

* Las cifras que pueden equivocarse en silencio (las que llevan decimales y los enteros de
  tres cifras o más) tienen que aparecer en alguna fuente versionada. Los enteros chicos
  sueltos no se revisan: aparecen en cualquier parte y el chequeo no probaría nada.
* Los pares «N de M» (48 de 70, 16 de 19), que suelen ser los resultados clave, tienen que
  aparecer juntos en una misma frase o fila del informe, o estar en LIBRO con su
  justificación. Solo se buscan en el informe, y escritos como par: en los JSON de los datos,
  una línea llena de enteros, y en la prosa, cualquier par aparece cerca.

Uso, desde la raíz del repo:
    python3 .agents/skills/portada/verificar_cifras.py [README.md]
Sale con código 1 si alguna cifra no tiene fuente.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

FUENTES = ["informe/main.tex", "presentacion/datos/*.json", "presentacion/index.qmd"]
FUENTE_PARES = "informe/main.tex"

# Pares que no están escritos así en el informe pero se deducen de él, con su porqué.
LIBRO = {
    "0 de 22": "Tabla V: «De los 22 tableros mal leídos, ninguno entrega una solución errónea»",
    "2 de 8": "README de TB1-KenKen-fotos.zip (release tb1): foto04 reparado y foto08 resuelto; "
              "las otras 6, ilegible o sin_solucion",
}

SEP_MILES = "[ \u00a0\u202f]|\\\\,"  # espacio, no separable, fino, o \, de LaTeX
# Versiones de herramientas: no son cifras del trabajo.
VERSION = re.compile(r"(?:JADE|Java|Python|OR-Tools|Tesseract|Capacitor|Quarto|JDK)\s+$")


def prosa(md: str) -> str:
    alts = " ".join(re.findall(r'alt="([^"]*)"', md))  # los alt también afirman cifras
    md = re.sub(r"```.*?```", " ", md, flags=re.DOTALL)  # bloques de código
    md = re.sub(r"`[^`]*`", " ", md)  # código en línea
    md = re.sub(r"\]\([^)]*\)", "]", md)  # destino de los enlaces
    md = re.sub(r"<[^>]*>", " ", md)  # etiquetas HTML y sus atributos
    return re.sub(r"https?://\S+", " ", md) + "\n" + alts


def cifras(texto: str) -> list[str]:
    patron = rf"(?<![\w.,])(\d{{1,3}}(?:(?:{SEP_MILES})\d{{3}})+|\d+(?:[.,]\d+)?)(?![\w])"
    encontradas = []
    for m in re.finditer(patron, texto):
        if VERSION.search(texto[max(0, m.start() - 12):m.start()]):
            continue
        limpio = re.sub(SEP_MILES, "", m.group(1))
        if "." in limpio or "," in limpio or len(limpio) >= 3:
            encontradas.append(limpio)
    return sorted(set(encontradas), key=lambda c: float(c.replace(",", ".")))


def variantes(c: str) -> list[str]:
    """Cómo puede aparecer la misma cifra en una fuente."""
    if "." in c or "," in c:
        return [c.replace(",", "."), c.replace(".", ",")]
    if len(c) <= 3:
        return [c]
    cabeza, cola = c[:-3], c[-3:]
    return [c] + [f"{cabeza}{sep}{cola}" for sep in ("\\,", ",", " ", "\u00a0")]


def pares(texto: str) -> list[tuple[str, str]]:
    return sorted(set(re.findall(r"(?<![\w.,])(\d+) de (\d+)(?![\w.,×])", texto)))


def juntos(n: str, m: str, corpus: str) -> bool:
    """El par escrito en el informe como «N de M» (con hasta dos palabras en medio: «16 de
    esas 19»), como «N/M», o en dos celdas vecinas de una tabla, total y parte («70 & 48»)."""
    a, b = rf"(?<![\d.]){n}(?![\d.])", rf"(?<![\d.]){m}(?![\d.])"
    return re.search(rf"{a}\s+de\s+(?:\w+\s+){{0,2}}{b}|{a}/{b}|{b}\s*&\s*{a}", corpus) is not None


def main() -> int:
    readme = Path(sys.argv[1] if len(sys.argv) > 1 else "README.md")
    texto = prosa(readme.read_text())
    corpus = "\n".join(p.read_text(errors="ignore") for patron in FUENTES
                       for p in sorted(Path(".").glob(patron)))
    informe = Path(FUENTE_PARES).read_text(errors="ignore")
    faltan = []
    for c in cifras(texto):
        ok = any(re.search(rf"(?<![\d.]){re.escape(v)}(?![\d])", corpus) for v in variantes(c))
        print(f"  {'ok   ' if ok else 'FALTA'}  {c}")
        if not ok:
            faltan.append(c)
    for n, m in pares(texto):
        par = f"{n} de {m}"
        if par in LIBRO:
            print(f"  libro  {par}: {LIBRO[par]}")
        elif juntos(n, m, informe):
            print(f"  ok     {par}")
        else:
            print(f"  FALTA  {par}")
            faltan.append(par)
    if faltan:
        print(f"\n{len(faltan)} cifra(s) sin fuente: {', '.join(faltan)}")
        return 1
    print("\nTodas las cifras revisadas tienen fuente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
