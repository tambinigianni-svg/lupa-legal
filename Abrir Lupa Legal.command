#!/bin/bash
# Doble clic para abrir Lupa Legal.
# El entorno de Python vive FUERA del Escritorio (~/.lupa-legal-venv) porque el Escritorio
# se sincroniza con iCloud y macOS puede mandar esos archivos a la nube (la página no abría por eso).
cd "$(dirname "$0")"
VENV="$HOME/.lupa-legal-venv"
if [ ! -x "$VENV/bin/python" ]; then
  echo "Preparando Lupa Legal por primera vez (1 minuto)..."
  python3 -m venv "$VENV" && "$VENV/bin/pip" install -q flask anthropic pypdf
fi
if curl -s -o /dev/null --max-time 2 http://127.0.0.1:5050/; then
  echo "Lupa Legal ya estaba abierta."
else
  "$VENV/bin/python" app.py &
  for i in $(seq 1 30); do curl -s -o /dev/null --max-time 1 http://127.0.0.1:5050/ && break; sleep 1; done
fi
open "http://127.0.0.1:5050"
echo "Lupa Legal está en http://127.0.0.1:5050  (no cierres esta ventana mientras la uses)"
wait
