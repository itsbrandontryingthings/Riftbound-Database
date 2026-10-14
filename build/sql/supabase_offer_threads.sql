-- Riftbound Database: offer conversations, offering your own cards, and a bad-word filter.
-- Paste into Supabase > SQL Editor > New query, then click Run. (Safe to run more than once.)
-- Needs supabase_offers.sql to have been run first.
--
-- * Each offer gets a secret reply code. The person who made it keeps that code in their browser, so they can follow
--   the offer, see counter offers, reply, accept a counter or withdraw, without an account.
-- * An offer can include cards the person would trade (trade), and keeps a short conversation (thread) and a status:
--   open, accepted, declined or withdrawn.
-- * The list's owner answers through owner_reply() (counter, accept, decline). Only the owner can read their offers.
-- * Names, offers and messages with bad words are refused (rb_bad_words), also catching tricks like "sh1t" or "f.u.c.k".

alter table public.shop_offers add column if not exists reply_token text not null default replace(gen_random_uuid()::text, '-', '');
alter table public.shop_offers add column if not exists trade jsonb not null default '[]'::jsonb;
alter table public.shop_offers add column if not exists thread jsonb not null default '[]'::jsonb;
alter table public.shop_offers add column if not exists status text not null default 'open';
alter table public.shop_offers add column if not exists updated_at timestamptz not null default now();
create unique index if not exists shop_offers_reply_idx on public.shop_offers (reply_token);
alter table public.shop_offers drop constraint if exists shop_offers_status_check;
alter table public.shop_offers add constraint shop_offers_status_check check (status in ('open', 'accepted', 'declined', 'withdrawn'));

-- true if the text has a swear word or slur (numbers and symbols like 1 3 4 5 0 @ $ ! count as letters)
create or replace function public.rb_bad_words(p text)
returns boolean language sql immutable set search_path = ''
as $$
  select translate(lower(coalesce(p, '')), '013457@$!', 'oieastasi') ~ 'f+[._*-]*u+[._*-]*c+[._*-]*k+|b+[._*-]*i+[._*-]*t+[._*-]*c+[._*-]*h+|w+[._*-]*h+[._*-]*o+[._*-]*r+[._*-]*e+|s+[._*-]*l+[._*-]*u+[._*-]*t+|b+[._*-]*a+[._*-]*s+[._*-]*t+[._*-]*a+[._*-]*r+[._*-]*d+|a+[._*-]*s+[._*-]*s+[._*-]*h+[._*-]*o+[._*-]*l+[._*-]*e+|n+[._*-]*i+[._*-]*g+[._*-]*g+|f+[._*-]*a+[._*-]*g+[._*-]*g+[._*-]*o+[._*-]*t+|r+[._*-]*e+[._*-]*t+[._*-]*a+[._*-]*r+[._*-]*d+|m+[._*-]*o+[._*-]*t+[._*-]*h+[._*-]*e+[._*-]*r+[._*-]*f+|d+[._*-]*i+[._*-]*l+[._*-]*d+[._*-]*o+|p+[._*-]*u+[._*-]*s+[._*-]*s+[._*-]*y+|c+[._*-]*o+[._*-]*c+[._*-]*k+[._*-]*s+[._*-]*u+[._*-]*c+[._*-]*k+|t+[._*-]*w+[._*-]*a+[._*-]*t+|w+[._*-]*a+[._*-]*n+[._*-]*k+|j+[._*-]*i+[._*-]*z+[._*-]*z+|s+[._*-]*h+[._*-]*i[._*-]*t+'
      or translate(lower(coalesce(p, '')), '013457@$!', 'oieastasi') ~ '\m(ass|asses|dick|dicks|cock|cocks|cum|tit|tits|piss|fag|fags|fuk|fck|hoe|hoes|kike|spic|spics|chink|tranny|rape|raping|rapist|nazi|porn|pedo|kys|nigga|niggas|cunt|cunts)\M';
$$;

-- a list of cards like [{"name": "Gust", "q": 2, "id": "ogn-169-298"}]: names 1-80 characters, 1-99 copies, no bad words
create or replace function public.rb_cards_ok(p jsonb, p_max int)
returns boolean language sql immutable set search_path = ''
as $$
  select p is not null and jsonb_typeof(p) = 'array' and jsonb_array_length(p) <= p_max
     and not exists (
       select 1 from jsonb_array_elements(p) e
       where coalesce(jsonb_typeof(e -> 'name'), '') <> 'string'
          or char_length(e ->> 'name') not between 1 and 80
          or coalesce(e ->> 'q', '') !~ '^[0-9]{1,2}$' or (e ->> 'q')::int < 1
          or (e ? 'id' and (coalesce(jsonb_typeof(e -> 'id'), '') <> 'string' or char_length(e ->> 'id') > 40))
          or public.rb_bad_words(e ->> 'name'));
$$;
create or replace function public.rb_cards_clean(p jsonb)
returns jsonb language sql immutable set search_path = ''
as $$
  select coalesce(jsonb_agg(jsonb_strip_nulls(jsonb_build_object('name', e ->> 'name', 'q', (e ->> 'q')::int, 'id', e ->> 'id'))), '[]'::jsonb)
  from jsonb_array_elements(coalesce(p, '[]'::jsonb)) e;
$$;

-- send an offer: cards from the list you have (p_items), what you offer in words (p_offer) and/or cards you'd trade
-- (p_trade). Returns the offer's secret reply code.
drop function if exists public.make_offer(text, text, jsonb, text);
drop function if exists public.make_offer(text, text, jsonb, text, jsonb);
create function public.make_offer(p_token text, p_name text, p_items jsonb, p_offer text, p_trade jsonb default '[]'::jsonb)
returns text
language plpgsql security definer set search_path = ''
as $$
declare
  v_owner uuid; v_reply text;
begin
  if char_length(coalesce(btrim(p_name), '')) not between 1 and 40 then raise exception 'name'; end if;
  if char_length(coalesce(p_offer, '')) > 200 then raise exception 'offer'; end if;
  if public.rb_bad_words(p_name) or public.rb_bad_words(p_offer) then raise exception 'words'; end if;
  if not public.rb_cards_ok(p_items, 100) or jsonb_array_length(p_items) < 1 then raise exception 'item'; end if;
  if not public.rb_cards_ok(coalesce(p_trade, '[]'::jsonb), 50) then raise exception 'item'; end if;
  if char_length(coalesce(btrim(p_offer), '')) = 0 and jsonb_array_length(coalesce(p_trade, '[]'::jsonb)) = 0 then raise exception 'offer'; end if;

  select s.owner into v_owner from public.shared_decks s
  where s.share_token = p_token and s.deck_id = '__shop__' and char_length(p_token) >= 20;
  if v_owner is null then raise exception 'link'; end if;

  if (select count(*) from public.shop_offers o where o.share_token = p_token and o.created_at > now() - interval '1 hour') >= 20 then
    raise exception 'busy';
  end if;

  insert into public.shop_offers (owner, share_token, from_name, items, offer, trade)
  values (v_owner, p_token, btrim(p_name), public.rb_cards_clean(p_items), btrim(coalesce(p_offer, '')), public.rb_cards_clean(p_trade))
  returning reply_token into v_reply;
  return v_reply;
end;
$$;
revoke all on function public.make_offer(text, text, jsonb, text, jsonb) from public;
grant execute on function public.make_offer(text, text, jsonb, text, jsonb) to anon, authenticated;

-- the person who made offers: see them (with the owner's counter offers) using their reply codes
create or replace function public.get_my_offers(p_replies text[])
returns table (reply_token text, list_name text, list_token text, from_name text, items jsonb, trade jsonb, offer text,
               thread jsonb, status text, created_at timestamptz, updated_at timestamptz)
language sql stable security definer set search_path = ''
as $$
  select o.reply_token, s.name, o.share_token, o.from_name, o.items, o.trade, o.offer, o.thread, o.status, o.created_at, o.updated_at
  from public.shop_offers o left join public.shared_decks s on s.share_token = o.share_token and s.deck_id = '__shop__'
  where o.reply_token = any (p_replies[1:100]) and char_length(o.reply_token) >= 20;
$$;
revoke all on function public.get_my_offers(text[]) from public;
grant execute on function public.get_my_offers(text[]) to anon, authenticated;

-- the person who made the offer: 'reply' (a message and/or more cards to trade), 'accept' (the owner's counter) or 'withdraw'
create or replace function public.offer_reply(p_reply text, p_action text, p_text text default '', p_trade jsonb default '[]'::jsonb)
returns text
language plpgsql security definer set search_path = ''
as $$
declare
  o public.shop_offers%rowtype; v_msg text := btrim(coalesce(p_text, ''));
begin
  select * into o from public.shop_offers where reply_token = p_reply and char_length(p_reply) >= 20;
  if not found then raise exception 'link'; end if;
  if o.status <> 'open' then raise exception 'closed'; end if;
  if char_length(v_msg) > 200 then raise exception 'offer'; end if;
  if public.rb_bad_words(v_msg) then raise exception 'words'; end if;
  if jsonb_array_length(o.thread) >= 40 then raise exception 'busy'; end if;
  if p_action = 'reply' then
    if not public.rb_cards_ok(coalesce(p_trade, '[]'::jsonb), 50) then raise exception 'item'; end if;
    if v_msg = '' and jsonb_array_length(coalesce(p_trade, '[]'::jsonb)) = 0 then raise exception 'offer'; end if;
    update public.shop_offers set thread = thread || jsonb_build_array(jsonb_build_object('by', 'them', 'text', v_msg, 'trade', public.rb_cards_clean(p_trade), 'at', now())), updated_at = now() where id = o.id;
  elsif p_action = 'accept' then
    if coalesce(o.thread -> -1 ->> 'by', '') <> 'owner' then raise exception 'closed'; end if;
    update public.shop_offers set status = 'accepted', thread = thread || jsonb_build_array(jsonb_build_object('by', 'them', 'text', coalesce(nullif(v_msg, ''), 'Accepted your counter offer.'), 'at', now())), updated_at = now() where id = o.id;
  elsif p_action = 'withdraw' then
    update public.shop_offers set status = 'withdrawn', thread = thread || jsonb_build_array(jsonb_build_object('by', 'them', 'text', 'Withdrew the offer.', 'at', now())), updated_at = now() where id = o.id;
  else raise exception 'action'; end if;
  return (select status from public.shop_offers where id = o.id);
end;
$$;
revoke all on function public.offer_reply(text, text, text, jsonb) from public;
grant execute on function public.offer_reply(text, text, text, jsonb) to anon, authenticated;

-- the list's owner: 'counter' (a message), 'accept' or 'decline' (each with an optional message)
create or replace function public.owner_reply(p_id uuid, p_action text, p_text text default '')
returns text
language plpgsql security definer set search_path = ''
as $$
declare
  o public.shop_offers%rowtype; v_msg text := btrim(coalesce(p_text, ''));
begin
  select * into o from public.shop_offers where id = p_id and owner = auth.uid();
  if not found then raise exception 'link'; end if;
  if o.status <> 'open' then raise exception 'closed'; end if;
  if char_length(v_msg) > 200 then raise exception 'offer'; end if;
  if public.rb_bad_words(v_msg) then raise exception 'words'; end if;
  if jsonb_array_length(o.thread) >= 40 then raise exception 'busy'; end if;
  if p_action = 'counter' then
    if v_msg = '' then raise exception 'offer'; end if;
    update public.shop_offers set thread = thread || jsonb_build_array(jsonb_build_object('by', 'owner', 'text', v_msg, 'at', now())), updated_at = now() where id = o.id;
  elsif p_action in ('accept', 'decline') then
    update public.shop_offers set status = case p_action when 'accept' then 'accepted' else 'declined' end,
      thread = thread || jsonb_build_array(jsonb_build_object('by', 'owner', 'text', coalesce(nullif(v_msg, ''), case p_action when 'accept' then 'Accepted your offer.' else 'Declined your offer.' end), 'at', now())),
      updated_at = now() where id = o.id;
  else raise exception 'action'; end if;
  return (select status from public.shop_offers where id = o.id);
end;
$$;
revoke all on function public.owner_reply(uuid, text, text) from public;
grant execute on function public.owner_reply(uuid, text, text) to authenticated;
