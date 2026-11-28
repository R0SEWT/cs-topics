# TB2 · Qué falta para entregar

Entrega: **jueves 03/12, 23:59** en el Aula Virtual. El Aula no acepta entregas tarde. Ese mismo
día vence la «(DD) Evaluación de desempeño» del curso.

Todo el trabajo está en esta carpeta (`labs/tb2/`), en la rama `feature/tb2-marte`
([PR 37](https://github.com/R0SEWT/cs-topics/pull/37)).

## Para ponerse en marcha

1. Clonar el repo y cambiar a la rama `feature/tb2-marte`.
2. Bajar del Aula Virtual `simulador.py`, `equipo_base.py` y `Enunciado.pdf` y ponerlos en
   `materials/evaluaciones/tb2/` (no se versionan: son material del profesor y el repo es público).
3. Probar: `cd labs/tb2 && uv run --no-project --with pygame python arena.py --semillas 1-3 --detalle`.
4. Para verlo con ventana: copiar `equipoA.py` junto a `simulador.py` y correr `python simulador.py`.

El [README](README.md) explica cada archivo.

## Lo que falta, en orden

- [ ] **Letra del equipo e integrantes.** Cambiar «Equipo X» y `[Integrante 1..4]` en
      `informe/informe.qmd` y renderizar (`cd informe && quarto render informe.qmd --to typst`).
- [ ] **Leer el informe completo** (`informe/Informe_EquipoX.pdf`, 11 páginas) contra la rúbrica
      del enunciado. Lo redactó una IA a partir del código y los datos: hay que validarlo.
- [ ] **Revisar `informe/revision-humanizar.md`**: 29 propuestas de edición, cada una con el pasaje
      original, el cambio y la razón. No se aplicó ninguna en bloque; decidir cuáles entran.
- [ ] **Decidir la nota de uso de IA** que está al final del informe. El enunciado no dice nada
      sobre IA: confirmar con el docente o el sílabo qué corresponde declarar.
- [ ] **Preguntar al docente** dos cosas que afectan la nota:
      1. ¿El torneo usa 50 o 100 unidades por equipo? El enunciado dice 100; el simulador crea 50.
      2. ¿La votación puede compartir papeletas y política sin mensajes? El equipo lo hace así
         (no viajan posiciones ni hallazgos) y el informe lo declara en la metodología.
- [ ] **Armar el zip**: `./empaquetar.sh LETRA` genera `entrega/Proyecto_Equipo<LETRA>.zip` con
      `equipo<LETRA>.py` y el informe. Avisa si quedan marcadores sin reemplazar.
- [ ] **Probar el zip** con el simulador y su ventana antes de subirlo.
- [ ] **Subir al Aula.**
- [ ] Opcional: repetir `latencia.py` con la máquina libre y volver a renderizar.

## Cómo está hoy

| | Nuestro equipo | Equipo base |
|---|---|---|
| Ratio medio (24 partidas, 4 esquinas) | 0,0331 | 0,0192 |
| Puesto medio | 1,42 | 2,86 |
| Errores en ejecución | 0 | — |
| Peor turno con 200 / 400 unidades | 3,7 ms / 8,7 ms | umbral: 40 ms |

Tres correcciones simuladas (un agente en el papel del docente, solo con el zip, el enunciado y
el material de clase) estimaron 15,5, 16,5 y 15 sobre 20. La versión actual corrige lo que señaló
la tercera y no se volvió a auditar.

## Dónde se pierden puntos y qué costaría recuperarlos

| Criterio | Qué descuenta | Qué habría que cambiar |
|---|---|---|
| Cumplimiento base | Patrullan 2 o 3 de 15 exploradores por turnos; el rover ocioso descansa entre rondas de búsqueda; hay recargas preventivas en la base. | Subir `exploradores` y bajar `cadencia` en `POLITICAS`, y `DESCANSO_BUSQUEDA`. Cuesta Ratio: la versión que casi no patrullaba daba 0,050. |
| S5 Elección social | La votación no mejora el Ratio; la política `CARRONA` nunca gobierna; papeletas sin costo de mensaje. | Rediseñar los puntajes de `_depositar_papeleta` o cobrar la votación por `api`. |
| S4 Contract Net | El 35 % de las subastas queda desierto; la reducción de viajes en vano la da la subasta implícita, no el CNP explícito. | Que los rovers también inicien subastas, o ampliar los candidatos. |
| S1 Memoria | La patrulla no llega a la esquina lejana del cuadrante; el rastro de tormentas se guarda pero no se usa. | Subir `RADIO_PATRULLA`; usar el rastro en `_centros`. |

Cualquier cambio de comportamiento en `equipoA.py` obliga a repetir las mediciones
(`experimentos.py`, `arena.py --rotar`, `latencia.py`: unos 45 minutos) y a renderizar el informe,
porque sus tablas salen de `reports/`.

## Reglas que no hay que romper

- Un solo archivo, solo librería estándar, sintaxis de Python 3.8, líneas de 79 columnas.
- Nada de hilos, `sleep`, red ni archivos dentro de `decidir_unidad`.
- Lo que una unidad sabe de hielo, restos o rescates fuera de su visión solo llega por `api`.
- Los interruptores `EXP_*` van todos en `True` en la entrega.
