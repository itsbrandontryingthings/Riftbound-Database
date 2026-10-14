-- Riftbound Database: shared decks and wish lists become private links.
-- Paste into Supabase > SQL Editor > New query, then click Run. (Safe to run more than once.)
--
-- Before: anyone signed in could read every shared deck and wish list.
-- After:  each shared item has a secret link token. Nobody can list or browse shared items;
--         a deck or wish list can only be opened by someone who has its link.
--         Owners can still see and change their own rows. Stopping sharing deletes the row, so the old link stops working.

-- 1) a secret token per shared item (32 random hex characters, about 122 bits of randomness)
alter table public.shared_decks add column if not exists share_token text;
update public.shared_decks set share_token = replace(gen_random_uuid()::text, '-', '') where share_token is null;
alter table public.shared_decks alter column share_token set default replace(gen_random_uuid()::text, '-', '');
alter table public.shared_decks alter column share_token set not null;
create unique index if not exists shared_decks_share_token_key on public.shared_decks (share_token);

-- 1b) the site no longer asks for a trades contact; clear any that were saved
update public.shared_decks set contact = null where contact is not null;

-- 2) nobody can browse the table any more: people can only read their own rows
drop policy if exists "signed-in people can read shared decks" on public.shared_decks;
drop policy if exists "read own shared decks" on public.shared_decks;
create policy "read own shared decks" on public.shared_decks
  for select to authenticated using ((select auth.uid()) = owner);

-- 3) opening a link: returns only the items whose tokens you pass in (no owner id, no email)
create or replace function public.get_shared(p_tokens text[])
returns table (id uuid, deck_id text, owner_name text, contact text, name text, list text,
               updated_at timestamptz, share_token text, is_mine boolean)
language sql stable security definer set search_path = ''
as $$
  select s.id, s.deck_id, s.owner_name, s.contact, s.name, s.list, s.updated_at, s.share_token,
         coalesce(s.owner = auth.uid(), false)
  from public.shared_decks s
  where s.share_token = any (p_tokens[1:200])
    and char_length(s.share_token) >= 20;
$$;
revoke all on function public.get_shared(text[]) from public;
grant execute on function public.get_shared(text[]) to anon, authenticated;
