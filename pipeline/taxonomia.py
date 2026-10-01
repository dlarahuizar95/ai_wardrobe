"""Listas fijas para catalogar y filtrar."""
TIPOS = ["top", "bodysuit", "camisa", "blusa", "sweater", "cardigan", "blazer", "chamarra", "abrigo", "vestido",
         "falda", "pantalon", "jeans", "shorts", "zapatos", "bolsa", "cinturon", "joyeria", "accesorio"]
TIPOS_ETIQUETA = {"top": "Top", "bodysuit": "Bodysuit", "camisa": "Camisa", "blusa": "Blusa", "sweater": "Sweater",
                  "cardigan": "Cardigan", "blazer": "Blazer", "chamarra": "Chamarra", "abrigo": "Abrigo", "vestido": "Vestido",
                  "falda": "Falda", "pantalon": "Pantalón", "jeans": "Jeans", "shorts": "Shorts", "zapatos": "Zapatos",
                  "bolsa": "Bolsa", "cinturon": "Cinturón", "joyeria": "Joyería", "accesorio": "Accesorio"}
COLORES = ["negro", "blanco", "beige", "gris", "cafe", "azul", "verde", "rojo", "rosa", "morado",
           "amarillo", "naranja", "dorado", "plateado", "multicolor"]
COLORES_ETIQUETA = {"cafe": "Café", **{c: c.capitalize() for c in COLORES if c != "cafe"}}
TALLAS = ["XS", "S", "M", "L", "XL", "XXL"]
FITS = [["desconocido", "Desconocido"], ["bien", "Bien"], ["incomodo", "Incómodo"], ["apretado", "Apretado"], ["flojo", "Flojo"], ["no_me_queda", "No me queda"]]
ESTADOS = ["pendiente", "aprobada", "cambiada", "rechazada"]
