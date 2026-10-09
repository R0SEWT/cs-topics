"""Arranca el nodo: `uv run python -m kenken_nodo [--lan] [--puerto 8723]`.

Por defecto escucha solo en 127.0.0.1: el celular llega por `adb reverse`, que no
necesita abrir el firewall. Con --lan escucha en todas las interfaces.
"""

import argparse
import os

import uvicorn


def main() -> None:
    p = argparse.ArgumentParser(description="Nodo de cómputo KenKen")
    p.add_argument("--lan", action="store_true", help="escuchar en la red local (0.0.0.0)")
    p.add_argument("--puerto", type=int, default=8723)
    p.add_argument("--guardar", metavar="CARPETA", help="guardar cada foto recibida y su respuesta")
    a = p.parse_args()
    if a.guardar:
        os.environ["KENKEN_GUARDAR"] = a.guardar
        print(f"Guardando fotos en {a.guardar}")
    host = "0.0.0.0" if a.lan else "127.0.0.1"
    print(f"Nodo KenKen en http://{host}:{a.puerto}")
    print(f"Celular por depuración: adb reverse tcp:{a.puerto} tcp:{a.puerto}")
    uvicorn.run("kenken_nodo.servidor:app", host=host, port=a.puerto)


if __name__ == "__main__":
    main()
