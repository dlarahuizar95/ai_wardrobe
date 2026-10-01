-- 004: campos normalizados para filtrar el catalogo
alter table prendas add column if not exists marca      text;   -- marca limpia: Zara, Mango, Uniqlo, '' si no hay
alter table prendas add column if not exists talla      text;   -- talla principal: XS S M L XL o numero MEX
alter table prendas add column if not exists color_base text;   -- familia de color: negro, blanco, beige, azul, ...
alter table prendas add column if not exists tipo       text;   -- tipo de prenda normalizado (taxonomia fija)
create index if not exists prendas_filtros_idx on prendas (tipo, color_base, talla, marca);
