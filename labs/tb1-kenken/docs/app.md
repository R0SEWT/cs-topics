# App móvil — especificación (borrador)

Estado: **borrador**, nada construido todavía. Patrón de referencia: el visor de
`R0SEWT/concurrente` (`tp/app/`), diseñado alrededor de una persona y con un principio de
diseño con nombre propio.

**El diseño centrado en las personas se fundamentará en papers** (ver "Fundamento en la
literatura", más abajo). Esa revisión se hace en otra sesión; hasta entonces, las
personas, los principios y la forma de validar de esta sección son **provisionales**.

## Para quién

### Personas (sintéticas, provisionales)

- **Diego, 22, estudiante.** Va en el bus con un cuadernillo de KenKen, se atasca en uno y
  quiere la respuesta *ya*, con una mano, para compararla con la suya. Le sobra cualquier
  pantalla que no sea la cámara.
- **Marta, 61, KenKen del periódico con lápiz.** Está en la mesa de la cocina, a mitad de
  un 9×9, y sospecha que tiene un error. No quiere que le regalen la solución, solo saber
  si va bien y, si no, dónde se equivocó. Necesita letra grande y mensajes sin tecnicismos.

### Principios de diseño (fundamentados en la literatura)

1. **Honestidad de lectura.** La app nunca muestra una solución que no pueda respaldar. Si
   lo que leyó no deja el tablero con solución única, dice qué no pudo leer y dónde, en vez
   de adivinar. Hoy el sistema ya cumple esto: de 16 tableros reales, 8 se resuelven bien y
   ninguno de los otros 8 devuelve una solución errónea (`scripts/medir_solver.py`).
   *Fundamento:* Directrices G1, G2 y G10 de interacción Humano-IA (Amershi et al., CHI 2019)
   y preservación de utilidad bajo incertidumbre (Horvitz, CHI 1999).
2. **Cero fricción.** La cámara aparece al abrir. La cuenta es solo tu nombre. Nada de
   formularios, contraseñas ni tutoriales obligatorios. Conexión al servidor vía código QR
   mostrado en la terminal/pantalla del nodo.
   *Fundamento:* Minimización de carga en memoria de trabajo y barreras cognitivas para adultos
   mayores (Gomez-Hernandez et al., JMIR 2023; Norman, 2013).
3. **Cada fallo dice qué hacer.** En lenguaje llano ("hay sombras sobre el papel, acércate a la
   luz"; "el borde inferior quedó cortado, aléjate un poco"), nunca "error" genérico ni códigos.
   *Fundamento:* Heurística 9 de Nielsen (recuperación de errores), directriz G11 de Amershi
   (explicar por qué falló la IA) y mitigación de fallos en captura móvil por contraste y
   contornos (Skoryukina et al., 2020).
4. **Tú decides cuánto quieres saber.** La ayuda va de menos a más (andamiaje) y nunca revela
   más de lo que se pidió. Marta no quiere spoilers. Cuatro niveles: 1) Estado global (¿voy bien?)
   → 2) Marcado de conflictos visibles → 3) Señalar la casilla errónea vía núcleo insatisfacible
   de CP-SAT → 4) Revelar el valor numérico.
   *Fundamento:* Teoría del andamiaje (*scaffolding*) pedagógico y desvanecimiento de asistencia
   (Wood, Bruner & Ross, 1976) y tutoría cognitiva sin respuestas prematuras (Gupta & MacLellan, AAAI 2021).
5. **Legible para todos.** Tipografía grande ($\ge 18\text{ sp}$), contraste cromático alto
   ($\ge 4.5:1$, objetivo $7:1$), touch targets de al menos $48 \times 48\text{ dp}$ con separación
   $\ge 8\text{ dp}$, y controles interactivos en la zona inferior del pulgar accesible con una mano.
   *Fundamento:* Revisión sistemática de pautas móviles para adultos mayores (Gomez-Hernandez et al.,
   JMIR 2023), listas de verificación empíricas para teléfonos móviles (Petrovčič et al., IJHCI 2018)
   y pautas WCAG 2.2 / ISO 9241-210.

### Fundamento en la literatura (resuelto en cst-byw.8)

El marco metodológico completo, el resumen crítico de cada paper, sus hallazgos empíricos y
su traducción a decisiones de arquitectura e interfaz se encuentran detallados en:
- Informe de revisión de literatura: [`docs/literatura_hcd.md`](file:///home/rody/Code/personal/cs-topics/labs/tb1-kenken/docs/literatura_hcd.md)
- Archivo de citas BibTeX completo: [`docs/references.bib`](file:///home/rody/Code/personal/cs-topics/labs/tb1-kenken/docs/references.bib)
- Repositorio de PDFs descargados: [`docs/papers/`](file:///home/rody/Code/personal/cs-topics/labs/tb1-kenken/docs/papers/) (y en `gdrive:cs-topics-hcd-papers/`)

### Validación con 5 usuarios reales (cst-byw.7)

La propuesta de probar con **5 personas reales** (pensando en voz alta) se fundamenta en el
modelo de optimización de descubrimiento de problemas de Nielsen & Landauer (1993) y Nielsen (2000),
donde 5 participantes identifican $\approx 85\%$ de los problemas de usabilidad. Para mitigar
la variabilidad observada empíricamente por Faulkner (2003) (donde muestras no representativas
pueden bajar al 55%), la muestra se estratificará intencionalmente entre perfiles jóvenes (tipo Diego)
y adultos mayores (tipo Marta). Detalles en [`docs/literatura_hcd.md`](file:///home/rody/Code/personal/cs-topics/labs/tb1-kenken/docs/literatura_hcd.md).

## v1 — Core loop: foto → solución

1. **La primera vez**, una sola pregunta: "¿Cómo te llamas?". Si el nombre ya existe,
   "¡Hola de nuevo, Marta!"; si no, se crea la cuenta. Las veces siguientes la app ya lo
   recuerda.
2. Aparece la cámara.
3. El usuario toma la foto.
4. La app lee el tablero y lo resuelve. **Objetivo: menos de 3 s** de foto a solución. El
   solver tarda menos de 50 ms; el tiempo se va en la red y en la Fase 1.
5. **Muestra la solución.** Hay dos maneras, y se decide en la validación con usuarios:
   - **Sobre tu propia foto:** ves tu hoja de papel tal como la fotografiaste, con los
     números de la solución escritos encima de cada casilla. Copiarlos al papel es directo
     porque todo está donde lo ves. Es la opción por defecto del prototipo, y el código ya
     guarda lo necesario para dibujarla (`Rejilla.homografia`).
   - **Tablero limpio:** un tablero redibujado, recto y nítido, con la solución. Se lee
     mejor si la foto salió torcida, pero hay que buscar la correspondencia con el papel.

   Un botón cambia de una vista a la otra.
6. Queda guardada en tu historial.

### Avisos

Cada fallo termina en un mensaje que dice qué pasó y qué hacer. Parte de las señales ya
existen en el pipeline:

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
| Sin solución, o más de una | `resolver` → `None`; `contar_soluciones` ≥ 2 | sí | "Leí algo mal: así el tablero no tiene solución." Resalta las jaulas sospechosas. |

Los umbrales de "muy inclinada", "poca luz" y "movida" **no se fijan a ojo**: se calibran
con el dataset fotografiado (cst-zol), igual que el margen del recorte se midió en vez de
fijarlo.

### Fallo conocido: la mitad de los tableros reales no sale

Hoy 8 de 16 tableros reales no se resuelven de punta a punta. Casi siempre falla una sola
cosa: el detector junta dos jaulas en una (6 de 8 casos, cst-90g) o una etiqueta de 4
cifras queda sin operador (2 de 8, cst-5h1). **Pedir otra foto no lo arregla**, porque no
es culpa de la foto. En v1 se avisa con honestidad y se resalta la pieza sospechosa.

Más adelante, una **corrección rápida**: el usuario toca la jaula sospechosa para partirla,
o escribe la etiqueta que no se pudo leer, y la app vuelve a resolver. Pendiente de
evaluar.

## v1.x — Cuenta e historial

- **Cuenta = solo tu nombre.** Escribes tu nombre y entras, o te registras si es nuevo. No
  hay contraseña.
- El historial vive en el servidor (SQLite en el nodo de cómputo), así que es el mismo
  desde cualquier teléfono.
- Por cada tablero se guarda: una miniatura de la foto, la instancia leída (JSON), la
  solución, la fecha y el estado (resuelto o sin resolver).
- Lista cronológica; al tocar un tablero se vuelve a ver su solución. Se puede borrar.
- **Límites que asumimos a sabiendas:**
  - Sin contraseña, quien escriba tu nombre ve tu historial. Vale para una demo en una red
    local, no para publicar la app.
  - Dos personas con el mismo nombre comparten cuenta.

## v2 — Modo verificación: "¿voy bien?"

Para Marta: fotografía su tablero a medio llenar, o terminado, escrito a mano.

1. **Leer los números escritos a mano.** Es una capacidad nueva: el OCR actual compara
   contra plantillas de tipografías impresas, y un dígito escrito a mano necesita un
   clasificador entrenado (aquí sí sirve la GPU del nodo). Hay que separar la etiqueta
   impresa (esquina superior izquierda) del número del usuario (centro de la celda) y
   distinguir las celdas vacías.
2. **Colorear los conflictos** sin necesidad de conocer la solución: repetidos en fila o
   columna, y jaulas completas que no cumplen su operación.
3. **Señalar el error.** Se cargan los números del usuario como suposiciones
   (*assumptions*) en el modelo. Si con ellas el tablero ya no tiene solución, CP-SAT
   devuelve un conjunto de suposiciones que no pueden ser todas ciertas
   (`SufficientAssumptionsForInfeasibility`). Eso señala dónde está el error **sin revelar
   la solución**, y es un argumento de Programación con Restricciones, que en la rúbrica
   pesa más que uno de visión.
4. **Ayuda graduada (principio 4),** de menos a más: "vas bien / hay un error" → resaltar
   los conflictos → marcar la casilla equivocada → mostrar la solución. Cada paso lo pide el
   usuario.

**Autoría:** la extensión del modelo CP (las suposiciones y el núcleo insatisfacible) es
parte del modelo de la Fase 2 y la escribe el equipo, como el solver (cst-76y). La IA
puede ayudar con la interfaz, la lectura de dígitos y los tests.

## Plataforma y arquitectura

```
 teléfono Android (APK)                 nodo de cómputo (PC con GPU)
 ┌───────────────────────┐   Wi-Fi     ┌──────────────────────────────────────────┐
 │ cliente Android       │   local     │ API en Python                             │
 │ (tecnología abierta)  │ ──────────► │  kenken_cv (Fase 1) → kenken_cp (CP-SAT)  │
 │ cámara nativa         │ ◄────────── │ SQLite: cuentas e historial               │
 └───────────────────────┘             └──────────────────────────────────────────┘
```

- **APK para Android, con la tecnología abierta.** Capacitor (el HTML/CSS/JS de
  `concurrente` empaquetado como APK), Android nativo en Kotlin, u otra opción: se decide
  sobre la marcha según lo que resulte más relevante. Cualquiera de las tres usa la cámara
  nativa y se instala directamente, sin pasar por Play Store. Lo que sí está fijado es el
  contrato con el nodo (la API), así que el cliente se puede cambiar sin tocar el servidor.
- **El servidor es un nodo de cómputo con GPU.** Se desarrolla en la máquina de Rody y se
  prueba en la PC de otro integrante, que tiene una **RTX 4060**. El pipeline es Python
  (OpenCV y OR-Tools), y meterlo dentro de una APK supondría reescribirlo; en el nodo se
  reutiliza tal cual. La v1 corre bien en CPU; la GPU entra con la v2 (dígitos a mano) y con
  el jurado de motores OCR.
- **Conexión: la misma Wi-Fi.**
  - Para no tener que escribir direcciones IP, el nodo muestra un **código QR** con su
    dirección y la app lo escanea una vez (principio 2).
  - Riesgo: las redes Wi-Fi de campus suelen aislar a los dispositivos entre sí. Plan B: el
    nodo se conecta al punto de acceso del teléfono.
  - Android bloquea por defecto el HTTP sin cifrar, sea cual sea el cliente. La app tiene
    que permitirlo para la red local con una configuración de seguridad de red.
- **Privacidad:** las fotos y el historial quedan en la PC del nodo. La app lo dice al crear
  la cuenta y deja borrar cualquier tablero.
- **Sin conexión no funciona** mientras el solver viva en el nodo.

## Cómo se mide

- Porcentaje de fotos reales que terminan en la solución correcta. Hoy, sobre PDF
  rasterizados, es 8/16.
- Porcentaje de fallos que terminan en un aviso específico, no genérico.
- Tiempo de foto a solución en un teléfono real (p50 y p95).
- En la validación con usuarios: tareas completadas sin ayuda, tiempo, y mensajes que no
  se entendieron. Las métricas definitivas salen de la revisión de literatura.
- Todo sobre fotos reales (cst-zol), no sobre sintéticos.

## Fuera de alcance

Contraseñas o autenticación real, iOS, publicar en Play Store, funcionamiento sin conexión,
generar KenKens nuevos y otros acertijos.

## Decisiones

**Tomadas (2026-10-02):**

- APK para Android con un servidor en un nodo con GPU: se desarrolla en la máquina de Rody
  y se prueba en la PC con RTX 4060 de otro integrante.
- Teléfono y nodo en la misma Wi-Fi.
- Cuenta solo con el nombre e historial en el servidor.
- La corrección rápida queda para después, registrada como fallo conocido.
- El diseño centrado en las personas se fundamenta en papers; la revisión, en otra sesión.

**Abiertas:**

1. La tecnología del cliente (Capacitor, Kotlin nativo u otra) se decide sobre la marcha.
2. La revisión de literatura para el diseño centrado en las personas, que define el
   método, los principios y la validación.
3. La vista de la solución (sobre la foto o tablero limpio), que se decide en la
   validación con usuarios.
