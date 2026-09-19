"""Resuelve tipografías del sistema por nombre de archivo, no por ruta fija.

La misma ``DejaVuSans.ttf`` vive en ``/usr/share/fonts/truetype/dejavu/`` en
Debian y en ``/usr/share/fonts/dejavu-sans-fonts/`` en Fedora. Fijar la ruta
absoluta ataba el lab a una distro.

No es cosmético: ``glyphs.BANCO`` es el banco de plantillas del OCR, así que si
en una máquina cargan siete tipografías y en otra cinco, las precisiones
medidas dejan de ser comparables y nadie se entera. Por eso aquí se falla
ruidosamente cuando falta una, en vez de saltársela en silencio.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

# Dónde miran las distros. Se recorren en orden; gana la primera coincidencia,
# así que lo instalado por el usuario pisa a lo del sistema.
RAICES: tuple[str, ...] = (
    "~/.fonts",
    "~/.local/share/fonts",
    "$XDG_DATA_HOME/fonts",
    "/usr/local/share/fonts",
    "/usr/share/fonts",
)

# Pista de instalación por familia, para que el error diga qué hacer. La clave
# es el prefijo del nombre del archivo.
PAQUETES: tuple[tuple[str, str], ...] = (
    ("DejaVuSerif", "dnf install dejavu-serif-fonts  |  apt install fonts-dejavu-core"),
    ("DejaVu", "dnf install dejavu-sans-fonts  |  apt install fonts-dejavu-core"),
    ("Free", "dnf install gnu-free-fonts-common gnu-free-serif-fonts gnu-free-sans-fonts"
             "  |  apt install fonts-freefont-ttf"),
    ("LiberationSansNarrow", "dnf install liberation-narrow-fonts  |  apt install fonts-liberation2"),
    ("Liberation", "dnf install liberation-fonts  |  apt install fonts-liberation"),
)


class FuenteAusente(RuntimeError):
    """El sistema no tiene una tipografía que el lab necesita."""


def _pista(nombre: str) -> str:
    for prefijo, orden in PAQUETES:
        if nombre.startswith(prefijo):
            return orden
    return "instala la tipografía en ~/.local/share/fonts"


@lru_cache(maxsize=1)
def _indice() -> dict[str, str]:
    """Mapa nombre-de-archivo -> ruta, recorriendo los directorios de fuentes."""
    encontradas: dict[str, str] = {}
    for raiz in RAICES:
        base = Path(os.path.expandvars(os.path.expanduser(raiz)))
        if "$" in str(base) or not base.is_dir():
            continue
        for carpeta, _, archivos in os.walk(base, followlinks=True):
            for archivo in archivos:
                encontradas.setdefault(archivo, str(Path(carpeta) / archivo))
    return encontradas


def resolver(nombre: str) -> str:
    """Ruta absoluta de `nombre`, o `FuenteAusente` si el sistema no la tiene."""
    return resolver_todas((nombre,))[0]


def resolver_todas(nombres: tuple[str, ...]) -> tuple[str, ...]:
    """Resuelve varias a la vez y, si faltan, las reporta TODAS de golpe.

    De una en una obligaría a instalar, volver a correr y tropezar con la
    siguiente.
    """
    indice = _indice()
    faltan = [n for n in nombres if n not in indice]
    if faltan:
        detalle = "\n".join(f"  - {n}\n      {_pista(n)}" for n in faltan)
        raise FuenteAusente(
            f"faltan {len(faltan)} tipografías que este lab necesita:\n{detalle}\n"
            "Sin ellas el banco de plantillas no es el mismo y las precisiones "
            "medidas no son comparables con las de otra máquina."
        )
    return tuple(indice[n] for n in nombres)
