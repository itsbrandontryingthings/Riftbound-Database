# Riftbound Database — guide for Claude Code

A free card database and collection tracker for the Riftbound TCG, live at **https://rbdatabase.pages.dev**
(Cloudflare Pages, auto-deploys from `main` of this repo, about a minute after a push). Owner: Brandon
(GitHub `itsbrandontryingthings`). He's not a developer: explain changes in plain words, test before pushing,
and keep the site working on phones.

## What's in the repo

| Path | What it is |
|---|---|
| `index.html` | The whole website (one file: HTML + CSS + JS). **Generated** — edit the patch scripts, not this file directly (see Build). |
| `cards.js` | Card data: `window.RB_META` (sets, dates, fx, counts) and `window.RB_CARDS` (one object per printing: id, set, num, name, type, rarity, domains, variant, tcg id, price in USD, foil, img/imgTcg/imgBase, ban/banSince, token…). Refreshed weekly by a scheduled task (see below). |
| `text.js` | Rules text, stats, flavour and tags: `window.RB_TEXT = {updated, n: {normalized name: [energy, might, power, text, flavour, tags, supertype]}, a: {riftbound_id or "tcg:<id>": artist}}`. Built by `tools/fetch_text.py` in GitHub Actions (`.github/workflows/card-text.yml`, Mondays + on change), which commits it. Flavour is cleaned there (Riftcodex drops opening quotes, leaves `<em?` junk); a speaker is stored as `"\n— Name"`. |
| `404.html` | Hand-written "Page Not Found" page (not generated). With it, Cloudflare Pages answers unknown paths with a real 404 instead of serving `index.html` (its default when no 404.html exists), so bot/scanner probes (`/.env`, `/info.php`…) show up as 404s in analytics, separate from real visits. |
| `functions/api/import.js` | Cloudflare Pages Function `GET /api/import?url=` — pulls a decklist from a deck page link (textarea/pre, embedded JSON like Piltover Archive, or "3 Card Name" lines). RiftDecks blocks servers (403), so the client tells people to use Export TXT instead. |
| `build/patches/` | The build: `patch_*.py` scripts, each a string-replace transform that **asserts its anchor text exists** (fails loudly if an earlier change moved it). `build.py` makes `cards.js` from raw Riftcodex rows + `build/tcg/*`. |
| `build/base/shared.html` | The original base page every website build starts from. |
| `build/tcg/` | Inputs for `build.py`: `prices.txt` (`productId:price[f]`, f = foil-only), `fx.txt` (USD→CAD `rate|date`, Bank of Canada), `extras.txt` (TCGplayer-only printings), `ven_map.txt`, `images.txt` (Riftcodex image file per card), `tcg_photos.txt`, `bans.txt` (`name|std or 2v2|since`). The weekly task's working copies live in Brandon's claude.ai Project "Personal" under `claude/riftbound-collection/`; keep them in sync if you change one. |
| `build/sql/` | Supabase SQL, run by Brandon in Supabase → SQL Editor: `supabase_setup.sql` (collections table), `supabase_sharing.sql` (shared_decks), `supabase_wishlist.sql` (wish column), `supabase_links.sql` (private share links), `supabase_offers.sql` (offers on shopping lists), `supabase_offer_threads.sql` (counter offers, trade cards, bad-word filter — see "Pending"), `supabase_offer_revise.sql` (revising an offer you made), `supabase_bad_words.sql` (stricter bad-word check). |
| `build/tests/` | `smoke.py` (loads the built site with stand-in images + fake Supabase; checks no JS errors, filters, info sheet), `links_test.py` (end-to-end private links), `offers_withdraw_test.py` (make an offer, withdraw it, check it's gone for both people), `offers_live_test.py` (a new offer and a counter offer show up with the sound without a refresh, and the "tap to turn on sounds" note; ~1 min), `fake_supabase.js` (in-browser stand-in that enforces the same rules as the real database). |
| `build/make.sh` | Rebuilds `index.html`; `--local` also builds the local Desktop copy. |
| `build/og/` | `og.html` (link preview picture: RBDB logo + a fan of cards with the "armpit Shen" (no foil, faint green glow), Shen - Eye of Twilight VEN 193, in the middle) and `logo.html` (the RBDB logo); `render.py` (Playwright) makes `og-image.jpg` and `logo-512.png` at the repo root. Re-run it after changing either page. |

## Build

```
./build/make.sh                      # rebuilds index.html from build/base/shared.html
python3 build/tests/smoke.py         # needs playwright + Chromium
```
Website pipeline (order matters):
`patch_local → patch_bans → patch_web → patch_accounts → patch_sharing → patch_mobile → patch_wish → patch_polish → patch_foil → patch_info → patch_links → patch_share_tidy → patch_decks_ui → patch_friends_ui → patch_shop → patch_offers → patch_shop_add → patch_uisize → patch_friends_size → patch_fixes → patch_chime → patch_offer_threads → patch_marketplace → patch_social → patch_sliders → patch_art → patch_deck_sort → patch_wish_lists → patch_withdrawn → patch_offer_live → patch_sound → patch_filters → patch_halloween → patch_winter → patch_perf → patch_sets → patch_special → patch_fresh`

To change the site: edit the right patch (usually add to the latest one — `patch_info.py` for card/filter UI,
`patch_links.py` for sharing — or start a new `patch_<name>.py` appended to the end of the pipeline in
`make.sh`), run `make.sh`, run the tests, look at a screenshot at desktop (1400px) and phone (390px) widths, then commit
`index.html` together with the patch. Never hand-edit `index.html`; the next build would wipe it.

What each patch does: local = thumbnails + enlarged preview (lightbox) + image URLs; bans = Banned pills/chip;
web = website wording; accounts = Supabase sign-in + cloud save; sharing = shared decks + Friends tab; mobile = grid view,
pager, S/M/L sizes, phone layout; wish = Token filter + Wish List tab; polish = tab names, My Decks intro, deck import,
list sizes, Friends sections; foil = rainbow shine on foil-only cards; info = card info sheet in the preview, keyword
and tag filters, ability search, page-number box, Reset filters; links = private share links; share_tidy = no trades-contact field, share name = "Name This Shared Deck/Wishlist" (the title friends see, no "by …"), no sharing an empty wish list; decks_ui = My Decks workspace (I have taps change the collection; the Need − / + was removed in patch_marketplace, list/grid S-M-L via st.dview + st.size, rule checks, add a card); friends_ui = Friends card lines with picture, "you have N", tap to preview; shop = Shopping List tab (missing cards across decks, settings in wish._shop, shared as deck_id "__shop__"); offers = friends send offers on a shared shopping list (RPC make_offer, table shop_offers, needs supabase_offers.sql), owner sees them in Shopping List; shop_add = Add a Card box in Shopping List (wish._shop.extra {card id: copies}), CA + US prices on the list; uisize = Page size S/M/L (CSS zoom on body, localStorage rb-ui-size); friends_size = S-M-L card lines and a sort menu in Friends (st.size, st.frsort); fixes = small bug fixes (Friends buttons use frLast when frCache was cleared); chime = cute poro "brrr-eep!" + mystical "ca-ching" (synthesized, not a recording) + "New" tag for new offers, offers checked every minute (rb-offers-seen, rb-offer-sound); offer_threads = counter offers / replies (thread + status per offer), cards you'd trade in an offer, bad-word filter (badWords here = rb_bad_words in SQL, keep the patterns the same); offerers keep secret reply codes in rb-my-offers / wish._myoffers; marketplace = the Shopping List tab renamed Marketplace (still `t-shop`/`view-shop`/`renderShop` in code), laid out Incoming Offers → Shopping List Overview → Add a Card to Shopping List → "My Shopping List" header → one small box with filters (search/domain/type/rarity, not saved) + sort/size/layout → cards; each card has a To buy − / + (deck cards: wish._shop.adj offsets), Need/Have, its decks, and "+ Collected 1" (undoable: note with Undo + "↶ Undo Collected" by the header, `shUndo`/`undoCollected`, this visit only); shared shopping list name starts blank with a note; 🛒 Buy button beside ♡ Want on every card (`shopBtn`, each tap adds one more copy to wish._shop.extra, the button shows the count and a `#shop-toast` note pops up at the bottom; lowering/removing is done in Marketplace; `setShopN` updates the buttons in place). Marketplace headers fold (`mkFold`, localStorage rb-mk-fold). Friends' shopping lists live at the end of Marketplace ("Friends' Shopping Lists", own filters `mkf`), not in Friends: renderFriends still builds them in #fr-list and groupFriends moves them into #mk-frlist, so every #fr-list listener is registered on both via `frListen`. Their search matches card names and list/owner names. Each incoming offer folds by tapping the sender's name (`offFold`, rb-offer-fold). New-offer sound: `coinChime()` plays `poroCoin` (the poro + ca-ching; the konbini chime and its menu were removed in patch_offer_live), with Sound on/off (rb-offer-sound). Offers can ask for cards back ("Cards you'd want", a straight swap): they're stored in the same `trade` jsonb as the cards offered, with `id` = `"want:<card id>"` (rb_cards_clean keeps name/q/id, so no SQL change); `tradeGive`/`tradeWant` split them. The offer form has "Your Offer Preview" (`offerPreview`): pictures of the cards being given and traded; social = Open Graph / Twitter tags in <head> (title, description, og-image.jpg) so links show a preview card in Discord etc., plus logo-512.png as the tab / home-screen icon and in front of the page heading, which reads "Riftbound Database" (was "Riftbound - Complete Database"; the offline copy still says the old name). Discord caches previews: add `?v=2` to the link to see a new one; sliders = Energy and Might range sliders (0–12, two handles) in every filter area: Collection, Wish List, My Shopping List, Friends' Shopping Lists (`RNG.c/w/s/f`, `rngOK` uses txOf e/m; narrowed = cards without that stat drop out); Reset filters clears them; this visit only. Any new filter area should get them too; art = decorative champion-art banners at the top (header panel overlaps it) and bottom of the page, zoomed into the illustration (`.art-t img` needs `max-width:none`, the base `img{max-width:100%}` undoes the zoom). Keep them cheap to draw: no backdrop-filter, mask-image or CSS filters (they made scrolling laggy); fades are gradient overlays; each strip is its own layer (contain:strict + translateZ), the bottom one is skipped off-screen (content-visibility:auto). Heights: top 200px / bottom 160px (phone 120 / 104); deck_sort = My Decks Sort menu (st.dsort: "" = set order, the default; list / name / energy / price), sorts each section on screen only (`dkSortRows`), the decklist text keeps its order; wish_lists = named lists inside the Wish List ("Master Yi Deck", "Art Deck"…): `wish._folders` [{id, name}] + `wish._wf` {list id: {card id: copies}}, while `wish[id]` stays the total (so sharing, trades and offers are unchanged) and copies in no list are "General" (`wfIn("", id)`); `wfSet` changes one list and the total, `wfClean` trims lists to the total. ♡ Want opens the picker `#wf-dlg` (`wfOpen`; tick lists, copies per list, Create & add, Remove from wish list). Wish List tab: list chips (All / General / each list / + New List, `st.wfold`: "" = All, "~gen" = General), Rename / Delete list (cards stay, under General); under All each card shows tags for its lists (plus a grey General tag when some copies are in no list); counts, cost, Copy and Add a Card follow the chosen list; Share is only shown under All and shares the whole wish list. withdrawn = withdrawn offers are hidden on both sides (the row stays in shop_offers with status 'withdrawn'; filtered in `loadOffers` / `loadMyOffers`), an "Offer withdrawn." note pops up, and a just-sent offer shows under "Your offers on this list" at once (`await loadMyOffers`); offer_live = offers checked every 10 s while the page is visible and on focus / coming back (`offerPoll`; busy flags are timestamps so a stuck request can't block polling), Incoming Offers redraws itself (`offersRedraw`, waits while you type in it), and counter offers / answers on offers you made show at the top of Incoming Offers under "Counter Offers on Your Offers" (`myOffersHTML(null, isCounter)`: open + last message from the owner, or New), with the same buttons (`moListen` adds #shop-offers), signed in or not; sound = the poro coin is rendered once (OfflineAudioContext, `poroGraph`) into a WAV played by an <audio> element (`chimeEl`; iPhones play those even on silent). Every play is that one recording (`chimeBuf`, normalized once to peak 0.1225: Brandon asked for half of the first 0.7, then 65% quieter; the Web Audio fallback plays the same buffer, never the quiet live graph) and a chime never starts while one is playing (`chimeAt`), so the loudness never changes, unlocked on every tap (`soundWake`), Web Audio as fallback; new offers call `offerChime()`, which shows a "Tap anywhere on the page to turn on sounds" note once a visit if the browser blocks it. Headless test browsers allow sound without a tap, so offers_live_test fakes the tap-first rule (`TAP_FIRST`); filters (last in both pipelines) = Collection domain chips match cards with ALL picked domains (Calm + Order + Legend = Shen, Azir, Ivern, Leona), and Type splits Unit into "Regular Unit" (value still `Unit`) + "Champion Unit" (`__champ`) + "Signature Unit" (`__sigunit`), Spell into "Spell" + "Signature Spell" (`__sig`), Gear into "Gear" + "Signature Gear" (`__siggear`), by text.js supertype (`TYPE_SUB`, `subOf`, `typeOK`); the plain types leave out the split-off cards; halloween (website only, last) = seasonal look that turns itself on by date: autumn Sep 22 – Nov 30 (`html.fall`: orange accent, warm glow on the top art and header) and Halloween Oct 1 – Nov 1 (`html.spooky`, Teemo themed: pumpkin/leaf/mushroom garland on the header, 🎃 after the title, a "Happy Halloween from Captain Teemo!" note with his face in a witch-hat frame (`.hw-hi`), bats over the top art, and the bottom art strip swapped for an all-Teemo strip (`.hw-teemo`) with a pumpkin and mushroom patch). Leaves fall behind the page content (`.hw-fall`, z-index -1; Brandon didn't want them over the cards); winter (website only, after halloween) = Nov 2 – Jan 6 (`html.winter`; autumn ends Nov 1): icy blue accent and glow, snow piled on the header with twinkling Christmas lights under it, 🎄 after the title, twinkling ❄ over the top art, "Happy Holidays from Captain Teemo!" in a Santa hat and beard (`.xm-hi`), presents/trees/snowmen along the bottom art. Light snowfall behind the page content (`.xm-fall`, z-index -1, so it never covers cards). `?season=winter` previews it. `?season=halloween|fall|off` previews it any time. Emoji + transform/opacity animations only, off for reduced motion. perf = keeps the site light so videos in other tabs don't stutter: the foil shine moves on every foil card again (Brandon asked for it back after a hover-only try; it's the heaviest animation, color-dodge repainted every frame), and the Web Audio fallback context is suspended once the <audio> chime is unlocked (`audioRest`) instead of being woken on every tap and left running. Every animation pauses while the window isn't focused (`html.rb-idle`, `rbIdle`), so a page left open on another monitor draws nothing (the seasonal decorations made Chrome draw frames nonstop). Keep new decorations to transform/opacity animations; never an infinite animation of background-position, filters or blend modes on many elements. sets (website only, last) = a Set menu (All sets / Vendetta / Unleashed / Spiritforged / Origins…, from RB_META.sets, sets with cards only) in every filter area: Collection's Filters panel (`#cset`, the same `st.set` as the set buttons at the top, kept in step in `render`), Wish List (`wlf.set`), My Shopping List (`shf.set`) and Friends' Shopping Lists (`mkf.set`); Reset filters clears it. Any new filter area should get it too. special (last in both pipelines) = "Only alt arts, overnumbered and promos" checkbox (`#only`, `st.only`) under "Show alt arts…" in Collection's Filters: hides regular cards (`isVariant`); ticking Only ticks Show, unticking Show unticks Only; counts and cost to complete follow it; Reset filters clears it. fresh (website only, last) = a new visit (new tab / window / browser session, marked by sessionStorage `rb-visit`) starts with every filter cleared (what Reset filters clears, plus the Wish List chip `st.wfold`) on the Collection tab; a refresh in the same tab keeps them. Display choices in rb-filters (list/grid, sizes, sort, currency) are kept.

## How the site works (key facts)

- Images come from Riot's CDN via Riftcodex: `https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/<file>?accountingTag=RB&fm=webp&q=92` (add `&w=N` for smaller). Use `referrerpolicy="no-referrer"`. TCGplayer photos are the fallback.
- Accounts: Supabase project `https://unemhzpqaygxpdjmtvuh.supabase.co`; the anon/publishable key is in `patch_accounts.py` (public by design). Table `collections` (id = user, counts, decks, wish jsonb) is owner-only via RLS. **Never ask for, store or use the database password.** Schema changes are SQL files for Brandon to run.
- Signed-out visitors save in localStorage; signing out clears local data.
- Sharing (after `supabase_links.sql`): each shared deck/wish list row in `shared_decks` has a secret `share_token`. Nobody can list rows (owners see only their own); viewers call RPC `get_shared(p_tokens text[])` (security definer, granted to anon). Link format: `https://rbdatabase.pages.dev/#share=<token>`. Stop sharing deletes the row (link dies); every Stop sharing button asks "Are you sure…?" first (`stopShareOK`, a browser confirm, so tests must accept dialogs). Wish list = row with `deck_id "__wish__"`. Links someone has opened are kept in localStorage `rb-links` and synced inside `wish._links` (keys starting with `_` aren't cards).
- Foil-only printings (`c.foil`) get the shine; every card tilts toward the pointer in the preview.
- Brandon prefers CAD + USD shown together; TCGplayer market prices are USD.

## The local Desktop copy

Brandon also keeps an accounts-free copy on his home PC: `C:\Users\brand\Desktop\Riftbound Database\Riftbound Database\`
(`Riftbound Database.html` + `cards.js` + `text.js`). Build it with `./build/make.sh --local` (same base page as the website;
local pipeline: `patch_local → patch_bans → patch_mobile → patch_wish → patch_polish → patch_foil → patch_info → patch_filters → patch_special`) and copy the three
files from `build/out/` into that folder. Personal decks are never part of this repo or the build.

## Weekly refresh (already scheduled)

The site header says so ("updated every Monday", last and next update, `#c-sched` in patch_marketplace); if the
schedule changes, change that wording too.

A Claude scheduled task, "Riftbound card list and prices refresh", runs Mondays 8:47am Pacific. It re-fetches the
card list/images (Riftcodex), prices (tcgcsv.com, TCGplayer category 89) and the exchange rate, rebuilds `cards.js`
with `build.py`, publishes two claude.ai artifacts and pushes only `cards.js` here. It uses the Project copies of
`build.py` and `tcg/*`. The GitHub Action separately refreshes `text.js` every Monday.

## Pending / known gaps

- All SQL files have been run in Supabase as of Oct 14, 2026: `supabase_links.sql`, `supabase_offers.sql`,
  `supabase_offer_threads.sql`, `supabase_offer_revise.sql` (revise offers, delete messages) and
  `supabase_bad_words.sql` (stricter `rb_bad_words`). The site checks words the same way (`badWords` +
  `BAD_MORE`/`BAD_MASK` in patch_marketplace); keep both pattern sets the same. A new SQL file is
  something Brandon runs in Supabase → SQL Editor; note it here until Brandon confirms "Success".
- **Radiance (RAD, released Oct 23, 2026) comes from TCGplayer for now**: Riftcodex hadn't added it at release, so its
  234 printings are rows in `build/tcg/extras.txt` (7th field = TCGplayer card type, so new cards get the right type and
  Champion/Signature flags), prices appended to `prices.txt`, photos in `tcg_photos.txt`, and `cards.js` was made with
  `build.py --extras-only build/tcg cards.js cards.js` (adds extras to an existing cards.js; no raw rows needed). `text.js`
  takes text from TCGplayer for any set Riftcodex doesn't list (`tcg_fallback` in `fetch_text.py`; plain words, no icons).
  **The weekly task uses the Project copies of `build.py`, `extras.txt` and `tcg_photos.txt`: they must get these changes
  (RAD in `SETS`, the 7th-field code, the RAD rows), or the Monday refresh drops Radiance.** Once Riftcodex has RAD, its
  rows win (extras with a known product id are skipped). 10 Signature printings have no picture anywhere yet.
- 26 printings have no text in `text.js` (Kennen – Heart of the Tempest, double-sided tokens like "Bird // Buff").
- The site is tested with a fake Supabase; real-database behaviour should be checked after SQL changes
  (share a deck, open its link in a private window).

## Working on more than one computer

GitHub is the one shared copy. Brandon works from more than one PC; don't copy or zip the project folder between
them, and don't put it in Dropbox / OneDrive (two syncs on one git folder can corrupt it).
- **Before any change:** `git pull` (this repo has `pull.rebase=true` and `rebase.autoStash=true`, so it rebases).
  If it reports a conflict, stop and explain it to Brandon before going on.
- **After a change:** commit, then **push it yourself** once the tests pass (Brandon asked for this on Oct 15, 2026):
  `git pull` then `GIT_TERMINAL_PROMPT=0 git push origin main`. Git Credential Manager on the home PC already has his
  GitHub sign-in. If the push fails (no sign-in yet on a new PC, a browser window needed, a conflict), tell him and give
  him the command: `git -C "C:\Users\brand\Desktop\Riftbound Database\repo" push origin main` (PowerShell has no `&&`).
- **New PC:** `git clone https://github.com/itsbrandontryingthings/Riftbound-Database.git repo` inside
  `Desktop\Riftbound Database`, then set `pull.rebase true` / `rebase.autoStash true`, and `user.name` /
  `user.email` as below. The offline copy (`Riftbound Database\Riftbound Database\`) is rebuilt with
  `./build/make.sh --local`, never copied.

## Conventions

- Commit as `itsbrandontryingthings` <itsbrandontryingthings@users.noreply.github.com>; pull (rebase) on `origin/main` before pushing (the Action and weekly task also push).
- Keep wording friendly and plain; headings in Title Case; tab names (in this order): Collection, Open Packs, My Decks, Marketplace, Wish List, Friends. The Wish List has
  its own Add a Card box and filters (`wlf`, `wlAdd`, in patch_marketplace).
- On a Windows PC (Git for Windows + Python from python.org) there's no `python3`: run the build as
  `bash -c 'python3(){ python "$@"; }; export -f python3; ./build/make.sh'` and the tests with `python -X utf8`.
  The home PC has the full python.org Python 3.12 (per-user, with pip) in `%LOCALAPPDATA%\Programs\Python\Python312`,
  on the user PATH with a `python3.exe` copy, so `./build/make.sh` runs as is. Playwright 1.64 + its Chromium are
  installed there too: `python -X utf8 build\tests\smoke.py` passes (Oct 14, 2026).
  (Its installer fails with 1603 while Windows has a restart pending.)
- After a change, tell Brandon in a couple of sentences what changed and where to see it.
- **Every push: confirm it's live.** After each push (yours, or Brandon's if he pushed), check that `git status -sb` shows nothing
  ahead of `origin/main` (if it does, the push didn't go through: tell him and give the command again), then watch
  https://rbdatabase.pages.dev until it serves the new version (curl with a cache-busting `?nc=` query and grep for
  a string the change added or changed; a background loop every ~15 s), and tell him it's live and at what time.
  Don't call it done until the live site shows the change.
