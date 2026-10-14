-- Riftbound Database: one private row per account (card counts + decks).
-- Paste into Supabase > SQL Editor > New query, then click Run.

create table if not exists public.collections (
  id uuid primary key references auth.users (id) on delete cascade,
  counts jsonb not null default '{}'::jsonb,
  decks jsonb not null default '[]'::jsonb,
  updated_at timestamptz not null default now()
);

alter table public.collections enable row level security;

-- Each person can only see and change their own row.
drop policy if exists "read own collection" on public.collections;
drop policy if exists "add own collection" on public.collections;
drop policy if exists "change own collection" on public.collections;
drop policy if exists "delete own collection" on public.collections;

create policy "read own collection" on public.collections
  for select to authenticated using ((select auth.uid()) = id);
create policy "add own collection" on public.collections
  for insert to authenticated with check ((select auth.uid()) = id);
create policy "change own collection" on public.collections
  for update to authenticated using ((select auth.uid()) = id) with check ((select auth.uid()) = id);
create policy "delete own collection" on public.collections
  for delete to authenticated using ((select auth.uid()) = id);

grant select, insert, update, delete on public.collections to authenticated;
revoke all on public.collections from anon;
