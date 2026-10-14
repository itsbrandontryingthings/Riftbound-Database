-- Riftbound Database: shared decks.
-- Paste into Supabase > SQL Editor > New query, then click Run. (Safe to run more than once.)
-- Anyone signed in can read shared decks; only the person who shared a deck can change or remove it.

create table if not exists public.shared_decks (
  id uuid primary key default gen_random_uuid(),
  owner uuid not null default auth.uid() references auth.users (id) on delete cascade,
  deck_id text not null check (char_length(deck_id) <= 40),
  owner_name text not null check (char_length(owner_name) between 1 and 40),
  contact text check (contact is null or char_length(contact) <= 80),
  name text not null check (char_length(name) between 1 and 80),
  list text not null check (char_length(list) <= 8000),
  updated_at timestamptz not null default now(),
  unique (owner, deck_id)
);

alter table public.shared_decks enable row level security;

drop policy if exists "signed-in people can read shared decks" on public.shared_decks;
drop policy if exists "share own decks" on public.shared_decks;
drop policy if exists "update own shared decks" on public.shared_decks;
drop policy if exists "remove own shared decks" on public.shared_decks;

create policy "signed-in people can read shared decks" on public.shared_decks
  for select to authenticated using (true);
create policy "share own decks" on public.shared_decks
  for insert to authenticated with check ((select auth.uid()) = owner);
create policy "update own shared decks" on public.shared_decks
  for update to authenticated using ((select auth.uid()) = owner) with check ((select auth.uid()) = owner);
create policy "remove own shared decks" on public.shared_decks
  for delete to authenticated using ((select auth.uid()) = owner);

grant select, insert, update, delete on public.shared_decks to authenticated;
revoke all on public.shared_decks from anon;
