# AI Wardrobe

Pipeline que convierte fotos del closet en un catálogo e-commerce: una imagen sobre maniquí invisible por prenda, con atributos estructurados y una página de revisión.

Cada lote vive en su carpeta (`Muestra_1/`, …) con las fotos originales en HEIC (ignoradas por git) y los JPG de trabajo en `jpg/` (también ignorados).

## Estructura

```
pipeline/      scripts compartidos (detectar, agrupar, recortar, maniqui, atributos, html, supabase)
lote.sh        corre el pipeline sobre una carpeta de lote
.env           GEMINI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_PUBLISHABLE_KEY (no va al repo)
.venv/         python 3 con pillow, google-genai, httpx
Muestra_1/     un lote: HEIC originales (ignorados), jpg/, detecciones.json, prendas.json, crops/, maniqui/, closet.html
Muestra_2/
```

## Nuevo lote

1. Crea una carpeta sin espacios (ej. `Lote_3`) y mete ahí los HEIC. El nombre en minúsculas es el `lote` en Supabase y la carpeta en el bucket.
2. `./lote.sh Lote_3 preparar` convierte a `jpg/` (sips, max 2048 px), detecta prendas por foto y las agrupa. Termina mostrando la tabla de prendas.
3. Revisa la tabla: categorías, juntar o separar prendas, descartadas. Corrige `prendas.json` si hace falta.
4. `./lote.sh Lote_3 generar` recorta, genera el maniquí por prenda, saca Color / Estilo / Material / Detalles, llena la composición solo si una etiqueta la muestra con porcentajes, arma `closet.html` y sube todo a Supabase.

La detección es reanudable: si se corta, vuelve a correr `preparar` y sigue donde iba. `maniqui.py` y los de atributos saltan lo ya hecho.

## Base de datos

`supabase/schema.sql` crea las tablas `prendas` y `apariciones` y el bucket `closet`. El estado de revisión (`pendiente`, `aprobada`, `cambiada`) vive en `prendas.estado`.

## Revisión en closet.html

Por prenda: botones Aprobar / Se cambió la prenda y un dropdown de Material con composiciones textiles comunes (`materiales.py`). Empieza en blanco salvo que una etiqueta muestre la composición con porcentajes. Las selecciones se guardan en el navegador; Exportar CSV y luego `python pipeline/aplicar_revision.py` desde la carpeta del lote las lleva a Supabase.
