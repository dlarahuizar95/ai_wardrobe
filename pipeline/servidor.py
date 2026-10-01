#!/usr/bin/env python3
"""Servidor local para mi_closet.html. Correr desde la raiz: python3 server.py  (o ./closet.sh)
- GET  /                 sirve mi_closet.html en http://localhost:8765
- GET  /api/revision     devuelve revision.json (espejo local de todo lo revisado)
- POST /api/revision     {id, ...campos}  -> Supabase (service key) + revision.json + prendas.json del lote
- POST /api/corregir     {id}  -> regenera el maniqui con el comentario como nota, lo sube y devuelve la fila
La service key nunca sale de esta maquina. Si Supabase falla, el cambio queda en revision.json y se reporta."""
import os, json, subprocess, datetime, sys, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import httpx

RAIZ = Path(__file__).resolve().parent.parent
URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ["SUPABASE_SERVICE_KEY"]
H = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}
PY = sys.executable
PUERTO = 8765
REVISION = RAIZ / "revision.json"
CAMPOS = {"estado", "material", "comentario", "tipo", "nombre", "fit", "misma_que", "favorito", "guardado", "color_base", "talla", "marca"}
LOCK = threading.Lock()

def ahora(): return datetime.datetime.now(datetime.timezone.utc).isoformat()

def leer_revision():
    try: return json.load(open(REVISION, encoding="utf-8"))
    except Exception: return {}

def guardar_revision(pid, cambios):
    with LOCK:
        rev = leer_revision()
        fila = rev.setdefault(pid, {}); fila.update(cambios); fila["revisado_at"] = ahora()
        json.dump(rev, open(REVISION, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def carpeta_lote(lote):
    for d in RAIZ.iterdir():
        if d.is_dir() and d.name.lower() == lote: return d
    raise FileNotFoundError(f"no hay carpeta para el lote {lote}")

def actualizar_json_lote(lote, codigo, cambios):
    ruta = carpeta_lote(lote) / "prendas.json"
    d = json.load(open(ruta, encoding="utf-8"))
    p = next(p for p in d["prendas"] if p["id"] == codigo)
    for k, v in cambios.items():
        if k == "material": p.setdefault("atributos", {})["composicion"] = v or ""
        elif k in ("tipo", "color_base", "talla", "marca"): p.setdefault("atributos", {})[k] = v or ""
        else: p[k] = v
    json.dump(d, open(ruta, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def patch_prenda(pid, cambios):
    """PATCH a Supabase. Si una columna aun no existe (PGRST204), la quita y reintenta con el resto;
    lo omitido queda en revision.json y se reporta en _faltan."""
    cambios = {**cambios, "updated_at": ahora()}; faltan = []
    for _ in range(len(cambios) + 1):
        r = httpx.patch(f"{URL}/rest/v1/prendas?id=eq.{pid}", headers=H, json=cambios, timeout=30)
        if r.status_code < 300: break
        try: err = r.json()
        except Exception: err = {}
        if err.get("code") == "PGRST204":
            import re
            m = re.search(r"'(\w+)' column", err.get("message", ""))
            if m and m.group(1) in cambios:
                faltan.append(m.group(1)); cambios.pop(m.group(1)); continue
        raise RuntimeError(f"Supabase {r.status_code}: {r.text[:160]}")
    filas = r.json()
    if not filas: raise RuntimeError("Supabase no encontro la prenda " + pid)
    fila = filas[0]
    if faltan: fila["_faltan"] = faltan
    return fila

def revision(body):
    pid = body["id"]; lote, codigo = pid.split("-", 1)
    cambios = {k: body[k] for k in CAMPOS if k in body}
    for k in ("material", "nombre", "misma_que", "comentario", "tipo", "marca", "talla", "color_base"):
        if k in cambios and isinstance(cambios[k], str) and not cambios[k].strip(): cambios[k] = None
    if not cambios: raise ValueError("nada que guardar")
    guardar_revision(pid, cambios)
    try: actualizar_json_lote(lote, codigo, cambios)
    except Exception as e: print("  prendas.json:", e)
    try:
        fila = patch_prenda(pid, {**cambios, "revisado_at": ahora()})
        faltan = fila.pop("_faltan", [])
        if faltan: return {**fila, **{k: cambios[k] for k in faltan}, "_supabase": False, "_error": "columnas sin crear en Supabase: " + ", ".join(faltan) + " (corre supabase/005_revision_completa.sql)"}
        return {**fila, "_supabase": True}
    except Exception as e:
        print("  supabase:", e)
        return {"id": pid, **cambios, "_supabase": False, "_error": str(e)[:200]}

def corregir(body):
    pid = body["id"]; lote, codigo = pid.split("-", 1)
    carpeta = carpeta_lote(lote)
    r = httpx.get(f"{URL}/rest/v1/prendas?id=eq.{pid}&select=comentario,version", headers=H, timeout=30); r.raise_for_status()
    fila = r.json()[0]
    comentario = (fila.get("comentario") or leer_revision().get(pid, {}).get("comentario") or "").strip()
    if not comentario: raise ValueError("Escribe primero qué tiene mal el maniquí.")
    actualizar_json_lote(lote, codigo, {"nota_maniqui": comentario})
    img = carpeta / "maniqui" / f"{codigo}.jpg"
    if img.exists():
        hist = carpeta / "maniqui" / "anteriores"; hist.mkdir(exist_ok=True)
        img.rename(hist / f"{codigo}_v{fila.get('version', 1)}.jpg")
    res = subprocess.run([PY, "-W", "ignore", str(RAIZ / "pipeline" / "maniqui.py"), "--solo", codigo],
                         cwd=carpeta, capture_output=True, text=True, env=os.environ, timeout=300)
    if not img.exists():
        raise RuntimeError("Gemini no devolvió imagen: " + (res.stdout + res.stderr)[-400:])
    up = httpx.post(f"{URL}/storage/v1/object/closet/{lote}/maniqui/{codigo}.jpg", content=img.read_bytes(), timeout=60,
                    headers={"apikey": KEY, "Authorization": f"Bearer {KEY}", "x-upsert": "true", "Content-Type": "image/jpeg"})
    up.raise_for_status()
    version = int(fila.get("version", 1)) + 1
    fila = patch_prenda(pid, {"version": version, "estado": "pendiente", "revisado_at": ahora()})
    guardar_revision(pid, {"estado": "pendiente", "version": version})
    actualizar_json_lote(lote, codigo, {"estado": "pendiente"})
    subprocess.run([PY, "-W", "ignore", str(RAIZ / "pipeline" / "generar_html.py")], cwd=carpeta, capture_output=True, env=os.environ)
    return {**fila, "_supabase": True}

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *a): print(f"{self.command} {self.path} -> {a[1] if len(a) > 1 else ''}")
    def _json(self, code, obj):
        data = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        if self.path in ("/", "/mi_closet.html", "/closet.html"):
            data = (RAIZ / "mi_closet.html").read_bytes()
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
        elif self.path == "/api/revision": self._json(200, leer_revision())
        else: self._json(404, {"error": "no existe"})
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(n) or b"{}")
        try:
            if self.path == "/api/revision": self._json(200, revision(body))
            elif self.path == "/api/corregir": self._json(200, corregir(body))
            else: self._json(404, {"error": "no existe"})
        except Exception as e:
            self._json(400, {"error": str(e)[:500]})

if __name__ == "__main__":
    print(f"Mi closet en http://localhost:{PUERTO}  (Ctrl+C para parar). Espejo local: {REVISION.name}")
    HTTPServer(("127.0.0.1", PUERTO), Handler).serve_forever()
