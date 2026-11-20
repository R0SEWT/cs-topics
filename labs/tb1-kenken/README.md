# TB1 · KenKen desde una foto

Las dos fases del Trabajo 1 (`materials/week-05/Topicos_CC-4.pdf`): la visión, que lee el
tablero de una imagen, y el modelo de Constraint Programming, que lo resuelve, verifica la
lectura y la repara. Además, el nodo y la app que los llevan a un celular. Entregado con el
tag [`tb1`](https://github.com/R0SEWT/cs-topics/releases/tag/tb1).

- **El resultado** está en la [portada del repo](../../README.md) y, con detalle, en el
  [informe](https://github.com/R0SEWT/cs-topics/releases/download/tb1/TB1-KenKen-Grupo3.pdf).
- **Esta página** es el manual del lab: qué hace cada módulo ([Estructura](#estructura)),
  cómo correrlo ([Uso](#uso)) y el contrato entre las fases.
- **Lo que sigue a continuación** es la bitácora del spike de septiembre, que decidió seguir
  con KenKen. Sus cifras son de entonces, sobre 16 tableros; las finales, sobre 70, son las
  del informe.

## Veredicto del spike: sí, seguimos con KenKen

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

La primera medición sobre las 412 etiquetas reales, **con el recorte todavía
defectuoso**, daba esto:

| método | etiqueta completa | operación | número |
|---|---:|---:|---:|
| Tesseract 5.3.4 (PSM 7) | 86.7% | 98.8% | 87.1% |
| Plantillas por correlación | 83.5% | 97.3% | 83.5% |
| CNN entrenada con sintéticos | 80.6% | 93.9% | 81.1% |

Y la ventaja de Tesseract **no resistía la prueba**: de 412 etiquetas los dos
primeros discrepaban en 57, ganando Tesseract 35 y las plantillas 22 — como
sacar 35 caras en 57 tiradas, que pasa por azar el 11% de las veces (McNemar
exacta, p = 0.111).

**La conclusión de verdad llegó después**: arreglar el recorte subió las
plantillas de 83.5% a **98.8%**, doce puntos, cuando entre motores había tres.
El cuello de botella nunca fue el OCR sino lo que se le daba de comer. Antes de
cambiar de motor, hay que arreglar la entrada.

Con el recorte arreglado la comparación está **sin rehacer** — es la primera
tarea pendiente, y `scripts/comparar_ocr.py` la automatiza. Aun así, la idea del
jurado sigue en pie para el resto de error: donde varios motores coinciden la
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

## Lo que faltaba al cierre del spike

1. **Rehacer la comparación de motores con el recorte arreglado.** Las cifras de
   Tesseract y la CNN son de antes del arreglo y ya no valen.
   `scripts/comparar_ocr.py` lo hace en un comando.
   *Hecho:* con el recorte arreglado, plantillas y Tesseract empatan (98.8% y 97.1% de
   412 etiquetas, p = 0.065); RapidOCR y TrOCR no leen los operadores (informe, Tabla III).
2. **Las etiquetas que desbordan su celda** (`2400×`): detectar que falta el
   operador y extender el recorte solo en ese caso, en vez de ensanchar siempre.
   Son 3 de 412, pero en un tablero 9x9 con 23 jaulas cuestan puntos.
   *Sigue abierto:* son las 3 etiquetas ilegibles de 895, que se rechazan antes del solver.
3. **Jurado de motores + reparación guiada por el solver.** Donde los motores
   coincidan, aceptar; donde discrepen, pasarle los candidatos al modelo CP y
   quedarse con el que deja el puzzle con solución única.
   *Hecha la reparación* ([`kenken_cp/reparar.py`](kenken_cp/reparar.py)): prueba las
   confusiones de glifo observadas con restricciones reificadas y repara 16 de las 19
   lecturas sin solución. El jurado quedó como cota: al menos un motor acierta el 99.8%.
4. **Dataset fotografiado.** Los PDF de KrazyDad son tinta real pero rasterizada
   de vectores: no tienen sombra, ni curvatura de papel, ni desenfoque de
   cámara. Eso hay que fotografiarlo.
   *Empezado:* 8 fotos con un Pixel 9a, en
   [Hugging Face](https://huggingface.co/datasets/rosewt/kenken-tb1-fotos) y en el release.

Lo que sigue está en la sección «Limitaciones y trabajo futuro» del informe.

## Para seguir en la máquina con GPU

Nada de lo que hay aquí necesita GPU — el pipeline es OpenCV y corre en CPU en
segundos. La GPU sirve para lo que viene:

```bash
cd labs/tb1-kenken
uv sync
PYTHONPATH=. uv run python scripts/dataset_real.py      # baja los PDF (no van al repo)
PYTHONPATH=. uv run python scripts/comparar_ocr.py      # los motores disponibles
```

`comparar_ocr.py` detecta CUDA solo para TrOCR. Para tener todos los motores:

```bash
uv pip install transformers torch rapidocr-onnxruntime   # trocr, rapidocr
sudo apt install tesseract-ocr                           # tesseract
```

Aquí Tesseract hubo que extraerlo de su `.deb` a un prefijo local por no haber
`sudo`; con permisos de administrador es una línea. El script admite
`TESSERACT_BIN` si el binario no está en el `PATH`.

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
| `kenken_cv/schema.py` | **El contrato con la Fase 2.** `Instance`, su JSON y `validate()`. |
| `kenken_cv/render.py` | Generador sintético: tableros válidos con ground truth + degradación. |
| `kenken_cv/grid.py` | Localiza el tablero, corrige perspectiva, deduce `n` y las líneas. |
| `kenken_cv/cages.py` | Mide el grosor de cada arista y agrupa celdas en jaulas. |
| `kenken_cv/glyphs.py` | Lee la etiqueta de cada jaula por correlación con plantillas. |
| `kenken_cv/fuentes.py` | Encuentra las tipografías del banco de plantillas, o falla diciendo cuál falta. |
| `kenken_cv/pipeline.py` | Une todo: imagen -> `Instance` validada. |
| `kenken_cp/solver.py` | **Fase 2.** El modelo CP-SAT: resuelve y cuenta soluciones con tope de dos. |
| `kenken_cp/reparar.py` | Repara una lectura sin solución con restricciones reificadas. |
| `kenken_nodo/` | API HTTP (FastAPI): la app manda una foto y recibe lectura, solución y correcciones. |
| `app/`, `movil/` | La app web y su envoltorio Android (Capacitor). |
| `solve.py` | CLI: imagen -> solución dibujada, sin intervención. |

Y en `scripts/`, un script por cifra del informe (la tabla está en la
[portada](../../README.md#probarlo)): `evaluar.py` y `generar_dataset.py` trabajan con
tableros generados; `scrapear_kenken.py`, `extraer_dataset.py` y
`punta_a_punta_scraped.py`, con los 70 tableros reales.

## Uso

El banco de plantillas usa tipografías del sistema; sin ellas el lab no arranca y el error
dice qué paquete instalar. En Debian o Ubuntu, las mismas que instala la CI:
`sudo apt install fonts-dejavu-core fonts-freefont-ttf fonts-liberation fonts-liberation-sans-narrow`.

```bash
cd labs/tb1-kenken
uv sync
uv run pytest                                               # 107 tests

# una foto de punta a punta, y el nodo para la app (http://127.0.0.1:8723)
uv run python solve.py ../../presentacion/datos/img/f1_foto.jpg --out resuelto.png
uv run python -m kenken_nodo

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

`labs/tb1-kenken` es raíz de proyecto independiente, como el resto de labs. El TB1 se
entregó desde este repo, que es el que cita el informe. Si hiciera falta un repositorio
propio para el grupo, `git subtree split` extrae esta carpeta sin tocar nada más.

## Procedencia de los datos

| Fuente | Qué aporta | Licencia |
|---|---|---|
| `render.py` | tableros generados con ground truth | propio |
| [KrazyDad Inkies](https://krazydad.com/inkies/) | 72 tableros reales de cinco cuadernillos (4x4, 6x6 y 9x9) + verdad exacta del PDF. El extractor no la produjo en dos, así que las mediciones de punta a punta usan 70 | © KrazyDad.com; su web autoriza uso escolar y prohíbe el comercial. Se descargan bajo demanda, **no se versionan**, y hay que citarlos en el informe. |
| Fotos propias | 8 fotos de tableros tomadas con un Pixel 9a | propias; en [Hugging Face](https://huggingface.co/datasets/rosewt/kenken-tb1-fotos) y en el release `tb1` |

Se descartó [`kennethjmyers/Metis-Projects`](https://github.com/kennethjmyers/Metis-Projects)
(370 glifos reales etiquetados, el único precedente de KenKen por visión que se
encontró): **no declara licencia**, y además sus recortes vienen estirados a
28x28, lo que destruye la proporción del glifo y hunde cualquier clasificador
que la respete. Sirvió para orientarse, no como referencia.

**No existe un dataset público etiquetado de KenKen.** Es un dato para el
informe: la sección de datos no es relleno, es trabajo propio.

## Nota de autoría

El andamiaje de visión de esta carpeta y los scripts de medición se desarrollaron con
asistencia de IA (Claude Code). El modelo de Constraint Programming de la Fase 2 no: lo
escribió el equipo. El enunciado y la política del curso obligan a declararlo; la
declaración completa está en el informe.
