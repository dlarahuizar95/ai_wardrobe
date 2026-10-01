#!/bin/zsh
# Abre mi_closet.html con edicion en vivo (Aprobar / Se cambio + comentario / Corregir maniqui).
RAIZ="$(cd "$(dirname "$0")" && pwd)"
set -a; source "$RAIZ/.env"; set +a
cd "$RAIZ"
"$RAIZ/.venv/bin/python" -W ignore pipeline/generar_closet_total.py
( sleep 1; open "http://localhost:8765" ) &
exec "$RAIZ/.venv/bin/python" -W ignore pipeline/servidor.py
