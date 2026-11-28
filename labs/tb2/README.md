# TB2 · Simulación multiagente competitiva en Marte

Trabajo final de Tópicos en CC. Cada equipo programa la IA de una facción (rovers, drones
exploradores y drones de recarga) en un archivo `equipoX.py` que el simulador del profesor carga
dinámicamente. Gana el mejor **Ratio = hielo depositado en base / batería total gastada**.

| Archivo | Qué es |
|---|---|
| `equipoA.py` | El equipo. Seis capas, una por sesión del curso: memoria, utilidad y FSM, mensajes FIPA-ACL, Contract Net, votación Copeland y rendimiento. Para entregar se renombra a `equipo<letra>.py`. |
| `arena.py` | Corre partidas sin ventana y mide Ratio, batería por causa, mensajes y latencia. |
| `desglose.py` | En qué se va la batería de nuestro equipo, promediado por semillas. |
| `experimentos.py` | Los experimentos "con y sin" del informe: apaga una pieza por variante. |
| `latencia.py` | Tiempo de decisión por turno contra el umbral de 40 ms. |
| `empaquetar.sh` | Arma `Proyecto_Equipo<LETRA>.zip` con los nombres del enunciado. |
| `PENDIENTES.md` | **Empezar por aquí**: qué falta para entregar y dónde se pierden puntos. |
| `informe/` | Fuente del informe técnico (Quarto + Typst). |
| `reports/` | Resultados de las corridas que cita el informe. |

## Correr

El motor (`simulador.py`, `equipo_base.py`) y el enunciado son material del profesor y **no se
versionan**: se bajan del Aula Virtual a `materials/evaluaciones/tb2/`. Con eso en su sitio:

```bash
cd labs/tb2
uv run --no-project --with pygame python arena.py --semillas 1-5 --detalle   # nosotros en A contra 3 bases
uv run --no-project --with pygame python arena.py --rotar --semillas 1-6     # rotando por las 4 esquinas
uv run --no-project --with pygame python experimentos.py                     # 14 variantes x 10 semillas
uv run --no-project --with pygame python latencia.py                         # con la máquina libre
```

Para verlo con la interfaz del profesor, copiar `equipoA.py` junto a `simulador.py` como
`equipoA.py` … `equipoD.py` y correr `python simulador.py`.

## Restricciones de la entrega

- Un solo archivo, solo librería estándar, sintaxis compatible con Python 3.8.
- Sin hilos, sin `sleep`, sin red ni escritura a disco: todo ocurre dentro de `decidir_unidad`.
- Lo que una unidad sabe de hielo, restos o rescates fuera de su visión solo le llega por `api`
  (cada mensaje cuesta 0,5 % al emisor y 0,5 % al receptor).
- El enunciado habla de 100 unidades por equipo; el simulador entregado crea 50 (30/15/5). El
  código no fija el tamaño de la flota.
