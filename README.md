# AI Wardrobe

Pipeline que convierte fotos del closet en un catálogo e-commerce: una imagen sobre maniquí invisible por prenda, con atributos estructurados y una página de revisión.

Cada lote vive en su carpeta (`Muestra_1/`, …) con las fotos originales en HEIC (ignoradas por git) y los JPG de trabajo en `jpg/` (también ignorados).

## Pipeline por lote

```
cd Muestra_1
set -a; source .env; set +a          # GEMINI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY
python detectar.py                   # 1. prendas por foto -> detecciones.json
python agrupar.py                    # 2. misma prenda física -> prendas.json  (revisar tabla antes de seguir)
python recortar.py                   # 3. crops/{prenda}/{foto}_{n}.jpg
python maniqui.py                    # 4. maniqui/{prenda}.jpg con gemini-2.5-flash-image
python atributos.py                  # 5. Color / Estilo / Material / Detalles -> prendas.json
python atributos_composicion.py      # 5b. composición textil SOLO si una etiqueta la muestra con % -> dropdown
python generar_html.py && open closet.html   # 6. página de revisión + Exportar CSV
python subir_supabase.py             # 7. imágenes a Storage y filas a prendas / apariciones
python aplicar_revision.py           # 8. sube estado y material desde ~/Downloads/closet_revision.csv
```

## Base de datos

`supabase/schema.sql` crea las tablas `prendas` y `apariciones` y el bucket `closet`. El estado de revisión (`pendiente`, `aprobada`, `cambiada`) vive en `prendas.estado`.

## Revisión en closet.html

Por prenda: botones Aprobar / Se cambió la prenda y un dropdown de Material con composiciones textiles comunes (`materiales.py`). Empieza en blanco salvo que una etiqueta muestre la composición con porcentajes. Las selecciones se guardan en el navegador; Exportar CSV y luego `aplicar_revision.py` las lleva a Supabase.
