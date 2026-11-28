#!/usr/bin/env bash
# Compila las FSM (Graphviz) y las une en una sola figura SVG.
set -euo pipefail
cd "$(dirname "$0")"
for f in fsm_rover fsm_explorador fsm_recargador; do dot -Tsvg "$f.dot" -o "$f.svg"; done
python3 - <<'PY'
import re
partes, x, alto = [], 0.0, 0.0
for n in ("fsm_rover", "fsm_explorador", "fsm_recargador"):
    s = open(n + ".svg").read()
    w, h = map(float, re.search(r'<svg width="([\d.]+)pt" height="([\d.]+)pt"', s).groups())
    cuerpo = s[s.index("<g id=\"graph0\""):s.rindex("</svg>")]
    cuerpo = re.sub(r'id="(\w+)"', lambda m: 'id="%s_%s"' % (n, m.group(1)), cuerpo)
    partes.append((x, h, cuerpo)); x += w + 14; alto = max(alto, h)
W = x - 14
out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%gpt" height="%gpt" viewBox="0 0 %g %g">' % (W, alto, W, alto)]
for x0, h, cuerpo in partes:
    out.append('<g transform="translate(%g,%g)">%s</g>' % (x0, alto - h, cuerpo))
out.append("</svg>")
open("fsm_todo.svg", "w").write("\n".join(out))
print("fsm_todo.svg %gx%g pt" % (W, alto))
PY
