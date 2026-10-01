#!/usr/bin/env python3
"""Paso 3 - RECORTE. Lee prendas.json y recorta cada aparicion con 8% de margen en crops/{prenda_id}/{foto}_{n}.jpg."""
import json
from pathlib import Path
from PIL import Image, ImageOps

CARPETA = Path("jpg")
SALIDA = Path("crops")
MARGEN = 0.08

def recortar(img, bbox):
    W, H = img.size
    x0, y0, x1, y1 = bbox
    mx, my = (x1 - x0) * MARGEN, (y1 - y0) * MARGEN
    caja = (max(0, x0 - mx) * W, max(0, y0 - my) * H, min(1, x1 + mx) * W, min(1, y1 + my) * H)
    return img.crop(tuple(int(round(v)) for v in caja))

def main():
    prendas = json.load(open("prendas.json", encoding="utf-8"))["prendas"]
    total = 0
    for p in prendas:
        carpeta = SALIDA / p["id"]
        carpeta.mkdir(parents=True, exist_ok=True)
        for a in p["apariciones"]:
            img = ImageOps.exif_transpose(Image.open(CARPETA / a["foto"])).convert("RGB")
            crop = recortar(img, a["bbox"])
            destino = carpeta / f"{Path(a['foto']).stem}_{a['n']}.jpg"
            crop.save(destino, quality=92)
            a["crop"] = str(destino)
            total += 1
            print(f"{p['id']}  {destino.name:18s} {crop.size[0]}x{crop.size[1]}{'  (detalle)' if a.get('es_detalle') else ''}")
    json.dump({"prendas": prendas, "descartadas": json.load(open("prendas.json", encoding="utf-8")).get("descartadas", [])},
              open("prendas.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n{total} recortes en {len(prendas)} prendas -> {SALIDA}/")

if __name__ == "__main__":
    main()
