# Experimentos con y sin cada pieza

Nuestro equipo en la esquina A contra tres equipos base, mismas semillas en todas las variantes.
Δ ratio es la diferencia media, semilla a semilla, contra `completo`.

| Sesión | Variante | Qué cambia | n | Ratio (media ± desv.) | Δ ratio | Hielo | Batería | Bat. mensajes | Bat. tormentas | Viajes en vano | Puesto medio |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| — | `completo` | Equipo tal como se entrega | 10 | 0.0310 ± 0.0103 | — | 130 | 4690 | 248 | 893 | 78.0 | 1.20 |
| S1 | `s1_un_solo_gajo` | Todos los exploradores patrullan la misma franja | 10 | 0.0342 ± 0.0116 | +0.0032 | 118 | 3945 | 199 | 730 | 73.0 | 1.20 |
| S1 | `s1_sin_olvido` | Una veta agotada solo se borra al pararse encima | 10 | 0.0323 ± 0.0054 | +0.0013 | 125 | 3949 | 201 | 639 | 165.7 | 1.00 |
| S2 | `s2_sin_evasion` | Sin esperar, rodear ni esquivar tormentas | 10 | 0.0283 ± 0.0076 | -0.0027 | 137 | 5257 | 261 | 2609 | 95.5 | 1.20 |
| S2 | `s2_w2_mitad` | Costo de desplazamiento a la mitad (w2 x0.5) | 10 | 0.0361 ± 0.0087 | +0.0050 | 138 | 4038 | 203 | 732 | 96.1 | 1.00 |
| S2 | `s2_w2_doble` | Costo de desplazamiento al doble (w2 x2) | 10 | 0.0258 ± 0.0115 | -0.0052 | 107 | 5080 | 316 | 1002 | 58.3 | 1.60 |
| S2 | `s2_w4_cero` | Sin penalizar tormenta en la utilidad (w4 x0) | 10 | 0.0330 ± 0.0083 | +0.0020 | 125 | 3977 | 212 | 769 | 94.4 | 1.10 |
| S2 | `s2_w4_triple` | Tormenta pesa el triple (w4 x3) | 10 | 0.0353 ± 0.0076 | +0.0043 | 124 | 3697 | 200 | 701 | 76.3 | 1.00 |
| S3 | `s3_sin_filtros` | Reportes sin deduplicar, sin enfriamiento ni umbral de valor | 10 | 0.0148 ± 0.0043 | -0.0162 | 139 | 10262 | 5185 | 1017 | 94.6 | 2.70 |
| S4 | `s4_sin_subastas` | Sin subasta implícita ni CNP: cada rover va a lo que ve | 10 | 0.0327 ± 0.0122 | +0.0017 | 149 | 5268 | 158 | 915 | 290.6 | 1.20 |
| S5 | `s5_tormenta_votando` | Alta tormenta (+3): con votación | 10 | 0.0174 ± 0.0078 | -0.0136 | 144 | 9750 | 601 | 2665 | 83.7 | 1.60 |
| S5 | `s5_tormenta_fija_ahorro` | Alta tormenta (+3): política fija AHORRO | 10 | 0.0185 ± 0.0120 | -0.0125 | 133 | 9370 | 574 | 2706 | 71.5 | 1.60 |
| S5 | `s5_tormenta_fija_expansion` | Alta tormenta (+3): política fija EXPANSION | 10 | 0.0171 ± 0.0101 | -0.0139 | 153 | 12043 | 860 | 3222 | 90.4 | 1.90 |
| S5 | `s5_normal_fija_ahorro` | Escenario normal: política fija AHORRO | 10 | 0.0374 ± 0.0110 | +0.0063 | 110 | 3192 | 143 | 692 | 62.5 | 1.00 |

## S1 · Cobertura del cuadrante propio (fracción de celdas vistas)

| Variante | tick 100 | tick 200 | tick 400 | tick 600 |
|---|---:|---:|---:|---:|
| `completo` | 92 % | 98 % | 100 % | 100 % |
| `s1_un_solo_gajo` | 81 % | 90 % | 99 % | 99 % |

## S6 · Latencia por turno del equipo completo (ms)

| media | p95 | p99 | máximo |
|---:|---:|---:|---:|
| 0.32 | 1.15 | 1.56 | 3.07 |

Ojo: estos tiempos se midieron con otras partidas corriendo en paralelo. Para el informe,
repetir con `latencia.py` y la máquina libre.

Errores atrapados por la red de seguridad en todas las partidas: **0**.
