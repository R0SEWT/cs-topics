# Experimentos con y sin cada pieza

Nuestro equipo en la esquina A contra tres equipos base, mismas semillas en todas las variantes.
Δ ratio es la diferencia media, semilla a semilla, contra `completo`.

| Sesión | Variante | Qué cambia | n | Ratio (media ± desv.) | Δ ratio | Hielo | Batería | Bat. mensajes | Bat. tormentas | Viajes en vano | Puesto medio |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| — | `completo` | Equipo tal como se entrega | 10 | 0.0502 ± 0.0078 | — | 110 | 2216 | 144 | 587 | 67.4 | 1.00 |
| S1 | `s1_un_solo_gajo` | Todos los exploradores patrullan la misma franja | 10 | 0.0560 ± 0.0177 | +0.0058 | 107 | 2036 | 136 | 615 | 66.6 | 1.00 |
| S1 | `s1_sin_olvido` | Una veta agotada solo se borra al pararse encima | 10 | 0.0491 ± 0.0073 | -0.0011 | 108 | 2217 | 142 | 520 | 116.9 | 1.00 |
| S2 | `s2_sin_evasion` | Sin esperar, rodear ni esquivar tormentas | 10 | 0.0444 ± 0.0085 | -0.0058 | 118 | 2696 | 160 | 1263 | 75.1 | 1.00 |
| S2 | `s2_w2_mitad` | Costo de desplazamiento a la mitad (w2 x0.5) | 10 | 0.0536 ± 0.0109 | +0.0035 | 127 | 2423 | 143 | 551 | 87.2 | 1.00 |
| S2 | `s2_w2_doble` | Costo de desplazamiento al doble (w2 x2) | 10 | 0.0383 ± 0.0112 | -0.0119 | 78 | 2183 | 132 | 740 | 46.9 | 1.00 |
| S2 | `s2_w4_cero` | Sin penalizar tormenta en la utilidad (w4 x0) | 10 | 0.0533 ± 0.0112 | +0.0031 | 108 | 2064 | 129 | 531 | 74.3 | 1.00 |
| S2 | `s2_w4_triple` | Tormenta pesa el triple (w4 x3) | 10 | 0.0538 ± 0.0080 | +0.0036 | 111 | 2084 | 137 | 554 | 65.8 | 1.00 |
| S3 | `s3_sin_filtros` | Reportes sin deduplicar, sin enfriamiento ni umbral de valor | 10 | 0.0299 ± 0.0082 | -0.0203 | 106 | 3679 | 1742 | 497 | 59.2 | 1.10 |
| S4 | `s4_sin_subastas` | Sin subasta implícita ni CNP: cada rover va a lo que ve | 10 | 0.0489 ± 0.0080 | -0.0013 | 134 | 2796 | 94 | 537 | 267.9 | 1.00 |
| S5 | `s5_tormenta_votando` | Alta tormenta (+3): con votación | 10 | 0.0375 ± 0.0119 | -0.0127 | 110 | 3131 | 173 | 1331 | 56.4 | 1.00 |
| S5 | `s5_tormenta_fija_ahorro` | Alta tormenta (+3): política fija AHORRO | 10 | 0.0372 ± 0.0148 | -0.0130 | 82 | 2409 | 120 | 1170 | 46.5 | 1.00 |
| S5 | `s5_tormenta_fija_expansion` | Alta tormenta (+3): política fija EXPANSION | 10 | 0.0375 ± 0.0096 | -0.0127 | 118 | 3314 | 265 | 1202 | 60.1 | 1.00 |
| S5 | `s5_normal_fija_ahorro` | Escenario normal: política fija AHORRO | 10 | 0.0482 ± 0.0097 | -0.0020 | 84 | 1761 | 95 | 627 | 53.5 | 1.00 |

## S1 · Cobertura del cuadrante propio (fracción de celdas vistas)

| Variante | tick 100 | tick 200 | tick 400 | tick 600 |
|---|---:|---:|---:|---:|
| `completo` | 96 % | 99 % | 100 % | 100 % |
| `s1_un_solo_gajo` | 81 % | 89 % | 96 % | 96 % |

## S6 · Latencia por turno del equipo completo (ms)

| media | p95 | p99 | máximo |
|---:|---:|---:|---:|
| 1.75 | 13.43 | 26.12 | 73.26 |

Ojo: estos tiempos se midieron con otras partidas corriendo en paralelo. Para el informe,
repetir con `latencia.py` y la máquina libre.

Errores atrapados por la red de seguridad en todas las partidas: **0**.
