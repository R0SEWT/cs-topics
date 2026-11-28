# Experimentos con y sin cada pieza

Nuestro equipo en la esquina A contra tres equipos base, mismas semillas en todas las variantes.
Δ ratio es la diferencia media, semilla a semilla, contra `completo`.

| Sesión | Variante | Qué cambia | n | Ratio (media ± desv.) | Δ ratio | Hielo | Batería | Bat. mensajes | Bat. tormentas | Viajes en vano | Puesto medio |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| — | `completo` | Equipo tal como se entrega | 10 | 0.0376 ± 0.0073 | — | 133 | 3637 | 188 | 628 | 51.8 | 1.00 |
| S1 | `s1_un_solo_gajo` | Todos los exploradores patrullan la misma franja | 10 | 0.0364 ± 0.0094 | -0.0012 | 139 | 4390 | 202 | 716 | 50.0 | 1.10 |
| S1 | `s1_sin_olvido` | Una veta agotada solo se borra al pararse encima | 10 | 0.0369 ± 0.0081 | -0.0007 | 133 | 3685 | 159 | 540 | 145.1 | 1.00 |
| S2 | `s2_sin_evasion` | Sin esperar, rodear ni esquivar tormentas | 10 | 0.0289 ± 0.0080 | -0.0087 | 152 | 5700 | 273 | 2684 | 67.8 | 1.10 |
| S2 | `s2_w2_mitad` | Costo de desplazamiento a la mitad (w2 x0.5) | 10 | 0.0351 ± 0.0082 | -0.0025 | 134 | 3993 | 209 | 678 | 56.5 | 1.00 |
| S2 | `s2_w2_doble` | Costo de desplazamiento al doble (w2 x2) | 10 | 0.0353 ± 0.0080 | -0.0023 | 127 | 3806 | 205 | 670 | 44.1 | 1.00 |
| S2 | `s2_w4_tercio` | Tormenta pesa un tercio (w4 x1/3) | 10 | 0.0348 ± 0.0105 | -0.0028 | 140 | 4684 | 228 | 804 | 54.5 | 1.20 |
| S2 | `s2_w4_cero` | Sin penalizar tormenta en la utilidad (w4 x0) | 10 | 0.0368 ± 0.0080 | -0.0008 | 140 | 3909 | 203 | 661 | 67.0 | 1.00 |
| S2 | `s2_w4_triple` | Tormenta pesa el triple (w4 x3) | 10 | 0.0376 ± 0.0075 | -0.0000 | 132 | 3631 | 189 | 607 | 52.3 | 1.00 |
| S2 | `s2_pesos_iniciales` | Pesos antes de calibrar (w2 x2, w4 x1/3) | 10 | 0.0322 ± 0.0106 | -0.0054 | 132 | 4703 | 253 | 842 | 43.3 | 1.20 |
| S3 | `s3_sin_filtros` | Reportes sin deduplicar, sin enfriamiento ni umbral de valor | 10 | 0.0171 ± 0.0037 | -0.0205 | 150 | 9666 | 4371 | 984 | 58.6 | 1.90 |
| S4 | `s4_sin_subastas` | Sin subasta implícita ni CNP: cada rover va a lo que ve | 10 | 0.0332 ± 0.0098 | -0.0044 | 171 | 5897 | 175 | 913 | 276.7 | 1.00 |
| S4 | `s4_sin_implicita` | Sin subasta implícita (queda el CNP explícito) | 10 | 0.0352 ± 0.0069 | -0.0024 | 177 | 5231 | 272 | 616 | 291.8 | 1.00 |
| S4 | `s4_sin_cnp` | Sin CNP explícito (queda la subasta implícita; avisos por INFORM) | 10 | 0.0367 ± 0.0065 | -0.0010 | 127 | 3545 | 97 | 666 | 44.4 | 1.00 |
| S5 | `s5_tormenta_votando` | Alta tormenta (+3): con votación | 10 | 0.0212 ± 0.0086 | -0.0164 | 161 | 9232 | 555 | 2287 | 57.7 | 1.10 |
| S5 | `s5_tormenta_fija_ahorro` | Alta tormenta (+3): política fija AHORRO | 10 | 0.0215 ± 0.0103 | -0.0161 | 140 | 8361 | 472 | 2328 | 47.4 | 1.20 |
| S5 | `s5_tormenta_fija_expansion` | Alta tormenta (+3): política fija EXPANSION | 10 | 0.0233 ± 0.0112 | -0.0143 | 175 | 10042 | 688 | 2379 | 69.5 | 1.50 |
| S5 | `s5_normal_fija_ahorro` | Escenario normal: política fija AHORRO | 10 | 0.0388 ± 0.0110 | +0.0012 | 117 | 3199 | 124 | 660 | 40.4 | 1.00 |

## S1 · Cobertura del cuadrante propio (fracción de celdas vistas)

| Variante | tick 100 | tick 200 | tick 400 | tick 600 |
|---|---:|---:|---:|---:|
| `completo` | 93 % | 98 % | 100 % | 100 % |
| `s1_un_solo_gajo` | 81 % | 92 % | 99 % | 99 % |

## S6 · Latencia por turno del equipo completo (ms)

| media | p95 | p99 | máximo |
|---:|---:|---:|---:|
| 0.78 | 2.79 | 6.38 | 17.24 |

Ojo: estos tiempos se midieron con otras partidas corriendo en paralelo. Para el informe,
repetir con `latencia.py` y la máquina libre.

Errores atrapados por la red de seguridad en todas las partidas: **0**.
