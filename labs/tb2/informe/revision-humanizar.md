# Revisión editorial de `informe.qmd` (skill «humanizar»)

Registro de propuestas, generado con un asistente de IA (Claude) el 2026-11-28. No se editó `informe.qmd` ni ningún otro archivo del manuscrito: todo lo que sigue es propuesta y cada cambio lo decide el autor.

**Ayuda permitida y qué queda por decidir.** La consigna (`materials/evaluaciones/tb2/Enunciado.pdf`, 8 páginas, leída completa) no dice nada sobre asistencia, atribución ni declaración de uso de IA: no aparecen los términos «IA», «inteligencia artificial», «generativa», «asistencia», «herramienta», «plagio» ni «originalidad»; la única mención cercana es AutoGen como mecanismo de consenso opcional de la Sesión 5. Lo único que fija sobre el informe es el formato: «Documento académico (máximo 12 páginas) estructurado explícitamente según las 6 sesiones» (§5.1). Como la norma del curso (sílabo, reglamento o indicación del docente) no está confirmada, esta revisión se entrega solo como propuestas. Queda al autor: (1) confirmar con el sílabo o el docente si la asistencia de IA está permitida y cómo debe declararse; (2) decidir si la nota final de «Uso de herramientas de IA generativa» describe bien el grado de ayuda (hoy dice «como apoyo» y no menciona la revisión editorial; ver propuesta 19); (3) confirmar la frase «El equipo revisó y validó el contenido», que solo el equipo puede afirmar; (4) aceptar, modificar o descartar cada propuesta.

Fuentes usadas para comprobar la evidencia: `informe.qmd`, el PDF renderizado (`pdftotext -layout`), `valores.json` y `reports/experimentos.md`. Nada más.

Formato: cada «Original» es una cita exacta de `informe.qmd` (incluidas las interpolaciones `` `#…`{=typst} ``) que aparece una sola vez en el archivo; cada propuesta se aplica sola, reemplazando ese texto por el de «Propuesta». Entre corchetes, tras la línea, el valor con que se renderiza hoy.

---

## A. Afirmaciones y evidencia

### 1. La conclusión sobre latencia omite un turno de 47,3 ms registrado en el torneo

- **Ubicación:** Conclusiones, línea 369.
- **Original:**

~~~text
y la latencia queda bajo el umbral también con 400 unidades (peor turno medido: `#l4.max_bruto`{=typst} ms).
~~~

- **Propuesta:**

~~~text
y en la medición de latencia ningún turno superó el umbral, tampoco con 400 unidades (peor turno de `latencia.py`: `#l4.max_bruto`{=typst} ms).
~~~

- **Pregunta:** `valores.json` trae `t.ms_max_torneo = 47,3` (y `t.ms_max_base = 27,1`), que el informe no usa en ninguna parte. Si es el peor turno del equipo en las 24 partidas del torneo, supera los 40 ms y «peor turno medido: 14,96 ms» no es cierto para el conjunto de lo medido. ¿Se corrió el torneo con partidas en paralelo? (`experimentos.md` advierte de ese problema para su propia tabla de latencia.) Si es así, conviene decirlo en «Perfilado» junto con el dato; si no, la conclusión necesita ese matiz.
- **Razón:** La propuesta acota la afirmación a lo que `latencia.py` midió (0 de 15 y 0 de 9 repeticiones sobre el umbral), que es lo que los datos sostienen; el 47,3 queda para que el autor lo explique o lo reporte.

### 2. La calibración se adoptó con una diferencia que el propio criterio del informe deja dentro del ruido

- **Ubicación:** Sesión 2, «Calibración de pesos», paso *Elección*, línea 156.
- **Original:**

~~~text
primer puesto en `#cal.ens_primeros`{=typst}), y se adoptó en las cuatro políticas (@tbl-pol).
~~~

- **Propuesta:**

~~~text
primer puesto en `#cal.ens_primeros`{=typst}). Esa diferencia queda dentro del ruido (criterio de la metodología); el cambio se adoptó en las cuatro políticas (@tbl-pol).
~~~

- **Razón:** El ensayo (0,0322 → 0,0378; Δ +0,0056; 7 de 10) es la misma diferencia que la Tabla 2 clasifica como «dentro del ruido» para `s2_pesos_iniciales`. Tal como está, el lector rápido entiende que el ensayo justificó la adopción; las Conclusiones ya dicen que la calibración no tuvo efecto medible, y el párrafo debería decir lo mismo.

### 3. «Verificación» parece ser la misma corrida que «Elección»

- **Ubicación:** Sesión 2, «Calibración de pesos», paso *Verificación*, línea 156.
- **Original:**

~~~text
*Verificación.* La @tbl-cal repite el barrido alrededor de los pesos adoptados, con la versión entregada: «Antes de calibrar» reproduce los pesos iniciales y da
~~~

- **Pregunta:** Los valores del ensayo (`cal.ens_antes` 0,0322; `cal.ens_despues` 0,0378; Δ +0,0056; «7 de 10»; «10 de 10») coinciden exactamente con la fila «Antes de calibrar» y la fila «Adoptados» de la Tabla 4 (0,0322; 0,0378; Δ −0,0056; «7 de 10»; «10 de 10»). ¿Son las mismas diez partidas? Si lo son, la «verificación» no confirma nada de forma independiente: es el mismo dato con el signo cambiado.
- **Propuesta (solo si son las mismas partidas):**

~~~text
*Barrido final.* La @tbl-cal repite el barrido alrededor de los pesos adoptados, con la versión entregada: «Antes de calibrar» es la misma comparación del ensayo, vista desde los pesos adoptados, y da
~~~

- **Razón:** «Verificación» promete una comprobación adicional; si el dato es el mismo, el nombre hace que el párrafo diga más de lo que hay.

### 4. «Diez no separan diferencias menores que 0,005» contradice la Tabla 2

- **Ubicación:** Conclusiones, línea 369.
- **Original:**

~~~text
porque diez no separan diferencias menores que 0,005;
~~~

- **Propuesta:**

~~~text
porque con diez no se separaron del ruido diferencias de hasta 0,0056;
~~~

- **Razón:** En la Tabla 2, −0,0056 (`s2_pesos_iniciales`) y −0,0047 (`s4_sin_subastas`) quedan «dentro del ruido»; la menor diferencia que sí se separa es −0,0089. El umbral real está entre 0,0056 y 0,0089, no en 0,005. **Esta propuesta cambia una cifra a propósito** (0,005 → 0,0056); si el 0,005 sale de otro cálculo, conviene citarlo.

### 5. La «extracción por batería invertida» es el mismo cociente que el Ratio, no una segunda evidencia

- **Ubicación:** Sesión 4, «Evidencia», línea 263.
- **Original:**

~~~text
La extracción por batería invertida pasa de `#x.completo.hielo_por_bat100`{=typst} a `#x.s4_sin_subastas.hielo_por_bat100`{=typst} u. por cada 100 puntos, y el Ratio de
~~~

- **Propuesta:**

~~~text
La extracción por batería invertida (hielo medio entre batería media, la misma magnitud que el Ratio) pasa de `#x.completo.hielo_por_bat100`{=typst} a `#x.s4_sin_subastas.hielo_por_bat100`{=typst} u. por cada 100 puntos, y el Ratio de
~~~

- **Razón:** 133/3627 = 3,67 y 171/5897 ≈ 2,9 por cada 100 puntos: es hielo entre batería, es decir, el Ratio calculado sobre las medias. Leído deprisa, «3,67 → 2,89» parece una mejora aparte de la del Ratio, cuya diferencia (−0,0047) el informe declara dentro del ruido. Confirmar que así se calcula `hielo_por_bat100`.

### 6. La comparación de alta tormenta no dice que 4 de cada 10 partidas se cortaron

- **Ubicación:** Sesión 5, «Impacto en el Ratio con alta tormenta», línea 314.
- **Original:**

~~~text
**`#x.veredicto_s5`{=typst}.**
~~~

- **Propuesta:**

~~~text
**`#x.veredicto_s5`{=typst}.** En cada una de las tres variantes, `#x.s5_tormenta_votando.cortadas`{=typst} de las 10 partidas se cortaron a los 3000 ticks; en ellas se compara el Ratio del momento del corte.
~~~

- **Razón:** `valores.json` da `cortadas = 4` en `s5_tormenta_votando`, `s5_tormenta_fija_ahorro` y `s5_tormenta_fija_expansion`: 12 de las 21 partidas cortadas de los experimentos están en esta comparación. La metodología da el total (21 de 160), pero no dónde se concentra, y es justo el experimento que la rúbrica pide para la Sesión 5. La propuesta añade un dato ya generado, sin cambiar el veredicto.

### 7. Se atribuye el menor hielo a dos decisiones que ningún experimento aísla

- **Ubicación:** Sesión 1, «Dos decisiones que se declaran», línea 88.
- **Original:**

~~~text
El costo de estas decisiones es que el equipo recoge menos hielo que los rivales (Resultados).
~~~

- **Propuesta:**

~~~text
El equipo recoge menos hielo que los rivales (Resultados); ningún experimento de este informe aísla cuánto se debe a estas decisiones.
~~~

- **Razón:** El dato observado es 157 frente a 173 u. en el torneo. Ninguna de las 16 variantes apaga los relevos de patrulla ni el descanso de los rovers, así que la causa es una interpretación. Si el autor tiene esa comparación, puede citarla y mantener la frase.

### 8. «El resultado depende de la esquina» no está probado

- **Ubicación:** Resultados del torneo, línea 353.
- **Original:**

~~~text
El resultado depende de la esquina (@tbl-torneo).
~~~

- **Propuesta:**

~~~text
El resultado varía entre esquinas (@tbl-torneo), con `#t.semillas`{=typst} semillas en cada una.
~~~

- **Pregunta:** ¿Se comprobó si la diferencia entre esquinas supera el ruido? En la Tabla 11 el Ratio medio va de 0,0309 (B) a 0,0362 (A), una diferencia de 0,0053 con 6 semillas por esquina y una desviación global de 0,0106.
- **Razón:** «Depende» afirma un efecto de la esquina; la tabla muestra variación con muestras de 6. «Varía» describe lo observado y deja ver el tamaño de muestra.

### 9. La conclusión sobre las subastas omite que sin ellas se deposita más hielo

- **Ubicación:** Conclusiones, línea 369.
- **Original:**

~~~text
las subastas reducen los viajes en vano de `#x.s4_sin_subastas.viajes`{=typst} a `#x.completo.viajes`{=typst} por partida,
~~~

- **Propuesta:**

~~~text
las subastas reducen los viajes en vano de `#x.s4_sin_subastas.viajes`{=typst} a `#x.completo.viajes`{=typst} por partida (con ellas el equipo deposita `#x.completo.hielo`{=typst} u. frente a `#x.s4_sin_subastas.hielo`{=typst} sin ellas),
~~~

- **Pregunta:** El criterio de dos errores estándar se aplicó solo al Ratio. ¿Hay dispersión por semilla de los viajes en vano? La diferencia (51,0 frente a 276,7) es grande, pero está bajo «Con evidencia a favor» sin la prueba que el informe exige al resto.
- **Razón:** La Tabla 7 muestra las dos caras (menos viajes en vano y menos batería en pasos, pero 133 u. frente a 171); la conclusión solo cuenta la favorable.

### 10. Lo que se probó fueron los filtros 1 a 5, no «el control del costo de mensajes»

- **Ubicación:** Conclusiones, línea 369.
- **Original:**

~~~text
el control del costo de mensajes es la pieza que más pesa (sin filtros,
~~~

- **Propuesta:**

~~~text
de las piezas probadas, los filtros de reporte son la que más pesa (sin los filtros 1 a 5,
~~~

- **Razón:** La variante `s3_sin_filtros` «apaga los filtros 1 a 5» (línea 242); el unicast, el silencio como `REFUSE` y el tope por turno (filtros 6 a 8) siguen activos. La conclusión debería nombrar lo que se apagó y acotar «la que más pesa» a las piezas probadas.

### 11. La explicación de por qué `CARRONA` nunca rige no cuadra con los restos que el equipo sí ve

- **Ubicación:** Sesión 5, «Comportamiento observado», línea 310.
- **Original:**

~~~text
así que hay pocos restos propios que voten por `CARRONA`.
~~~

- **Propuesta:**

~~~text
así que casi no deja restos propios que sumen al puntaje de `CARRONA`.
~~~

- **Pregunta:** ¿$n_c$ cuenta también los restos de rivales? El equipo consume 5,4 restos por partida y envía 40,8 mensajes de restos, y los rivales terminan con 29,5 de 50 unidades vivas: restos hay. Si $n_c$ los cuenta, la razón de que `CARRONA` rija en 0 de 24 partidas estaría en la forma del puntaje (por ejemplo, el término $[\beta < \text{0,5}]$), no en la falta de restos propios.
- **Razón:** «Restos que voten» es un referente confuso (votan las unidades). La propuesta solo arregla la frase; la causa queda como pregunta porque los datos no la confirman.

### 12. «Lo que explica la alternancia» es una deducción de las fórmulas, no una medición

- **Ubicación:** Sesión 5, «Comportamiento observado», línea 310.
- **Original:**

~~~text
, lo que explica la alternancia entre ambas.
~~~

- **Propuesta:**

~~~text
, lo que es coherente con la alternancia entre ambas (@fig-pol).
~~~

- **Razón:** No hay un registro de σ frente a la política ganadora; la frase deduce la causa a partir de los coeficientes. «Coherente con» conserva la idea sin presentarla como resultado.

### 13. «Sin duplicar viajes» en las recargas no tiene dato que lo respalde

- **Ubicación:** Sesión 4, «Arquitectura», línea 246.
- **Original:**

~~~text
; así varios pedidos simultáneos se reparten sin duplicar viajes.
~~~

- **Propuesta:**

~~~text
; el propósito es que varios pedidos simultáneos se repartan sin duplicar viajes.
~~~

- **Pregunta:** ¿Hay algún contador de recargadores que acuden al mismo rover? En `valores.json` solo están `requests`, `agree`, `failure` y `recargas`.
- **Razón:** Es una intención de diseño escrita como hecho, en el mismo párrafo que admite que la subasta implícita «no garantiza un ganador único».

### 14. El argumento de la expiración se apoya en una duración mínima que no lo sostiene

- **Ubicación:** Sesión 1, «Actualización y olvido», inciso (d), línea 82.
- **Original:**

~~~text
; como las partidas del torneo que terminan duran desde `#t.ticks_min`{=typst} ticks, en la práctica actúa primero el decaimiento.
~~~

- **Propuesta:**

~~~text
; para entonces el decaimiento ya dejó su confianza por debajo del 10 % ($\gamma = 2^{-900/250}$), así que en la práctica actúa primero.
~~~

- **Razón:** 673 es la partida más corta; según `valores.json` las terminadas llegan a 1813 ticks y las cortadas a 3000, así que una veta sí puede pasar 900 ticks sin verse. Lo que sostiene la conclusión es la propia fórmula ($2^{-3,6} \approx 0{,}08$). **Esta propuesta retira una cifra del texto** (673) y añade una calculada; el autor decide si prefiere conservar el dato de duración con otra redacción.

### 15. «Todos los números provienen de las corridas descritas en la metodología» no es exacto

- **Ubicación:** Introducción, línea 43.
- **Original:**

~~~text
y todos los números provienen de las corridas descritas en la metodología.
~~~

- **Propuesta:**

~~~text
y los resultados provienen de las corridas descritas en la metodología, salvo el barrido inicial de la calibración (Sesión 2) y la primera versión (Limitaciones), medidos con versiones anteriores del código.
~~~

- **Razón:** El propio informe dice que el barrido previo (Ratio de partida 0,0310) y la primera versión (0,0502) son de otras versiones; tampoco está en la metodología la corrida de 60 s con Pygame de la Sesión 6. Un «todos» que el lector puede desmentir tres páginas después resta crédito al resto.

### 16. «Todas las mediciones» con el simulador de 50 unidades, salvo una

- **Ubicación:** Entorno y metodología, línea 61.
- **Original:**

~~~text
todas las mediciones de este informe son con el simulador entregado, sin modificarlo.**
~~~

- **Propuesta:**

~~~text
todas las mediciones de este informe son con el simulador entregado, sin modificarlo; solo la segunda medición de latencia (Sesión 6) usa 100 unidades por equipo, que el arnés crea duplicando la flota.**
~~~

- **Razón:** La frase en negrita sigue a «crea 50» y se lee como «todo se midió con 50»; la Sesión 6 y las Limitaciones ya declaran la excepción. Ponerla aquí evita que parezca una contradicción.

### 17. La metodología describe la medición de latencia como «5 partidas»

- **Ubicación:** Entorno y metodología, línea 63.
- **Original:**

~~~text
(iii) *Latencia* (`latencia.py`): `#l.semillas`{=typst} partidas en un solo proceso.
~~~

- **Propuesta:**

~~~text
(iii) *Latencia* (`latencia.py`): `#l.semillas`{=typst} semillas con 200 unidades y `#l4.semillas`{=typst} con 400, cada una repetida `#l.repeticiones`{=typst} veces, en un solo proceso.
~~~

- **Razón:** La Sesión 6 y `valores.json` dan 5 semillas × 3 repeticiones (15 corridas) con 200 unidades y 3 × 3 (9) con 400. «5 partidas» describe menos de lo que se hizo y no coincide con la Tabla 10.

### 18. «Atrapó 0 errores»: las corridas no ejercitaron la red de seguridad

- **Ubicación:** Sesión 6, «Arquitectura», línea 325.
- **Original:**

~~~text
En las `#x.partidas`{=typst} partidas de los experimentos esa red atrapó `#x.errores`{=typst} errores, y en las `#t.partidas`{=typst} del torneo, `#t.errores`{=typst}.
~~~

- **Propuesta:**

~~~text
En las `#x.partidas`{=typst} partidas de los experimentos y las `#t.partidas`{=typst} del torneo no hubo excepciones que atrapar (`#x.errores`{=typst} y `#t.errores`{=typst}): las corridas muestran estabilidad, pero no ejercitan la red.
~~~

- **Razón:** Separa el resultado (cero excepciones) de la garantía de diseño de la frase anterior («un error nunca llega al simulador»), que estos datos no ponen a prueba.

### 19. La nota de uso de IA no menciona la revisión editorial

- **Ubicación:** Nota final «Uso de herramientas de IA generativa», línea 375.
- **Original:**

~~~text
y en la redacción de este informe.
~~~

- **Propuesta:**

~~~text
y en la redacción y la revisión editorial de este informe.
~~~

- **Pregunta:** La nota cubre implementación, ejecución y análisis de experimentos y redacción; falta esta revisión. Además, ¿«como apoyo» describe bien el grado de ayuda en la implementación y la redacción? Y la frase «El equipo revisó y validó el contenido» solo es fiel si esa revisión se hizo (incluidas las preguntas abiertas de este registro). Ambas cosas las decide el equipo; la consigna no fija ningún formato.
- **Razón:** Ajuste mínimo para que la declaración coincida con la ayuda efectivamente prestada.

---

## B. Claridad

### 20. «La transferencia reactiva» se lee como adjetivo

- **Ubicación:** Sesión 2, «Carroña», línea 174.
- **Original:**

~~~text
mientras que la transferencia reactiva al aliado detenido sin esperar a un dron.
~~~

- **Propuesta:**

~~~text
mientras que transferirlo vuelve a poner en marcha al aliado detenido sin esperar a un dron.
~~~

- **Pregunta:** El umbral para transferir es «al menos 70 %», pero la razón que se da es que «a un rover con más de 80 % le sobraría parte de los 20 u.». ¿Por qué 70 y no 80? Entre 70 y 80 % no sobra nada.
- **Razón:** «Reactiva» es aquí verbo («reactivar») y el lector tropieza porque espera «transferencia reactiva» como sintagma.

### 21. El mismo contador recibe dos nombres

- **Ubicación:** Sesión 1, «Actualización y olvido», línea 82.
- **Original:**

~~~text
los viajes a vetas ya agotadas pasan de
~~~

- **Propuesta:**

~~~text
los viajes en vano (definidos en la Sesión 4) pasan de
~~~

- **Razón:** Las cifras (51,0 → 145,0) son las de la columna «V. vano» de la Tabla 2, que la Sesión 4 define como «viaje en vano». Con dos nombres el lector no sabe que es la misma medida.

### 22. Final de frase telegráfico en el resultado del gajo único

- **Ubicación:** Sesión 1, «Exploración y cobertura», línea 86.
- **Original:**

~~~text
, con desviación `#x.s1_un_solo_gajo.sd`{=typst} frente a `#x.completo.sd`{=typst} y partidas cortadas: `#x.s1_un_solo_gajo.cortadas`{=typst} frente a `#x.completo.cortadas`{=typst}.
~~~

- **Propuesta:**

~~~text
; su desviación entre semillas es `#x.s1_un_solo_gajo.sd`{=typst} frente a `#x.completo.sd`{=typst}, y se cortó `#x.s1_un_solo_gajo.cortadas`{=typst} partida frente a `#x.completo.cortadas`{=typst}.
~~~

- **Razón:** «Con desviación… y partidas cortadas: 1 frente a 0» obliga a releer para saber qué se compara con qué. [Hoy: 0,0094 frente a 0,0075; 1 frente a 0.]

### 23. Un paréntesis explicativo parte la enumeración de las 3481 elecciones

- **Ubicación:** Sesión 5, «Una elección real», línea 292.
- **Original:**

~~~text
en `#vs.inercia`{=typst} la regla de inercia anuló a la ganadora y mantuvo la política vigente (la regla existe para que el equipo no cambie de postura cada `#c.PERIODO_VOTACION`{=typst} ticks por uno o dos votos); `#vs.borda`{=typst} el desempate de Borda y `#vs.orden_fijo`{=typst} el orden fijo.
~~~

- **Propuesta:**

~~~text
`#vs.borda`{=typst}, el desempate de Borda; `#vs.orden_fijo`{=typst}, el orden fijo; y en `#vs.inercia`{=typst} la regla de inercia anuló a la ganadora y mantuvo la política vigente. La regla existe para que el equipo no cambie de postura cada `#c.PERIODO_VOTACION`{=typst} ticks por uno o dos votos.
~~~

- **Razón:** La lista «3267…; en 161… (paréntesis largo); 53… y 0…» pierde el hilo a mitad. Con el mismo contenido, los cuatro conteos quedan seguidos y la justificación de la regla va después. [3267 + 53 + 0 + 161 = 3481, comprobado.]

### 24. «Cada dron empieza en un gajo distinto» con 15 exploradores y 5 gajos

- **Ubicación:** Sesión 1, «Exploración y cobertura», línea 86.
- **Original:**

~~~text
Cada dron empieza en un gajo distinto según su índice, lo que reparte las franjas al inicio;
~~~

- **Pregunta:** Hay 15 exploradores y 5 gajos, y el gajo es $(j + s) \bmod 5$: los 15 no pueden empezar cada uno en un gajo distinto. ¿Se refiere a los que están de turno a la vez (de 1 a 3 según la política)?
- **Propuesta (solo si es eso):**

~~~text
Los exploradores de turno empiezan en gajos distintos según su índice, lo que reparte las franjas al inicio;
~~~

- **Razón:** La frase es la que sustenta «evitar redundancia de cobertura» en la rúbrica; conviene que sea literalmente cierta.

### 25. La comparación con la primera versión no dice qué magnitud ni con cuántas semillas

- **Ubicación:** Limitaciones, línea 365.
- **Original:**

~~~text
obtuvo `#v.ant.ratio`{=typst} desde la esquina A frente a
~~~

- **Propuesta:**

~~~text
obtuvo un Ratio de `#v.ant.ratio`{=typst} desde la esquina A (`#v.ant.n`{=typst} semillas) frente a
~~~

- **Razón:** «Obtuvo 0,0502» obliga a inferir que es el Ratio; el tamaño de muestra (`ant.n = 10`) ya está en `valores.json` y deja comparar con el 0,0378 de la entregada. Pendiente para el autor: si son las mismas semillas.

---

## C. Redundancia

### 26. El descanso de 300 ticks se repite en el mismo párrafo

- **Ubicación:** Sesión 1, «Dos decisiones que se declaran», línea 88.
- **Original:**

~~~text
ni que el rover ocioso busque sin interrupción (descansa `#c.DESCANSO_BUSQUEDA`{=typst} ticks entre rondas).
~~~

- **Propuesta:**

~~~text
ni que el rover ocioso busque sin interrupción.
~~~

- **Razón:** Cuatro frases antes ya se dice «descansa 300 ticks entre rondas (`_buscar_o_esperar`)». La cifra se conserva allí.

### 27. Los divisores 5 y 40 se explican dos veces

- **Ubicación:** Sesión 2, «Función de utilidad», párrafo tras las fórmulas, línea 154.
- **Original:**

~~~text
descontada por la confianza; 5 es la capacidad del rover. El costo es *marginal*: cuánto alarga la vuelta a la base pasar por la veta, dividido entre 40 pasos; así
~~~

- **Propuesta:**

~~~text
descontada por la confianza. El costo es *marginal*: cuánto alarga la vuelta a la base pasar por la veta; así
~~~

- **Razón:** El párrafo anterior (línea 143) ya deriva ambos divisores («el rover carga 5… se divide entre 5»; «se dividen entre 40, que es del orden de un viaje largo…») y las fórmulas los muestran. Aquí solo hace falta lo nuevo: vecinas, carga libre, confianza y costo marginal.

### 28. Limitaciones y Conclusiones dicen lo mismo sobre qué piezas tienen efecto

- **Ubicación:** Limitaciones, línea 365.
- **Original:**

~~~text
De las piezas probadas, solo muestran efecto sobre el Ratio fuera del ruido las que la @tbl-exp marca con asterisco; el resto cambia otras magnitudes (viajes en vano, batería en tormentas, hielo y batería totales) sin mover el cociente de forma medible con `#x.semillas`{=typst} semillas.
~~~

- **Propuesta:** suprimir la frase (y el espacio que la sigue).
- **Razón:** La metodología ya nombra las dos variantes con efecto y las Conclusiones, diez líneas después, enumeran una por una las piezas «sin efecto medible sobre el Ratio con 10 semillas». Es la tercera vez que se dice. Si el autor prefiere conservarla aquí, la alternativa es acortar la lista de las Conclusiones.

### 29. La ruta bajo tormenta «nunca se elige» repite el argumento del veto

- **Ubicación:** Sesión 2, «Calibración de pesos», última frase, línea 156.
- **Original:**

~~~text
Con los pesos adoptados, una carga completa y reciente vale $\hat g = 1$ y una ruta enteramente bajo tormenta resta $w_4$, mayor que la ganancia máxima, por lo que nunca se elige.
~~~

- **Propuesta:** suprimir la frase (y el espacio que la precede).
- **Pregunta (si se conserva):** «Nunca se elige» vale para la elección por $U$ (con la Tabla 5, $w_1 - w_4 < 0 < u_{\min}$ en las cuatro políticas), pero la Sesión 4 dice que un contrato CNP «tiene prioridad sobre $U$». ¿Puede un rover con contrato tomar esa ruta? Si puede, «nunca» sobra.
- **Razón:** «Función de utilidad» ya dice que $w_4$ es «mayor que la ganancia máxima, de modo que una ruta muy expuesta queda descartada casi como por un veto».

---

## Se queda tal cual

- **Introducción, línea 43:** «Como la batería está en el denominador, el diseño del equipo «Permafrost» parte de una idea: no gastar un paso ni un mensaje que no traiga hielo.» Es la tesis del informe en una frase, sin rodeos, y todo lo demás se lee contra ella.
- **Sesión 5, línea 314:** «La gobernanza cambia de verdad el comportamiento del equipo, pero en estos datos no mejora el Ratio.» Distingue lo observado (4,7 y 9,4 cambios de política por partida) de lo que no se pudo mostrar, y «en estos datos» acota bien. «De verdad» responde al «ajuste real» de la rúbrica.
- **Metodología, línea 74:** «Es una lectura de la regla y se declara como tal: con la lectura más estricta, cada elección costaría del orden de un mensaje por votante…» Repite «lectura» respecto del encabezado, pero es una declaración de integridad con su costo cuantificado; acortarla le quitaría fuerza.
- **Términos repetidos** («viaje en vano», «dentro del ruido», «fuera del ruido», «partidas cortadas»): se repiten porque son las etiquetas de las tablas; sustituirlos por sinónimos los volvería ambiguos. También se queda «0,0 reasignaciones por partida» (línea 261): admite que el mecanismo no llegó a usarse.

---

## Cotejo final

**Comprobado**

- Los 29 «Original» son citas exactas de `informe.qmd` y cada uno aparece una sola vez (comprobación automática de subcadenas); ningún par de propuestas se solapa, así que pueden aplicarse en cualquier orden y combinación.
- Todas las interpolaciones `` `#…`{=typst} `` y cifras literales de cada «Original» siguen en su «Propuesta», con estas excepciones deliberadas, señaladas en su ficha: la **4** corrige 0,005 por 0,0056; la **14** retira `#t.ticks_min` (673) y añade $2^{-900/250}$ y «10 %»; la **26** y la **27** quitan repeticiones de `#c.DESCANSO_BUSQUEDA` (300), 5 y 40 que siguen en el mismo párrafo o en el anterior; la **28** y la **29** suprimen frases enteras cuyo contenido figura en otro lugar del informe.
- Interpolaciones que las propuestas añaden, todas existentes en `valores.json`: `x.s5_tormenta_votando.cortadas` (4; igual en las otras dos variantes de alta tormenta), `t.semillas` (6), `x.completo.hielo` (133), `x.s4_sin_subastas.hielo` (171), `l4.semillas` (3), `l.repeticiones` (3), `v.ant.n` (10). Cifras literales que añaden, todas ya presentes en el informe: 10 partidas y 3000 ticks (6), filtros 1 a 5 (10), 100 unidades por equipo (16), 200 y 400 unidades (17).
- Ninguna propuesta cambia un signo, una unidad, una negación ni una cita bibliográfica [1]–[6]. Los matices de incertidumbre se conservan o se refuerzan («dentro del ruido», «en estos datos»); ninguna propuesta introduce una afirmación causal nueva, y las 7, 8, 12 y 13 rebajan causalidad.
- Cifras del texto cotejadas con `valores.json` y `experimentos.md` y coincidentes: Tabla 2 completa (16 variantes), Tabla 4, Tabla 7, cobertura a los ticks 100 y 600, totales del torneo, conteos de elecciones (suma 3481), partidas cortadas (suma 21) y latencias de `latencia.py`.
- La consigna no contiene ninguna norma sobre asistencia o IA (lectura completa y búsqueda de términos).

**Pendiente (no se puede comprobar con los archivos autorizados)**

- Qué es `t.ms_max_torneo = 47,3` y en qué condiciones se midió (propuesta 1).
- Si «Elección» y «Verificación» de la calibración son las mismas partidas (propuestas 2 y 3).
- Cómo se calcula `hielo_por_bat100` (propuesta 5) y si hay dispersión por semilla de los viajes en vano y del hielo y la batería por política (propuesta 9; también afecta a «Lo que sí cambia con la política es el punto de operación», línea 314, que compara medias sin dispersión).
- Si $n_c$ cuenta restos de rivales (11), el reparto inicial de gajos (24), el umbral de 70 % de la carroña (20), si un contrato puede cruzar una tormenta (29) y si la primera versión usó las mismas semillas (25).
- La corrida de 60 s con Pygame en Python 3.8 (línea 325) y todo lo que el texto afirma sobre el código (`equipoX.py`, `arena.py`): no se abrieron.
- La tabla de latencia de `experimentos.md` (máximo 2,83 ms, medida con partidas en paralelo) difiere de la Tabla 10 (2,10 ms; `latencia.py`); el informe usa la segunda, como pide la nota de ese archivo. No requiere cambio.
- Fuera del alcance editorial, pero visible en el PDF: el encabezado sigue con «Equipo X» y «[Integrante 1] · … · [Integrante 4]».
- La norma del curso sobre IA: confirmarla antes de aplicar cualquier propuesta de redacción.

*Este registro fue elaborado con IA generativa; sus observaciones deben ser validadas por el equipo autor antes de incorporarse.*
