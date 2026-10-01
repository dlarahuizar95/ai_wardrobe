#!/usr/bin/env python3
"""Paso 7 - SUBIR. Imagenes (maniqui + crops) al bucket 'closet' y filas a prendas / apariciones.
Requiere SUPABASE_URL y SUPABASE_SERVICE_KEY en el entorno. Idempotente: upsert de filas y sobreescritura de archivos."""
import os, json, sys
from pathlib import Path
import httpx

URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ["SUPABASE_SERVICE_KEY"]
LOTE = Path.cwd().name.lower()          # muestra_1
BUCKET = "closet"
H = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}

def subir_archivo(ruta: Path) -> str:
    destino = f"{LOTE}/{ruta.as_posix()}"
    r = httpx.post(f"{URL}/storage/v1/object/{BUCKET}/{destino}", headers={**H, "x-upsert": "true", "Content-Type": "image/jpeg"},
                   content=ruta.read_bytes(), timeout=60)
    r.raise_for_status()
    return f"{URL}/storage/v1/object/public/{BUCKET}/{destino}"

def upsert(tabla, filas, conflicto):
    r = httpx.post(f"{URL}/rest/v1/{tabla}?on_conflict={conflicto}",
                   headers={**H, "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates,return=minimal"},
                   json=filas, timeout=60)
    if r.status_code >= 300:
        sys.exit(f"{tabla}: {r.status_code} {r.text}")

def main():
    prendas = json.load(open("prendas.json", encoding="utf-8"))["prendas"]
    filas_p, filas_a = [], []
    for p in prendas:
        pid = f"{LOTE}-{p['id']}"
        man = Path("maniqui") / f"{p['id']}.jpg"
        url_man = subir_archivo(man) if man.exists() else None
        at = p.get("atributos", {})
        filas_p.append({"id": pid, "lote": LOTE, "codigo": p["id"], "categoria": p["categoria"],
                        "marca_talla": p.get("marca_talla") or None, "descripcion": p["descripcion"],
                        "color": at.get("color"), "estilo": at.get("estilo"), "material": at.get("composicion") or None,
                        "detalles": at.get("detalles"), "maniqui_url": url_man})
        for a in p["apariciones"]:
            filas_a.append({"prenda_id": pid, "foto": a["foto"], "n": a["n"], "bbox": a["bbox"],
                            "es_detalle": a.get("es_detalle", False), "descripcion_foto": a.get("descripcion_foto"),
                            "crop_url": subir_archivo(Path(a["crop"])) if a.get("crop") else None})
        print(f"{p['id']}  maniqui + {len(p['apariciones'])} crops subidos")
    upsert("prendas", filas_p, "id")
    upsert("apariciones", filas_a, "prenda_id,foto,n")
    print(f"\n{len(filas_p)} prendas y {len(filas_a)} apariciones en Supabase (lote {LOTE})")

if __name__ == "__main__":
    main()
