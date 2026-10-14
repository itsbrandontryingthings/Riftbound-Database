-- Riftbound Database: save each person's wish list with their account.
-- Paste into Supabase > SQL Editor > New query, then click Run. (Safe to run more than once.)
-- Sharing a wish list uses the shared_decks table you already created, so nothing else is needed.

alter table public.collections add column if not exists wish jsonb not null default '{}'::jsonb;
