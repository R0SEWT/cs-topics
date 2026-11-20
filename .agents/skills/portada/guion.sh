#!/usr/bin/env bash
# Guion gráfico de un SVG animado: copias en línea congeladas en varios instantes del ciclo
# (Web Animations API) y una captura de Firefox headless. Sirve para revisar una animación
# cuadro a cuadro sin grabar video.
#
#   .agents/skills/portada/guion.sh <svg> <png-salida> <segundos,separados,por,coma> [ancho]
set -euo pipefail
svg=$(realpath "$1"); out=$(realpath -m "$2"); tiempos=$3; ancho=${4:-480}
if [ -x /snap/bin/firefox ]; then W=$HOME/snap/firefox/common/vista-previa
else W=${XDG_CACHE_HOME:-$HOME/.cache}/vista-previa; fi
mkdir -p "$W"

python3 - "$svg" "$tiempos" "$ancho" > "$W/guion.html" <<'PY'
import re, sys
svg = open(sys.argv[1]).read()
ts = [float(x) for x in sys.argv[2].split(",")]
svg = re.sub(r'width="\d+" height="\d+"', f'width="{sys.argv[3]}"', svg, count=1)
cuadros = "".join(f'<figure><div class="c" data-t="{t}">{svg}</div>'
                  f'<figcaption>t = {t:g} s</figcaption></figure>' for t in ts)
print(f"""<!doctype html><html><head><meta charset="utf-8"><style>
body{{margin:0;padding:12px;background:#888;font:14px sans-serif;display:flex;flex-wrap:wrap;gap:10px}}
figure{{margin:0}} figcaption{{color:#fff}}</style></head><body>{cuadros}
<script>
for (const c of document.querySelectorAll('.c')) {{
  const t = parseFloat(c.dataset.t) * 1000;
  for (const a of c.getAnimations({{subtree: true}})) {{ a.pause(); a.currentTime = t; }}
}}
</script></body></html>""")
PY

perfil="$W/perfil-guion"; rm -rf "$perfil"; mkdir -p "$perfil"
echo 'user_pref("browser.shell.checkDefaultBrowser", false);' > "$perfil/user.js"
n=$(echo "$tiempos" | tr ',' '\n' | wc -l)
columnas=$(( 1900 / (ancho + 10) )); filas=$(( (n + columnas - 1) / columnas ))
timeout 120 firefox --headless --no-remote --profile "$perfil" \
  --window-size="1920,$(( filas * (ancho * 6 / 10 + 60) + 40 ))" \
  --screenshot "$W/guion.png" "file://$W/guion.html" >/dev/null 2>&1 || true
mv "$W/guion.png" "$out"
echo "$out"
