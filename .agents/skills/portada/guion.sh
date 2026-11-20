#!/usr/bin/env bash
# Guion gráfico de un SVG animado: copias en línea congeladas en varios instantes del ciclo
# (Web Animations API) y una captura de Firefox headless. Sirve para revisar una animación
# cuadro a cuadro sin grabar video.
#
#   .agents/skills/portada/guion.sh <svg> <png-salida> <segundos,separados,por,coma> [ancho]
set -euo pipefail
svg=$(realpath "$1"); out=$(realpath -m "$2"); tiempos=$3; ancho=${4:-480}
# El ancho entra en la aritmética de bash, que evalúa lo que reciba: solo un entero.
[[ $ancho =~ ^[1-9][0-9]*$ ]] && (( ancho >= 100 && ancho <= 1880 )) ||
  { echo "guion.sh: el ancho tiene que ser un entero entre 100 y 1880" >&2; exit 2; }
if [ -x /snap/bin/firefox ]; then W=$HOME/snap/firefox/common/vista-previa
else W=${XDG_CACHE_HOME:-$HOME/.cache}/vista-previa; fi
mkdir -p "$W"
# Cada corrida en su carpeta: dos a la vez no se pisan y no quedan perfiles viejos.
R=$(mktemp -d "$W/guion.XXXXXX"); trap 'rm -rf "$R"' EXIT

# Escribe la página y devuelve el alto de cada cuadro, con la proporción del viewBox.
alto=$(python3 - "$svg" "$tiempos" "$ancho" "$R/guion.html" <<'PY'
import re, sys
ruta, tiempos, ancho, pagina = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
svg = open(ruta).read()
# Las figuras de la portada son vector puro: un SVG con algo activo no se abre en el navegador.
if re.search(r"<script|<foreignObject|\son[a-z]+\s*=|javascript:", svg, re.I):
    sys.exit(f"guion.sh: {ruta} trae script, eventos o foreignObject; no se abre")
ts = [float(x) for x in tiempos.split(",")]
_, _, vw, vh = (float(v) for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split())
svg = re.sub(r'width="\d+" height="\d+"', f'width="{ancho}"', svg, count=1)
cuadros = "".join(f'<figure><div class="c" data-t="{t}">{svg}</div>'
                  f'<figcaption>t = {t:g} s</figcaption></figure>' for t in ts)
with open(pagina, "w") as f:
    f.write(f"""<!doctype html><html><head><meta charset="utf-8"><style>
body{{margin:0;padding:12px;background:#888;font:14px sans-serif;display:flex;flex-wrap:wrap;gap:10px}}
figure{{margin:0}} figcaption{{color:#fff}}</style></head><body>{cuadros}
<script>
for (const c of document.querySelectorAll('.c')) {{
  const t = parseFloat(c.dataset.t) * 1000;
  for (const a of c.getAnimations({{subtree: true}})) {{ a.pause(); a.currentTime = t; }}
}}
</script></body></html>""")
print(round(ancho * vh / vw))
PY
)

mkdir -p "$R/perfil"
echo 'user_pref("browser.shell.checkDefaultBrowser", false);' > "$R/perfil/user.js"
n=$(echo "$tiempos" | tr ',' '\n' | wc -l)
columnas=$(( 1900 / (ancho + 10) )); filas=$(( (n + columnas - 1) / columnas ))
timeout 120 firefox --headless --no-remote --profile "$R/perfil" \
  --window-size="1920,$(( filas * (alto + 60) + 40 ))" \
  --screenshot "$R/guion.png" "file://$R/guion.html" >/dev/null 2>&1 || true
mv "$R/guion.png" "$out"
echo "$out"
