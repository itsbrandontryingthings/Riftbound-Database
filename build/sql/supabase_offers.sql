-- Riftbound Database: offers on shared shopping lists.
-- Paste into Supabase > SQL Editor > New query, then click Run. (Safe to run more than once.)
-- Needs supabase_links.sql to have been run first.
--
-- Anyone with a shopping list's link (signed in or not) can send its owner an offer: their name, which cards they
-- have and how many, and their offer in their own words ("$20", "a trade", "a McChicken"). Only the list's owner can
-- read or delete offers on it. An offer can only be sent through make_offer(), which checks the link and the values.

create table if not exists public.shop_offers (
  id uuid primary key default gen_random_uuid(),
  owner uuid not null references auth.users (id) on delete cascade,
  share_token text not null,
  from_name text not null check (char_length(from_name) between 1 and 40),
  items jsonb not null,
  offer text not null default '' check (char_length(offer) <= 200),
  created_at timestamptz not null default now()
);
-- (an earlier draft of this file had price columns; this brings such a table up to date)
alter table public.shop_offers add column if not exists offer text not null default '' check (char_length(offer) <= 200);
alter table public.shop_offers drop column if exists currency;
alter table public.shop_offers drop column if exists total;
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

-- send an offer on a shared shopping list (p_items: [{"name": "Gust", "q": 2}, ...]; p_offer: free text)
drop function if exists public.make_offer(text, text, jsonb, text);
create function public.make_offer(p_token text, p_name text, p_items jsonb, p_offer text)
returns uuid
language plpgsql security definer set search_path = ''
as $$
declare
  v_owner uuid; v_id uuid;
begin
  if char_length(coalesce(btrim(p_name), '')) not between 1 and 40 then raise exception 'name'; end if;
  if char_length(coalesce(btrim(p_offer), '')) not between 1 and 200 then raise exception 'offer'; end if;
  if p_items is null or jsonb_typeof(p_items) <> 'array' or jsonb_array_length(p_items) not between 1 and 100 then raise exception 'items'; end if;
  if exists (
    select 1 from jsonb_array_elements(p_items) e
    where coalesce(jsonb_typeof(e -> 'name'), '') <> 'string'
       or char_length(e ->> 'name') not between 1 and 80
       or coalesce(e ->> 'q', '') !~ '^[0-9]{1,2}$' or (e ->> 'q')::int < 1
  ) then raise exception 'item'; end if;

  select s.owner into v_owner from public.shared_decks s
  where s.share_token = p_token and s.deck_id = '__shop__' and char_length(p_token) >= 20;
  if v_owner is null then raise exception 'link'; end if;

  -- keep a list from being flooded: at most 20 offers per list per hour
  if (select count(*) from public.shop_offers o where o.share_token = p_token and o.created_at > now() - interval '1 hour') >= 20 then
    raise exception 'busy';
  end if;

  insert into public.shop_offers (owner, share_token, from_name, items, offer)
  values (v_owner, p_token, btrim(p_name),
          (select jsonb_agg(jsonb_build_object('name', e ->> 'name', 'q', (e ->> 'q')::int)) from jsonb_array_elements(p_items) e),
          btrim(p_offer))
  returning id into v_id;
  return v_id;
end;
$$;
revoke all on function public.make_offer(text, text, jsonb, text) from public;
grant execute on function public.make_offer(text, text, jsonb, text) to anon, authenticated;
