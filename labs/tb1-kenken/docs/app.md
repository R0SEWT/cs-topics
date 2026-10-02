# App móvil — especificación (borrador)

Estado: **borrador**. Las decisiones abiertas están al final; nada de esto está construido
todavía. Patrón de referencia: el visor de `R0SEWT/concurrente` (`tp/app/`), que es una
app web pensada primero para el celular, diseñada con diseño centrado en el usuario, con
una usuaria sintética y un principio de diseño con nombre propio.

## Qué es

El usuario apunta el teléfono a un KenKen en papel y obtiene la solución sin escribir
nada. Si la foto no sirve, la app le dice por qué y qué hacer. Más adelante podrá además
revisar un tablero que el usuario llenó a mano y señalarle dónde se equivocó.

### Principio: honestidad de lectura

> La app nunca muestra una solución que no pueda respaldar. Si lo que leyó no deja el
> tablero con solución única, dice qué no pudo leer y dónde, en vez de adivinar.

No es una aspiración, es lo que hoy ya hace el sistema: sobre 16 tableros reales, 8 se
resuelven bien y en los otros 8 **ninguno devuelve una solución errónea**. La instancia se
rechaza o el solver demuestra que no tiene solución (ver `scripts/medir_solver.py`). La app
tiene que conservar esa propiedad y hacerla visible.

### Usuarios (sintéticos)

- **Marta, 61, KenKen del periódico con lápiz.** Se atasca a mitad de un 9×9 y quiere
  saber si lo que lleva está bien, sin que le regalen la solución entera. Es la usuaria del
  modo verificación (v2).
- **Diego, 22, estudiante.** Encuentra un KenKen en un cuadernillo y quiere la respuesta ya
  para comprobar la suya. Es el usuario del core loop (v1).

## v1 — Core loop: foto → solución

1. Abre la app y aparece directamente la cámara, sin pantalla de inicio que haya que
   cruzar.
2. Toma la foto.
3. La app lee el tablero y lo resuelve: **objetivo de menos de 3 s** de foto a solución en
   la red local. El solver tarda menos de 50 ms; el tiempo se va en subir la foto y en la
   Fase 1.
4. Muestra la solución **sobre la propia foto**. `Rejilla.homografia` ya se guarda
   justamente para proyectar la solución sobre la imagen original. Un botón cambia a la
   vista de tablero limpio.
5. Se guarda en el historial (ver v1.x).

### Avisos (v1)

Cada fallo termina en un mensaje que dice **qué pasó y qué hacer**, nunca en un error
genérico. Parte de las señales ya existen en el pipeline:

| Situación | Cómo se detecta | ¿Existe? | Qué ve el usuario |
|---|---|---|---|
| No hay un KenKen en la foto | `TableroNoEncontrado`: el contorno mayor ocupa menos del 5% de la imagen | sí | "No encuentro un tablero. Encuádralo entero y acércate." |
| Tablero cortado | alguna esquina del cuadrilátero toca el borde de la imagen | **no** | "Falta una parte del tablero. Aléjate un poco." |
| Foto muy inclinada | ángulos del cuadrilátero lejos de 90° o lados muy desiguales antes de rectificar | **no** | "La foto está muy inclinada. Ponte más de frente al papel." |
| Borde roto (luz o sombra) | `approxPolyDP` no da 4 vértices y se cae a `minAreaRect` sin avisar | a medias | "No veo bien el borde del tablero." |
| Poca luz o bajo contraste | brillo y contraste del recorte del tablero | **no** | "Hay poca luz. Busca más luz o evita tu sombra." |
| Foto movida | varianza del laplaciano del tablero rectificado | **no** | "La foto salió movida. Apoya el teléfono y vuelve a intentarlo." |
| Jaulas dudosas | `Particion.fiable` (margen menor a 1.35) | sí | aviso suave junto a la solución |
| Etiqueta ilegible | `EtiquetaIlegible` con la celda | sí | resalta la celda: "No pude leer esta etiqueta." |
| Lectura incoherente | `InstanciaInvalida` con la jaula | sí | resalta la jaula: "Esta jaula no me cuadra." |
| Sin solución, o más de una | `resolver` → `None`; `contar_soluciones` ≥ 2 | sí | "Leí algo mal: el tablero así no tiene solución." Resalta las jaulas sospechosas. |

Los umbrales de "muy inclinada", "poca luz" y "movida" **no se fijan a ojo**: se calibran
con el dataset fotografiado (cst-zol), igual que el margen del recorte se midió en vez de
fijarlo.

### Corrección rápida (propuesta, por decidir)

Hoy la mitad de los tableros reales no sale de punta a punta. Casi siempre falla una sola
cosa: dos jaulas fundidas (6 de 8 casos) o una etiqueta de 4 cifras (2 de 8). En vez de
pedir otra foto, la app mostraría lo que leyó con la pieza sospechosa resaltada, y el
usuario la arreglaría con un toque: partir la jaula o escribir la etiqueta. Luego se
vuelve a resolver. Con esto, la mayoría de los fallos se recuperan sin otra foto.

## v1.x — Historial (por definir)

Propuesta mínima para discutir:

- Se guarda **en el teléfono** (IndexedDB), sin cuentas ni base de datos en el servidor.
- Por cada tablero: miniatura de la foto, instancia leída (JSON), solución, fecha, si hubo
  correcciones y el estado (resuelto / sin resolver).
- Lista cronológica; al tocar un tablero se ve otra vez su solución.

Preguntas abiertas: ¿hace falta sincronizar entre dispositivos?, ¿se puede exportar o
compartir un tablero?, ¿se borra solo?, ¿se guarda la foto completa o solo la miniatura?

## v2 — Modo verificación: "¿voy bien?"

Para Marta: fotografía su tablero a medio llenar, o terminado, escrito a mano.

1. **Leer los números a mano.** Es una capacidad nueva: el OCR actual compara contra
   plantillas de tipografías impresas, y un dígito escrito a mano necesita un clasificador
   entrenado. Hay que separar la etiqueta impresa (esquina superior izquierda) del número
   del usuario (centro de la celda) y distinguir las celdas vacías.
2. **Colorear los conflictos** sin necesidad de conocer la solución: repetidos en fila o
   columna, y jaulas completas que no cumplen su operación.
3. **Señalar el error.** Cargando los números del usuario como suposiciones (*assumptions*)
   en el modelo, CP-SAT puede decir si todavía tiene solución. Si no la tiene, devuelve un
   conjunto de esas suposiciones que no pueden ser todas ciertas
   (`SufficientAssumptionsForInfeasibility`). Eso señala dónde está el error **sin revelar
   la solución**, y es un argumento de Programación con Restricciones, que en la rúbrica
   pesa más que uno de visión.
4. Niveles de ayuda, de menos a más: "vas bien / hay un error" → resaltar los conflictos →
   marcar la celda equivocada → mostrar la solución.

**Autoría:** la extensión del modelo CP (las suposiciones y el núcleo insatisfacible) es
parte del modelo de la Fase 2 y la escribe el equipo, como el solver (cst-76y). La IA
puede ayudar con la interfaz, la lectura de dígitos y los tests.

## Plataforma y arquitectura

- **Una app web para el celular, como en `concurrente`**: HTML, CSS y JS sin framework, que
  se pueda instalar como PWA. No es una app nativa.
- **Hace falta un servidor.** OR-Tools no tiene versión para el navegador, así que la app
  sube la foto a una API en Python que reutiliza `kenken_cv` y `kenken_cp` tal cual. La
  misma API sirve los archivos de la app, así que es un solo proceso. Para la demo: el
  servidor en la laptop y el teléfono en la misma Wi-Fi.
- **Cámara:** en v1 se usa `<input type="file" accept="image/*" capture="environment">`, que
  abre la cámara nativa y funciona sin HTTPS. Un visor en vivo con guía en tiempo real
  ("acércate", "más luz") necesita `getUserMedia`, y eso exige HTTPS: queda para después.
- **Privacidad:** el servidor procesa la foto y no la guarda. El historial vive en el
  teléfono.
- **Sin conexión no funciona** mientras el solver viva en el servidor.

## Cómo se mide

- Porcentaje de fotos reales que terminan en la solución correcta, con y sin corrección
  rápida. Hoy, sobre PDF rasterizados, es 8/16.
- Porcentaje de fallos que terminan en un aviso específico, no genérico.
- Tiempo de foto a solución en un teléfono real (p50 y p95).
- Todo sobre el dataset fotografiado (cst-zol), no sobre sintéticos: la lección de la
  Fase 1 es que lo sintético no mide.

## Fuera de alcance

Cuentas de usuario, generar KenKens nuevos, otros acertijos (sudoku y similares),
funcionamiento sin conexión y app nativa.

## Decisiones abiertas

1. ¿Corrección rápida en v1, o solo avisar y pedir otra foto?
2. Historial: ¿solo en el teléfono, o hace falta sincronizar?
3. Solución sobre la foto, o tablero limpio por defecto.
4. ¿Dónde corre el servidor en la demo y la entrega: la laptop en la misma Wi-Fi, o un
   hosting?
