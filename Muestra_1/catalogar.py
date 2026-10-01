#!/usr/bin/env python3
"""Cataloga fotos de ropa con Gemini. Uso: python catalogar.py <carpeta_jpg> [salida_base]"""
import os, sys, json, csv, time
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image

MODEL = "gemini-3.6-flash"

SCHEMA = {
    "type": "object",
    "properties": {
        "categoria":       {"type": "string", "description": "vestido, blusa, camisa, pantalon, jeans, falda, short, chamarra, abrigo, sueter, sudadera, top, traje_de_bano, calzado, bolsa, accesorio, conjunto, otro"},
        "subtipo":         {"type": "string", "description": "ej. midi, maxi, crop, wide leg, blazer, cardigan"},
        "color_principal": {"type": "string"},
        "colores_secundarios": {"type": "string"},
        "estampado":       {"type": "string", "description": "liso, floral, rayas, cuadros, animal print, geometrico, ornamental, logo, otro"},
        "material_aparente": {"type": "string"},
        "marca":           {"type": "string", "description": "solo si es visible en etiqueta o logo; si no, 'no visible'"},
        "talla_visible":   {"type": "string", "description": "solo si se lee en etiqueta; si no, 'no visible'"},
        "temporada":       {"type": "string", "description": "primavera-verano, otono-invierno, todo el ano"},
        "ocasion":         {"type": "string", "description": "casual, oficina, fiesta, playa, deporte, formal"},
        "estado":          {"type": "string", "description": "nuevo con etiqueta, como nuevo, buen estado, con desgaste, dañado"},
        "descripcion_corta": {"type": "string", "description": "maximo 12 palabras, estilo titulo de anuncio"},
        "nombre_archivo_sugerido": {"type": "string", "description": "snake_case sin acentos, ej. vestido_negro_ornamental_maxi"},
        "notas":           {"type": "string", "description": "detalles, defectos, si hay varias prendas, si la foto es de etiqueta/detalle"},
    },
    "required": ["categoria","color_principal","estampado","material_aparente","marca","temporada","ocasion","estado","descripcion_corta","nombre_archivo_sugerido"],
}

PROMPT = (
    "Eres un catalogador de ropa para inventario de closet. Analiza la foto y llena el JSON en español. "
    "Sé preciso y conservador: si algo no se ve, escribe 'no visible'. "
    "Si la foto muestra solo una etiqueta o un detalle, indícalo en notas y usa la categoria 'otro'."
)

def analizar(client, path):
    img = Image.open(path)
    for intento in range(3):
        try:
            r = client.models.generate_content(
                model=MODEL,
                contents=[img, PROMPT],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=SCHEMA,
                    temperature=0.2,
                ),
            )
            return json.loads(r.text)
        except Exception as e:
            if intento == 2: return {"error": str(e)[:200]}
            time.sleep(2 * (intento + 1))

def main():
    carpeta = Path(sys.argv[1] if len(sys.argv) > 1 else "jpg")
    base = sys.argv[2] if len(sys.argv) > 2 else "catalogo"
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    fotos = sorted(p for p in carpeta.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    filas = []
    for i, p in enumerate(fotos, 1):
        d = analizar(client, p)
        d = {"archivo": p.name, **d}
        filas.append(d)
        print(f"[{i}/{len(fotos)}] {p.name} -> {d.get('descripcion_corta', d.get('error'))}", flush=True)

    cols = ["archivo"] + list(SCHEMA["properties"].keys()) + ["error"]
    with open(f"{base}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(filas)
    with open(f"{base}.json", "w", encoding="utf-8") as f:
        json.dump(filas, f, ensure_ascii=False, indent=2)
    print(f"\nListo: {base}.csv y {base}.json ({len(filas)} fotos)")

if __name__ == "__main__":
    main()
