-- Yapa · persistencia de usuarios, catálogo, pedidos y administración
-- Ejecutar en Supabase SQL Editor. Es idempotente para poder aplicarlo más de una vez.

create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  name text not null,
  phone text,
  district text,
  role text not null default 'customer' check (role in ('customer', 'admin')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.profiles add column if not exists role text not null default 'customer';
alter table public.profiles add column if not exists updated_at timestamptz not null default now();

create table if not exists public.products (
  id text primary key,
  name text not null,
  category text not null,
  price numeric(10,2) not null check (price >= 0),
  unit text not null,
  detail text not null,
  art text not null default 'rice',
  image text not null,
  stock integer not null default 0 check (stock >= 0),
  active boolean not null default true,
  updated_at timestamptz not null default now()
);

alter table public.products add column if not exists art text not null default 'rice';
alter table public.products add column if not exists active boolean not null default true;
alter table public.products add column if not exists updated_at timestamptz not null default now();

create table if not exists public.addresses (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  district text not null,
  address_line text not null,
  reference text,
  latitude numeric(10,7),
  longitude numeric(10,7),
  created_at timestamptz not null default now()
);

create table if not exists public.orders (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete set null,
  order_code text unique not null,
  district text not null,
  address_line text not null,
  reference text,
  latitude numeric(10,7),
  longitude numeric(10,7),
  delivery_window text not null,
  payment_method text not null,
  status text not null default 'RECIBIDO' check (status in ('RECIBIDO', 'PREPARANDO', 'EN RUTA', 'ENTREGADO')),
  total numeric(10,2) not null check (total >= 0),
  created_at timestamptz not null default now()
);

create table if not exists public.order_items (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references public.orders(id) on delete cascade,
  product_id text not null references public.products(id),
  product_name text not null,
  quantity integer not null check (quantity > 0),
  unit_price numeric(10,2) not null check (unit_price >= 0)
);

create index if not exists addresses_user_id_idx on public.addresses(user_id);
create index if not exists orders_user_id_created_at_idx on public.orders(user_id, created_at desc);
create index if not exists order_items_order_id_idx on public.order_items(order_id);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists profiles_set_updated_at on public.profiles;
create trigger profiles_set_updated_at
before update on public.profiles
for each row execute function public.set_updated_at();

drop trigger if exists products_set_updated_at on public.products;
create trigger products_set_updated_at
before update on public.products
for each row execute function public.set_updated_at();

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, name, phone, district)
  values (
    new.id,
    coalesce(new.raw_user_meta_data ->> 'name', split_part(coalesce(new.email, ''), '@', 1), 'Amigo'),
    new.raw_user_meta_data ->> 'phone',
    coalesce(new.raw_user_meta_data ->> 'district', 'Lince')
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute function public.handle_new_user();

create or replace function public.is_admin()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1 from public.profiles
    where id = auth.uid() and role = 'admin'
  );
$$;

alter table public.profiles enable row level security;
alter table public.products enable row level security;
alter table public.addresses enable row level security;
alter table public.orders enable row level security;
alter table public.order_items enable row level security;

drop policy if exists "users can read own profile" on public.profiles;
drop policy if exists "users can update own profile" on public.profiles;
drop policy if exists "admins can read profiles" on public.profiles;
drop policy if exists "admins can update profiles" on public.profiles;
create policy "users can read own profile" on public.profiles for select to authenticated using (auth.uid() = id);
create policy "users can update own profile" on public.profiles for update to authenticated using (auth.uid() = id) with check (auth.uid() = id and role = 'customer');
create policy "admins can read profiles" on public.profiles for select to authenticated using (public.is_admin());
create policy "admins can update profiles" on public.profiles for update to authenticated using (public.is_admin()) with check (public.is_admin());

drop policy if exists "public can read active products" on public.products;
drop policy if exists "admins can read all products" on public.products;
drop policy if exists "admins can insert products" on public.products;
drop policy if exists "admins can update products" on public.products;
drop policy if exists "admins can delete products" on public.products;
create policy "public can read active products" on public.products for select using (active = true);
create policy "admins can read all products" on public.products for select to authenticated using (public.is_admin());
create policy "admins can insert products" on public.products for insert to authenticated with check (public.is_admin());
create policy "admins can update products" on public.products for update to authenticated using (public.is_admin()) with check (public.is_admin());
create policy "admins can delete products" on public.products for delete to authenticated using (public.is_admin());

drop policy if exists "users can manage own addresses" on public.addresses;
create policy "users can manage own addresses" on public.addresses for all to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "users can read own orders" on public.orders;
drop policy if exists "users can create own orders" on public.orders;
drop policy if exists "admins can read orders" on public.orders;
drop policy if exists "admins can update orders" on public.orders;
create policy "users can read own orders" on public.orders for select to authenticated using (auth.uid() = user_id);
create policy "users can create own orders" on public.orders for insert to authenticated with check (auth.uid() = user_id);
create policy "admins can read orders" on public.orders for select to authenticated using (public.is_admin());
create policy "admins can update orders" on public.orders for update to authenticated using (public.is_admin()) with check (public.is_admin());

drop policy if exists "users can read own order items" on public.order_items;
drop policy if exists "admins can read order items" on public.order_items;
create policy "users can read own order items" on public.order_items for select to authenticated using (exists (select 1 from public.orders where orders.id = order_items.order_id and orders.user_id = auth.uid()));
create policy "admins can read order items" on public.order_items for select to authenticated using (public.is_admin());

create or replace function public.create_order(
  p_order_code text,
  p_district text,
  p_address_line text,
  p_reference text,
  p_latitude numeric,
  p_longitude numeric,
  p_delivery_window text,
  p_payment_method text,
  p_total numeric,
  p_items jsonb
)
returns public.orders
language plpgsql
security definer
set search_path = public
as $$
declare
  new_order public.orders;
  calculated_subtotal numeric;
begin
  if auth.uid() is null then
    raise exception 'Debes iniciar sesión para registrar un pedido';
  end if;

  if length(trim(coalesce(p_address_line, ''))) < 8 then
    raise exception 'La dirección de entrega es obligatoria';
  end if;

  select coalesce(sum(item.quantity * item.unit_price), 0)
  into calculated_subtotal
  from jsonb_to_recordset(p_items) as item(product_id text, product_name text, quantity integer, unit_price numeric);

  if calculated_subtotal < 50 then
    raise exception 'El pedido mínimo es de S/ 50.00';
  end if;

  if exists (
    select 1
    from jsonb_to_recordset(p_items) as item(product_id text, product_name text, quantity integer, unit_price numeric)
    left join public.products product on product.id = item.product_id
    where product.id is null or product.active = false or item.quantity <= 0 or product.stock < item.quantity
  ) then
    raise exception 'Uno de los productos ya no está disponible';
  end if;

  insert into public.orders (user_id, order_code, district, address_line, reference, latitude, longitude, delivery_window, payment_method, total)
  values (auth.uid(), p_order_code, p_district, trim(p_address_line), nullif(trim(coalesce(p_reference, '')), ''), p_latitude, p_longitude, p_delivery_window, p_payment_method, p_total)
  returning * into new_order;

  insert into public.order_items (order_id, product_id, product_name, quantity, unit_price)
  select new_order.id, item.product_id, item.product_name, item.quantity, item.unit_price
  from jsonb_to_recordset(p_items) as item(product_id text, product_name text, quantity integer, unit_price numeric);

  insert into public.addresses (user_id, district, address_line, reference, latitude, longitude)
  values (auth.uid(), p_district, trim(p_address_line), nullif(trim(coalesce(p_reference, '')), ''), p_latitude, p_longitude);

  return new_order;
end;
$$;

revoke all on function public.create_order(text, text, text, text, numeric, numeric, text, text, numeric, jsonb) from public;
grant execute on function public.create_order(text, text, text, text, numeric, numeric, text, text, numeric, jsonb) to authenticated;

insert into public.products (id, name, category, price, unit, detail, art, image, stock, active)
values
  ('arroz-extra', 'Arroz extra', 'Despensa', 4.80, 'kg', 'Grano largo, calidad mayorista', 'rice', '/images/products/arroz-extra.png', 28, true),
  ('aceite-vegetal', 'Aceite vegetal', 'Despensa', 8.90, 'L', 'Botella familiar de 1 litro', 'oil', '/images/products/aceite-vegetal.png', 16, true),
  ('platano-seda', 'Plátano de seda', 'Frutas', 3.90, 'kg', 'Dulce y listo para la semana', 'banana', '/images/products/platano-seda.png', 22, true),
  ('tomate-italiano', 'Tomate italiano', 'Verduras', 5.60, 'kg', 'Cosecha seleccionada del día', 'tomato', '/images/products/tomate-italiano.png', 18, true),
  ('papa-amarilla', 'Papa amarilla', 'Verduras', 4.20, 'kg', 'Textura cremosa para guisos', 'potato', '/images/products/papa-amarilla.png', 31, true),
  ('leche-pack', 'Leche evaporada', 'Lácteos', 21.60, 'pack x 6', 'Seis latas para la despensa', 'milk', '/images/products/leche-pack.png', 12, true)
on conflict (id) do nothing;

-- Después de crear un usuario administrador en Authentication > Users,
-- promuévelo manualmente una sola vez:
-- update public.profiles set role = 'admin' where id = '<UUID_DEL_USUARIO>';
