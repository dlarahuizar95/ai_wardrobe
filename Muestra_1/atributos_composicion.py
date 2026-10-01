#!/usr/bin/env python3
"""Paso 5b - COMPOSICION. Lee las fotos de etiqueta de cada prenda y, SOLO si se ve la composicion con porcentajes,
elige la opcion mas cercana de materiales.MATERIALES. Si no se ve, deja ''. Escribe atributos.composicion en prendas.json."""
import os, json
from PIL import Image
from google import genai
from google.genai import types
from materiales import MATERIALES

MODEL = "gemini-3.6-flash"
SCHEMA = {"type": "object", "properties": {
    "visible": {"type": "boolean", "description": "true solo si una etiqueta muestra composicion textil con porcentajes"},
    "texto_etiqueta": {"type": "string", "description": "la composicion tal cual se lee, '' si no se ve"},
    "opcion": {"type": "string", "enum": MATERIALES + ["Sin dato"], "description": "opcion mas cercana de la lista; 'Sin dato' si visible es false"},
}, "required": ["visible", "texto_etiqueta", "opcion"]}
PROMPT = ("Estas son fotos de una prenda y sus etiquetas. Busca una etiqueta de COMPOSICION TEXTIL con porcentajes "
          "(ej. '95% algodon 5% elastano'). Si la ves, transcribela y elige la opcion mas cercana de la lista. "
          "Si NO se ve ninguna composicion con porcentajes, responde visible=false y opcion='Sin dato'. No adivines por la apariencia.")

def main():
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    datos = json.load(open("prendas.json", encoding="utf-8"))
    for p in datos["prendas"]:
        at = p.setdefault("atributos", {})
        if "composicion" in at:
            print(f"{p['id']}  ya revisada ({at['composicion'] or 'en blanco'}), salto"); continue
        detalles = [a for a in p["apariciones"] if a.get("es_detalle")] or p["apariciones"][:1]
        imgs = [Image.open(a["crop"]).convert("RGB") for a in detalles[:4]]
        resp = client.models.generate_content(model=MODEL, contents=imgs + [PROMPT],
            config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=SCHEMA))
        r = json.loads(resp.text)
        at["composicion"] = r["opcion"] if r["visible"] and r["opcion"] in MATERIALES else ""
        at["composicion_etiqueta"] = r["texto_etiqueta"] if r["visible"] else ""
        print(f"{p['id']}  visible={r['visible']}  -> {at['composicion'] or '(en blanco)'}  {r['texto_etiqueta'][:60]}")
    json.dump(datos, open("prendas.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
