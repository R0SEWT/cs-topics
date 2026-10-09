# Especificación de UI (User Interface) — App Móvil KenKen (TB1)

> **Documento de Diseño Visual, Sistema de Tokens y Especificación de Componentes**  
> **Grounded en:** Google Material Design 3, WCAG 2.2 AAA, directrices de pantallas táctiles para adultos mayores (*Petrovčič et al., JMIR 2023*) y *Human-AI Interaction* (*Amershi et al., CHI 2019*).

---

## 1. Sistema de Tokens Visuales (Design Tokens)

### 1.1 Paleta Cromática Semántica y Accesibilidad (WCAG AAA)
Todas las combinaciones de color de texto sobre fondo cumplen un **ratio de contraste mínimo de 7:1** (Nivel AAA para texto normal) y **4.5:1** para componentes gráficos o títulos grandes.

| Token | Valor Hex | Uso / Semántica | Ratio de Contraste |
|---|---|---|---|
| `--md-primary` | `#0B57D0` | Botón principal de acción, enlaces interactivos y estado activo. | `8.2:1` sobre blanco |
| `--md-primary-container` | `#D3E3FD` | Contenedores sutiles de selección y fondos de chips activos. | `11.4:1` con texto oscuro |
| `--md-on-primary` | `#FFFFFF` | Texto o iconos sobre botones primarios. | `8.2:1` sobre azul |
| `--md-surface` | `#FFFFFF` | Superficie base de pantallas diurnas. | — |
| `--md-surface-container` | `#F0F4F9` | Fondos de tarjetas elevadas, tableros y modales. | `1.15:1` sobre surface |
| `--md-text-primary` | `#1F1F1F` | Títulos, etiquetas de jaula y valores principales. | `16.1:1` sobre blanco |
| `--md-text-secondary` | `#444746` | Explicaciones lógicas de pistas y textos secundarios. | `9.4:1` sobre blanco |
| `--md-accent-amber` | `#B06000` | Alertas de conflicto en Modo Asistencia (Nivel 1 y 2). | `7.3:1` sobre blanco |
| `--md-amber-container` | `#FEF7E0` | Fondo pulsante de jaula en conflicto y tarjetas de pista. | `18.5:1` con texto oscuro |
| `--md-accent-green` | `#0F9D58` | Retícula lista para capturar y badge de solución verificada. | `4.6:1` sobre blanco |
| `--md-accent-red` | `#BA1A1A` | Borde fuera de límites y diálogo de desconexión. | `7.8:1` sobre blanco |
| `--pen-blue` | `#1A73E8` | Números de la solución proyectados sobre la foto (Modo Rápido). | `8.0:1` sobre papel claro |
| `--pencil-graphite` | `#3C4043` | Números manuscritos detectados del usuario (Modo Asistencia). | `10.8:1` sobre papel claro |

### 1.2 Escala Tipográfica Accesible
Para asegurar la legibilidad de Marta (61 años con presbicia común) sin degradar la compacidad para Diego, el cuerpo de texto base se escala a **$\ge 18$ sp** con interlineado holgado ($1.4\times$).

```
Display Large:   36 sp / 44 sp line-height · Bold 800 (Números resueltos del tablero)
Headline Medium: 22 sp / 28 sp line-height · Bold 700 (Títulos de pantallas y modales)
Title Medium:    18 sp / 24 sp line-height · SemiBold 600 (Etiquetas de jaula y avisos de pista)
Body Large:      18 sp / 26 sp line-height · Regular 400 (Explicaciones lógicas y ayudas)
Label Large:     16 sp / 20 sp line-height · Bold 600 (Texto dentro de botones de acción)
Label Small:     12 sp / 16 sp line-height · Medium 500 (Badges de latencia y estado de nodo)
```

### 1.3 Grilla de Espaciado y Zonas Táctiles (Touch Ergonomics)
- **Unidad base:** Grilla de **8 dp** (espaciados de 8, 16, 24, 32 dp).
- **Áreas táctiles (Touch Targets):**
  - **Mínimo absoluto:** $48 \times 48\text{ dp}$ (*WCAG 2.2 Success Criterion 2.5.8*).
  - **Botones primarios y obturador:** **$56\text{ dp}$ a $76\text{ dp}$** (*Petrovčič et al., 2023*).
  - **Separación mínima entre botones adyacentes:** **$12\text{ dp}$** para prevenir toques accidentales (*slips* de motricidad fina).

---

## 2. Especificación Detallada de las Vistas

```
 ┌────────────────────────┐      ┌────────────────────────┐      ┌────────────────────────┐
 │ VISTA 1: VISOR ACTIVO  │      │ VISTA 2: ASISTENCIA    │      │ VISTA 3: MODO RÁPIDO   │
 ├────────────────────────┤      ├────────────────────────┤      ├────────────────────────┤
 │ [💡 Asist] [⚡ Rápido] │      │ [< Cámara]   Modo Asist│      │ [< Cámara]  [Foto|Clean│
 │ ● Nodo Wi-Fi: OK       │      │                        │      │                        │
 │                        │      │  ┌──────────────────┐  │      │  ┌──────────────────┐  │
 │     ┌────────────┐     │      │  │ Tablero a lápiz  │  │      │  │ Foto con números │  │
 │     │ ⤹        ⤸ │     │      │  │ [Jaula amarilla] │  │      │  │ proyectados azul │  │
 │     │ Retícula   │     │      │  └──────────────────┘  │      │  └──────────────────┘  │
 │     │ verde      │     │      │                        │      │                        │
 │     │ ⤸        ⤹ │     │      │ ⚠️ 1 número no cuadra  │      │ ✓ Resuelto en 280 ms   │
 │     └────────────┘     │      │ [🔍 Señalar jaula]     │      │                        │
 │                        │      │ [💡 Explicar regla]    │      │ [📸 Capturar otro]     │
 │ 🔍 Verificar (¿Voy b?  │      │                        │      │                        │
 │      [  ⚪  ]          │      │ [Revelar solución...]  │      │                        │
 └────────────────────────┘      └────────────────────────┘      └────────────────────────┘
```

---

### Vista 1: Visor de Cámara con Guía Activa (Active Viewfinder HUD)

#### Anatomía y Componentes
1. **Header de Modos (`ModeHeader`):**
   - Altura: $56\text{ dp}$. Fondo oscuro `#121212` con borde sutil `#2A2A2A`.
   - Contenedor conmutador tipo píldora (`ModeSwitchPill`): dos botones con icono y texto claro:
     - `💡 Asistencia (Por defecto)`: Fondo azul primario `#0B57D0` cuando está activo.
     - `⚡ Modo Rápido`: Fondo translúcido inactivo, se ilumina al tocar.
   - **Persistencia:** Almacena la elección en almacenamiento local para no exigir reelección.
2. **Barra de Telemetría del Sistema (`SystemStatusBar`):**
   - Indicador de conexión circular ($8\text{ dp}$):
     - Verde brillante pulsante: `Nodo Wi-Fi conectado: 192.168.1.45`.
     - Rojo ámbar: `Buscando nodo Wi-Fi... (Desconectado)`.
3. **Retícula Guía Holográfica (`ActiveReticle`):**
   - Tamaño: $310 \times 310\text{ dp}$ centrado en la vista.
   - 4 esquinas curvadas con trazo de $4\text{ dp}$ y radio de $8\text{ dp}$.
   - **Estados dinámicos:**
     - **Verde (`#0F9D58`):** Tablero completo, ángulo $< 15^\circ$, contraste óptimo. Dispara un pulso háptico de $25\text{ ms}$.
     - **Ámbar (`#F4B400`):** Inclinación moderada o poca luz. Texto: *"Ponte más de frente"* o *"Poca luz"*.
     - **Rojo (`#D93025`):** Esquina cortada o fuera de cuadro. Texto: *"Aléjate para ver las 4 esquinas"*.
4. **Capa de Escaneo Láser y Latencia (`ScanningLaserLayer`):**
   - Al presionar el obturador, una línea láser cian (`#00E5FF`) barre verticalmente el fotograma congelado con sombra de resplandor (*glow*).
   - Badge flotante en el centro: `Analizando con OR-Tools CP-SAT... 180 ms`.
5. **Zona de Control Inferior (`ThumbZoneControls`):**
   - Altura mínima: $124\text{ dp}$. Fondo negro puro.
   - **Etiqueta dinámica sobre el obturador:** Píldora translúcida con borde:
     - En Modo Asistencia: `🔍 Verificar mi avance a lápiz (¿Voy bien?)`.
     - En Modo Rápido: `⚡ Resolver todo el tablero (Modo Rápido)`.
   - **Botón Obturador:** Círculo exterior blanco de $76\text{ dp}$, botón interior de $62\text{ dp}$, efecto de compresión al pulsar (`scale(0.85)`).

---

### Vista 2: Modo Asistencia (Marta) — Verificación y Andamiaje Cognitivo

Diseñada bajo los principios de *Scaffolding & Fading* (*Wood et al., 1976*) y las directrices de adultos mayores (*Petrovčič et al., 2023*).

#### Anatomía y Componentes
1. **Header Accesible:**
   - Botón `‹ Cámara` con área táctil de $48 \times 48\text{ dp}$ en tipografía $18\text{ sp}$.
   - Título central: `Modo Asistencia`.
   - Botón secundario: `Tablero limpio` (vectorial de alto contraste).
2. **Tablero de Avance a Lápiz:**
   - Visualización de la imagen capturada con los dígitos manuscritos del usuario renderizados en tipografía grafito `#3C4043`.
   - **Jaula en Conflicto (Nivel 2):** Fondo amarillo suave `#FEF7E0` con animación de pulsación luminosa suave (`1.5s infinite alternate`). Sin números alterados.
3. **Tarjeta de Andamiaje Graduado (`ScaffoldingCard`):**
   - Tarjeta elevada con borde de $2\text{ dp}$ `#DADCE0` y radio de $20\text{ dp}$.
   - **Nivel 1 (Validación no punitiva):**
     - Icono `⚠️` grande ($24\text{ dp}$).
     - Título: *"Hay 1 número que no cuadra"*.
     - Subtítulo: *"El resto de tus casillas va por excelente camino"*.
     - Botón primario ($56\text{ dp}$ de alto, fondo ámbar suave `#FFF3E0` con texto `#B06000` en negrita $16\text{ sp}$): `🔍 Señalar la jaula con el error`.
   - **Nivel 2 (Localización espacial):**
     - Icono `📍`. Título: *"Conflicto en la jaula destacada en amarillo"*.
     - Botón secundario ($56\text{ dp}$, azul `#E8F0FE` con texto `#1A73E8`): `💡 Explicar por qué no cuadra`.
   - **Nivel 3 (Explicación de la regla lógica):**
     - Icono `🧠`. Caja de texto con fondo destacado:
       *"La jaula pide que el producto sea 20. Tus números actuales (3, 1 y 3) multiplican 9 y además repites el 3 en la fila"*.
     - Botón de asistencia focalizada ($56\text{ dp}$, gris `#F1F3F4`): `👁️ Ver la solución de esta jaula sola`.
4. **Footer de Escape Controlado (`AntiSpoilerFooter`):**
   - Enlace discreto subrayado al pie: `Revelar solución completa del tablero...`.
   - Al pulsar, abre el diálogo modal anti-spoilers requiriendo confirmación consciente.

---

### Vista 3: Modo Rápido (Diego) — Solución Inmediata

Diseñada para completarse con una mano en entornos de tránsito rápido.

#### Anatomía y Componentes
1. **Header con Conmutador de Perspectiva:**
   - Botón `‹ Cámara`.
   - Conmutador central segmentado: `[ Sobre tu foto | Tablero limpio ]`.
2. **Lienzo de Proyección de Solución:**
   - **Modo Sobre tu Foto:** Imagen fotográfica original con las cifras de la solución superpuestas matemáticamente en cada casilla mediante la matriz de homografía.
   - **Cifras de Solución:** Tamaño grande ($32\text{ sp}$), negrita $800$, color azul intenso `#0B57D0` con halo blanco fino para garantizar legibilidad incluso sobre fondos oscuros o manchados.
   - **Modo Tablero Limpio:** Rejilla vectorial SVG de trazo perfecto, marco exterior grueso ($3\text{ px}$), divisiones interiores finas ($1\text{ px}$) y números centrados.
3. **Fila de Badges de Rendimiento:**
   - Badge de éxito: `✓ Resuelto en 280 ms` (fondo verde `#E6F4EA`, texto `#137333`).
   - Badge de contexto: `Tablero 4×4 · Confianza 98%`.
4. **Botón Flotante de Acción Rápida:**
   - Botón ancho inferior ($56\text{ dp}$ alto, radio $28\text{ dp}$, azul primario `#0B57D0`): `📸 Capturar otro tablero`.

---

### Vista 4: Sistema de Diálogos Modales de Recuperación Constructiva

Implementa la **Heurística #9 de Nielsen** (*Ayudar a reconocer, diagnosticar y recuperarse de errores*) y la directriz **G11 de Amershi** (*Hacer claro por qué el sistema hizo lo que hizo*).

#### Estructura Estándar de Modal (`ActionableErrorModal`)
- **Fondo desenfocado:** Overlay oscuro semitransparente con `backdrop-filter: blur(4px)`.
- **Tarjeta central:** Radio de $28\text{ dp}$, fondo blanco puro, padding de $24\text{ dp}$.
- **Componentes interiores:**
  1. *Icono semántico:* $38\text{ dp}$ centrado (📐 ángulo, 💡 luz, ✂️ corte, 🧩 jaula dudosa, 📡 red).
  2. *Título llano:* Enfoque en la acción humana, no en el error del software (ej. *"La foto está muy inclinada"*, nunca *"Error 422: HomographyFailed"*).
  3. *Explicación del porqué:* Texto claro de $15\text{ sp}$ explicando qué impidió la lectura.
  4. *Caja de consejo práctico (`TipBox`):* Fondo amarillo cálido `#FEF7E0` con bombilla: *"Consejo: Mantén el teléfono paralelo a la mesa"*.
  5. *Botón de acción única:* Botón azul primario de $48\text{ dp}$: `Entendido, volver a intentar`.

---

## 3. Matriz de Estados e Interacciones

| Componente | Estado Reposo | Estado Activo / Pulsado | Estado Alerta / Advertencia |
|---|---|---|---|
| **Botón Obturador** | Blanco sólido $76\text{ dp}$, sombra suave. | `scale(0.85)` con vibración de $30\text{ ms}$. | Bloqueado si condición es roja, abre modal. |
| **Retícula de Enfoque** | Esquinas verdes `#0F9D58` ($4\text{ px}$). | Pulso verde al detectar encuadre. | Amarillo ámbar o rojo con mensaje correctivo. |
| **Jaula en Conflicto** | Borde fino estándar. | Pulsación luminosa `#FEF7E0` a `#FFF0B3`. | Trazos punteados si es jaula dudosa (`cst-90g`). |
| **Selector de Modo** | Píldora inactiva `#222326`, texto `#9AA0A6`. | Píldora activa `#0B57D0`, texto blanco con sombra. | — |
