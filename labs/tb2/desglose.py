"""desglose.py — en qué se va la batería de nuestro equipo, promediado por semillas.

    uv run --no-project --with pygame python desglose.py [archivo.py] [semillas] [letra]
"""
import sys
from collections import Counter

import arena

archivo = sys.argv[1] if len(sys.argv) > 1 else "equipoA.py"
semillas = arena._rango(sys.argv[2] if len(sys.argv) > 2 else "1-8")
letra = sys.argv[3] if len(sys.argv) > 3 else "A"
tmp = arena.preparar({k: (archivo if k == letra else "base") for k in arena.LETRAS})
gasto, cont = Counter(), Counter()
filas = []
for s in semillas:
    r = arena.partida(tmp, s)
    e = r["equipos"][letra]
    filas.append((s, r["ticks"], e["puesto"], e["recursos"], int(e["bateria"]), e["ratio"]))
    gasto.update(e["gasto"])
    cont.update(e["interno"]["contadores"])
n = len(semillas)
for f in filas:
    print("semilla %2d ticks %5d puesto %d rec %3d bat %5d ratio %.4f" % f)
import statistics
print("ratio medio %.4f mediana %.4f | rec %.0f | bat %.0f" % (sum(f[5] for f in filas) / n, statistics.median(f[5] for f in filas), sum(f[3] for f in filas) / n, sum(f[4] for f in filas) / n))
print("GASTO  ", {k: round(v / n) for k, v in sorted(gasto.items(), key=lambda kv: -kv[1])})
print("PASOS  ", {k[6:]: round(v / n) for k, v in sorted(cont.items(), key=lambda kv: -kv[1]) if k.startswith("pasos_")})
print("MSG    ", {k[4:]: round(v / n) for k, v in sorted(cont.items()) if k.startswith("msg_")})
print("OTROS  ", {k: round(v / n) for k, v in sorted(cont.items()) if not k.startswith(("pasos_", "msg_"))})
