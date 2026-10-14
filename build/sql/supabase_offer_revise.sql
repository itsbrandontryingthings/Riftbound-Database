-- Riftbound Database: let the person who made an offer revise it (the cards they give, the money / words, and the cards
-- they'd trade or want back), and let either side delete a message they sent.
-- Paste into Supabase > SQL Editor > New query, then click Run. (Safe to run more than once.)
-- Needs supabase_offer_threads.sql to have been run first.
--
-- * offer_revise() replaces the offer's items, offer text and trade list, and adds a note to the conversation
--   ("Revised the offer.") that keeps the old version under "was", so the list's owner can see what changed.
-- * Same checks as make_offer: 1-100 cards from the list, up to 50 trade cards, 200 characters, no bad words.
--   Only open offers can be revised, and only with the offer's secret reply code.

create or replace function public.offer_revise(p_reply text, p_items jsonb, p_offer text, p_trade jsonb default '[]'::jsonb, p_text text default '')
returns text
language plpgsql security definer set search_path = ''
as $$
declare
  o public.shop_offers%rowtype; v_msg text := btrim(coalesce(p_text, ''));
begin
  select * into o from public.shop_offers where reply_token = p_reply and char_length(p_reply) >= 20;
  if not found then raise exception 'link'; end if;
  if o.status <> 'open' then raise exception 'closed'; end if;
  if char_length(coalesce(p_offer, '')) > 200 or char_length(v_msg) > 200 then raise exception 'offer'; end if;
  if public.rb_bad_words(p_offer) or public.rb_bad_words(v_msg) then raise exception 'words'; end if;
  if not public.rb_cards_ok(p_items, 100) or jsonb_array_length(p_items) < 1 then raise exception 'item'; end if;
  if not public.rb_cards_ok(coalesce(p_trade, '[]'::jsonb), 50) then raise exception 'item'; end if;
  if char_length(coalesce(btrim(p_offer), '')) = 0 and jsonb_array_length(coalesce(p_trade, '[]'::jsonb)) = 0 then raise exception 'offer'; end if;
  if jsonb_array_length(o.thread) >= 40 then raise exception 'busy'; end if;
  update public.shop_offers set
    items = public.rb_cards_clean(p_items),
    offer = btrim(coalesce(p_offer, '')),
    trade = public.rb_cards_clean(p_trade),
    thread = thread || jsonb_build_array(jsonb_build_object(
      'by', 'them', 'text', coalesce(nullif(v_msg, ''), 'Revised the offer.'), 'revised', true,
      'was', jsonb_build_object('items', o.items, 'offer', o.offer, 'trade', o.trade), 'at', now())),
    updated_at = now()
  where id = o.id;
  return 'open';
end;
$$;
revoke all on function public.offer_revise(text, jsonb, text, jsonb, text) from public;
grant execute on function public.offer_revise(text, jsonb, text, jsonb, text) to anon, authenticated;

-- delete a message you sent in an open offer's conversation (found by its time, "at"). Revision notes stay.
-- The person who made the offer (with the reply code):
create or replace function public.offer_delete_msg(p_reply text, p_at text)
returns text
language plpgsql security definer set search_path = ''
as $$
declare
  o public.shop_offers%rowtype;
begin
  select * into o from public.shop_offers where reply_token = p_reply and char_length(p_reply) >= 20;
  if not found then raise exception 'link'; end if;
  if o.status <> 'open' then raise exception 'closed'; end if;
  update public.shop_offers set
    thread = coalesce((select jsonb_agg(e order by i) from jsonb_array_elements(o.thread) with ordinality t(e, i)
                       where not (e ->> 'by' = 'them' and e ->> 'at' = p_at and coalesce(e ->> 'revised', 'false') <> 'true')), '[]'::jsonb),
    updated_at = now()
  where id = o.id;
  return 'open';
end;
$$;
revoke all on function public.offer_delete_msg(text, text) from public;
grant execute on function public.offer_delete_msg(text, text) to anon, authenticated;

-- The list's owner (signed in):
create or replace function public.owner_delete_msg(p_id uuid, p_at text)
returns text
language plpgsql security definer set search_path = ''
as $$
declare
  o public.shop_offers%rowtype;
begin
  select * into o from public.shop_offers where id = p_id and owner = auth.uid();
  if not found then raise exception 'link'; end if;
  if o.status <> 'open' then raise exception 'closed'; end if;
  update public.shop_offers set
    thread = coalesce((select jsonb_agg(e order by i) from jsonb_array_elements(o.thread) with ordinality t(e, i)
                       where not (e ->> 'by' = 'owner' and e ->> 'at' = p_at)), '[]'::jsonb),
    updated_at = now()
  where id = o.id;
  return 'open';
end;
$$;
revoke all on function public.owner_delete_msg(uuid, text) from public;
grant execute on function public.owner_delete_msg(uuid, text) to authenticated;
