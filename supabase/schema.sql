-- AI Wardrobe: esquema inicial
create table if not exists prendas (
  id          text primary key,                 -- '{lote}-{codigo}', ej. muestra_1-P01
  lote        text not null,
  codigo      text not null,                    -- P01
  categoria   text,
  marca_talla text,
  descripcion text,
  color       text,
  estilo      text,
  material    text,
  detalles    text,
  maniqui_url text,
  estado      text not null default 'pendiente' check (estado in ('pendiente','aprobada','cambiada')),
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now(),
  unique (lote, codigo)
);

create table if not exists apariciones (
  id               bigint generated always as identity primary key,
  prenda_id        text not null references prendas(id) on delete cascade,
  foto             text not null,
  n                int  not null,
  bbox             real[] not null,             -- [x0, y0, x1, y1] normalizado
  es_detalle       boolean not null default false,
  descripcion_foto text,
  crop_url         text,
  unique (prenda_id, foto, n)
);

create index if not exists apariciones_prenda_idx on apariciones(prenda_id);

-- Solo la service key escribe; lectura publica de ambas tablas
alter table prendas     enable row level security;
alter table apariciones enable row level security;
create policy "lectura publica prendas"     on prendas     for select using (true);
create policy "lectura publica apariciones" on apariciones for select using (true);

-- Bucket publico para maniquies y crops
insert into storage.buckets (id, name, public) values ('closet', 'closet', true)
on conflict (id) do nothing;
