#!/usr/bin/env python3
"""Paso 2 - AGRUPACION. Lee detecciones.json, agrupa detecciones en prendas fisicas y escribe prendas.json."""
import os, json, time
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image, ImageOps

MODEL = "gemini-3.6-flash"
CARPETA = Path("jpg")

# Gemini devolvio [y_min, x_min, y_max, x_max] sobre la imagen SIN rotar (verificado visualmente).
# Convertimos a [x_min, y_min, x_max, y_max] sobre la imagen ya rotada segun EXIF, que es la que se recorta.
def bbox_a_display(b, orient):
    y0, x0, y1, x1 = b
    if orient == 6:   return [1 - y1, x0, 1 - y0, x1]   # rotar 90 CW
    if orient == 8:   return [y0, 1 - x1, y1, 1 - x0]   # rotar 90 CCW
    if orient == 3:   return [1 - x1, 1 - y1, 1 - x0, 1 - y0]
    return [x0, y0, x1, y1]

SCHEMA = {
    "type": "object",
    "properties": {
        "prendas": {"type": "array", "items": {"type": "object", "properties": {
            "categoria": {"type": "string"},
            "descripcion": {"type": "string", "description": "consolidada de todas sus apariciones: color, patron, manga, largo, cuello, material, detalles"},
            "marca_talla": {"type": "string", "description": "de las etiquetas leidas; '' si no hay"},
            "detecciones": {"type": "array", "items": {"type": "object", "properties": {
                "foto": {"type": "string"}, "n": {"type": "integer"}}, "required": ["foto", "n"]}},
            "posible_duplicado_de": {"type": "integer", "description": "indice (1-based) de otra prenda de esta lista si dudas que sea la misma; 0 si no"},
            "dudas": {"type": "string", "description": "por que dudaste; '' si nada"},
        }, "required": ["categoria", "descripcion", "marca_talla", "detecciones", "posible_duplicado_de", "dudas"]}},
        "descartadas": {"type": "array", "items": {"type": "object", "properties": {
            "foto": {"type": "string"}, "n": {"type": "integer"}, "motivo": {"type": "string"}},
            "required": ["foto", "n", "motivo"]}},
    },
    "required": ["prendas", "descartadas"],
}

PROMPT = """Te doy fotos de un closet y la lista de prendas detectadas en cada una (foto + numero n).
Tarea: agrupar las detecciones que sean LA MISMA PRENDA FISICA (mismo color, patron, categoria, detalles).

Reglas:
1. Las fotos van en orden de captura: fotos consecutivas suelen ser la misma prenda desde otro angulo o un detalle (etiqueta, pretina). Asigna cada foto de detalle a la prenda de las fotos vecinas si el color y material coinciden.
2. DESCARTA las detecciones que sean objetos de fondo y no la prenda fotografiada: prendas dobladas/amontonadas en la orilla, parcialmente visibles, muy pequenas, cojines, cobijas. Ponlas en 'descartadas' con motivo.
3. Si dudas si dos grupos son la misma prenda, NO los juntes: dejalos separados y marca posible_duplicado_de con el indice del otro.
4. Toda deteccion debe quedar en exactamente una prenda o en descartadas. No inventes detecciones.
5. La categoria final debe ser una de: top, camisa, blusa, sweater, cardigan, blazer, chamarra, abrigo, vestido, falda, pantalon, jeans, shorts, zapatos, bolsa, cinturon, accesorio, incierto. Si las fotos de una misma prenda discrepan (p.ej. vestido vs pantalon), elige viendo las fotos y explica en dudas.

DETECCIONES:
"""

def main():
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    fotos = json.load(open("detecciones.json", encoding="utf-8"))

    # contenido: lista de detecciones en texto + todas las fotos etiquetadas
    lineas, partes = [], []
    for f in fotos:
        for d in f["prendas"]:
            if "error" in d: continue
            lineas.append(f"- {f['foto']} n={d['n']}: {d['categoria']}, {d['color_principal']}, "
                          f"{'DETALLE, ' if d.get('es_detalle') else ''}{d['descripcion']}"
                          + (f" [etiqueta: {d['etiqueta_texto']}]" if d.get("etiqueta_texto") else ""))
    partes.append(PROMPT + "\n".join(lineas) + "\n\nFOTOS (en orden):")
    for f in fotos:
        im = ImageOps.exif_transpose(Image.open(CARPETA / f["foto"])).convert("RGB")
        im.thumbnail((640, 640))
        partes += [f"\n{f['foto']}:", im]

    for intento in range(3):
        try:
            r = client.models.generate_content(model=MODEL, contents=partes,
                config=types.GenerateContentConfig(response_mime_type="application/json",
                                                   response_schema=SCHEMA, temperature=0.1))
            res = json.loads(r.text); break
        except Exception as e:
            if intento == 2: raise
            print("reintento:", str(e)[:120]); time.sleep(3 * (intento + 1))

    # indexar detecciones originales para adjuntar bbox convertido
    idx = {(f["foto"], d["n"]): (f, d) for f in fotos for d in f["prendas"] if "n" in d}
    prendas = []
    for i, p in enumerate(res["prendas"], 1):
        aps = []
        for det in p["detecciones"]:
            k = (det["foto"], det["n"])
            if k not in idx: continue
            f, d = idx[k]
            orient = Image.open(CARPETA / f["foto"]).getexif().get(274, 1)
            aps.append({"foto": f["foto"], "n": d["n"], "bbox": [round(v, 4) for v in bbox_a_display(d["bbox"], orient)],
                        "es_detalle": d.get("es_detalle", False), "descripcion_foto": d["descripcion"]})
        prendas.append({"id": f"P{i:02d}", "categoria": p["categoria"], "descripcion": p["descripcion"],
                        "marca_talla": p["marca_talla"],
                        "posible_duplicado_de": f"P{p['posible_duplicado_de']:02d}" if p["posible_duplicado_de"] else "",
                        "dudas": p["dudas"], "apariciones": aps})
    salida = {"prendas": prendas, "descartadas": res["descartadas"]}
    json.dump(salida, open("prendas.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # verificacion: ninguna deteccion perdida ni repetida
    usadas = [(a["foto"], a["n"]) for p in prendas for a in p["apariciones"]] + [(d["foto"], d["n"]) for d in res["descartadas"]]
    faltan = set(idx) - set(usadas); repes = {u for u in usadas if usadas.count(u) > 1}
    if faltan: print("AVISO detecciones sin asignar:", sorted(faltan))
    if repes:  print("AVISO detecciones repetidas:", sorted(repes))

    print(f"\n{'ID':4} {'CATEGORIA':10} {'FOTOS':>5}  {'MARCA/TALLA':14} DESCRIPCION")
    for p in prendas:
        print(f"{p['id']:4} {p['categoria']:10} {len(p['apariciones']):>5}  {p['marca_talla'][:14]:14} {p['descripcion'][:90]}")
        if p["posible_duplicado_de"] or p["dudas"]:
            print(f"     ! dup_de={p['posible_duplicado_de'] or '-'}  {p['dudas']}")
    print(f"\nDescartadas ({len(res['descartadas'])}):")
    for d in res["descartadas"]: print(f"  {d['foto']} n={d['n']}: {d['motivo']}")
    print("\nListo: prendas.json")

if __name__ == "__main__":
    main()
