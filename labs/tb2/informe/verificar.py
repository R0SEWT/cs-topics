"""verificar.py — comprueba que cada función y constante citada en el informe existe en ../equipoA.py.

    python3 verificar.py
"""
import re
from pathlib import Path

AQUI = Path(__file__).resolve().parent
codigo = (AQUI.parent / "equipoA.py").read_text()
texto = (AQUI / "informe.qmd").read_text() + (AQUI / "diagramas" / "secuencia.typ").read_text()
citados = set(re.findall(r"`(_[a-z_]+|[A-Z][A-Z_]{3,})`", texto))
externos = {"REQUEST", "INFORM", "PROPOSE", "ACCEPT_PROPOSAL", "REJECT_PROPOSAL", "AGREE", "FAILURE", "ACCEPT"}
faltan = sorted(n for n in citados - externos if not re.search(r"\b%s\b" % re.escape(n), codigo))
print("%d nombres citados; faltan en equipoA.py: %s" % (len(citados), faltan or "ninguno"))
