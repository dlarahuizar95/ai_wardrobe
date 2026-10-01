-- 005: catalogo filtrable (incluye lo de 004 por si no se corrio) + revision completa
alter table prendas add column if not exists marca      text;
alter table prendas add column if not exists talla      text;
alter table prendas add column if not exists color_base text;
alter table prendas add column if not exists tipo       text;
create index if not exists prendas_filtros_idx on prendas (tipo, color_base, talla, marca);

alter table prendas add column if not exists nombre    text;                                   -- nombre corto editable
alter table prendas add column if not exists fit       text not null default 'desconocido';    -- bien / incomodo / apretado / flojo / no_me_queda / desconocido
alter table prendas add column if not exists misma_que text;                                   -- id de otra prenda si es la misma
alter table prendas add column if not exists favorito  boolean not null default false;
alter table prendas add column if not exists guardado  boolean not null default false;         -- false = en el closet, true = guardada

alter table prendas drop constraint if exists prendas_estado_check;
alter table prendas add constraint prendas_estado_check check (estado in ('pendiente','aprobada','cambiada','rechazada'));
alter table prendas drop constraint if exists prendas_fit_check;
alter table prendas add constraint prendas_fit_check check (fit in ('bien','incomodo','apretado','flojo','no_me_queda','desconocido'));
