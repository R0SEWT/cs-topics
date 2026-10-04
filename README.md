<a id="inicio"></a>

<div align="center">

<h1>cs-topics</h1>

<p>
  <strong>Constraint Programming con OR-Tools, agentes con JADE</strong>,<br>
  y un TB1 que lee tableros KenKen impresos para que un modelo CP los resuelva.
</p>

<p>
  Cuaderno del curso <em>Tópicos en Ciencias de la Computación</em> (UPC 1ACC0058, ciclo 2026-20)
</p>

<p>
  <img alt="Python" src="https://img.shields.io/badge/Python-uv-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img alt="OR-Tools" src="https://img.shields.io/badge/OR--Tools-CP--SAT-4285F4?style=for-the-badge&logo=google&logoColor=white">
  <img alt="Java" src="https://img.shields.io/badge/Java_21-JADE_4.3-ED8B00?style=for-the-badge&logo=openjdk&logoColor=white">
  <img alt="CI Python" src="https://img.shields.io/github/actions/workflow/status/R0SEWT/cs-topics/python.yml?branch=develop&style=for-the-badge&label=pytest">
  <img alt="CI JADE" src="https://img.shields.io/github/actions/workflow/status/R0SEWT/cs-topics/jade.yml?branch=develop&style=for-the-badge&label=jade%20build">
</p>

<p>
  <a href="#resultados">Resultados</a> ·
  <a href="#empezar">Empezar</a> ·
  <a href="labs/tb1-kenken/README.md">TB1: visión sobre KenKen</a>
</p>

</div>

<details>
  <summary>Contenido</summary>
  <ol>
    <li><a href="#que-es">Qué es</a></li>
    <li><a href="#resultados">Resultados</a></li>
    <li><a href="#empezar">Empezar</a></li>
    <li><a href="#mapa">Mapa del repo</a></li>
    <li><a href="#curso">El curso</a></li>
    <li><a href="#convenciones">Convenciones</a></li>
  </ol>
</details>

<a id="que-es"></a>

## Qué es

Apuntes por sesión y código del curso, organizado por toolchain y no por semana: las unidades
pueden reordenarse, los labs no.

| Lab | Stack | Para qué |
|---|---|---|
| `labs/cp/` | Python + OR-Tools CP-SAT | Constraint Programming, unidades 2 a 4 |
| `labs/tb1-kenken/` | Python + OpenCV | TB1, fase 1: leer un tablero KenKen y entregar la instancia al modelo CP |
| `labs/agents/` | Java 21 + JADE 4.3 | Agentes, MDP y FIPA, unidad 5 |

El TB1 se parte en dos. La fase 1 es visión: de la imagen de un tablero sale una instancia en JSON
(tamaño, jaulas, operación y objetivo de cada una), validada contra el contrato de
[`schema.py`](labs/tb1-kenken/kenken_cv/schema.py). La fase 2 es el modelo CP que la resuelve.

<p align="right">(<a href="#inicio">volver arriba</a>)</p>

<a id="resultados"></a>

## Resultados

**TB1, fase 1**, contra 16 tableros reales de los cuadernillos de KrazyDad (6x6 y 9x9), con la
verdad sacada del texto vectorial de los propios PDF:

| Métrica | Resultado |
|---|---:|
| Tamaño del tablero (n) | **16/16** |
| Anclas de jaula correctas | **98,6 %** (412/418), sin falsos positivos |
| Etiqueta completa (operación + número) | **98,8 %** |
| Tablero de 16 jaulas leído entero | 82,3 % |
| Tablero de 23 jaulas leído entero | 75,5 % |

- **El conjunto sintético no mide nada.** Después de dar 100 % en tableros generados, el pipeline
  falló en los 16 reales, por cuatro supuestos que el generador nunca puso a prueba. La cifra que
  vale es la de los tableros impresos.
- **El cuello de botella era el recorte, no el OCR.** Medir el margen en vez de fijarlo subió las
  etiquetas de 83,5 % a 98,8 %; entre motores de OCR había tres puntos de diferencia.
- **Con el recorte arreglado, las plantillas (98,8 %) y Tesseract (97,1 %) no se distinguen**
  (McNemar, p = 0,065), y se equivocan en etiquetas distintas: solo coinciden en errar las tres
  que desbordan su celda. Eso es lo que hace viable un jurado de motores.
- **No existe un dataset público etiquetado de KenKen.** La sección de datos del informe es trabajo
  propio.

El detalle, lo que falta y lo que se probó sin éxito está en
[`labs/tb1-kenken/README.md`](labs/tb1-kenken/README.md).

<p align="right">(<a href="#inicio">volver arriba</a>)</p>

<a id="empezar"></a>

## Empezar

**Requisitos:** [uv](https://docs.astral.sh/uv/) y Java 21. El Python 3.14 del sistema no sirve
para OR-Tools; los labs fijan `<3.14` y `uv` baja un intérprete compatible.

**1. Constraint Programming.**

```bash
cd labs/cp
uv sync
uv run pytest -q
uv run python models/nqueens.py
```

**2. TB1.** Los tests corren sin datos; las cifras reales necesitan bajar los PDF una vez.

```bash
cd labs/tb1-kenken
uv sync
uv run pytest -q
PYTHONPATH=. uv run python scripts/dataset_real.py    # baja los tableros (no se versionan)
PYTHONPATH=. uv run python scripts/evaluar_real.py
```

**3. Agentes.** `make build` baja `jade.jar` de Maven Central la primera vez.

```bash
cd labs/agents
make build
make run AGENT=upc.topicos.week11.HolaAgent    # la plataforma no termina sola: Ctrl-C
```

> [!IMPORTANT]
> `materials/` (slides, enunciados y rúbricas del Aula Virtual) no se versiona: el repo es público
> y el material es del profesor. `manifest.json` es el índice, y `aula sync`
> (de `chrome-helper`) reconstruye la carpeta a partir de él.

<p align="right">(<a href="#inicio">volver arriba</a>)</p>

<a id="mapa"></a>

## Mapa del repo

| Ruta | Qué hay |
|------|---------|
| `labs/` | Un proyecto independiente por lab, cada uno con su README y sus comandos. |
| `notes/` | Apuntes por sesión, `week-NN-<tema>.md`. `_template.md` es la plantilla. |
| `manifest.json` | Inventario del Aula Virtual: documentos, adjuntos, enlaces y estado de cada descarga. |
| `materials/AULA-VIRTUAL-ESTADO.md` | Resumen propio del estado del curso; lo único versionado de `materials/`. |
| `.github/workflows/` | CI: `pytest` en los labs de Python y `make build` en el de JADE. |

<p align="right">(<a href="#inicio">volver arriba</a>)</p>

<a id="curso"></a>

## El curso

| Unidad | Semana | Tema |
|---|---:|---|
| 1 | 1 | Research in Computer Science |
| 2 | 3–5 | Constraint Programming: introducción, consistencia local, problemas sobrerrestringidos |
| 3 | 6–7 | Fixtures; generación de texto con CP |
| 4 | 9–10 | Problemas reales; CP y data mining |
| 5 | 11–13 | Agentes y MDP; sistemas multiagente; FIPA |
| 6 | — | Outcome ABET 1 — Análisis de Problemas |

> [!NOTE]
> Al 2026-08-28 el E-Sílabo no estaba publicado y no había fechas de evaluación oficiales, así que
> la numeración de unidades puede moverse. El detalle está en
> [`materials/AULA-VIRTUAL-ESTADO.md`](materials/AULA-VIRTUAL-ESTADO.md).

<p align="right">(<a href="#inicio">volver arriba</a>)</p>

<a id="convenciones"></a>

## Convenciones

- **TDD**: el test antes que el modelo o el agente.
- **Git Flow**: nada entra directo a `develop` ni a `main`. Una rama por unidad de trabajo, PR con
  la CI en verde, y una fusión a `main` por entregable, con tag (`tb1`, …).
- **Tareas en beads** (`bd ready`), no en TODOs sueltos.
- **IA declarada**: el andamiaje de visión del TB1 se hizo con asistencia de IA (Claude Code); el
  modelo CP de la fase 2 lo escribe el equipo.

Las reglas completas están en [`CLAUDE.md`](CLAUDE.md).

<p align="right">(<a href="#inicio">volver arriba</a>)</p>

<p align="center"><sub>Tópicos en Ciencias de la Computación · UPC · 2026-20 · Docente: Willy Gustavo Ugarte Rojas</sub></p>
