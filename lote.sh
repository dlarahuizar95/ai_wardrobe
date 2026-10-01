#!/bin/zsh
# Uso:  ./lote.sh Muestra_2 preparar   -> HEIC a jpg/, deteccion, agrupacion. Termina mostrando la tabla para revisar.
#       ./lote.sh Muestra_2 generar    -> tras confirmar la tabla: recorte, maniqui, atributos, composicion, HTML, Supabase.
set -e
RAIZ="$(cd "$(dirname "$0")" && pwd)"
LOTE="$1"; FASE="${2:-preparar}"
[[ -d "$RAIZ/$LOTE" ]] || { echo "No existe la carpeta $LOTE"; exit 1; }
set -a; source "$RAIZ/.env"; set +a
PY="$RAIZ/.venv/bin/python"
P="$RAIZ/pipeline"
cd "$RAIZ/$LOTE"
run() { echo "\n=== $1 ==="; "$PY" -W ignore "$P/$1" "${@:2}" 2>&1 | grep -v -e Warning -e warnings.warn; }

if [[ "$FASE" == "preparar" ]]; then
  mkdir -p jpg
  n=0
  for f in *.HEIC(N) *.heic(N) *.JPG(N) *.jpeg(N); do
    out="jpg/${f:r}.jpg"
    [[ -f "$out" ]] && continue
    sips -s format jpeg -s formatOptions 85 --resampleHeightWidthMax 2048 "$f" --out "$out" >/dev/null && n=$((n+1))
  done
  echo "jpg/: $n convertidas, $(ls jpg | wc -l | tr -d ' ') en total"
  run detectar.py
  run agrupar.py
  echo "\nRevisa la tabla. Si esta bien:  ./lote.sh $LOTE generar"
elif [[ "$FASE" == "generar" ]]; then
  run recortar.py
  run maniqui.py
  run atributos.py
  run atributos_composicion.py
  run generar_html.py
  run subir_supabase.py
  open closet.html
else
  echo "Fase desconocida: $FASE (preparar | generar)"; exit 1
fi
