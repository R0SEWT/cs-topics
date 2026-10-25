# TB1 — Fase 1: visión computacional sobre KenKen

Spike de viabilidad para el Trabajo 1 (`materials/week-05/Topicos_CC-4.pdf`).
Responde a una sola pregunta: **¿es KenKen abordable, o conviene cambiar de
acertijo?**

## Veredicto: sí, seguimos con KenKen

Lo que se temía de KenKen —detectar las **jaulas**, que los otros tres acertijos
no tienen— es la parte resuelta. El cuello de botella es el OCR de las
etiquetas, y ese problema lo tienen los cuatro por igual: cambiar de puzzle
costaría todo el trabajo de topología sin quitar el cuello de botella.

### Contra tableros REALES

Fuente: 16 tableros de los cuadernillos de KrazyDad (6x6 y 9x9), con la verdad
sacada del texto vectorial de los propios PDF. Reproducible con
`scripts/dataset_real.py` y `scripts/evaluar_real.py`.

| métrica | resultado |
|---|---:|
| tamaño del tablero (n) | **16/16** |
| anclas de jaula correctas | **98.6%** (412/418), sin un solo falso positivo |
| etiqueta completa (operación + número) | **98.8%** |
| tablero de 16 jaulas leído entero | 82.3% |
| tablero de 23 jaulas leído entero | 75.5% |

Quedan 5 fallos de 412: dos `5-` leídos como `6-`, y tres etiquetas de cuatro
cifras (`2400×`, `4800×`, `2160×`) cuyo operador queda fuera del recorte porque
la etiqueta desborda su propia celda. Ese desbordamiento es del original, no del
recorte: hay que detectarlo, no ensanchar más la ventana (ensanchando entra la
línea vecina y se lee como un `1`).

### Lo que el conjunto sintético escondía

**Al estrenar datos reales el pipeline falló en los 16 tableros**, después de dar
100% en los generados. Cuatro supuestos que el generador nunca puso a prueba:

1. **La rejilla llegaba fragmentada.** El generador dibujaba siempre la rejilla
   fina completa; un KenKen impreso interrumpe la línea allí donde una jaula la
   atraviesa, y medio grado de sesgo la trocea en tramos a alturas distintas.
   Se exigía que cada línea cruzase el tablero, y así ninguna valía. Ahora el
   tamaño se decide por periodicidad: el n mayor cuyas líneas estén *todas*
   presentes. El n correcto deja su línea más floja en ~29% del ancho;
   cualquier n equivocado cae a cero exacto, así que el criterio separa limpio.
2. **La tinta no cae donde se la predice.** Al medir el grosor de una arista se
   exigía tinta en el píxel exacto previsto. En un tablero real la rectificación
   deja unos píxeles de error, la arista salía con grosor cero, se tomaba por
   línea fina y dos jaulas distintas se fundían en una. Buscando el trazo *más
   cercano*: anclas correctas de 62.2% a 96.0%.
3. **El margen del recorte era una constante, y era el mayor error del
   pipeline.** Estaba fijado al 10% de la celda y cortaba la parte de arriba de
   los dígitos: un `40` se leía `4U`. Barrido sobre tableros reales, la lectura
   iba de 79.9% (4%) a 95.6% (7%) y volvía a 83.5% (10%) — demasiada pendiente
   para un número elegido a mano. Ahora el margen **se mide**: se busca dónde
   acaba la línea de la rejilla y se deja un respiro proporcional. Con eso, y
   filtrando el copyright del pie que contaminaba la verdad, la etiqueta pasó de
   83.5% a **98.8%**, y el tablero completo de 5.6% a **82.3%**.
4. **Cada editor imprime otros glifos.** KrazyDad usa `/` y `-` ASCII donde el
   generador ponía `÷` y `−`. El alfabeto de plantillas no los tenía.

La moraleja para el informe: el conjunto sintético sirve para desarrollar y para
tener ground truth barato, pero **no mide nada**. La cifra que vale es la de los
tableros reales.

### Qué OCR conviene

Las 412 etiquetas reales, con el recorte ya arreglado (`scripts/comparar_ocr.py`,
2026-09-25, todo en CPU):

| método | etiqueta completa | operación | número |
|---|---:|---:|---:|
| Plantillas por correlación (el pipeline) | **98.8%** | 99.3% | 98.8% |
| Tesseract 5.3.4 (PSM 7) | 97.1% | 97.8% | 97.8% |
| RapidOCR (PP-OCR sobre onnxruntime) | 64.8% | 68.4% | 94.2% |
| TrOCR base printed | 60.9% | 63.6% | 95.1% |

**Plantillas y Tesseract no se distinguen.** Discrepan en 11 etiquetas: 9 a favor
de las plantillas y 2 de Tesseract, p = 0.065 (McNemar exacta). Las plantillas
van primero, pero con 412 etiquetas no alcanza para decir que sean mejores. Los
otros dos quedan muy por debajo de ambos (p < 0.001) y no se distinguen entre sí
(p = 0.289).

**Los dos buenos se equivocan en cosas distintas**, y eso vale más que el ranking:

- Las plantillas fallan 5: dan por ilegibles las tres etiquetas de cuatro cifras
  que desbordan su celda (`2400×`, `4800×`, `2160×`) y leen dos `5-` como `6-`.
- Tesseract falla 12: no devuelve nada en seis etiquetas cortas (`8×`, `3-`,
  `1-`…), lee `14+` como `144+` dos veces y `7+` como `1+`. En las tres de cuatro
  cifras **acierta el número** y solo pierde el operador.

Al menos un motor acierta el 99.8% de las etiquetas (411 de 412); los cuatro a la
vez, el 38.1%. Ese es el techo de un jurado, y la etiqueta que no lee nadie es
una de las tres que desbordan.

RapidOCR y TrOCR leen bien los números pero no los operadores, y no es un
problema de la medición: de los 130 operadores que falla RapidOCR, 107 son el
signo menos, que devuelve vacío o como `■`. Son motores genéricos de texto; el
`-` fino de un KenKen no es algo que hayan visto.

La primera medición, **con el recorte todavía defectuoso**, daba Tesseract
86.7%, plantillas 83.5% y una CNN entrenada con sintéticos 80.6%, y la ventaja de
Tesseract ya entonces era azar (p = 0.111). Arreglar el recorte subió las
plantillas quince puntos y Tesseract diez, cuando entre motores había tres: el
cuello de botella nunca fue el OCR, sino lo que se le daba de comer. Antes de
cambiar de motor, hay que arreglar la entrada. La CNN no se volvió a medir: su
código no quedó en el repo.

La idea del jurado sale reforzada: donde plantillas y Tesseract coinciden, la
lectura es fiable, y donde discrepan hay una lista corta de candidatos que el
modelo CP puede desempatar, porque una lectura mala deja el puzzle sin solución.
Eso es un argumento de Constraint Programming, que en la rúbrica pesa más que
uno de visión.

Un detalle que costó dos intentos: **la proporción del glifo es información**.
Entrenar una CNN con glifos estirados a un cuadrado y clasificar conservando la
forma la hundió al 29.9%; con la proporción respetada en ambos lados subió al
80.6%. El mismo error invalida el conjunto de glifos reales de Myers
(`base_images_true`), que viene estirado a 28x28.

### Contra tableros sintéticos

Se conserva porque da ground truth gratis y cubre condiciones que los PDF no
tienen (perspectiva, luz desigual, ruido). 80 tableros, n de 4 a 7:

| condición | tipografía | rejilla | jaulas | etiquetas | instancia completa |
|---|---|---:|---:|---:|---:|
| limpio | en el banco | 100% | 100% | 100% | 100% |
| foto | en el banco | 100% | 100% | 99.8% | 96.6% |
| limpio | no vista | 100% | 100% | 99.4% | 81.0% |
| foto | no vista | 100% | 100% | 95.9% | 52.4% |

## Lo que falta (en orden de rentabilidad)

1. **Las etiquetas que desbordan su celda** (`2400×`): detectar que falta el
   operador y extender el recorte solo en ese caso, en vez de ensanchar siempre.
   Son 3 de 412, pero en un tablero 9x9 con 23 jaulas cuestan puntos. Hay un
   atajo: Tesseract ya lee bien el número de las tres, y un objetivo mayor que
   `n × (celdas de la jaula)` solo puede ser una multiplicación, así que el
   operador se deduce sin tocar el recorte.
2. **Jurado de motores + reparación guiada por el solver.** Donde plantillas y
   Tesseract coincidan, aceptar; donde discrepen, pasarle los candidatos al
   modelo CP y quedarse con el que deja el puzzle con solución única.
3. **Dataset fotografiado.** Los PDF de KrazyDad son tinta real pero rasterizada
   de vectores: no tienen sombra, ni curvatura de papel, ni desenfoque de
   cámara. Eso hay que fotografiarlo.

## Para correr todos los motores

Nada de lo que hay aquí necesita GPU: el pipeline es OpenCV y corre en CPU en
segundos, y la comparación completa, TrOCR incluido, también se midió en CPU. La
GPU solo acelera los motores basados en redes.

```bash
cd labs/tb1-kenken
uv sync
PYTHONPATH=. uv run python scripts/dataset_real.py      # baja los PDF (no van al repo)
PYTHONPATH=. uv run python scripts/comparar_ocr.py      # los motores disponibles
```

Cada motor que falte se salta con un aviso. Para tenerlos todos sin tocar
`pyproject.toml` ni `uv.lock`, se suman al vuelo con `--with`:

```bash
PYTHONPATH=. TESSERACT_BIN=... uv run --frozen \
  --with rapidocr-onnxruntime --with torch --with 'transformers<5' \
  --index https://download.pytorch.org/whl/cpu \
  python scripts/comparar_ocr.py
```

- `transformers<5`: la 5.x no logra construir el tokenizador de
  `trocr-base-printed`, y TrOCR queda "no disponible".
- `--index .../whl/cpu` trae el torch de CPU (unos 700 MB instalado), sin las
  librerías de CUDA que trae el de PyPI y que sin GPU no sirven. En la máquina
  con GPU se quita, y `comparar_ocr.py` usa CUDA para TrOCR.
- Tesseract: `sudo apt install tesseract-ocr`. Sin `sudo`, se bajan los `.deb`
  (`apt-get download tesseract-ocr libtesseract5 liblept5 tesseract-ocr-eng
  tesseract-ocr-osd`), se extraen con `dpkg -x` a un prefijo propio y
  `TESSERACT_BIN` apunta a un envoltorio que fija `LD_LIBRARY_PATH` y
  `TESSDATA_PREFIX` hacia ese prefijo.

Registrar un motor nuevo es añadir una función a `MOTORES` en ese script: recibe
la lista de recortes y devuelve `(operación, objetivo)` por cada uno. Candidatos
que valen la pena con GPU: TrOCR base/large, PARSeq, y los modelos de documento
de 2026 (GLM-OCR, DeepSeek-OCR, dots.ocr) — estos últimos son para páginas
enteras, así que tendría más sentido pasarles el tablero completo y ver si
devuelven también la estructura de jaulas, no solo las etiquetas.

Si se prueba algo por API con clave, que la clave viva en el entorno y **nunca
en el repo**.

## Lo que se probó y NO funcionó

Se añadieron rasgos estructurales al clasificador —número de huecos cerrados
(para separar `3` de `8`) y tramos de tinta en la banda central (para separar
`+` de `÷`)— como bonificación sobre la correlación. **Empeoró**: de 99.4% a
95.4%, porque agrupaba `0`/`6`/`9` (los tres tienen un hueco) y la correlación
no volvía a separarlos. La ablación está en el historial; lo que sí resolvió las
confusiones fue **ampliar el banco tipográfico**. No reintroducir la idea sin
volver a medir.

## Estructura

| Módulo | Responsabilidad |
|---|---|
| `schema.py` | **El contrato con la Fase 2.** `Instance`, su JSON y `validate()`. |
| `render.py` | Generador sintético: tableros válidos con ground truth + degradación. |
| `grid.py` | Localiza el tablero, corrige perspectiva, deduce `n` y las líneas. |
| `cages.py` | Mide el grosor de cada arista y agrupa celdas en jaulas. |
| `glyphs.py` | Lee la etiqueta de cada jaula por correlación con plantillas. |
| `pipeline.py` | Une todo: imagen -> `Instance` validada. |

Y en `scripts/`: `evaluar.py` y `generar_dataset.py` trabajan con tableros
generados; `dataset_real.py` y `evaluar_real.py`, con tableros impresos reales.

## Uso

```bash
cd labs/tb1-kenken
uv sync
uv run pytest                                               # 53 tests

# tableros generados: ground truth gratis, condiciones extremas
PYTHONPATH=. uv run python scripts/evaluar.py 80
PYTHONPATH=. uv run python scripts/generar_dataset.py 12

# tableros REALES: la cifra que vale (descarga los PDF la primera vez)
PYTHONPATH=. uv run python scripts/dataset_real.py
PYTHONPATH=. uv run python scripts/evaluar_real.py
PYTHONPATH=. uv run python scripts/comparar_ocr.py
```

Leer un tablero:

```python
from kenken_cv.pipeline import leer

lectura = leer("dataset/00_limpio_n4.png")
print(lectura.instancia.to_json())   # esto es lo que consume el modelo CP
print(lectura.confianza, lectura.avisos)
```

## El contrato con la Fase 2

La visión entrega esto y nada más:

```json
{
  "size": 4,
  "cages": [
    {"cells": [[0, 0], [1, 0]], "op": "-", "target": 3},
    {"cells": [[0, 1]], "op": "=", "target": 2}
  ]
}
```

Celdas `[fila, columna]`, origen 0 arriba a la izquierda. Operaciones `+ - * / =`;
`=` es la jaula de una sola celda. `Instance.validate()` garantiza al modelo CP
que la partición cubre el tablero, que cada jaula es contigua, y que `-` y `/`
solo aparecen sobre dos celdas.

El modelo CP puede escribirse contra instancias a mano sin esperar a la visión:

```python
from kenken_cv.schema import Instance
instancia = Instance.from_json(open("dataset/00_limpio_n4.png".replace(".png", ".json")).read())
```

## Sobre dónde vive esto

`labs/tb1-kenken` es raíz de proyecto independiente, como el resto de labs. El
enunciado pide un **repositorio GitHub propio** para el grupo, y `cs-topics` es el
cuaderno personal del curso: cuando haya grupo, esta carpeta se extrae a su propio
repo (`git subtree split`) sin tocar nada más.

## Procedencia de los datos

| Fuente | Qué aporta | Licencia |
|---|---|---|
| `render.py` | tableros generados con ground truth | propio |
| [KrazyDad Inkies](https://krazydad.com/inkies/) | 16 tableros reales + verdad exacta del PDF | © KrazyDad.com; su web autoriza uso escolar y prohíbe el comercial. Se descargan bajo demanda, **no se versionan**, y hay que citarlos en el informe. |

Se descartó [`kennethjmyers/Metis-Projects`](https://github.com/kennethjmyers/Metis-Projects)
(370 glifos reales etiquetados, el único precedente de KenKen por visión que se
encontró): **no declara licencia**, y además sus recortes vienen estirados a
28x28, lo que destruye la proporción del glifo y hunde cualquier clasificador
que la respete. Sirvió para orientarse, no como referencia.

**No existe un dataset público etiquetado de KenKen.** Es un dato para el
informe: la sección de datos no es relleno, es trabajo propio.

## Nota de autoría

El andamiaje de visión de esta carpeta se desarrolló con asistencia de IA
(Claude Code). El modelo de Constraint Programming de la Fase 2 no: lo escribe
el equipo. El enunciado y la política del curso obligan a declararlo.
