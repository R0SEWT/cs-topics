"""Posproceso del HTML de la API para que la vista previa se parezca a github.com.

* <picture> con el <img> envuelto en <a>: en GitHub lo resuelve el JS de themed-picture;
  aquí se desenvuelve para que el navegador elija el <source> según el tema.
* Alertas (> [!NOTE] …): el modo `markdown` de la API no las pinta y GitHub sí, en un
  README del repo. Se convierten al marcado que usa GitHub.
"""
import re
import sys

html = sys.stdin.read()

html = re.sub(
    r"(<picture>.*?)<a [^>]*>(<img [^>]*>)</a>(.*?</picture>)",
    lambda m: m.group(1) + m.group(2) + m.group(3),
    html, flags=re.DOTALL)

TITULOS = {"NOTE": "Note", "TIP": "Tip", "IMPORTANT": "Important",
           "WARNING": "Warning", "CAUTION": "Caution"}


def alerta(m: re.Match) -> str:
    tipo, resto = m.group(1), m.group(2)
    resto = re.sub(r"^\s*(<br>)?\s*", "", resto)
    return (f'<div class="markdown-alert markdown-alert-{tipo.lower()}">'
            f'<p class="markdown-alert-title">{TITULOS[tipo]}</p><p>{resto}</div>')


html = re.sub(r"<blockquote>\s*<p>\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\](.*?)</blockquote>",
              alerta, html, flags=re.DOTALL)
sys.stdout.write(html)
