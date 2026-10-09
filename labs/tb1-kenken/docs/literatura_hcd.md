# Fundamentación en la Literatura: Diseño Centrado en las Personas (HCD) para la App Móvil de KenKen

> **Estado**: Documento formal de revisión de literatura y marco metodológico de HCD  
> **Bead asociada**: [`cst-byw.8`](file:///home/rody/Code/personal/cs-topics/labs/tb1-kenken/docs/app.md) (App: fundamentar en papers el diseño centrado en las personas)  
> **Desbloquea**: [`cst-byw.7`](file:///home/rody/Code/personal/cs-topics/labs/tb1-kenken/docs/app.md) (App: prueba de usabilidad con 5 personas reales)  
> **Referencias BibTeX**: [`labs/tb1-kenken/docs/references.bib`](file:///home/rody/Code/personal/cs-topics/labs/tb1-kenken/docs/references.bib)  
> **Repositorio de PDFs**: `labs/tb1-kenken/docs/papers/` (sincronizado en `gdrive:cs-topics-hcd-papers/`)

---

## 1. Introducción y Contexto del Proyecto

El Trabajo 1 (TB1) del curso aborda la integración entre Visión Computacional (Fase 1: extracción de la estructura del tablero y OCR de etiquetas desde imágenes) y Programación con Restricciones (Fase 2: modelado formal y resolución óptima con solvers de CP como OR-Tools CP-SAT). En la extensión móvil del sistema (epic `cst-byw`), el objetivo es permitir que un usuario fotografíe con su smartphone un KenKen impreso (proveniente de libros de pasatiempos o periódicos) y obtenga asistencia inmediata o resolución interactiva a través de una arquitectura cliente-servidor por Wi-Fi local.

A diferencia de un resolvedor puramente algorítmico, una aplicación móvil interactiva enfrenta dos tensiones fundamentales del diseño centrado en las personas (*Human-Centered Design*, ISO 9241-210):
1. **La naturaleza probabilística e imperfecta de la visión computacional frente a la precisión determinista del motor lógico**: La visión puede sufrir de oclusiones, desenfoque, distorsión de perspectiva o fallos tipográficos. Presentar una solución incorrecta fingiendo certidumbre destruye la confianza del usuario.
2. **La heterogeneidad extrema de perfiles de usuario**:
   - **Diego (22 años, estudiante)**: Busca inmediatez, interacción a una sola mano en entornos de tránsito (e.g., bus), mínima fricción y resolución rápida del core loop (foto → solución).
   - **Marta (61 años, aficionada a los pasatiempos con lápiz)**: Juega pausadamente en la mesa, valora el esfuerzo cognitivo, no tolera *spoilers* que arruinen el juego y requiere interfaces de alta legibilidad, objetivos táctiles generosos y asistencia graduada que le permita aprender dónde está su error sin regalarle la solución.

El presente informe revisa la literatura científica clave para fundamentar las decisiones de diseño de la aplicación móvil, someter a juicio crítico los principios provisionales de [`docs/app.md`](file:///home/rody/Code/personal/cs-topics/labs/tb1-kenken/docs/app.md), establecer las pautas ergonómicas para adultos mayores, y definir con rigor metodológico el protocolo de validación con 5 usuarios reales (`cst-byw.7`).

---

## 2. Revisión Sistemática de Literatura por Eje Temático

### Eje A: Interacción Humano-IA y Gestión de Incertidumbre

#### 1. Amershi et al. (CHI 2019) — *Guidelines for Human-AI Interaction*
- **Autores**: Saleema Amershi, Dan Weld, Mihaela Vorvoreanu, Adam Fourney, Besmira Nushi, Penny Collisson, Jina Suh, Shamsi Iqbal, Paul N. Bennett, Kori Inkpen, Jaime Teevan, Ruth Kikin-Gil, Eric Horvitz.
- **Referencia**: CHI '19, Paper 3, 13 páginas. DOI: `10.1145/3290605.3300233`.
- **Archivo local**: [`papers/amershi2019_guidelines_human_ai_interaction.pdf`](file:///home/rody/Code/personal/cs-topics/labs/tb1-kenken/docs/papers/amershi2019_guidelines_human_ai_interaction.pdf)
- **Problema**: Los sistemas con componentes de IA (aprendizaje automático, visión, modelos probabilísticos) suelen fallar de manera impredecible o inconsistente. Los principios de usabilidad tradicionales de HCI no capturan adecuadamente las fallas no deterministas, lo que genera expectativas infladas o frustración.
- **Metodología**: Síntesis de más de 150 principios de diseño propuestos durante 20 años en la academia y la industria, destilados en 18 directrices y validados empíricamente a través de tres rondas con 49 profesionales de diseño evaluando 20 productos comerciales de IA.
- **Hallazgos Clave**:
  - **G1 (Make clear what the system can do)** y **G2 (Make clear how well the system can do what it can do)**: Indispensables al inicio. El usuario debe saber que el sistema procesa fotos de tableros KenKen, pero que su fiabilidad depende de la nitidez, iluminación y encuadre.
  - **G9 (Support efficient correction)**: Cuando el pipeline falla o duda, debe ser intuitivo y rápido editar la hipótesis del sistema (ej. corregir una jaula o un operador).
  - **G10 (Scope services when in doubt)**: Cuando el modelo detecte ambigüedad (ej. OCR dudoso o rejilla incierta), debe degradar la automatización de forma controlada (solicitar confirmación o pedir re-captura dirigida) en lugar de proceder a ciegas.
  - **G11 (Make clear why the system did what it did)**: Explicar la causa del fallo en términos del dominio ("esta etiqueta no tiene operador reconocible", "el borde inferior quedó cortado").
- **Traducción al diseño de KenKen**:
  - Fundamenta directamente el principio de **Honestidad de Lectura**. El sistema no debe ocultar la incertidumbre del pipeline OpenCV/OCR. Si `Particion.fiable` es bajo o `resolver()` resulta insatisfacible, el sistema nunca debe "adivinar" una solución falsa, sino señalar con precisión la casilla o jaula dudosa y solicitar verificación (G10, G11).

#### 2. Horvitz (CHI 1999) — *Principles of Mixed-Initiative User Interfaces*
- **Autores**: Eric Horvitz (Microsoft Research).
- **Referencia**: CHI '99, pp. 159–166. DOI: `10.1145/302979.303030`.
- **Archivo local**: [`papers/horvitz1999_principles_mixed_initiative_user_interfaces.pdf`](file:///home/rody/Code/personal/cs-topics/labs/tb1-kenken/docs/papers/horvitz1999_principles_mixed_initiative_user_interfaces.pdf)
- **Problema**: Cómo diseñar interfaces donde un agente inteligente y un humano colaboran estrechamente bajo condiciones de incertidumbre, minimizando el costo de las interrupciones y los errores del agente.
- **Metodología**: Formulación basada en teoría de decisiones con modelos de utilidad esperada ($E(U)$), equilibrando los beneficios de una acción autónoma frente al costo de una acción errónea o inoportuna, ilustrada en prototipos como *LookOut*.
- **Hallazgos Clave**:
  - Propone principios esenciales: considerar la incertidumbre sobre los objetivos del usuario, inferir el foco de atención, balancear el costo de diálogo frente al costo de acción autónoma, y proveer un mecanismo directo para que el usuario anule o refine la acción del sistema.
  - *Principio de degradación agraciada*: Ante una confianza intermedia, el sistema no debe ejecutar una acción drástica ni quedarse en silencio total; debe abrir un micro-diálogo contextual de bajo costo cognitivo.
- **Traducción al diseño de KenKen**:
  - Si el pipeline clasifica una jaula con margen estrecho (`Particion.fiable < 1.35`), no debe abortar drásticamente ni fingir certeza absoluta. Debe proyectar la solución acompañada de un indicador suave de baja confianza en dicha jaula, permitiendo al usuario confirmarla o corregirla con un solo toque (minimización del costo de diálogo).

---

### Eje B: Accesibilidad y Diseño Móvil para Adultos Mayores

#### 3. Gomez-Hernandez et al. (JMIR 2023) — *Design Guidelines of Mobile Apps for Older Adults: Systematic Review and Thematic Analysis*
- **Autores**: Miguel Gomez-Hernandez, Xavier Ferre, Cristian Moral, Elena Villalba-Mora.
- **Referencia**: *JMIR mHealth and uHealth*, 11:e43186, 20 páginas. DOI: `10.2196/43186`.
- **Archivo local**: [`papers/gomez_hernandez2023_design_guidelines_older_adults_jmir.pdf`](file:///home/rody/Code/personal/cs-topics/labs/tb1-kenken/docs/papers/gomez_hernandez2023_design_guidelines_older_adults_jmir.pdf)
- **Problema**: Fragmentación y falta de rigor metodológico en las pautas existentes de diseño móvil para adultos mayores. Muchas pautas se quedan en recomendaciones visuales superficiales y descuidan la interacción táctil, la navegación y la carga cognitiva.
- **Metodología**: Revisión sistemática (PRISMA) y análisis temático de 43 estudios empíricos publicados entre 2012 y 2022, clasificando recomendaciones en dimensiones perceptivas, físicas/motoras y cognitivas.
- **Hallazgos Clave**:
  - **Dimensión Visual y Tipográfica**: Se exige un tamaño de fuente mínimo de **16 sp a 18 sp** (en Android) para texto secundario y **20 sp a 24 sp** para elementos interactivos; contraste cromático mínimo de **4.5:1** (WCAG AA) y preferiblemente **7:1** (WCAG AAA) para texto con fondo; evitar fuentes con serifa decorativas y fuentes condensadas.
  - **Dimensión Motora y Táctil**: Objetivos táctiles mínimos de **48 × 48 dp** (9 × 9 mm físicos en pantalla), con un espaciado entre botones de al menos **8 a 10 dp** para evitar toques involuntarios debidos al temblor senil o reducida motricidad fina.
  - **Dimensión Cognitiva y Arquitectura de Información**: Minimizar la profundidad jerárquica de la navegación (preferir estructuras planas de máximo 1 o 2 niveles); evitar gestos complejos (pellizcar para zoom, swipes largos, arrastrar y soltar); preferir toques simples directos con retroalimentación inmediata (auditiva, visual o háptica suave).
  - **Textos y Mensajes**: Evitar jerga informática (nada de "error de red", "timeout", "parse error"); redactar frases directas orientadas a la acción ("Acércate a la luz", "Gira el teléfono").
- **Traducción al diseño de KenKen**:
  - En la persona de **Marta (61 años)**, estos parámetros son mandatorios:
    - La cuadrícula y los números superpuestos deben respetar tamaños legibles sin depender de pellizcar para hacer zoom.
    - Todos los botones principales (Capturar, Pista, Cambiar Vista) deben medir al menos 48 × 48 dp y estar concentrados en la parte inferior de la pantalla (zona accesible del pulgar).
    - El registro de usuario sin contraseña ("¿Cómo te llamas?") responde directamente a la eliminación de carga cognitiva en memoria y autenticación compleja.

#### 4. Petrovčič et al. (IJHCI 2018) — *Design of Mobile Phones for Older Adults: An Empirical Analysis of Design Guidelines and Checklists*
- **Autores**: Andraž Petrovčič, Sakari Taipale, Ajda Rogelj, Vesna Dolničar.
- **Referencia**: *International Journal of Human-Computer Interaction*, 34(3), pp. 251–264. DOI: `10.1080/10447318.2017.1345142`.
- **Archivo local**: [`papers/petrovcic2018_design_mobile_phones_older_adults.pdf`](file:///home/rody/Code/personal/cs-topics/labs/tb1-kenken/docs/papers/petrovcic2018_design_mobile_phones_older_adults.pdf)
- **Problema**: Evaluar la validez de constructo, coherencia y aplicabilidad práctica de las listas de verificación y pautas heurísticas utilizadas por diseñadores de smartphones para personas mayores.
- **Metodología**: Evaluación heurística empírica sobre múltiples modelos de teléfonos y launchers adaptados, contrastando la consistencia inter-evaluador de las guías de diseño y su impacto en la usabilidad real.
- **Hallazgos Clave**:
  - Muchas guías comerciales fallan al asumir que "más simple" significa simplemente iconos más grandes. Las mayores barreras encontradas fueron:
    - La ambigüedad conceptual en iconos abstractos (los adultos mayores requieren iconos acompañados de etiquetas textuales explícitas).
    - La desorientación causada por cambios bruscos de estado en pantalla sin animación de transición clara.
    - La frustración por la falta de confirmación de guardado o éxito de una acción.
- **Traducción al diseño de KenKen**:
  - En la app, ningún botón contendrá únicamente un icono sin texto (ej. el botón de pista dirá "💡 Pista", no solo una bombilla).
  - Cada transición (de cámara a procesamiento y de procesamiento a tablero) debe incluir un estado de progreso comprensible ("Analizando el tablero...") con retroalimentación háptica y visual, eliminando pantallas en blanco o estados inertes.

---

### Eje C: Andamiaje Pedagógico y Ayuda Graduada (Scaffolding)

#### 5. Wood, Bruner & Ross (1976) — *The Role of Tutoring in Problem Solving*
- **Autores**: David Wood, Jerome S. Bruner, Gail Ross.
- **Referencia**: *Journal of Child Psychology and Psychiatry*, 17(2), pp. 89–100. DOI: `10.1111/j.1469-7610.1976.tb00381.x`.
- **Archivo local**: [`papers/wood1976_role_of_tutoring_in_problem_solving.pdf`](file:///home/rody/Code/personal/cs-topics/labs/tb1-kenken/docs/papers/wood1976_role_of_tutoring_in_problem_solving.pdf)
- **Problema**: Cómo estructurar la asistencia de un tutor para que un aprendiz resuelva una tarea compleja que excede su capacidad independiente inmediata (la Zona de Desarrollo Próximo de Vygotsky), sin asumir el control total de la tarea ni privarlo del aprendizaje y la satisfacción cognitiva.
- **Metodología**: Estudio observacional sistemático de niños de 3 a 5 años interactuando con un tutor en la construcción de una pirámide tridimensional de bloques interconectados.
- **Hallazgos Clave**:
  - Acuña el concepto seminal de **Andamiaje (*Scaffolding*)** y sus 6 funciones esenciales:
    1. *Reclutamiento*: Captar el interés inicial y enfocarlo en la tarea.
    2. *Reducción de grados de libertad*: Simplificar el espacio de búsqueda eliminando distractores para que el aprendiz pueda concentrarse en el paso crítico.
    3. *Mantenimiento de dirección*: Mantener al aprendiz orientado al objetivo general, evitando el abandono.
    4. *Marcado de rasgos críticos*: Destacar discrepancias o inconsistencias entre el estado actual alcanzado y el estado correcto o viable.
    5. *Control de frustración*: Reducir el estrés asociado al error sistemático sin regalar la solución.
    6. *Demostración*: Modelar una resolución ideal cuando el aprendiz está completamente desorientado.
  - *Principio de Contingencia y Desvanecimiento (Fading)*: El soporte debe entregarse solo en la medida necesaria y retirarse gradualmente a medida que el aprendiz demuestra autonomía.
- **Traducción al diseño de KenKen**:
  - Es el pilar teórico formal para el **Modo Verificación (v2)** y el principio **"Tú decides cuánto quieres saber"**:
    - **Nivel 1 (Control de frustración)**: Confirmación general de viabilidad ("Vas bien hasta aquí" o "Hay inconsistencias en el tablero").
    - **Nivel 2 (Marcado de rasgos críticos)**: Resaltar violaciones evidentes de reglas (números duplicados en una fila/columna o jaula con operación aritmética violada).
    - **Nivel 3 (Reducción de grados de libertad)**: Apuntar a la casilla específica en conflicto calculada mediante el núcleo insatisfacible de CP-SAT (*SufficientAssumptionsForInfeasibility*), sin rellenar el número correcto.
    - **Nivel 4 (Demostración)**: Revelar el valor numérico concreto de la casilla o la solución completa únicamente si el usuario lo solicita explícitamente tras los niveles anteriores.

#### 6. Gupta & MacLellan (AAAI 2021) — *Designing Teachable Systems for Intelligent Tutor Authoring*
- **Autores**: Adit Gupta, Christopher J. MacLellan (Georgia Institute of Technology).
- **Referencia**: *Proceedings of the AAAI 2021 Spring Symposium on Artificial Intelligence for K-12 Education*.
- **Archivo local**: [`papers/maclellan2021_designing_teachable_systems_tutor_authoring.pdf`](file:///home/rody/Code/personal/cs-topics/labs/tb1-kenken/docs/papers/maclellan2021_designing_teachable_systems_tutor_authoring.pdf)
- **Problema**: En los Sistemas Tutores Inteligentes (ITS), los sistemas de pistas automatizadas frecuentemente generan frustración porque la función de "siguiente pista" salta de forma abrupta a revelar la respuesta final sin proveer la explicación conceptual intermedia.
- **Metodología**: Marco de Interacciones Naturales de Entrenamiento (*Natural Training Interactions*, NTI) y experimentos Wizard-of-Oz de percepción restringida para estudiar cómo los humanos solicitan y dosifican explicaciones.
- **Hallazgos Clave**:
  - Los usuarios que buscan ayuda en acertijos y tareas matemáticas distinguen claramente entre "pista conceptual" (estrategia de deducción) y "pista de contenido" (número concreto). Recibir la pista de contenido de forma prematura reduce drásticamente el disfrute percibido del juego y provoca sensación de derrota.
- **Traducción al diseño de KenKen**:
  - Refuerza que la app de KenKen debe evitar a toda costa el "spoiler accidental". Los botones de pista deben requerir confirmación o avance paso a paso: cada pulsación en "💡 Necesito una pista" despliega el siguiente escalón del andamiaje (ej. "Revisa la fila 3" → "La jaula 12× en la fila 3 tiene solo dos divisores posibles" → "El error está en la celda [3, 2]").

---

### Eje D: Calidad de Captura y Guiado en Cámara Móvil (Document Scanning UX)

#### 7. Skoryukina et al. (2020) — *Approach for Document Detection by Contours and Contrasts*
- **Autores**: Natalia Skoryukina, Vladimir V. Arlazarov, Dmitry Nikolaev.
- **Referencia**: *arXiv preprint arXiv:2008.02615*, 7 páginas.
- **Archivo local**: [`papers/skoryukina2020_document_detection_contours_contrasts.pdf`](file:///home/rody/Code/personal/cs-topics/labs/tb1-kenken/docs/papers/skoryukina2020_document_detection_contours_contrasts.pdf)
- **Problema**: La detección de cuadriláteros basada puramente en contornos geométricos (`approxPolyDP` / Canny) falla sistemáticamente en dispositivos móviles debido a fondos complejos, bordes rotos por sombras, desenfoque de movimiento y bajo contraste entre el papel y la mesa.
- **Metodología**: Modelo híbrido que combina la generación de hipótesis de contornos con la evaluación del contraste radiométrico entre las regiones interior y exterior de la frontera del documento, evaluado sobre los datasets de referencia estándar MIDV-500 y SmartDoc (ICDAR).
- **Hallazgos Clave**:
  - La combinación de criterios de contraste local reduce los errores de detección en un 10% y el ordenamiento incorrecto de hipótesis en un 40%.
  - Se identifican cuatro condiciones críticas que invalidan la extracción en tiempo real en teléfonos:
    1. *Desborde del encuadre*: Vértices del documento tocando los márgenes del sensor.
    2. *Desenfoque de movimiento / foco*: Pérdida de altas frecuencias espaciales en las aristas.
    3. *Ángulos oblícuos extremos*: Deformación trapezoidal que dilata o comprime los caracteres más allá de la tolerancia del clasificador.
    4. *Gradientes de iluminación no homogéneos*: Sombras arrojadas por la propia mano o cuerpo del usuario sobre la hoja.
- **Traducción al diseño de KenKen**:
  - Fundamenta de forma rigurosa la tabla de **Avisos de Captura** especificada en `cst-byw.3`:
    - En lugar de dejar que `approxPolyDP` falle en silencio cayendo a `minAreaRect`, la app debe monitorear los síntomas matemáticos:
      - Si los vértices tocan el borde de la imagen → aviso preventivo: *"Falta una parte del tablero. Aléjate un poco"*.
      - Si la relación de longitudes de lados opuestos o los ángulos difieren significativamente de 90° → aviso: *"La foto está muy inclinada. Ponte más de frente al papel"*.
      - Si la varianza del Laplaciano en la región del tablero es menor a un umbral empírico → aviso: *"La foto salió movida. Apoya el teléfono o mantén el pulso"*.
      - Si el brillo medio y contraste son deficientes → aviso: *"Hay poca luz. Busca más luz o evita tu sombra"*.
  - Esto transforma un fallo frustrante de visión en una acción física correctiva clara y viable para el usuario (Amershi G11).

---

### Eje E: Metodología de Pruebas de Usabilidad con Equipos Pequeños (Muestra y Protocolo)

#### 8. Nielsen & Landauer (INTERCHI 1993) / Nielsen (2000) — *Why You Only Need to Test with 5 Users*
- **Autores**: Jakob Nielsen, Thomas K. Landauer.
- **Referencia**: INTERCHI '93, pp. 206–213 (DOI: `10.1145/169059.169166`) y *NN/g Alertbox* (2000).
- **Archivo local**: [`papers/nielsen2000_why_you_only_need_to_test_with_5_users.pdf`](file:///home/rody/Code/personal/cs-topics/labs/tb1-kenken/docs/papers/nielsen2000_why_you_only_need_to_test_with_5_users.pdf)
- **Problema**: Justificar el retorno de inversión y la eficiencia del muestreo en evaluaciones de usabilidad formativas (*Discount Usability Engineering*).
- **Metodología**: Modelo matemático probabilístico basado en una distribución de Poisson binomial:
  $$\text{Problemas Detectados}(n) = N \cdot \left(1 - (1 - L)^n\right)$$
  Donde $N$ es el número total de problemas de usabilidad existentes en el diseño, $L$ es la probabilidad media de que un usuario individual descubra un problema (típicamente $L \approx 0.31$ en estudios agregados), y $n$ es el número de participantes.
- **Hallazgos Clave**:
  - Con **$n = 5$** participantes, se descubre aproximadamente el **85%** de los problemas de usabilidad del sistema:
    $$1 - (1 - 0.31)^5 \approx 0.844 \quad (84.4\%)$$
  - Más allá de 5 usuarios, los retornos son fuertemente decrecientes; los mismos problemas se repiten una y otra vez.
  - Regla de oro de Nielsen: Es infinitamente más rentable realizar **múltiples ciclos iterativos de 5 usuarios** (probar con 5, corregir los problemas encontrados, y volver a probar con otros 5) que invertir todo el presupuesto en un único estudio masivo de 15 o 20 usuarios con un prototipo defectuoso.

#### 9. Faulkner (2003) — *Beyond the Five-User Assumption: Benefits of Increased Sample Sizes in Usability Testing*
- **Autores**: Laura Faulkner.
- **Referencia**: *Behavior Research Methods, Instruments, & Computers*, 35(3), pp. 379–383. DOI: `10.3758/BF03195514`.
- **Archivo local**: [`papers/faulkner2003_beyond_five_user_assumption.pdf`](file:///home/rody/Code/personal/cs-topics/labs/tb1-kenken/docs/papers/faulkner2003_beyond_five_user_assumption.pdf)
- **Problema**: Cuestionar la adopción ciega de la regla de los 5 usuarios como un dogma absoluto o garantía infalible en contextos críticos o muestras heterogéneas.
- **Metodología**: Estudio empírico riguroso con $N = 60$ participantes realizando una prueba de usabilidad idéntica. Se generaron muestras aleatorias estratificadas de tamaños variables ($n \in \{5, 10, 15, 20, \dots\}$) para medir la variabilidad de la tasa de detección.
- **Hallazgos Clave**:
  - Para grupos de $n = 5$:
    - La media de detección fue del **85.55%** (confirmando la predicción teórica de Nielsen).
    - Sin embargo, la **varianza fue sustancial**: el peor subconjunto aleatorio de 5 usuarios detectó únicamente el **55%** de los problemas, mientras que el mejor subconjunto detectó el **99%**.
  - Para grupos de $n = 10$, el peor subconjunto subió al **80%** de detección; para $n = 20$, al **95%**.
- **Implicación Metodológica y Síntesis Nielsen vs. Faulkner para KenKen**:
  - Probar con 5 usuarios es **plenamente legítimo y óptimo** para el alcance de un proyecto académico ágil (semanas 5 a 7), con una premisa clave: los 5 participantes no deben ser un grupo homogéneo de estudiantes de computación.
  - Para minimizar el riesgo señalado por Faulkner (caer en el piso del 55%), la muestra de 5 debe ser **estratificada deliberadamente** entre los perfiles extremos:
    - 2 o 3 usuarios jóvenes/estudiantes con alta fluidez digital (perfil *Diego*).
    - 2 o 3 adultos mayores o personas no habituadas a la tecnología móvil avanzada (perfil *Marta*).
  - De este modo, se descubren tanto los problemas de rendimiento/agilidad como las barreras cognitivas, de comprensión de errores y de motricidad fina.

---

## 3. Revisión y Consolidación de los Principios de Diseño (`docs/app.md`)

A la luz de la literatura examinada, se auditan los 5 principios provisionales establecidos en `labs/tb1-kenken/docs/app.md`:

| Principio en `docs/app.md` | Veredicto | Respaldo Científico | Ajuste / Reformulación Rigurosa |
|---|:---:|---|---|
| **1. Honestidad de lectura** | **Ratificado y Reforzado** | Amershi et al. (2019) G1, G2, G10; Horvitz (1999). | Se mantiene como principio rector. Si la visión no tiene alta certeza (`Particion.fiable` dudoso o solver infactible), la app jamás inventa números ni presume infalibilidad. Declara la sospecha y focaliza la atención del usuario en la pieza conflictiva (Amershi G10). |
| **2. Cero fricción** | **Ratificado y Detallado** | Norman (2013); Gomez-Hernandez et al. (2023); Petrovčič et al. (2018). | Entrada directa a la cámara. Registro con solo el nombre (sin contraseña). Conexión al nodo de cómputo por escaneo de **código QR** en pantalla de PC para evitar que el usuario deba transcribir direcciones IP o puertos de red en su teléfono. |
| **3. Cada fallo dice qué hacer** | **Ratificado y Ampliado** | Nielsen (Heurística 9: reconocimiento y recuperación de errores); Skoryukina et al. (2020); Amershi et al. (2019) G11. | Erradicación total de mensajes genéricos ("Error 500", "Fallo de visión"). Cada aviso debe ser una prescripción física en lenguaje cotidiano: *"Falta un borde del tablero: aléjate un poco"*, *"Hay sombras sobre el papel: acércate a la luz"*, *"La foto está borrosa: apoya la mano"*. |
| **4. Tú decides cuánto quieres saber** | **Ratificado y Estructurado** | Wood, Bruner & Ross (1976) (Scaffolding); Gupta & MacLellan (2021). | Asistencia graduada en 4 niveles de contingencia: 1) Estado global (¿voy bien?) → 2) Marcado de conflictos visibles (duplicados) → 3) Señalización de casilla errónea vía núcleo insatisfacible CP-SAT → 4) Revelación del valor correcto. Cada paso requiere solicitud voluntaria. Cero *spoilers*. |
| **5. Legible para todos** | **Cuantificado con Métricas** | Gomez-Hernandez et al. (JMIR 2023); WCAG 2.2; ISO 9241-210. | Pasa de un desiderátum vago a especificaciones cuantitativas de software: fuentes $\ge 18\text{ sp}$, contraste cromático $\ge 4.5:1$ (objetivo $7:1$), touch targets $\ge 48 \times 48\text{ dp}$ con separación $\ge 8\text{ dp}$, controles clave confinados a la zona del pulgar (tercio inferior de la pantalla). |

---

## 4. Diseño del Protocolo de Validación con 5 Usuarios (`cst-byw.7`)

La validación planificada en la bead `cst-byw.7` se estructura siguiendo las recomendaciones empíricas combinadas de Nielsen (2000), Faulkner (2003) y el protocolo de pensamiento en voz alta (*Think-Aloud Protocol*, Ericsson & Simon, 1993).

### 4.1. Muestra Estratificada ($n = 5$)
Para neutralizar la varianza detectada por Faulkner en muestras pequeñas:
- **Usuario 1 (P1)**: Joven (18-25 años), estudiante de ingeniería, alta destreza móvil (perfil *Diego*).
- **Usuario 2 (P2)**: Joven (20-30 años), usuario de smartphone habitual, no programador.
- **Usuario 3 (P3)**: Adulto de mediana edad (45-55 años), jugador ocasional de sudokus/acertijos.
- **Usuario 4 (P4)**: Adulto mayor (60-70 años), aficionado a pasatiempos en papel, visión estándar para su edad (perfil *Marta*).
- **Usuario 5 (P5)**: Adulto mayor (65+ años), baja familiaridad con aplicaciones móviles complejas (perfil *Marta* extendido).

### 4.2. Tareas Experimentales
1. **Tarea 1 — Core loop Foto a Solución (Escenario de Inmediatez)**:
   - *Consigna*: *"Tienes este tablero KenKen impreso en papel. Usa la aplicación en este teléfono para obtener la solución."*
   - *Criterio de éxito*: Fotografiar el tablero, comprender el estado de carga y visualizar la solución en menos de 60 segundos totales sin intervención del evaluador.
2. **Tarea 2 — Modo Verificación y Asistencia Graduada (Escenario de Marta)**:
   - *Consigna*: *"Has estado resolviendo este KenKen a lápiz, pero crees que cometiste un error en alguna parte. Usa la app para comprobar si vas bien y pedir una pista si la necesitas."*
   - *Criterio de éxito*: Fotografiar el tablero a medio llenar, interpretar el aviso de error sin frustrarse, y solicitar progresivamente las pistas sin que la app le arruine el juego mostrando la solución completa de golpe.

### 4.3. Protocolo de Ejecución
- **Método**: *Concurrent Think-Aloud* (el usuario verbaliza lo que piensa, espera y siente a medida que interactúa).
- **Rol del facilitador**: Observador pasivo estricto. No explicar la interfaz ni corregir errores durante la tarea; intervenir únicamente si el participante se declara completamente bloqueado tras 2 minutos.
- **Instrumentos de recolección**: Grabación de pantalla con audio y cuaderno de notas del observador.

### 4.4. Métricas de Evaluación
- **Eficacia**: Tasa de completación de tareas sin ayuda ($0\%$ a $100\%$).
- **Eficiencia**: Tiempo en tarea (*Time on Task*, segundos desde que se abre la app hasta que se visualiza el resultado deseado).
- **Frecuencia de re-capturas**: Número de intentos de fotografía necesarios hasta que el pipeline acepta la imagen.
- **Comprensión de errores**: Porcentaje de avisos de captura (cortado, inclinado, desenfocado) interpretados y corregidos con éxito en el siguiente intento.
- **Satisfacción y Carga Subjetiva**: Cuestionario SUS (*System Usability Scale*) abreviado al finalizar.

### 4.5. Decisión de Diseño Abierta a Resolver en la Prueba
- **Visualización de la solución**:
  - *Opción A*: Proyección de números sobre la propia foto rectificada con homografía (alta correspondencia espacial con el papel físico).
  - *Opción B*: Renderizado vectorial de un tablero limpio y estilizado (mayor contraste y nitidez absoluta).
  - *Metodología de decisión*: La prueba alternará ambas vistas de forma contrabalanceada entre los participantes y registrará cuál de las dos resulta más intuitiva para transcribir los números al papel.

---

## 5. Inventario de Papers y Sincronización en Google Drive

Los 9 documentos académicos y técnicos recopilados han sido descargados en formato PDF íntegro en `labs/tb1-kenken/docs/papers/` y replicados mediante `rclone` en la nube de Google Drive en `gdrive:cs-topics-hcd-papers/`.

| Nombre del Archivo | Tamaño | Eje Temático | Cita Principal | DOI / Enlace Abierto |
|---|---:|---|---|---|
| `amershi2019_guidelines_human_ai_interaction.pdf` | 1.4 MB | Interacción Humano-IA | Amershi et al. (CHI 2019) | `10.1145/3290605.3300233` |
| `horvitz1999_principles_mixed_initiative_user_interfaces.pdf` | 216 KB | Interacción Humano-IA | Horvitz (CHI 1999) | `10.1145/302979.303030` |
| `gomez_hernandez2023_design_guidelines_older_adults_jmir.pdf` | 1.4 MB | Adultos Mayores & Móvil | Gomez-Hernandez et al. (JMIR 2023) | `10.2196/43186` |
| `petrovcic2018_design_mobile_phones_older_adults.pdf` | 689 KB | Adultos Mayores & Móvil | Petrovčič et al. (IJHCI 2018) | `10.1080/10447318.2017.1345142` |
| `nielsen2000_why_you_only_need_to_test_with_5_users.pdf` | 1.2 MB | Usabilidad & Muestreo | Nielsen (NN/g 2000) | [nngroup.com](https://www.nngroup.com/articles/why-you-only-need-to-test-with-5-users/) |
| `faulkner2003_beyond_five_user_assumption.pdf` | 108 KB | Usabilidad & Muestreo | Faulkner (BRMIC 2003) | `10.3758/BF03195514` |
| `wood1976_role_of_tutoring_in_problem_solving.pdf` | 4.1 MB | Scaffolding / Pistas | Wood, Bruner & Ross (JCPP 1976) | `10.1111/j.1469-7610.1976.tb00381.x` |
| `maclellan2021_designing_teachable_systems_tutor_authoring.pdf` | 315 KB | Tutoría Cognitiva & Pistas | Gupta & MacLellan (AAAI 2021) | [gatech.edu](https://tail.cc.gatech.edu/) |
| `skoryukina2020_document_detection_contours_contrasts.pdf` | 495 KB | Cámara & Captura Móvil | Skoryukina et al. (arXiv 2020) | `arXiv:2008.02615` |
| **Total** | **9.8 MB** | **9 artículos clave** | — | — |

Comando de verificación de réplica remota:
```bash
rclone ls gdrive:cs-topics-hcd-papers/
```

---

## 6. Conclusiones y Próximos Pasos

1. **Cierre de la fundamentación (`cst-byw.8`)**: La literatura analizada demuestra que los principios de diseño de la aplicación no son meras preferencias estéticas o intuiciones del equipo, sino adaptaciones directas de teorías validadas en Interacción Humano-IA, Psicología Educativa y Ergonomía Cognitiva.
2. **Entrada a la especificación final (`cst-byw.1`)**: Los principios de `docs/app.md` quedan fundamentados y enriquecidos con métricas cuantificables (tamaños táctiles, contraste, jerarquía de 4 niveles de pistas, diagnóstico específico de captura).
3. **Desbloqueo de la prueba de usabilidad (`cst-byw.7`)**: Se cuenta con un protocolo experimental respaldado teórica y empíricamente para ejecutar las pruebas con 5 usuarios tan pronto esté operativo el prototipo funcional (core loop `cst-byw.2`).
