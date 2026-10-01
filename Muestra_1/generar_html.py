#!/usr/bin/env python3
"""Paso 5 - HTML. Genera closet.html: una tarjeta por prenda con maniqui, crops, y revision Aprobar / Se cambio la prenda."""
import json, html
from pathlib import Path

prendas = json.load(open("prendas.json", encoding="utf-8"))["prendas"]
datos = []
for p in prendas:
    aps = sorted(p["apariciones"], key=lambda a: a.get("es_detalle", False))
    datos.append({"id": p["id"], "categoria": p["categoria"], "descripcion": p["descripcion"],
                  "marca_talla": p.get("marca_talla", ""), "atributos": p.get("atributos", {}), "maniqui": f"maniqui/{p['id']}.jpg",
                  "maniqui_existe": Path(f"maniqui/{p['id']}.jpg").exists(),
                  "crops": [{"src": a["crop"], "foto": a["foto"], "detalle": a.get("es_detalle", False)} for a in aps]})

tarjetas = []
for d in datos:
    crops = "".join(f'<a href="{c["src"]}" target="_blank" title="{c["foto"]}{" (detalle)" if c["detalle"] else ""}">'
                    f'<img src="{c["src"]}" loading="lazy"></a>' for c in d["crops"])
    maniqui = f'<img src="{d["maniqui"]}">' if d["maniqui_existe"] else '<div class="sin">Sin imagen generada</div>'
    campos = "".join(f'<div><dt>{et}</dt><dd>{html.escape(d["atributos"].get(k, "") or "—")}</dd></div>'
                     for k, et in [("color", "Color"), ("estilo", "Estilo"), ("material", "Material"), ("detalles", "Detalles")])
    marca = f'<span class="marca">{html.escape(d["marca_talla"])}</span>' if d["marca_talla"] else ""
    tarjetas.append(f'''
<article class="card" data-id="{d["id"]}">
  <div class="maniqui">{maniqui}</div>
  <div class="crops">{crops}</div>
  <div class="meta">
    <div class="fila"><span class="id">{d["id"]}</span><span class="cat">{html.escape(d["categoria"])}</span>{marca}</div>
    <dl>{campos}</dl>
  </div>
  <div class="acciones">
    <button class="ok" onclick="marcar('{d["id"]}','aprobada')">Aprobar</button>
    <button class="no" onclick="marcar('{d["id"]}','cambiada')">Se cambió la prenda</button>
  </div>
</article>''')

pagina = f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Closet — revisión</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {{ --gris:#e5e5e5; --texto:#111; --sec:#666; --ok:#1f7a3a; --no:#b3261e; }}
  * {{ box-sizing:border-box }}
  body {{ margin:0; background:#fff; color:var(--texto); font:15px/1.45 -apple-system, "Helvetica Neue", Inter, Arial, sans-serif }}
  header {{ position:sticky; top:0; background:#fff; border-bottom:1px solid var(--gris); padding:14px 28px; display:flex; align-items:center; gap:24px; z-index:2 }}
  header h1 {{ font-size:18px; font-weight:600; margin:0 }}
  header .conteo {{ display:flex; gap:18px; color:var(--sec); font-size:14px }}
  header .conteo b {{ color:var(--texto) }}
  header .exportar {{ margin-left:auto }}
  button {{ font:inherit; border:1px solid var(--gris); background:#fff; border-radius:6px; padding:8px 14px; cursor:pointer }}
  button:hover {{ border-color:#999 }}
  main {{ display:grid; grid-template-columns:repeat(3,1fr); gap:24px; padding:28px; max-width:1500px; margin:0 auto }}
  @media (max-width:1000px) {{ main {{ grid-template-columns:repeat(2,1fr) }} }}
  @media (max-width:640px) {{ main {{ grid-template-columns:1fr; padding:16px }} }}
  .card {{ border:1px solid var(--gris); border-radius:10px; overflow:hidden; display:flex; flex-direction:column; background:#fff }}
  .card.aprobada {{ border-color:var(--ok); box-shadow:0 0 0 2px var(--ok) inset }}
  .card.cambiada {{ border-color:var(--no); box-shadow:0 0 0 2px var(--no) inset }}
  .maniqui {{ background:#f3f3f3; aspect-ratio:4/5; display:flex; align-items:center; justify-content:center }}
  .maniqui img {{ width:100%; height:100%; object-fit:contain }}
  .sin {{ color:var(--sec) }}
  .crops {{ display:flex; gap:6px; padding:10px 12px 0; overflow-x:auto }}
  .crops img {{ height:72px; width:auto; border-radius:4px; border:1px solid var(--gris); display:block }}
  .meta {{ padding:12px 14px 6px }}
  .fila {{ display:flex; gap:10px; align-items:baseline; margin-bottom:6px }}
  .id {{ font-weight:600 }}
  .cat {{ color:var(--sec); text-transform:capitalize }}
  .marca {{ color:var(--sec); font-size:13px; margin-left:auto }}
  dl {{ margin:0; display:grid; grid-template-columns:auto 1fr; row-gap:4px; column-gap:12px; font-size:14px }}
  dl div {{ display:contents }}
  dt {{ color:var(--sec); font-weight:500 }}
  dd {{ margin:0; color:#222 }}
  .acciones {{ display:flex; gap:8px; padding:10px 14px 14px; margin-top:auto }}
  .acciones button {{ flex:1 }}
  .card.aprobada .ok {{ background:var(--ok); color:#fff; border-color:var(--ok) }}
  .card.cambiada .no {{ background:var(--no); color:#fff; border-color:var(--no) }}
</style></head>
<body>
<header>
  <h1>Closet · Muestra 1</h1>
  <div class="conteo"><span>Prendas <b id="c-total">0</b></span><span>Aprobadas <b id="c-ok">0</b></span><span>Cambiadas <b id="c-no">0</b></span><span>Pendientes <b id="c-pend">0</b></span></div>
  <button class="exportar" onclick="exportar()">Exportar CSV</button>
</header>
<main>{"".join(tarjetas)}</main>
<script>
const DATOS = {json.dumps(datos, ensure_ascii=False)};
const KEY = "closet_muestra1_estado";
let estado = {{}};
try {{ estado = JSON.parse(localStorage.getItem(KEY) || "{{}}"); }} catch (e) {{ estado = {{}}; }}
function pintar() {{
  let ok = 0, no = 0;
  for (const d of DATOS) {{
    const card = document.querySelector(`.card[data-id="${{d.id}}"]`);
    card.classList.remove("aprobada", "cambiada");
    if (estado[d.id]) card.classList.add(estado[d.id]);
    if (estado[d.id] === "aprobada") ok++; else if (estado[d.id] === "cambiada") no++;
  }}
  document.getElementById("c-total").textContent = DATOS.length;
  document.getElementById("c-ok").textContent = ok;
  document.getElementById("c-no").textContent = no;
  document.getElementById("c-pend").textContent = DATOS.length - ok - no;
}}
function marcar(id, valor) {{
  estado[id] = estado[id] === valor ? undefined : valor;
  if (!estado[id]) delete estado[id];
  try {{ localStorage.setItem(KEY, JSON.stringify(estado)); }} catch (e) {{}}
  pintar();
}}
function csv(v) {{ v = String(v ?? ""); return /[",\\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; }}
function exportar() {{
  const filas = [["id", "categoria", "marca_talla", "color", "estilo", "material", "detalles", "estado", "maniqui", "fotos"]];
  for (const d of DATOS) filas.push([d.id, d.categoria, d.marca_talla, d.atributos.color, d.atributos.estilo, d.atributos.material, d.atributos.detalles, estado[d.id] || "pendiente", d.maniqui, d.crops.map(c => c.foto).join(" ")]);
  const blob = new Blob(["\\ufeff" + filas.map(f => f.map(csv).join(",")).join("\\n")], {{ type: "text/csv;charset=utf-8" }});
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "closet_revision.csv"; a.click();
}}
pintar();
</script>
</body></html>'''
Path("closet.html").write_text(pagina, encoding="utf-8")
print(f"closet.html: {len(datos)} tarjetas")
