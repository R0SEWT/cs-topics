#!/usr/bin/env bash
# empaquetar.sh LETRA — arma Proyecto_Equipo<LETRA>.zip tal como lo pide el enunciado (5.1):
#   equipo<LETRA>.py + Informe_Equipo<LETRA>.pdf
# Antes verifica que el código compile como Python 3.8 y que el informe no pase de 12 páginas.
set -euo pipefail
cd "$(dirname "$0")"
LETRA="${1:?uso: ./empaquetar.sh LETRA   (A, B, C o D; X para un paquete provisional)}"
python3 -c "import ast,sys; ast.parse(open('equipoA.py').read(), feature_version=(3, 8))"
paginas="$(pdfinfo informe/Informe_EquipoX.pdf | awk '/^Pages/{print $2}')"
[ "$paginas" -le 12 ] || { echo "El informe tiene $paginas páginas (máximo 12)"; exit 1; }
if [ "$LETRA" != "X" ] && pdftotext informe/Informe_EquipoX.pdf - | grep -q "Integrante [0-9]\|Equipo X"; then
  echo "AVISO: el informe todavía dice 'Equipo X' o tiene marcadores [Integrante n]."
fi
dest="entrega/Proyecto_Equipo$LETRA"
rm -rf "$dest" "$dest.zip" && mkdir -p "$dest"
# El simulador importa el módulo `equipo<LETRA>` con la letra en MAYÚSCULA.
cp equipoA.py "$dest/equipo$LETRA.py"
cp informe/Informe_EquipoX.pdf "$dest/Informe_Equipo$LETRA.pdf"
(cd entrega && zip -qr "Proyecto_Equipo$LETRA.zip" "Proyecto_Equipo$LETRA")
echo "listo: $dest.zip ($paginas páginas de informe)"; unzip -l "$dest.zip" | tail -4
