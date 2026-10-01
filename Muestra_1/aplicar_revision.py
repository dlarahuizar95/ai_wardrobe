#!/usr/bin/env python3
"""Paso 8 - REVISION. Lee el CSV exportado desde closet.html (por defecto ~/Downloads/closet_revision.csv)
y actualiza estado y material de cada prenda en Supabase. Usa la service key del .env."""
import os, sys, csv
from pathlib import Path
import httpx

URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ["SUPABASE_SERVICE_KEY"]
LOTE = Path.cwd().name.lower()
H = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "Prefer": "return=minimal"}

def main():
    ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Downloads" / "closet_revision.csv"
    if not ruta.exists():
        sys.exit(f"No encuentro {ruta}. Exporta el CSV desde closet.html o pasa la ruta como argumento.")
    filas = list(csv.DictReader(open(ruta, encoding="utf-8-sig")))
    for f in filas:
        cambios = {"estado": f["estado"] or "pendiente", "material": f["material"] or None}
        r = httpx.patch(f"{URL}/rest/v1/prendas?lote=eq.{LOTE}&codigo=eq.{f['id']}", headers=H, json=cambios, timeout=30)
        if r.status_code >= 300:
            sys.exit(f"{f['id']}: {r.status_code} {r.text}")
        print(f"{f['id']}  estado={cambios['estado']:9s} material={cambios['material'] or '(en blanco)'}")
    print(f"\n{len(filas)} prendas actualizadas en Supabase (lote {LOTE})")

if __name__ == "__main__":
    main()
