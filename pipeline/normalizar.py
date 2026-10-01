#!/usr/bin/env python3
"""Normaliza marca, talla, color_base y tipo de TODAS las prendas con Gemini (texto, en lotes de 60) y escribe
en Supabase (service key) y en el prendas.json de cada lote. Reanudable: salta lo ya normalizado en el json local.
Correr desde la raiz: python pipeline/normalizar.py  [--solo-subir]"""
import os, json, sys, time
from pathlib import Path
import httpx
from google import genai
from google.genai import types
from taxonomia import TIPOS, COLORES, TALLAS

RAIZ = Path(__file__).resolve().parent.parent
URL = os.environ["SUPABASE_URL"].rstrip("/"); KEY = os.environ["SUPABASE_SERVICE_KEY"]
H = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "Prefer": "return=minimal"}
MODEL = "gemini-3.6-flash"
SCHEMA = {"type": "object", "properties": {"prendas": {"type": "array", "items": {"type": "object", "properties": {
    "id": {"type": "string"},
    "tipo": {"type": "string", "enum": TIPOS},
    "color_base": {"type": "string", "enum": COLORES},
    "marca": {"type": "string", "description": "marca con mayusculas normales (Zara, Mango, Uniqlo, Stradivarius, Tommy Hilfiger); MNG=Mango; '' si no hay marca"},
    "talla": {"type": "string", "description": "XS/S/M/L/XL/XXL si aparece una letra; si solo hay numeros usa el MEX; si no hay MEX el primer numero; '' si no hay"},
}, "required": ["id", "tipo", "color_base", "marca", "talla"]}}}, "required": ["prendas"]}
PROMPT = ("Normaliza estas prendas de un closet. Para cada id devuelve tipo (de la lista), color_base (la familia de color "
          "dominante; 'multicolor' solo si hay 3+ colores fuertes o estampado multicolor; un estampado de 2 colores va con el "
          "color de fondo), marca y talla limpias. No inventes marca ni talla: '' si no estan en marca_talla.\n\n")

def lotes_locales():
    return {d.name.lower(): d for d in RAIZ.iterdir() if d.is_dir() and (d / "prendas.json").exists()}

def main():
    solo_subir = "--solo-subir" in sys.argv
    r = httpx.get(f"{URL}/rest/v1/prendas?select=id,lote,codigo,categoria,marca_talla,color,descripcion&limit=1000&order=id", headers=H); r.raise_for_status()
    filas = r.json()
    locales = lotes_locales(); jsons = {}
    def local(lote):
        if lote not in jsons: jsons[lote] = json.load(open(locales[lote] / "prendas.json", encoding="utf-8"))
        return jsons[lote]
    def atrib(f):
        p = next(p for p in local(f["lote"])["prendas"] if p["id"] == f["codigo"]); return p.setdefault("atributos", {})
    pendientes = [f for f in filas if not atrib(f).get("tipo")]
    print(f"{len(filas)} prendas, {len(pendientes)} por normalizar")
    if pendientes and not solo_subir:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        for i in range(0, len(pendientes), 60):
            chunk = pendientes[i:i+60]
            texto = PROMPT + "\n".join(json.dumps({k: f[k] for k in ("id", "categoria", "marca_talla", "color", "descripcion")}, ensure_ascii=False) for f in chunk)
            for intento in range(4):
                try:
                    resp = client.models.generate_content(model=MODEL, contents=texto,
                        config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=SCHEMA, temperature=0))
                    res = {x["id"]: x for x in json.loads(resp.text)["prendas"]}; break
                except Exception as e:
                    if intento == 3: raise
                    print("  reintento:", str(e)[:80]); time.sleep(5 * (intento + 1))
            for f in chunk:
                x = res.get(f["id"])
                if not x: print("  sin respuesta para", f["id"]); continue
                a = atrib(f); a.update({"tipo": x["tipo"], "color_base": x["color_base"], "marca": x["marca"].strip(), "talla": x["talla"].strip().upper()})
            print(f"  normalizadas {min(i+60, len(pendientes))}/{len(pendientes)}")
        for lote, d in jsons.items():
            json.dump(d, open(locales[lote] / "prendas.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    # subir a Supabase
    ok = 0
    for f in filas:
        a = atrib(f)
        if not a.get("tipo"): continue
        r = httpx.patch(f"{URL}/rest/v1/prendas?id=eq.{f['id']}", headers=H, timeout=30,
                        json={"tipo": a["tipo"], "color_base": a["color_base"], "marca": a["marca"] or None, "talla": a["talla"] or None})
        if r.status_code >= 300: sys.exit(f"Supabase {r.status_code} en {f['id']}: {r.text[:200]}  (¿ya corriste supabase/004_catalogo.sql?)")
        ok += 1
    print(f"{ok} prendas actualizadas en Supabase")

if __name__ == "__main__":
    main()
