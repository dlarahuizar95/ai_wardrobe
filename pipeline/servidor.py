#!/usr/bin/env python3
"""Servidor local para mi_closet.html. Correr desde la raiz: python pipeline/servidor.py  (o ./closet.sh)
- Sirve mi_closet.html en http://localhost:8765
- POST /api/revision  {id, estado?, material?, comentario?}  -> guarda en Supabase con la service key y en prendas.json del lote
- POST /api/corregir  {id}  -> regenera el maniqui de esa prenda usando el comentario como nota, lo sube y devuelve la URL nueva
La service key nunca sale de esta maquina."""
import os, json, subprocess, datetime, sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import httpx

RAIZ = Path(__file__).resolve().parent.parent
URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ["SUPABASE_SERVICE_KEY"]
H = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}
PY = sys.executable
PUERTO = 8765

def carpeta_lote(lote):
    for d in RAIZ.iterdir():
        if d.is_dir() and d.name.lower() == lote: return d
    raise FileNotFoundError(f"no hay carpeta para el lote {lote}")

def patch_prenda(pid, cambios):
    cambios["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    r = httpx.patch(f"{URL}/rest/v1/prendas?id=eq.{pid}", headers=H, json=cambios, timeout=30)
    r.raise_for_status()
    return r.json()[0]

def actualizar_json_lote(lote, codigo, **campos):
    ruta = carpeta_lote(lote) / "prendas.json"
    d = json.load(open(ruta, encoding="utf-8"))
    p = next(p for p in d["prendas"] if p["id"] == codigo)
    p.update(campos)
    json.dump(d, open(ruta, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def revision(body):
    pid = body["id"]; lote, codigo = pid.split("-", 1)
    cambios = {k: body[k] for k in ("estado", "material", "comentario") if k in body}
    if "material" in cambios and not cambios["material"]: cambios["material"] = None
    cambios["revisado_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    fila = patch_prenda(pid, cambios)
    local = {}
    if "estado" in cambios: local["estado"] = cambios["estado"]
    if "comentario" in cambios: local["comentario"] = cambios["comentario"]
    if "material" in cambios: local["composicion"] = cambios["material"] or ""
    if local:
        extra = {k: v for k, v in local.items() if k != "composicion"}
        d_ruta = carpeta_lote(lote) / "prendas.json"
        d = json.load(open(d_ruta, encoding="utf-8"))
        p = next(p for p in d["prendas"] if p["id"] == codigo)
        p.update(extra)
        if "composicion" in local: p.setdefault("atributos", {})["composicion"] = local["composicion"]
        json.dump(d, open(d_ruta, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return fila

def corregir(body):
    pid = body["id"]; lote, codigo = pid.split("-", 1)
    carpeta = carpeta_lote(lote)
    r = httpx.get(f"{URL}/rest/v1/prendas?id=eq.{pid}&select=comentario,version", headers=H, timeout=30); r.raise_for_status()
    fila = r.json()[0]
    comentario = (fila.get("comentario") or "").strip()
    if not comentario: raise ValueError("Escribe primero qué tiene mal el maniquí.")
    # nota para el prompt + regenerar solo esa prenda
    actualizar_json_lote(lote, codigo, nota_maniqui=comentario)
    img = carpeta / "maniqui" / f"{codigo}.jpg"
    if img.exists():
        hist = carpeta / "maniqui" / "anteriores"; hist.mkdir(exist_ok=True)
        img.rename(hist / f"{codigo}_v{fila.get('version', 1)}.jpg")
    res = subprocess.run([PY, "-W", "ignore", str(RAIZ / "pipeline" / "maniqui.py"), "--solo", codigo],
                         cwd=carpeta, capture_output=True, text=True, env=os.environ, timeout=300)
    if not img.exists():
        raise RuntimeError("Gemini no devolvió imagen: " + (res.stdout + res.stderr)[-400:])
    destino = f"{lote}/maniqui/{codigo}.jpg"
    up = httpx.post(f"{URL}/storage/v1/object/closet/{destino}", content=img.read_bytes(), timeout=60,
                    headers={"apikey": KEY, "Authorization": f"Bearer {KEY}", "x-upsert": "true", "Content-Type": "image/jpeg"})
    up.raise_for_status()
    version = int(fila.get("version", 1)) + 1
    fila = patch_prenda(pid, {"version": version, "estado": "pendiente", "revisado_at": datetime.datetime.now(datetime.timezone.utc).isoformat()})
    actualizar_json_lote(lote, codigo, estado="pendiente")
    # regenerar el closet.html del lote para que quede consistente
    subprocess.run([PY, "-W", "ignore", str(RAIZ / "pipeline" / "generar_html.py")], cwd=carpeta, capture_output=True, env=os.environ)
    return fila

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *a): print(f"{self.command} {self.path} -> {a[1] if len(a) > 1 else ''}")
    def _json(self, code, obj):
        data = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        if self.path in ("/", "/mi_closet.html"):
            data = (RAIZ / "mi_closet.html").read_bytes()
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
        else:
            self._json(404, {"error": "no existe"})
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
    print(f"Mi closet en http://localhost:{PUERTO}  (Ctrl+C para parar)")
    HTTPServer(("127.0.0.1", PUERTO), Handler).serve_forever()
