#!/usr/bin/env python3
"""Paso 8 - REVISION. Lee el CSV exportado desde closet.html o mi_closet.html (por defecto el mas reciente en ~/Downloads)
y actualiza estado y material de cada prenda en Supabase. Usa la service key del .env."""
import os, sys, csv
from pathlib import Path
import httpx

URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ["SUPABASE_SERVICE_KEY"]
LOTE = Path.cwd().name.lower()
H = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "Prefer": "return=minimal"}

def main():
    if len(sys.argv) > 1:
        ruta = Path(sys.argv[1])
    else:
        cands = sorted((Path.home() / "Downloads").glob("*closet*revision*.csv"), key=lambda p: p.stat().st_mtime)
        ruta = cands[-1] if cands else None
    if not ruta or not ruta.exists():
        sys.exit("No encuentro un CSV de revision en ~/Downloads. Exporta desde closet.html o mi_closet.html, o pasa la ruta.")
    print(f"Leyendo {ruta}")
    filas = list(csv.DictReader(open(ruta, encoding="utf-8-sig")))
    for f in filas:
        cambios = {"estado": f["estado"] or "pendiente", "material": f["material"] or None}
        lote = f.get("lote") or LOTE                      # CSV de mi_closet.html trae lote; el de closet.html no
        codigo = f.get("codigo") or f["id"]
        r = httpx.patch(f"{URL}/rest/v1/prendas?lote=eq.{lote}&codigo=eq.{codigo}", headers=H, json=cambios, timeout=30)
        if r.status_code >= 300:
            sys.exit(f"{f['id']}: {r.status_code} {r.text}")
        print(f"{lote}-{codigo}  estado={cambios['estado']:9s} material={cambios['material'] or '(en blanco)'}")
    print(f"\n{len(filas)} prendas actualizadas en Supabase (lote {LOTE})")

if __name__ == "__main__":
    main()
