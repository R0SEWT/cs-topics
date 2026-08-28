#!/usr/bin/env bash
# Baja las dependencias de JADE desde Maven Central.
# Aula Virtual bloqueó la descarga de jade.jar / commons-codec-1.3.jar
# (ver manifest.json, status: blocked_by_browser_policy), así que se toman del repo oficial.
set -euo pipefail
cd "$(dirname "$0")/lib"

fetch() { # url  destino
  [ -f "$2" ] && { echo "  ya existe: $2"; return; }
  echo "  bajando: $2"
  curl -fsSL "$1" -o "$2"
}

fetch https://repo1.maven.org/maven2/net/sf/ingenias/jade/4.3/jade-4.3.jar jade.jar
fetch https://repo1.maven.org/maven2/commons-codec/commons-codec/1.3/commons-codec-1.3.jar commons-codec-1.3.jar

echo "Listo. Jars en $(pwd):"
ls -1sh ./*.jar
