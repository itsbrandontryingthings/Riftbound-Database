-- Riftbound Database: a stricter bad-word check for names, offers and messages (both sides of an offer).
-- Paste into Supabase > SQL Editor > New query, then click Run. (Safe to run more than once.)
-- Needs supabase_offer_threads.sql to have been run first (this replaces its rb_bad_words).
--
-- On top of the old check (swear words and slurs, with numbers and symbols standing in for letters, repeated letters
-- and dots between letters), it also catches:
--   * letters hidden with * or # (f*ck, sh*t, f***),
--   * words spelled out with spaces or dots ("f u c k"),
--   * more words: damn, crap, hell, bloody, dumbass, jackass, wtf, stfu and others.
-- Keep the patterns the same as badWords in build/patches/patch_marketplace.py.

create or replace function public.rb_bad_words(p text)
returns boolean language sql immutable set search_path = ''
as $$
  with n as (select translate(lower(coalesce(p, '')), '013457@$!', 'oieastasi') as a),
       v as (select a from n
             union all
             select regexp_replace(a, '\m([a-z])[[:space:]._*-]+(?=[a-z]\M)', '\1', 'g') from n)
  select exists (
    select 1 from v
    where a ~ 'f+[._*-]*u+[._*-]*c+[._*-]*k+|b+[._*-]*i+[._*-]*t+[._*-]*c+[._*-]*h+|w+[._*-]*h+[._*-]*o+[._*-]*r+[._*-]*e+|s+[._*-]*l+[._*-]*u+[._*-]*t+|b+[._*-]*a+[._*-]*s+[._*-]*t+[._*-]*a+[._*-]*r+[._*-]*d+|a+[._*-]*s+[._*-]*s+[._*-]*h+[._*-]*o+[._*-]*l+[._*-]*e+|n+[._*-]*i+[._*-]*g+[._*-]*g+|f+[._*-]*a+[._*-]*g+[._*-]*g+[._*-]*o+[._*-]*t+|r+[._*-]*e+[._*-]*t+[._*-]*a+[._*-]*r+[._*-]*d+|m+[._*-]*o+[._*-]*t+[._*-]*h+[._*-]*e+[._*-]*r+[._*-]*f+|d+[._*-]*i+[._*-]*l+[._*-]*d+[._*-]*o+|p+[._*-]*u+[._*-]*s+[._*-]*s+[._*-]*y+|c+[._*-]*o+[._*-]*c+[._*-]*k+[._*-]*s+[._*-]*u+[._*-]*c+[._*-]*k+|t+[._*-]*w+[._*-]*a+[._*-]*t+|w+[._*-]*a+[._*-]*n+[._*-]*k+|j+[._*-]*i+[._*-]*z+[._*-]*z+|s+[._*-]*h+[._*-]*i[._*-]*t+'
       or a ~ '\m(ass|asses|dick|dicks|cock|cocks|cum|tit|tits|piss|fag|fags|fuk|fck|hoe|hoes|kike|spic|spics|chink|tranny|rape|raping|rapist|nazi|porn|pedo|kys|nigga|niggas|cunt|cunts)\M'
       or a ~ '\m(damn|damned|dammit|goddamn|crap|crappy|hell|bloody|bugger|bollocks|prick|pricks|dumbass|jackass|smartass|asshat|asswipe|wtf|stfu|gtfo|douche|douchebag|skank|mf|mfer)\M'
       or a ~ 'f[*#]+c?k|f[*#]{2,}|sh[*#]+t|b[*#]+t?ch|c[*#]+nt|d[*#]+ck|a[*#]{2}|p[*#]+ss');
$$;