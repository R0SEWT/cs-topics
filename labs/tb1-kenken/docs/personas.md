# Diseño Centrado en las Personas (HCD): Personas Sintéticas y Flujos de Experiencia

Documento de especificación de UX/UI para la aplicación móvil KenKen (TB1).
Fundamentado en **ISO 9241-210**, Goal-Directed Design (*Cooper, 2014*), directrices de interacción Humano-IA (*Amershi et al., CHI 2019*) y pautas de accesibilidad táctil para adultos mayores (*Petrovčič et al., JMIR 2023*).

---

## 1. Justificación Metodológica: ¿Por qué Personas Sintéticas?

Una persona sintética no es una invención caprichosa ni un promedio demográfico abstracto; es un **arquetipo de comportamiento y objetivos operacionales** diseñado para resolver tensiones de diseño concretas (*Cooper, 2014*).

En esta aplicación conviven dos objetivos polares:
1. **La búsqueda de inmediatez y automatización total** (comprobación rápida de resultados).
2. **La búsqueda de aprendizaje, preservación del desafío cognitivo y acompañamiento sin revelaciones forzadas** (resolución asistida con andamiaje).

Para garantizar que el software responda a las personas y no a la conveniencia del backend, modelamos dos personas arquetípicas: **Diego** y **Marta**. La validación empírica posterior con 5 usuarios reales (*cst-byw.7*, siguiendo a *Faulkner, 2003*) evaluará qué tan bien la interfaz satisface estas metas en la práctica.

---

## 2. Ficha de Persona 1: Diego — "El comprobador exprés en movimiento"

```
 ┌────────────────────────────────────────────────────────────────────────┐
 │ DIEGO, 22 AÑOS                                                         │
 │ Estudiante universitario · Nivel tecnológico: Alto                     │
 │ "Quiero saber en 2 segundos si lo que hice está bien antes de bajarme."│
 └────────────────────────────────────────────────────────────────────────┘
```

### Contexto de Uso y Entorno Físico (ISO 9241-210)
- **Escenario:** Viajando en transporte público (bus, metro) o caminando por los pasillos de la universidad con un cuadernillo de pasatiempos.
- **Entorno:** Iluminación inestable (sombras cambiantes de árboles o ventanas en movimiento), vibración constante por el transporte.
- **Interacción física:** **Operación estricta con una sola mano (One-handed thumb interaction)**. Una mano sostiene la mochila o el pasamanos del bus; el pulgar de la otra mano controla todo el teléfono.

### Objetivos
- **Objetivo de experiencia:** Cero fricción mental, fluidez absoluta, no tener que detenerse a configurar ni leer tutoriales.
- **Objetivo final:** Comparar su tablero físico con la solución exacta calculada por el nodo para detectar inmediatamente la casilla en discordia.

### Frustraciones y Puntos de Dolor (Pain Points)
- Pantallas de bienvenida, logins, pedidos de contraseña o menús complejos que se interponen entre abrir la app y ver la cámara.
- Tiempos de espera mayores a 3 segundos (abandona o se impacienta).
- Botones en la parte superior de la pantalla fuera del radio de alcance de su pulgar (*Thumb Zone*).
- Soluciones en pantallas abstractas que obligan a saltar la vista repetidamente entre el papel y el móvil para encontrar correspondencias.

### Requisitos de Diseño Derivados (Grounded in HCI)
1. **Cámara al abrir (*Zero-friction start*):** No hay onboarding forzado ni menús iniciales. La app abre directamente en el visor de captura.
2. **Obturador en la zona natural del pulgar:** Botón flotante centrado en el tercio inferior, con diámetro $\ge 64$ dp.
3. **Solución proyectada sobre la propia foto:** Gracias a la matriz de homografía de la rejilla, la app superpone los números resueltos sobre la imagen de su papel original. Diego no necesita reinterpretar coordenadas: cada número aparece exactamente sobre su casilla física.
4. **Respuesta en < 3 s con indicador de progreso no invasivo:** Animación de barrido translúcida con etiqueta de tiempo en milisegundos para dar visibilidad del estado (*Nielsen Heuristic #1*).

---

## 3. Ficha de Persona 2: Marta — "La jugadora perseverante que odia los spoilers"

```
 ┌────────────────────────────────────────────────────────────────────────┐
 │ MARTA, 61 AÑOS                                                         │
 │ Docente jubilada · Nivel tecnológico: Medio-Bajo                        │
 │ "Juego para mantener activa mi mente; si me das la respuesta,          │
 │  me arruinaste el pasatiempo de la mañana."                            │
 └────────────────────────────────────────────────────────────────────────┘
```

### Contexto de Uso y Entorno Físico (ISO 9241-210)
- **Escenario:** En la mesa del comedor o la cocina, desayunando con el periódico abierto, resolviendo un KenKen de 6×6 o 9×9 a lápiz.
- **Entorno:** Iluminación fija pero a menudo con sombras proyectadas por su propio cuerpo o la lámpara de techo. Papel periódico de bajo contraste con borrones de goma o tachaduras.
- **Interacción física:** Teléfono sostenido con ambas manos o apoyado en la mesa. Disminución fisiológica natural de la agudeza visual cercana (presbicia) y motricidad fina reducida (toques más lentos y mayor propensión a deslices involuntarios).

### Objetivos
- **Objetivo de experiencia:** Sentir el orgullo y la satisfacción de haber resuelto el reto por sí misma; sentirse respaldada por una herramienta amable y paciente.
- **Objetivo final:** Confirmar si los números que ya colocó a lápiz son correctos hasta el momento y, si cometió un error, recibir una pequeña pista lógica que le permita razonar la corrección sin revelarle la respuesta.

### Frustraciones y Puntos de Dolor (Pain Points)
- **El spoiler total:** Que la app le pinte de golpe el tablero lleno, destruyendo el misterio del juego.
- Tipografías pequeñas (< 16 pt), etiquetas con poco contraste o iconos ambiguos sin texto aclaratorio.
- Mensajes de error crípticos o que suenan a culpa del usuario ("Error 422: Instancia infactible", "Rejilla mal formada").
- Gestos complejos como pellizcar para hacer zoom (*pinch-to-zoom*) o pulsar prolongado (*long-press*).

### Requisitos de Diseño Derivados (Grounded in Petrovčič 2023 & Wood et al. 1976)
1. **Andamiaje cognitivo progresivo (*Progressive Scaffolding*):**
   - **Nivel 1 (Validación binaria):** "¿Voy bien?" $\rightarrow$ *"¡Todo va bien hasta aquí!"* o *"Hay un conflicto en tus números"*. Cero números revelados.
   - **Nivel 2 (Localización espacial):** "¿Dónde está el problema?" $\rightarrow$ Colorea en amarillo suave la jaula o fila en conflicto, sin alterar los números.
   - **Nivel 3 (Explicación de la restricción):** "¿Por qué falla?" $\rightarrow$ Mensaje en lenguaje natural: *"Esta jaula suma 7 con dos casillas, pero tus números actuales (3 y 5) suman 8"*.
   - **Nivel 4 (Revelación controlada):** Botón secundario *"Ver la solución de esta jaula"*, requiriendo un toque de confirmación para evitar revelaciones accidentales.
2. **Accesibilidad táctil reforzada:** Botones con altura y anchura mínimas de $48 \times 48$ dp y espaciado de $12$ dp para evitar pulsaciones erróneas.
3. **Alto contraste y tipografía grande:** Textos de $18$ pt en cuerpo, números en negrita legible (sans-serif de trazo uniforme) y ratio de contraste superior a 7:1 (cumpliendo WCAG AAA).
4. **Opción de tablero limpio de alto contraste:** Un conmutador de fácil acceso para ver el tablero redibujado digitalmente en vectores nítidos si el papel periódico está manchado o roto.

---

## 4. Matriz de Coexistencia: ¿Cómo conviven Diego y Marta en una sola App?

| Componente | Modo Diego (Solución Rápida) | Modo Marta (Verificación y Pistas) |
|---|---|---|
| **Pantalla de inicio** | Visor de cámara con marco de asistencia activo. | Visor de cámara con marco de asistencia activo. |
| **Acción tras la foto** | Botón prominente: **"Resolver tablero"**. | Botón prominente: **"¿Voy bien?"** (Modo verificación). |
| **Presentación por defecto** | Proyección sobre la foto original. | Tablero con sus números y avisos de andamiaje. |
| **Entrega de información** | Respuesta instantánea y completa. | Respuesta graduada de 4 niveles (a demanda). |
| **Alternancia de vista** | Conmutador a "Tablero limpio". | Conmutador a "Tablero limpio" / "Ver solución". |

---

## 5. Especificación de Pantallas y Estados de la UI

### Estado 1: Visor de Cámara con Asistencia Activa (Active Viewfinder)
- **Heurística:** Prevención de errores (*Nielsen #5*) y guía en tiempo real (*Harrison et al., PACMAD*).
- **Elementos en pantalla:**
  1. *Header:* Indicador de estado de conexión con el nodo (`● Nodo Wi-Fi conectado: 192.168.1.45`) e icono de ayuda accesible.
  2. *Área central:* Recuadro de encuadre translúcido con esquinas resaltadas:
     - **Borde Verde:** Tablero detectado, ángulo $< 15^\circ$, iluminación adecuada $\rightarrow$ Listo para capturar.
     - **Borde Amarillo:** *"Mucha inclinación, ponte más de frente"* o *"Poca luz, acércate a una lámpara"*.
     - **Borde Rojo:** *"Falta un borde del tablero, aléjate un poco"*.
  3. *Footer:* Botón obturador circular grande (72 dp) accesible con el pulgar.

### Estado 2: Pantalla de Diego (Solución Inmediata)
- **Header:** Botón retroceder (`<`) y conmutador `[Sobre la foto | Tablero limpio]`.
- **Área central:** Imagen original con los números de la solución proyectados geométricamente sobre cada celda en tipografía azul de alto contraste.
- **Badge inferior:** `✓ Resuelto en 280 ms · Tablero 6×6`.
- **Botón de acción rápida:** `[ Capturar otro KenKen ]` (ancho completo, zona inferior).

### Estado 3: Pantalla de Marta (Verificación y Andamiaje Graduado)
- **Header:** Nombre de la persona (`Marta`) y selector de vista.
- **Área central:** Tablero fotográfico o vectorial limpio mostrando sus números manuscritos.
- **Tarjeta de diagnóstico (Nivel 1):**
  - Banner en amarillo suave (no punitivo): *"Encontramos 1 conflicto en tu avance"*.
- **Controles de asistencia (Niveles 2 y 3):**
  - Botón: `[ 🔍 Ver qué jaula tiene el conflicto ]` (resalta la jaula en pantalla).
  - Botón: `[ 💡 Explicar la regla que no se cumple ]` (despliega texto explicativo).
- **Control de último recurso (Nivel 4):**
  - Botón secundario discreto: `[ Ver solución completa ]` (muestra diálogo de confirmación: *"¿Estás segura? Te mostraremos todos los números"*).

### Estado 4: Manejo de Errores Accionables (Actionable Error Recovery)
- **Principio:** Cada fallo dice qué pasó y qué hacer en lenguaje llano (*Nielsen Heuristic #9, Amershi G11*).
- **Ejemplos en pantalla:**
  - *Tablero cortado:* Icono de encuadre con una esquina truncada + *"No veo las 4 esquinas del tablero. Aléjate unos centímetros y vuelve a probar"*.
  - *Lectura incoherente:* Resalta la jaula con borde punteado + *"No pude leer bien la etiqueta de esta jaula (arriba a la izquierda). ¿Puedes enfocarla con más luz?"*.
  - *Sin solución:* *"Leí algo mal en estas dos celdas: con estos números el tablero no tiene solución posible. Prueba desde otro ángulo"*.
