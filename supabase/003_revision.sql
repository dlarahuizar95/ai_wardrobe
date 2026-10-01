-- 003: columnas para la revision desde mi_closet.html
alter table prendas add column if not exists comentario  text;          -- que tiene mal el maniqui, escrito por Daniela
alter table prendas add column if not exists revisado_at timestamptz;   -- ultima accion de revision
alter table prendas add column if not exists version     int not null default 1;  -- sube con cada maniqui regenerado
