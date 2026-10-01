#!/usr/bin/env python3
"""Pagina acumulada de TODO el closet con revision en vivo. Lee prendas desde Supabase (llave publica) y escribe
a traves del servidor local (pipeline/servidor.py), que usa la service key. Correr desde la raiz o con ./closet.sh"""
import os, json
from pathlib import Path
from materiales import MATERIALES

URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ["SUPABASE_PUBLISHABLE_KEY"]

pagina = r'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Mi closet</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root { --gris:#e5e5e5; --texto:#111; --sec:#666; --ok:#1f7a3a; --no:#b3261e; --warn:#8a6d00; }
  * { box-sizing:border-box }
  body { margin:0; background:#fff; color:var(--texto); font:15px/1.45 -apple-system, "Helvetica Neue", Inter, Arial, sans-serif }
  header { position:sticky; top:0; background:#fff; border-bottom:1px solid var(--gris); padding:12px 28px; display:flex; align-items:center; gap:18px; flex-wrap:wrap; z-index:2 }
  header h1 { font-size:18px; font-weight:600; margin:0 }
  .conteo { display:flex; gap:16px; color:var(--sec); font-size:14px }
  .conteo b { color:var(--texto) }
  .filtros { display:flex; gap:8px; margin-left:auto }
  select, button, textarea { font:inherit; font-size:14px; border:1px solid var(--gris); background:#fff; border-radius:6px; padding:7px 10px; color:#222 }
  button { cursor:pointer } button:hover { border-color:#999 } button:disabled { opacity:.5; cursor:default }
  #aviso { display:none; background:#fff6d6; color:var(--warn); padding:10px 28px; font-size:14px; border-bottom:1px solid #f0e2a0 }
  main { display:grid; grid-template-columns:repeat(4,1fr); gap:20px; padding:24px 28px; max-width:1700px; margin:0 auto }
  @media (max-width:1200px) { main { grid-template-columns:repeat(3,1fr) } }
  @media (max-width:900px) { main { grid-template-columns:repeat(2,1fr) } }
  @media (max-width:560px) { main { grid-template-columns:1fr; padding:16px } }
  .card { border:1px solid var(--gris); border-radius:10px; overflow:hidden; display:flex; flex-direction:column; background:#fff; position:relative }
  .card.aprobada { box-shadow:0 0 0 2px var(--ok) inset }
  .card.cambiada { box-shadow:0 0 0 2px var(--no) inset }
  .pill { position:absolute; top:10px; left:10px; font-size:12px; padding:3px 8px; border-radius:99px; background:#fff; border:1px solid var(--gris); color:var(--sec) }
  .card.aprobada .pill { background:var(--ok); color:#fff; border-color:var(--ok) }
  .card.cambiada .pill { background:var(--no); color:#fff; border-color:var(--no) }
  .maniqui { background:#f3f3f3; aspect-ratio:4/5; display:flex; align-items:center; justify-content:center; position:relative }
  .maniqui img { width:100%; height:100%; object-fit:contain }
  .maniqui .velo { position:absolute; inset:0; background:rgba(255,255,255,.75); display:none; align-items:center; justify-content:center; color:var(--sec); font-size:14px }
  .card.trabajando .velo { display:flex }
  .crops { display:flex; gap:5px; padding:8px 10px 0; overflow-x:auto }
  .crops img { height:60px; width:auto; border-radius:4px; border:1px solid var(--gris); display:block }
  .meta { padding:10px 12px 4px }
  .fila { display:flex; gap:8px; align-items:baseline; margin-bottom:6px; font-size:13px }
  .id { font-weight:600; font-size:14px } .cat { color:var(--sec); text-transform:capitalize } .lote { color:var(--sec); margin-left:auto } .marca { color:var(--sec) }
  dl { margin:0; display:grid; grid-template-columns:auto 1fr; row-gap:3px; column-gap:10px; font-size:13px }
  dl div { display:contents } dt { color:var(--sec) } dd { margin:0; color:#222 }
  dd select { width:100%; padding:3px 6px; font-size:13px }
  .comentario { margin:8px 12px 0; font-size:13px; color:var(--no); background:#fdf1f0; border-radius:6px; padding:6px 8px; display:none }
  .card.cambiada .comentario { display:block }
  .acciones { display:flex; gap:6px; padding:8px 12px 12px; margin-top:auto }
  .acciones button { flex:1; font-size:13px; padding:6px 8px }
  .card.aprobada .ok { background:var(--ok); color:#fff; border-color:var(--ok) }
  .card.cambiada .no { background:var(--no); color:#fff; border-color:var(--no) }
  .corregir { background:#222; color:#fff; border-color:#222 }
  .form { display:none; padding:0 12px 12px; gap:6px; flex-direction:column }
  .card.editando .form { display:flex } .card.editando .acciones { display:none }
  .form textarea { width:100%; min-height:64px; resize:vertical }
  .form .botones { display:flex; gap:6px } .form .botones button { flex:1; font-size:13px }
  #estado { padding:40px; color:var(--sec); grid-column:1/-1; text-align:center }
  .msg { font-size:12px; color:var(--sec); padding:0 12px 8px; min-height:16px }
</style></head>
<body>
<header>
  <h1>Mi closet</h1>
  <div class="conteo"><span>Prendas <b id="c-total">0</b></span><span>Aprobadas <b id="c-ok">0</b></span><span>Cambiadas <b id="c-no">0</b></span><span>Pendientes <b id="c-pend">0</b></span></div>
  <div class="filtros">
    <select id="f-lote"><option value="">Todos los lotes</option></select>
    <select id="f-cat"><option value="">Todas las categorías</option></select>
    <select id="f-est"><option value="">Todos los estados</option><option value="pendiente">Pendientes</option><option value="aprobada">Aprobadas</option><option value="cambiada">Cambiadas</option></select>
    <button onclick="exportar()">Exportar CSV</button>
  </div>
</header>
<div id="aviso">Estás viendo el archivo directo. Para aprobar, comentar y corregir, ábrelo con <code>./closet.sh</code> (http://localhost:8765).</div>
<main id="grid"><div id="estado">Cargando desde Supabase…</div></main>
<script>
const URL_SB = "__URL__", KEY_SB = "__KEY__";
const MATERIALES = __MATERIALES__;
const H = { "apikey": KEY_SB, "Authorization": "Bearer " + KEY_SB };
const EN_VIVO = location.protocol.startsWith("http");
if (!EN_VIVO) document.getElementById("aviso").style.display = "block";
let prendas = [];
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const porId = id => prendas.find(p => p.id === id);
const card = id => document.querySelector(`.card[data-id="${CSS.escape(id)}"]`);

async function cargar() {
  const [rp, ra] = await Promise.all([
    fetch(`${URL_SB}/rest/v1/prendas?select=*&order=lote,codigo`, { headers: H }),
    fetch(`${URL_SB}/rest/v1/apariciones?select=prenda_id,foto,n,es_detalle,crop_url&order=prenda_id,es_detalle,foto`, { headers: H }),
  ]);
  if (!rp.ok || !ra.ok) { document.getElementById("estado").textContent = "No se pudo leer Supabase (" + rp.status + "/" + ra.status + ")"; return; }
  prendas = await rp.json();
  const aps = await ra.json();
  for (const p of prendas) p.crops = aps.filter(a => a.prenda_id === p.id);
  const lotes = [...new Set(prendas.map(p => p.lote))], cats = [...new Set(prendas.map(p => p.categoria))].sort();
  document.getElementById("f-lote").innerHTML += lotes.map(l => `<option value="${esc(l)}">${esc(l)}</option>`).join("");
  document.getElementById("f-cat").innerHTML += cats.map(c => `<option value="${esc(c)}">${esc(c)}</option>`).join("");
  pintar();
}
function visibles() {
  const fl = document.getElementById("f-lote").value, fc = document.getElementById("f-cat").value, fe = document.getElementById("f-est").value;
  return prendas.filter(p => (!fl || p.lote === fl) && (!fc || p.categoria === fc) && (!fe || (p.estado || "pendiente") === fe));
}
function imgUrl(p) { return p.maniqui_url ? `${p.maniqui_url}?v=${p.version || 1}` : ""; }
function tarjeta(p) {
  const est = p.estado || "pendiente";
  return `
<article class="card ${est === "pendiente" ? "" : est}" data-id="${esc(p.id)}">
  <span class="pill">${est === "aprobada" ? "Aprobada" : est === "cambiada" ? "Se cambió" : "Pendiente"}</span>
  <div class="maniqui">${p.maniqui_url ? `<img src="${esc(imgUrl(p))}" loading="lazy">` : ""}<div class="velo">Corrigiendo con Gemini…</div></div>
  <div class="crops">${p.crops.map(c => `<a href="${esc(c.crop_url)}" target="_blank" title="${esc(c.foto)}${c.es_detalle ? " (detalle)" : ""}"><img src="${esc(c.crop_url)}" loading="lazy"></a>`).join("")}</div>
  <div class="meta">
    <div class="fila"><span class="id">${esc(p.codigo)}</span><span class="cat">${esc(p.categoria)}</span>${p.marca_talla ? `<span class="marca">${esc(p.marca_talla)}</span>` : ""}<span class="lote">${esc(p.lote)}</span></div>
    <dl>
      <div><dt>Color</dt><dd>${esc(p.color || "—")}</dd></div>
      <div><dt>Estilo</dt><dd>${esc(p.estilo || "—")}</dd></div>
      <div><dt>Material</dt><dd><select onchange="material('${esc(p.id)}', this.value)"><option value="">—</option>${MATERIALES.map(m => `<option value="${esc(m)}"${m === p.material ? " selected" : ""}>${esc(m)}</option>`).join("")}</select></dd></div>
      <div><dt>Detalles</dt><dd>${esc(p.detalles || "—")}</dd></div>
    </dl>
  </div>
  <div class="comentario">${esc(p.comentario || "")}</div>
  <div class="msg"></div>
  <div class="acciones">
    <button class="ok" onclick="aprobar('${esc(p.id)}')">Aprobar</button>
    <button class="no" onclick="abrirForm('${esc(p.id)}')">Se cambió la prenda</button>
    ${est === "cambiada" && p.comentario ? `<button class="corregir" onclick="corregir('${esc(p.id)}')">Corregir</button>` : ""}
  </div>
  <div class="form">
    <textarea placeholder="¿Qué tiene distinto el maniquí? Ej. la pretina es solo de resorte, sin cordón; el color es más oscuro…">${esc(p.comentario || "")}</textarea>
    <div class="botones"><button onclick="cerrarForm('${esc(p.id)}')">Cancelar</button><button onclick="enviarCambio('${esc(p.id)}', false)">Guardar comentario</button><button class="corregir" onclick="enviarCambio('${esc(p.id)}', true)">Enviar y corregir</button></div>
  </div>
</article>`;
}
function pintar() {
  const lista = visibles();
  document.getElementById("grid").innerHTML = lista.length ? lista.map(tarjeta).join("") : '<div id="estado">Nada con esos filtros</div>';
  let ok = 0, no = 0;
  for (const p of prendas) { if (p.estado === "aprobada") ok++; else if (p.estado === "cambiada") no++; }
  document.getElementById("c-total").textContent = prendas.length;
  document.getElementById("c-ok").textContent = ok;
  document.getElementById("c-no").textContent = no;
  document.getElementById("c-pend").textContent = prendas.length - ok - no;
}
function repintar(p) { const c = card(p.id); if (c) c.outerHTML = tarjeta(p); pintar(); }
function msg(id, texto, error) { const c = card(id); if (!c) return; const m = c.querySelector(".msg"); m.textContent = texto; m.style.color = error ? "var(--no)" : "var(--sec)"; }
async function api(ruta, body) {
  if (!EN_VIVO) throw new Error("Abre la página con ./closet.sh para editar en vivo.");
  const r = await fetch(ruta, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const j = await r.json();
  if (!r.ok) throw new Error(j.error || r.status);
  return j;
}
async function aprobar(id) {
  const p = porId(id);
  try { Object.assign(p, await api("/api/revision", { id, estado: p.estado === "aprobada" ? "pendiente" : "aprobada" })); repintar(p); }
  catch (e) { msg(id, e.message, true); }
}
function abrirForm(id) { card(id).classList.add("editando"); card(id).querySelector("textarea").focus(); }
function cerrarForm(id) { card(id).classList.remove("editando"); }
async function enviarCambio(id, yCorregir) {
  const p = porId(id), texto = card(id).querySelector("textarea").value.trim();
  if (!texto) { msg(id, "Escribe qué tiene distinto.", true); return; }
  try {
    Object.assign(p, await api("/api/revision", { id, estado: "cambiada", comentario: texto }));
    repintar(p);
    if (yCorregir) await corregir(id);
  } catch (e) { msg(id, e.message, true); }
}
async function corregir(id) {
  const p = porId(id), c = card(id);
  c.classList.add("trabajando"); c.querySelectorAll("button").forEach(b => b.disabled = true);
  try { Object.assign(p, await api("/api/corregir", { id })); repintar(p); msg(id, "Maniquí regenerado. Revísalo y aprueba o vuelve a comentar."); }
  catch (e) { c.classList.remove("trabajando"); c.querySelectorAll("button").forEach(b => b.disabled = false); msg(id, e.message, true); }
}
async function material(id, valor) {
  const p = porId(id);
  try { Object.assign(p, await api("/api/revision", { id, material: valor })); msg(id, "Material guardado."); }
  catch (e) { msg(id, e.message, true); }
}
function csv(v) { v = String(v ?? ""); return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; }
function exportar() {
  const filas = [["id", "lote", "codigo", "categoria", "marca_talla", "color", "estilo", "material", "detalles", "estado", "comentario", "maniqui"]];
  for (const p of prendas) filas.push([p.id, p.lote, p.codigo, p.categoria, p.marca_talla, p.color, p.estilo, p.material, p.detalles, p.estado || "pendiente", p.comentario, p.maniqui_url]);
  const blob = new Blob(["﻿" + filas.map(f => f.map(csv).join(",")).join("\n")], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "mi_closet_revision.csv"; a.click();
}
for (const id of ["f-lote", "f-cat", "f-est"]) document.getElementById(id).addEventListener("change", pintar);
cargar();
</script>
</body></html>'''
pagina = pagina.replace("__URL__", URL).replace("__KEY__", KEY).replace("__MATERIALES__", json.dumps(MATERIALES, ensure_ascii=False))
Path("mi_closet.html").write_text(pagina, encoding="utf-8")
print("mi_closet.html generado")
