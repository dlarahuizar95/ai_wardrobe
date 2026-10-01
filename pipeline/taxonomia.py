"""Listas fijas para catalogar y filtrar."""
TIPOS = ["top", "blusa", "camisa", "sweater", "cardigan", "blazer", "chamarra", "abrigo", "vestido",
         "falda", "pantalon", "jeans", "shorts", "zapatos", "bolsa", "cinturon", "accesorio"]
TIPOS_ETIQUETA = {"top": "Top", "blusa": "Blusa", "camisa": "Camisa", "sweater": "Sweater", "cardigan": "Cardigan",
                  "blazer": "Blazer", "chamarra": "Chamarra", "abrigo": "Abrigo", "vestido": "Vestido", "falda": "Falda",
                  "pantalon": "Pantalón", "jeans": "Jeans", "shorts": "Shorts", "zapatos": "Zapatos", "bolsa": "Bolsa",
                  "cinturon": "Cinturón", "accesorio": "Accesorio"}
COLORES = ["negro", "blanco", "beige", "gris", "cafe", "azul", "verde", "rojo", "rosa", "morado",
           "amarillo", "naranja", "dorado", "plateado", "multicolor"]
COLORES_ETIQUETA = {"cafe": "Café", **{c: c.capitalize() for c in COLORES if c != "cafe"}}
TALLAS = ["XS", "S", "M", "L", "XL", "XXL"]
