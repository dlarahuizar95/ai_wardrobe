#!/usr/bin/env python3
"""Paso 4 - MANIQUI. Una imagen e-commerce por prenda con Gemini (gemini-2.5-flash-image) a partir de hasta 3 crops."""
import os, io, json, time, datetime, sys
from pathlib import Path
from PIL import Image
from google import genai
from google.genai import types

MODEL = "gemini-2.5-flash-image"
SALIDA = Path("maniqui"); SALIDA.mkdir(exist_ok=True)
LOG = Path("errores.log")
REINTENTOS = 2

PROMPT = ("Estas imágenes muestran la misma prenda desde distintos ángulos: {descripcion}. "
          "Recréala una sola vez con la técnica de maniquí invisible (ghost mannequin): la prenda aparece con volumen "
          "de cuerpo pero NO se ve ningún maniquí. Nada de cabeza, cuello, torso, brazos, cadera, piernas ni base: "
          "donde termina la prenda solo hay fondo. Fondo de estudio gris claro uniforme, luz suave, encuadre frontal "
          "completo, estilo e-commerce. Conserva exactamente color, patrón, manga, largo, cuello y proporciones. "
          "No agregues, quites ni cambies nada. Sin modelo, sin texto, sin accesorios extra.")

def log(msg):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S}  {msg}\n")

def referencias(prenda):
    aps = sorted(prenda["apariciones"], key=lambda a: a.get("es_detalle", False))  # completas primero
    return [Image.open(a["crop"]).convert("RGB") for a in aps[:3]]

def generar(client, prenda):
    texto = PROMPT.format(descripcion=prenda["descripcion"])
    if prenda.get("nota_maniqui"):
        texto += " DETALLE OBLIGATORIO: " + prenda["nota_maniqui"]
    partes = referencias(prenda) + [texto]
    resp = client.models.generate_content(
        model=MODEL, contents=partes,
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )
    for cand in resp.candidates or []:
        for part in cand.content.parts or []:
            if part.inline_data and part.inline_data.data:
                return Image.open(io.BytesIO(part.inline_data.data)).convert("RGB")
    raise RuntimeError(f"sin imagen en la respuesta: {getattr(resp, 'text', '')!r}")

def main():
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    prendas = json.load(open("prendas.json", encoding="utf-8"))["prendas"]
    if "--solo" in sys.argv:                      # python maniqui.py --solo P05
        solo = sys.argv[sys.argv.index("--solo") + 1]
        prendas = [p for p in prendas if p["id"] == solo]
    ok = fallo = saltado = 0
    for p in prendas:
        destino = SALIDA / f"{p['id']}.jpg"
        if destino.exists():
            print(f"{p['id']}  ya existe, salto"); saltado += 1; continue
        for intento in range(1, REINTENTOS + 2):
            try:
                img = generar(client, p)
                img.save(destino, quality=92)
                print(f"{p['id']}  OK  {img.size[0]}x{img.size[1]}  (intento {intento})"); ok += 1
                break
            except Exception as e:
                msg = f"{p['id']} intento {intento}: {type(e).__name__}: {str(e)[:300]}"
                print("  ", msg); log(msg)
                if intento <= REINTENTOS: time.sleep(4 * intento)
        else:
            fallo += 1
    print(f"\nGeneradas {ok}, saltadas {saltado}, fallidas {fallo} -> {SALIDA}/")

if __name__ == "__main__":
    main()
