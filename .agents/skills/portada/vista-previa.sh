#!/usr/bin/env bash
# Vista previa del README como lo pinta GitHub, para mirarlo antes de subirlo.
#
#   .agents/skills/portada/vista-previa.sh <README.md> <salida> <etiqueta>
#
# El Markdown pasa por la API de GitHub (modo `markdown`, el de los archivos del repo: mismo
# saneado de HTML), `post.py` imita lo que en github.com hace el JS (themed-picture, alertas),
# se envuelve con github-markdown-css y Firefox headless saca tres capturas: escritorio claro,
# escritorio oscuro y celular (412 px). Por defecto con movimiento reducido, así los SVG
# animados se ven en su estado final; MOVIMIENTO_REDUCIDO=0 lo apaga. Cada captura se recorta
# y se parte en tramos de 1400 px (<etiqueta>-claro-t0.png, …) para mirarlos de a uno.
#
# Pide `gh` autenticado, Firefox y uv. Corre desde la raíz del repo.
set -euo pipefail
md=$1; out=$(realpath -m "$2"); tag=$3; alto=${ALTO:-9000}
repo=$(git rev-parse --show-toplevel)
aqui=$(cd "$(dirname "$0")" && pwd)

# Firefox en snap solo ve $HOME: el HTML y los perfiles van donde pueda leerlos.
if [ -x /snap/bin/firefox ]; then W=$HOME/snap/firefox/common/vista-previa
else W=${XDG_CACHE_HOME:-$HOME/.cache}/vista-previa; fi
mkdir -p "$out" "$W"
[ -s "$W/gh-md.css" ] || curl -sSfL -o "$W/gh-md.css" \
  https://cdn.jsdelivr.net/npm/github-markdown-css@5.8.1/github-markdown.css

frag=$(gh api -X POST /markdown -f text="$(cat "$md")" -f mode=markdown | python3 "$aqui/post.py")

pagina() {  # $1 = ancho del artículo en px
cat <<EOF
<!doctype html><html><head><meta charset="utf-8">
<base href="file://$repo/">
<link rel="stylesheet" href="file://$W/gh-md.css">
<style>
  body { margin:0; background:#ffffff; }
  @media (prefers-color-scheme: dark) { body { background:#0d1117; } }
  .markdown-body { box-sizing:border-box; width:$1px; margin:0 auto; padding:24px 16px 48px; }
</style></head>
<body><article class="markdown-body">
$frag
</article></body></html>
EOF
}
pagina 880 > "$W/$tag-escritorio.html"
pagina 380 > "$W/$tag-celular.html"

captura() {  # $1 html, $2 png, $3 ancho de ventana, $4 alto, $5 tema (0 oscuro, 1 claro)
  local perfil="$W/perfil-$5"
  rm -rf "$perfil"; mkdir -p "$perfil"
  cat > "$perfil/user.js" <<EOF
user_pref("layout.css.prefers-color-scheme.content-override", $5);
user_pref("ui.systemUsesDarkTheme", $(( 1 - $5 )));
user_pref("ui.prefersReducedMotion", ${MOVIMIENTO_REDUCIDO:-1});
user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("datareporting.policy.dataSubmissionEnabled", false);
user_pref("toolkit.telemetry.reportingpolicy.firstRun", false);
EOF
  timeout 120 firefox --headless --no-remote --profile "$perfil" \
    --window-size="$3,$4" --screenshot "$W/captura.png" "file://$1" >/dev/null 2>&1 || true
  mv "$W/captura.png" "$2"
}
captura "$W/$tag-escritorio.html" "$out/$tag-claro.png"   912 "$alto" 1
captura "$W/$tag-escritorio.html" "$out/$tag-oscuro.png"  912 "$alto" 0
captura "$W/$tag-celular.html"    "$out/$tag-celular.png" 412 $(( alto * 2 )) 1

uv run --quiet --with pillow python - "$out" "$tag" <<'PY'
import sys
from pathlib import Path
from PIL import Image, ImageChops
out, tag = Path(sys.argv[1]), sys.argv[2]
for tema in ("claro", "oscuro", "celular"):
    p = out / f"{tag}-{tema}.png"
    im = Image.open(p).convert("RGB")
    fondo = Image.new("RGB", im.size, im.getpixel((2, im.height - 2)))
    caja = ImageChops.difference(im, fondo).getbbox()
    im = im.crop((0, 0, im.width, min((caja[3] + 40) if caja else im.height, im.height)))
    im.save(p)
    for viejo in out.glob(f"{tag}-{tema}-t*.png"):
        viejo.unlink()
    for i, y in enumerate(range(0, im.height, 1400)):
        im.crop((0, y, im.width, min(y + 1400, im.height))).save(out / f"{tag}-{tema}-t{i}.png")
    print(f"{p}: {im.width}x{im.height}")
PY
