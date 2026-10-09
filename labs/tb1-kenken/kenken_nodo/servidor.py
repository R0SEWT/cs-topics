"""API HTTP del nodo: la app manda una foto y recibe la lectura y la solución.

El nodo es la PC que corre el pipeline. El celular le habla por HTTP; con depuración
(USB o inalámbrica) basta `adb reverse tcp:8723 tcp:8723` para que `localhost:8723` del
celular llegue aquí, sin abrir puertos en el firewall.

Principio de la app: honestidad de lectura. Si lo leído no deja un tablero con solución
única, el nodo no devuelve solución: dice en llano qué pasó y qué probar.
"""

from __future__ import annotations

import base64
import binascii
import json
import os
import platform
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from kenken_cp.reparar import reparar
from kenken_cp.solver import contar_soluciones, resolver
from kenken_cv.glyphs import EtiquetaIlegible
from kenken_cv.grid import TableroNoEncontrado
from kenken_cv.pipeline import leer
from kenken_cv.schema import InstanciaInvalida

MENSAJES = {
    "resuelto": "Listo.",
    "reparado": "Leí mal {k} y lo corregí con el solver: es la única corrección que deja "
    "el tablero con solución única. Revisa las jaulas marcadas.",
    "varias": "Leí el tablero, pero así como lo leí tiene más de una solución: "
    "seguramente confundí alguna etiqueta. Toma otra foto, más de frente y con buena luz.",
    "sin_solucion": "Leí el tablero, pero así como lo leí no tiene solución: "
    "seguramente confundí algún número. Toma otra foto, más de frente y con buena luz.",
    "ilegible": "Encontré el tablero, pero no pude leer alguna etiqueta. "
    "Acércate un poco y evita sombras sobre el papel.",
    "jaulas": "Encontré el tablero, pero las jaulas no me cuadran. "
    "Prueba con una foto más de frente, sin que el papel se doble.",
    "sin_tablero": "No encuentro el tablero en la foto. "
    "Que el borde exterior entre completo y que haya buena luz.",
}

# Si KENKEN_GUARDAR apunta a una carpeta, cada foto recibida se guarda ahí junto con lo que
# el nodo respondió: así las pruebas con tableros impresos alimentan el dataset fotográfico.
CARPETA_FOTOS = Path(os.environ["KENKEN_GUARDAR"]) if os.environ.get("KENKEN_GUARDAR") else None

app = FastAPI(title="Nodo KenKen", version="1")
# La app corre en un WebView (origen capacitor/localhost) o en un navegador de prueba.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class Pedido(BaseModel):
    imagen: str  # base64 o data URL


def _decodificar(imagen: str) -> np.ndarray:
    """Base64 (con o sin prefijo data:) -> imagen en grises. 400 si no es una imagen."""
    if imagen.startswith("data:"):
        imagen = imagen.split(",", 1)[-1]
    try:
        crudo = base64.b64decode(imagen, validate=False)
    except (binascii.Error, ValueError):
        crudo = b""
    gris = cv2.imdecode(np.frombuffer(crudo, np.uint8), cv2.IMREAD_GRAYSCALE) if crudo else None
    if gris is None:
        raise HTTPException(status_code=400, detail="la imagen no se pudo decodificar")
    return gris


def _respuesta(estado: str, t_vision: float, *, mensaje: str | None = None, lectura=None,
               solucion=None, t_solver: float = 0.0, instancia=None, correcciones=()) -> dict:
    instancia = instancia or (lectura.instancia if lectura else None)
    return {
        "estado": estado,
        "mensaje": mensaje or MENSAJES[estado],
        "n": instancia.size if instancia else None,
        "jaulas": [
            {"celdas": [list(c) for c in jaula.cells], "op": jaula.op, "objetivo": jaula.target}
            for jaula in (instancia.cages if instancia else ())
        ],
        "solucion": [list(fila) for fila in solucion] if solucion else None,
        "confianza": round(lectura.confianza, 3) if lectura else None,
        "avisos": list(lectura.avisos) if lectura else [],
        "correcciones": [
            {"celda": list(c.celda),
             "leido": {"op": c.leido[0], "objetivo": c.leido[1]},
             "corregido": {"op": c.corregido[0], "objetivo": c.corregido[1]}}
            for c in correcciones
        ],
        "ms": {"vision": round(t_vision, 1), "solver": round(t_solver, 1)},
    }


@app.get("/salud")
def salud() -> dict:
    return {"ok": True, "nodo": platform.node(), "version": app.version}


def _guardar(gris: np.ndarray, respuesta: dict) -> None:
    CARPETA_FOTOS.mkdir(parents=True, exist_ok=True)
    nombre = datetime.now().strftime("foto_%Y%m%d_%H%M%S_%f")
    cv2.imwrite(str(CARPETA_FOTOS / f"{nombre}.jpg"), gris, [cv2.IMWRITE_JPEG_QUALITY, 92])
    (CARPETA_FOTOS / f"{nombre}.json").write_text(json.dumps(respuesta, ensure_ascii=False, indent=2))


@app.post("/resolver")
def resolver_foto(pedido: Pedido) -> dict:
    gris = _decodificar(pedido.imagen)
    respuesta = _resolver(gris)
    if CARPETA_FOTOS:
        _guardar(gris, respuesta)
    return respuesta


def _resolver(gris: np.ndarray) -> dict:

    t0 = time.perf_counter()
    try:
        lectura = leer(gris)
    except TableroNoEncontrado:
        return _respuesta("sin_tablero", 1000 * (time.perf_counter() - t0))
    except EtiquetaIlegible:
        return _respuesta("ilegible", 1000 * (time.perf_counter() - t0))
    except InstanciaInvalida:
        return _respuesta("sin_solucion", 1000 * (time.perf_counter() - t0), mensaje=MENSAJES["jaulas"])
    t_vision = 1000 * (time.perf_counter() - t0)

    t1 = time.perf_counter()
    solucion = resolver(lectura.instancia)
    unica = solucion is not None and contar_soluciones(lectura.instancia, tope=2) == 1
    t_solver = 1000 * (time.perf_counter() - t1)

    if solucion is None:
        # Antes de rendirse, el solver intenta reparar la lectura (ver kenken_cp.reparar).
        r = reparar(lectura.instancia)
        t_solver = 1000 * (time.perf_counter() - t1)
        if r is None:
            return _respuesta("sin_solucion", t_vision, lectura=lectura, t_solver=t_solver)
        k = len(r.correcciones)
        return _respuesta(
            "reparado", t_vision, lectura=lectura, instancia=r.instancia, solucion=r.solucion,
            t_solver=t_solver, correcciones=r.correcciones,
            mensaje=MENSAJES["reparado"].format(k="una etiqueta" if k == 1 else f"{k} etiquetas"),
        )
    if not unica:
        return _respuesta("varias", t_vision, lectura=lectura, t_solver=t_solver)
    return _respuesta("resuelto", t_vision, lectura=lectura, solucion=solucion, t_solver=t_solver)
