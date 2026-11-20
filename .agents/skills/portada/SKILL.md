---
name: portada
description: Método para escribir y mantener la portada del repo (el README raíz) — inventario de activos, lectores, rúbrica, libro de cifras con fuente y un bucle de iteración que mira el README tal como lo pinta GitHub, en claro, oscuro y ancho de celular. Úsala cuando haya que rehacer o actualizar el README raíz, al cerrar un entregable (TB1, TB2, …) que deba aparecer en la portada, o cuando cambie una cifra del informe.
---

# La portada: método

El README raíz no documenta: **convence y orienta**. Documentar es trabajo del README de cada
lab, del informe y de las diapositivas. La portada decide qué ve primero cada lector y adónde
va después.

## 1. Inventario antes de escribir

Lista cada activo con dónde vive, qué prueba y si la portada lo usa. Un activo de mucho valor
que no aparece necesita una razón escrita para quedarse fuera.

| Tipo | Dónde buscar |
|---|---|
| Cifras canónicas | `informe/main.tex` (líneas `% CANON`), `presentacion/datos/*.json` |
| Evidencia visual | `informe/fig/`, `presentacion/img/`, `presentacion/datos/img/`, `presentacion/video/` |
| Entregables | `gh release list` (PDF, fotos, diapositivas en un archivo), <https://kenken.rosewt.dev>, dataset en Hugging Face |
| Código que se ejecuta | CLI (`solve.py`), nodo (`python -m kenken_nodo`), app (`app/`, `movil/`), tests |
| Proceso | CI, TDD, Git Flow, beads, declaración de IA |

## 2. Lectores y su pregunta

| Lector | Llega preguntando | Tiene que resolverlo en | Dónde |
|---|---|---|---|
| Visitante | ¿Qué es y funciona? | 10 s, sin scroll | título, la pregunta, una línea con la cifra clave y la animación justo debajo |
| Docente o jurado | ¿Dónde está el entregable y se sostiene? | 1 min | botones a informe, diapositivas y release; resultados con fuente |
| Quien quiere correrlo | ¿Cómo lo pruebo? | 5 min | «Probarlo», con comandos ejecutados |
| Equipo, yo del futuro | ¿Dónde está cada cosa? | — | mapa, convenciones |

## 3. Un solo hilo

Pregunta → idea, con la animación y su foto real → en el celular → cómo funciona → resultados
con sus límites → probarlo → entregables → mapa del repo → convenciones → equipo. La pregunta es la del entregable estrella; para el TB1, la del informe:
**¿qué sobrevive a una lectura equivocada?** Cada sección responde a la anterior.

## 4. Libro de cifras

Toda cifra de la portada sale de una fuente versionada, con el mismo redondeo que el informe.
`verificar_cifras.py` extrae los números del README, también los de los `alt`, y avisa de los
que no aparecen en ninguna fuente. Los pares «N de M» tienen que estar escritos como par en el
informe (texto, `N/M` o celdas vecinas de una tabla) o en su `LIBRO`, con la justificación: en
los JSON, una línea llena de enteros, cualquier par «aparece». Si cambia una cifra, cambia en el
informe primero. Una cifra suelta vale menos que una con denominador: «48 de
70» explica a los «22 mal leídos»; «111 ms», una sola medición, no explica nada.

La declaración de uso de IA también sale de una fuente: la portada cita la del informe, tal
cual, y agrega una frase que declara la propia portada.

## 5. Sistema visual

- **La misma identidad que las diapositivas** (`presentacion/tema.scss`): índigo para lo que el
  sistema decide bien, naranja para la lectura equivocada y su reparación, papel y tinta.
- **Figuras generadas, no dibujadas**: `labs/tb1-kenken/scripts/figuras_portada.py` las escribe
  en `.github/portada/` a partir de los datos. Ninguna cifra de una figura está a mano.
- **Claro y oscuro** con `<picture>` y `prefers-color-scheme`; GitHub lo envuelve en
  `themed-picture` y respeta el tema elegido en la cuenta.
- **Legible a 380 px**: el texto de una figura no baja de ~11 px a ancho de celular. Una figura
  de 1000 de ancho no llega: el héroe mide 880 (estados a 28). La arquitectura y los tableros
  todavía no cumplen (bead `cst-ukg`).
- **El formato del repo hermano**, [R0SEWT/concurrente](https://github.com/R0SEWT/concurrente):
  anclas propias (`<a id>`), «Contenido» plegable, «volver arriba» al final de cada sección,
  badges de stack y de CI en la cabecera, y al final Convenciones y Equipo con avatares.
- **El color nunca va solo**: siempre con texto o forma; `alt` que describe lo que se ve.
- **Peso**: el GIF bajo 3 MB, cada SVG bajo 150 kB.

## 6. Qué sobrevive al saneado de GitHub

- Se descarta `style`, `class`, `id` y `script`. Quedan `align`, `width`, `height`, `<picture>`,
  `<details>`, `<sub>`, `<kbd>`, tablas, alertas (`> [!NOTE]`) y anclas por encabezado.
- Un SVG en `<img>` no ejecuta JS ni carga nada de afuera, y lo incrustado como `data:` podría
  bloquearlo la CSP de GitHub (ver abajo): las figuras van en vector puro, con las tipografías
  del sistema. Las animaciones CSS sí corren; respeta `prefers-reduced-motion`.
- Un video del repo no se incrusta: solo los subidos por la web (user-attachments). Desde el
  repo, GIF y enlace al video o a la diapositiva de la demo.

## 7. El bucle

1. **Ver**: `vista-previa.sh README.md <salida> vN` pasa el README por la API de GitHub,
   lo envuelve con su CSS y saca capturas en claro, oscuro y 380 px.
2. **Puntuar** con la rúbrica mirando las capturas, no el Markdown.
3. **Crítica independiente**: un subagente sin contexto recibe las capturas y la rúbrica, no
   las conclusiones propias.
4. **Arreglar lo peor primero** y anotar en la PR qué cambió en cada ronda y por qué.

Termina cuando todo puntúa 4 o más, el crítico no deja nada importante y una ronda entera no
encuentra mejoras de fondo.

Antes de fusionar, con la rama ya subida, una última mirada en github.com:
`https://github.com/<dueño>/<repo>/blob/<rama>/README.md`, capturada con el mismo Firefox
headless y las mismas preferencias de `vista-previa.sh`, en claro y oscuro. Es lo único que
confirma lo que `post.py` imita: `<picture>`, las alertas y los SVG animados.

## 8. Rúbrica (1 a 5)

| Criterio | Se cumple si… |
|---|---|
| Diez segundos | Sin hacer scroll se entiende qué hace, que funciona y por qué importa. |
| Hilo | Una sola pregunta guía; cada sección responde a la anterior. |
| Verdad | Cifras con fuente y actuales; los límites a la vista; ningún superlativo vacío. |
| Evidencia | Muestra (foto real, demo, datos) en vez de afirmar. |
| Acción | Los comandos funcionan copiados tal cual: se ejecutaron. |
| Escaneo | Títulos que dicen algo; párrafos cortos; tablas para comparar. |
| Oficio visual | Jerarquía, consistencia, claro y oscuro, celular, peso. |
| Voz | El español del repo: frases declarativas, la cifra que vale, nada de marketing. Sin calcos: «la verdad» por *ground truth* (mejor «las respuestas correctas»), «en llano», «fallan distinto». |
| Mantenimiento | Se actualiza sin rehacer: figuras regenerables, cada cifra en un solo lugar. |

## Herramientas

| Archivo | Para qué |
|---|---|
| `vista-previa.sh` | Capturas del README tal como lo pinta GitHub: claro, oscuro y celular. |
| `post.py` | Lo usa `vista-previa.sh`: imita en local lo que en github.com hace el JS. |
| `guion.sh` | Congela un SVG animado en varios instantes para revisarlo cuadro a cuadro. |
| `verificar_cifras.py` | El libro de cifras: cada número del README tiene que estar en una fuente. |
| `labs/tb1-kenken/scripts/figuras_portada.py` | Regenera las figuras de `.github/portada/` desde los datos. |

```bash
python3 .agents/skills/portada/verificar_cifras.py README.md
.agents/skills/portada/vista-previa.sh README.md /tmp/portada v1
.agents/skills/portada/guion.sh .github/portada/heroe-claro.svg /tmp/guion.png 1,4,7,10
cd labs/tb1-kenken && uv run --with imageio-ffmpeg python scripts/figuras_portada.py --gif
```

## Lo que ya costó caro

- **La API tiene dos modos y ninguno es el del README.** `mode=gfm` es el de los comentarios:
  cada salto de línea se vuelve `<br>` (los badges salen apilados y los párrafos, cortados).
  `mode=markdown` es el de los archivos, pero no pinta las alertas. `post.py` las convierte.
- **`<picture>` no cambia de tema en una vista previa estática.** GitHub mete el `<img>` en un
  `<a>` y deja que el JS de `themed-picture` elija; sin ese JS, el navegador ignora el
  `<source>`. `post.py` desenvuelve el `<a>`. Se ponen los dos `<source>`, claro y oscuro,
  como en la documentación de GitHub.
- **Firefox en snap no ve `/tmp`.** El HTML y el perfil tienen que vivir bajo `$HOME`.
- **Una animación capturada al cargar se ve vacía.** Por eso la vista previa usa movimiento
  reducido: el SVG muestra su estado final, que es además lo que ve quien lo tiene activado.
- **A tamaño chico, `÷` y `+` se confunden**, el mismo error que comete la visión. Las
  etiquetas que importan en una figura van más grandes que el resto.
- **El lab de TB1 no corre sin las tipografías del banco** (`fonts-freefont-ttf` y otras). Para
  probar comandos sin `sudo`: `apt download` del paquete, `dpkg-deb -x` y `XDG_DATA_HOME`
  apuntando a la carpeta, que `kenken_cv/fuentes.py` revisa.
- **El crítico independiente vale lo que cuesta.** En la primera ronda encontró lo que el autor
  no vio: que `solve.py` no cuenta soluciones ni repara (la portada lo daba a entender) y que
  las 8 fotos no decían qué eran. Dale el informe para cotejar y pídele que corra los comandos;
  verifica lo que diga antes de aplicarlo.
- **«Reales» junto a «desde una foto» se lee como «fotos».** Toda cifra dice de qué sale: PDF
  rasterizado, foto o sintético. Si en fotos el resultado es otro (2 de 8), va junto a las
  cifras, no tres pantallas más abajo.
- **Un comando que bloquea la terminal** (el nodo) deja sin correr al siguiente: va en otra
  terminal y se dice. Los requisitos van antes de los comandos, no después.
- **La tarjeta de cifras 2×2, con aire de tablero de KPIs, no le gustó al equipo.** Las cifras
  van en una línea bajo la pregunta y en la tabla de Resultados, con el estilo de GitHub.
- **El héroe no abre la página.** Primero título, pregunta, badges e índice, para que la
  animación tenga tiempo de cargar; ella abre «Qué es».
- **El GIF muestra lo esencial**: la foto, su solución y el tablero limpio. El tramo de Modo
  Asistencia lo alargaba sin sumar.
- **Sin verificar en github.com:** que una imagen `data:` dentro de un SVG del repo se vea. La
  CSP con que GitHub sirve los SVG (`default-src 'none'; style-src 'unsafe-inline'`) haría
  pensar que no; por eso las figuras no la usan.
