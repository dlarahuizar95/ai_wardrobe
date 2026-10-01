#!/usr/bin/env python3
"""Paso 1 - DETECCION. Lee jpg/*.jpg y genera detecciones.json con las prendas de cada foto."""
import os, json, time
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image

MODEL = "gemini-3.6-flash"
CARPETA = Path("jpg")
SALIDA = "detecciones.json"

CATEGORIAS = ["top","camisa","blusa","sweater","cardigan","blazer","chamarra","abrigo","vestido",
              "falda","pantalon","jeans","shorts","zapatos","bolsa","cinturon","accesorio","incierto"]

SCHEMA = {
    "type": "object",
    "properties": {
        "prendas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "bbox": {"type": "array", "items": {"type": "number"}, "minItems": 4, "maxItems": 4,
                             "description": "[x_min, y_min, x_max, y_max] normalizado 0-1, origen arriba-izquierda"},
                    "categoria": {"type": "string", "enum": CATEGORIAS},
                    "color_principal": {"type": "string"},
                    "descripcion": {"type": "string",
                                    "description": "literal: color, patron, manga, largo, cuello, material aparente, detalles (botones, cierres, forro)"},
                    "es_detalle": {"type": "boolean",
                                   "description": "true si la foto es un acercamiento (etiqueta, pretina, textura) y no se ve la prenda completa"},
                    "etiqueta_texto": {"type": "string", "description": "marca y talla si se leen; si no, ''"},
                },
                "required": ["bbox","categoria","color_principal","descripcion","es_detalle","etiqueta_texto"],
            },
        }
    },
    "required": ["prendas"],
}

PROMPT = (
    "Detecta TODAS las prendas de ropa visibles en la foto (puede haber varias). "
    "Para cada una da su bounding box normalizada [x_min, y_min, x_max, y_max] entre 0 y 1 "
    "que cubra la prenda completa, su categoria, color principal y una descripcion literal en espanol "
    "(color, patron, manga, largo, cuello, material aparente, botones/cierres/forro). "
    "Ignora la superficie de fondo (cobija, piso). Si la foto es un acercamiento de etiqueta o detalle, "
    "marca es_detalle=true y describe la prenda a la que pertenece. Si no estas seguro de la categoria usa 'incierto'."
)

def detectar(client, path):
    img = Image.open(path)
    for intento in range(3):
        try:
            r = client.models.generate_content(
                model=MODEL,
                contents=[img, PROMPT],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json", response_schema=SCHEMA, temperature=0.1),
            )
            return json.loads(r.text)["prendas"]
        except Exception as e:
            if intento == 2: return [{"error": str(e)[:200]}]
            time.sleep(2 * (intento + 1))

def main():
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    fotos = sorted(p for p in CARPETA.iterdir() if p.suffix.lower() in (".jpg", ".jpeg"))
    # reanudable: conserva lo ya detectado y salta esas fotos
    salida = json.load(open(SALIDA, encoding="utf-8")) if Path(SALIDA).exists() else []
    hechas = {f["foto"] for f in salida if not any("error" in d for d in f["prendas"])}
    salida = [f for f in salida if f["foto"] in hechas]
    for i, p in enumerate(fotos, 1):
        if p.name in hechas:
            continue
        w, h = Image.open(p).size
        prendas = detectar(client, p)
        for n, d in enumerate(prendas, 1):
            d["n"] = n
            if "bbox" in d:  # asegurar rango 0-1 y orden correcto
                x0, y0, x1, y1 = [min(max(float(v), 0.0), 1.0) for v in d["bbox"]]
                d["bbox"] = [min(x0,x1), min(y0,y1), max(x0,x1), max(y0,y1)]
        salida.append({"foto": p.name, "ancho": w, "alto": h, "prendas": prendas})
        resumen = " | ".join(f"{d.get('categoria','?')} {d.get('color_principal','')}"
                             + (" [detalle]" if d.get("es_detalle") else "") for d in prendas)
        print(f"[{i}/{len(fotos)}] {p.name}: {resumen}", flush=True)
        salida.sort(key=lambda f: f["foto"])
        json.dump(salida, open(SALIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    total = sum(len(f["prendas"]) for f in salida)
    print(f"\nListo: {SALIDA} ({total} detecciones en {len(fotos)} fotos)")

if __name__ == "__main__":
    main()
