# App móvil — especificación (borrador)

Estado: **borrador**, nada construido todavía. Patrón de referencia: el visor de
`R0SEWT/concurrente` (`tp/app/`), diseñado alrededor de una persona y con un principio de
diseño con nombre propio. Aquí vamos un paso más allá: **se valida con personas reales, no
solo con personas sintéticas.**

## Para quién

### Personas (sintéticas, a validar)

- **Diego, 22, estudiante.** Va en el bus con un cuadernillo de KenKen, se atasca en uno y
  quiere la respuesta *ya*, con una mano, para compararla con la suya. Le sobra cualquier
  pantalla que no sea la cámara.
- **Marta, 61, KenKen del periódico con lápiz.** Está en la mesa de la cocina, a mitad de
  un 9×9, y sospecha que tiene un error. No quiere que le regalen la solución, solo saber
  si va bien y, si no, dónde se equivocó. Necesita letra grande y mensajes sin tecnicismos.

### Principios de diseño

1. **Honestidad de lectura.** La app nunca muestra una solución que no pueda respaldar. Si
   lo que leyó no deja el tablero con solución única, dice qué no pudo leer y dónde, en vez
   de adivinar. Hoy el sistema ya cumple esto: de 16 tableros reales, 8 se resuelven bien y
   ninguno de los otros 8 devuelve una solución errónea (`scripts/medir_solver.py`).
2. **Cero fricción.** La cámara aparece al abrir. La cuenta es solo tu nombre. Nada de
   formularios, contraseñas ni tutoriales obligatorios.
3. **Cada fallo dice qué hacer.** En lenguaje llano ("hay poca luz, acércate a la
   ventana"), nunca "error" ni códigos.
4. **Tú decides cuánto quieres saber.** La ayuda va de menos a más y nunca revela más de
   lo que se pidió. Marta no quiere spoilers.
5. **Legible para todos.** Texto grande, alto contraste, todo al alcance del pulgar y
   usable con una mano.

### Cómo lo validamos

Una persona sintética sirve para diseñar, pero no para medir: es la misma lección que dejó
el conjunto sintético de la Fase 1. Antes de dar la app por buena se prueba con
**5 personas reales** (compañeros, familia; idealmente alguien del perfil de Marta).

- **Tareas:** "resuelve este KenKen con la app" y "averigua si este tablero a medio
  llenar está bien".
- **Método:** piensan en voz alta mientras lo hacen, sin ayuda del equipo.
- **Qué se anota:** si completan la tarea, cuánto tardan, dónde dudan y qué mensajes no
  entienden.
- Las dudas de diseño que no sabemos resolver de antemano, como la forma de mostrar la
  solución, se deciden ahí y no en una discusión.

## v1 — Core loop: foto → solución

1. **La primera vez**, una sola pregunta: "¿Cómo te llamas?". Si el nombre ya existe,
   "¡Hola de nuevo, Marta!"; si no, se crea la cuenta. Las veces siguientes la app ya lo
   recuerda.
2. Aparece la cámara.
3. El usuario toma la foto.
4. La app lee el tablero y lo resuelve. **Objetivo: menos de 3 s** de foto a solución. El
   solver tarda menos de 50 ms; el tiempo se va en la red y en la Fase 1.
5. **Muestra la solución.** Hay dos maneras, y se decide en la prueba con usuarios:
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
 teléfono Android (APK)                 nodo de cómputo (PC con GPU de un integrante)
 ┌───────────────────────┐   Wi-Fi     ┌──────────────────────────────────────────┐
 │ HTML/CSS/JS en        │   local     │ API en Python                             │
 │ Capacitor             │ ──────────► │  kenken_cv (Fase 1) → kenken_cp (CP-SAT)  │
 │ cámara nativa         │ ◄────────── │ SQLite: cuentas e historial               │
 └───────────────────────┘             └──────────────────────────────────────────┘
```

- **APK para Android.** Se escribe como la app de `concurrente` (HTML, CSS y JS sin
  framework) y se empaqueta como APK con Capacitor. Usa el plugin nativo de cámara, se
  instala directamente sin pasar por Play Store y deja abierta la puerta a un visor en vivo
  que guíe la foto en tiempo real.
- **El servidor es la PC de uno de los integrantes**, usada como nodo de cómputo. El
  pipeline es Python (OpenCV y OR-Tools), y meterlo dentro de una APK supondría reescribirlo;
  en el nodo se reutiliza tal cual. La v1 corre bien en CPU; la GPU entra con la v2 (dígitos
  a mano) y con el jurado de motores OCR.
- **Conexión: la misma Wi-Fi.**
  - Para no tener que escribir direcciones IP, el nodo muestra un **código QR** con su
    dirección y la app lo escanea una vez (principio 2).
  - Riesgo: las redes Wi-Fi de campus suelen aislar a los dispositivos entre sí. Plan B: el
    nodo se conecta al punto de acceso del teléfono.
  - Android bloquea por defecto el HTTP sin cifrar. La app tiene que permitirlo para la
    red local (configuración de seguridad de red, o hacer las peticiones con el cliente
    HTTP nativo de Capacitor).
- **Privacidad:** las fotos y el historial quedan en la PC del nodo. La app lo dice al crear
  la cuenta y deja borrar cualquier tablero.
- **Sin conexión no funciona** mientras el solver viva en el nodo.

## Cómo se mide

- Porcentaje de fotos reales que terminan en la solución correcta. Hoy, sobre PDF
  rasterizados, es 8/16.
- Porcentaje de fallos que terminan en un aviso específico, no genérico.
- Tiempo de foto a solución en un teléfono real (p50 y p95).
- En la prueba con usuarios: tareas completadas sin ayuda, tiempo, y mensajes que no se
  entendieron.
- Todo sobre fotos reales (cst-zol), no sobre sintéticos.

## Fuera de alcance

Contraseñas o autenticación real, iOS, publicar en Play Store, funcionamiento sin conexión,
generar KenKens nuevos y otros acertijos.

## Decisiones

**Tomadas (2026-10-02):**

- APK para Android, con el servidor en la PC con GPU de un integrante.
- Teléfono y nodo en la misma Wi-Fi.
- Cuenta solo con el nombre e historial en el servidor.
- La corrección rápida queda para después, registrada como fallo conocido.
- Diseño centrado en las personas, validado con usuarios reales.

**Abiertas:**

1. ¿Qué PC hace de nodo, y qué GPU tiene?
2. ¿Capacitor, o Android nativo (Kotlin)? Recomendado: Capacitor, para reutilizar el estilo
   y el código web de `concurrente`.
3. La vista de la solución (sobre la foto o tablero limpio) se decide en la prueba con
   usuarios.
