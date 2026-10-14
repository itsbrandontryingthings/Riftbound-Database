-- Riftbound Database: offers on shared shopping lists.
-- Paste into Supabase > SQL Editor > New query, then click Run. (Safe to run more than once.)
-- Needs supabase_links.sql to have been run first.
--
-- Anyone with a shopping list's link (signed in or not) can send its owner an offer: their name, and for each card
-- how many they have and their price. Only the list's owner can read or delete offers on it. Nobody else can
-- list offers, and an offer can only be sent through make_offer(), which checks the link and the values.

create table if not exists public.shop_offers (
  id uuid primary key default gen_random_uuid(),
  owner uuid not null references auth.users (id) on delete cascade,
  share_token text not null,
  from_name text not null check (char_length(from_name) between 1 and 40),
  items jsonb not null,
  currency text not null default 'CAD' check (currency in ('CAD', 'USD')),
  total numeric(12, 2) not null default 0,
  created_at timestamptz not null default now()
);
create index if not exists shop_offers_owner_idx on public.shop_offers (owner, created_at desc);
create index if not exists shop_offers_token_idx on public.shop_offers (share_token, created_at desc);

alter table public.shop_offers enable row level security;
drop policy if exists "owners read their offers" on public.shop_offers;
drop policy if exists "owners remove their offers" on public.shop_offers;
create policy "owners read their offers" on public.shop_offers
  for select to authenticated using ((select auth.uid()) = owner);
create policy "owners remove their offers" on public.shop_offers
  for delete to authenticated using ((select auth.uid()) = owner);
revoke all on public.shop_offers from anon, authenticated;
grant select, delete on public.shop_offers to authenticated;

-- send an offer on a shared shopping list (p_items: [{"name": "Gust", "q": 2, "price": 1.50}, ...])
create or replace function public.make_offer(p_token text, p_name text, p_items jsonb, p_currency text)
returns uuid
language plpgsql security definer set search_path = ''
as $$
declare
  v_owner uuid; v_id uuid; v_total numeric;
begin
  if char_length(coalesce(btrim(p_name), '')) not between 1 and 40 then raise exception 'name'; end if;
  if p_currency is null or p_currency not in ('CAD', 'USD') then raise exception 'currency'; end if;
  if p_items is null or jsonb_typeof(p_items) <> 'array' or jsonb_array_length(p_items) not between 1 and 100 then raise exception 'items'; end if;
  if exists (
    select 1 from jsonb_array_elements(p_items) e
    where coalesce(jsonb_typeof(e -> 'name'), '') <> 'string'
       or char_length(e ->> 'name') not between 1 and 80
       or coalesce(e ->> 'q', '') !~ '^[0-9]{1,2}$' or (e ->> 'q')::int < 1
       or coalesce(e ->> 'price', '') !~ '^[0-9]{1,6}(\.[0-9]{1,2})?$'
  ) then raise exception 'item'; end if;

  select s.owner into v_owner from public.shared_decks s
  where s.share_token = p_token and s.deck_id = '__shop__' and char_length(p_token) >= 20;
  if v_owner is null then raise exception 'link'; end if;

  -- keep a list from being flooded: at most 20 offers per list per hour
  if (select count(*) from public.shop_offers o where o.share_token = p_token and o.created_at > now() - interval '1 hour') >= 20 then
    raise exception 'busy';
  end if;

  select coalesce(sum((e ->> 'q')::int * (e ->> 'price')::numeric), 0) into v_total from jsonb_array_elements(p_items) e;
  insert into public.shop_offers (owner, share_token, from_name, items, currency, total)
  values (v_owner, p_token, btrim(p_name), p_items, p_currency, v_total)
  returning id into v_id;
  return v_id;
end;
$$;
revoke all on function public.make_offer(text, text, jsonb, text) from public;
grant execute on function public.make_offer(text, text, jsonb, text) to anon, authenticated;
