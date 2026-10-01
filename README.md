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
python generar_html.py && open closet.html   # 6. página de revisión + Exportar CSV
python subir_supabase.py             # 7. imágenes a Storage y filas a prendas / apariciones
```

## Base de datos

`supabase/schema.sql` crea las tablas `prendas` y `apariciones` y el bucket `closet`. El estado de revisión (`pendiente`, `aprobada`, `cambiada`) vive en `prendas.estado`.
