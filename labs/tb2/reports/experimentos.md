# Experimentos con y sin cada pieza

Nuestro equipo en la esquina A contra tres equipos base, mismas semillas en todas las variantes.
Δ ratio es la diferencia media, semilla a semilla, contra `completo`.

| Sesión | Variante | Qué cambia | n | Ratio (media ± desv.) | Δ ratio | Hielo | Batería | Bat. mensajes | Bat. tormentas | Viajes en vano | Puesto medio |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| — | `completo` | Equipo tal como se entrega | 10 | 0.0378 ± 0.0075 | — | 133 | 3627 | 187 | 632 | 51.0 | 1.00 |
| S1 | `s1_un_solo_gajo` | Todos los exploradores patrullan la misma franja | 10 | 0.0364 ± 0.0094 | -0.0015 | 139 | 4390 | 202 | 716 | 50.0 | 1.10 |
| S1 | `s1_sin_olvido` | Una veta agotada solo se borra al pararse encima | 10 | 0.0362 ± 0.0083 | -0.0017 | 133 | 3751 | 162 | 557 | 145.0 | 1.00 |
| S2 | `s2_sin_evasion` | Sin esperar, rodear ni esquivar tormentas | 10 | 0.0289 ± 0.0080 | -0.0089 | 152 | 5695 | 274 | 2680 | 67.8 | 1.10 |
| S2 | `s2_w2_mitad` | Costo de desplazamiento a la mitad (w2 x0.5) | 10 | 0.0351 ± 0.0082 | -0.0028 | 134 | 3993 | 209 | 678 | 56.5 | 1.00 |
| S2 | `s2_w2_doble` | Costo de desplazamiento al doble (w2 x2) | 10 | 0.0353 ± 0.0080 | -0.0026 | 127 | 3806 | 205 | 670 | 44.1 | 1.00 |
| S2 | `s2_w4_tercio` | Tormenta pesa un tercio (w4 x1/3) | 10 | 0.0348 ± 0.0105 | -0.0030 | 140 | 4684 | 228 | 804 | 54.5 | 1.20 |
| S2 | `s2_w4_cero` | Sin penalizar tormenta en la utilidad (w4 x0) | 10 | 0.0371 ± 0.0077 | -0.0007 | 142 | 3923 | 199 | 663 | 67.4 | 1.00 |
| S2 | `s2_w4_triple` | Tormenta pesa el triple (w4 x3) | 10 | 0.0378 ± 0.0077 | -0.0000 | 133 | 3621 | 188 | 611 | 51.5 | 1.00 |
| S2 | `s2_pesos_iniciales` | Pesos antes de calibrar (w2 x2, w4 x1/3) | 10 | 0.0322 ± 0.0106 | -0.0056 | 132 | 4703 | 253 | 842 | 43.3 | 1.20 |
| S3 | `s3_sin_filtros` | Reportes sin deduplicar, sin enfriamiento ni umbral de valor | 10 | 0.0176 ± 0.0047 | -0.0203 | 151 | 9587 | 4254 | 994 | 58.9 | 1.70 |
| S4 | `s4_sin_subastas` | Sin subasta implícita ni CNP: cada rover va a lo que ve | 10 | 0.0332 ± 0.0098 | -0.0047 | 171 | 5897 | 175 | 913 | 276.7 | 1.00 |
| S5 | `s5_tormenta_votando` | Alta tormenta (+3): con votación | 10 | 0.0212 ± 0.0086 | -0.0166 | 160 | 9192 | 552 | 2283 | 58.2 | 1.10 |
| S5 | `s5_tormenta_fija_ahorro` | Alta tormenta (+3): política fija AHORRO | 10 | 0.0215 ± 0.0103 | -0.0164 | 140 | 8361 | 472 | 2328 | 47.4 | 1.20 |
| S5 | `s5_tormenta_fija_expansion` | Alta tormenta (+3): política fija EXPANSION | 10 | 0.0233 ± 0.0113 | -0.0146 | 176 | 10097 | 680 | 2401 | 69.7 | 1.50 |
| S5 | `s5_normal_fija_ahorro` | Escenario normal: política fija AHORRO | 10 | 0.0388 ± 0.0110 | +0.0009 | 117 | 3199 | 124 | 660 | 40.4 | 1.00 |

## S1 · Cobertura del cuadrante propio (fracción de celdas vistas)

| Variante | tick 100 | tick 200 | tick 400 | tick 600 |
|---|---:|---:|---:|---:|
| `completo` | 93 % | 98 % | 100 % | 100 % |
| `s1_un_solo_gajo` | 81 % | 92 % | 99 % | 99 % |

## S6 · Latencia por turno del equipo completo (ms)

| media | p95 | p99 | máximo |
|---:|---:|---:|---:|
| 0.39 | 1.23 | 1.87 | 2.83 |

Ojo: estos tiempos se midieron con otras partidas corriendo en paralelo. Para el informe,
repetir con `latencia.py` y la máquina libre.

Errores atrapados por la red de seguridad en todas las partidas: **0**.
