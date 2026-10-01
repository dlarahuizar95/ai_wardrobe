#!/usr/bin/env python3
"""Paso 5a - ATRIBUTOS. Convierte la descripcion de cada prenda en campos: color, estilo, material, detalles. Escribe prendas.json."""
import os, json
from PIL import Image
from google import genai
from google.genai import types

MODEL = "gemini-3.6-flash"
SCHEMA = {"type": "object", "properties": {
    "color": {"type": "string", "description": "color(es) y patron, ej. 'Negro con estampado barroco blanco'"},
    "estilo": {"type": "string", "description": "tipo de prenda y corte, ej. 'Palazzo de tiro alto, pierna ancha'"},
    "material": {"type": "string", "description": "tela o material aparente, ej. 'Piel sintetica con forro afelpado'"},
    "detalles": {"type": "string", "description": "manga, largo, cuello, cierres, adornos; corto"},
}, "required": ["color", "estilo", "material", "detalles"]}

PROMPT = ("Prenda: {descripcion}\nCategoria: {categoria}\n"
          "Con la descripcion y la foto, llena los campos en español, cada uno en una frase corta sin punto final, "
          "empezando con mayuscula. Solo lo que se ve o se describe; si no se sabe el material, pon lo aparente.")

def main():
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    datos = json.load(open("prendas.json", encoding="utf-8"))
    for p in datos["prendas"]:
        if p.get("atributos"):
            print(f"{p['id']}  ya tiene atributos, salto"); continue
        foto = next((a for a in p["apariciones"] if not a.get("es_detalle")), p["apariciones"][0])
        resp = client.models.generate_content(
            model=MODEL,
            contents=[Image.open(foto["crop"]).convert("RGB"), PROMPT.format(**p)],
            config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=SCHEMA),
        )
        p["atributos"] = json.loads(resp.text)
        print(f"{p['id']}  " + " | ".join(f"{k}: {v}" for k, v in p["atributos"].items()))
    json.dump(datos, open("prendas.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
