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
| `functions/api/import.js` | Cloudflare Pages Function `GET /api/import?url=` — pulls a decklist from a deck page link (textarea/pre, embedded JSON like Piltover Archive, or "3 Card Name" lines). RiftDecks blocks servers (403), so the client tells people to use Export TXT instead. |
| `build/patches/` | The build: `patch_*.py` scripts, each a string-replace transform that **asserts its anchor text exists** (fails loudly if an earlier change moved it). `build.py` makes `cards.js` from raw Riftcodex rows + `build/tcg/*`. |
| `build/base/shared.html` | The original base page every website build starts from. |
| `build/tcg/` | Inputs for `build.py`: `prices.txt` (`productId:price[f]`, f = foil-only), `fx.txt` (USD→CAD `rate|date`, Bank of Canada), `extras.txt` (TCGplayer-only printings), `ven_map.txt`, `images.txt` (Riftcodex image file per card), `tcg_photos.txt`, `bans.txt` (`name|std or 2v2|since`). The weekly task's working copies live in Brandon's claude.ai Project "Personal" under `claude/riftbound-collection/`; keep them in sync if you change one. |
| `build/sql/` | Supabase SQL, run by Brandon in Supabase → SQL Editor: `supabase_setup.sql` (collections table), `supabase_sharing.sql` (shared_decks), `supabase_wishlist.sql` (wish column), `supabase_links.sql` (private share links), `supabase_offers.sql` (offers on shopping lists), `supabase_offer_threads.sql` (counter offers, trade cards, bad-word filter — see "Pending"). |
| `build/tests/` | `smoke.py` (loads the built site with stand-in images + fake Supabase; checks no JS errors, filters, info sheet), `links_test.py` (end-to-end private links), `fake_supabase.js` (in-browser stand-in that enforces the same rules as the real database). |
| `build/make.sh` | Rebuilds `index.html`; `--local` also builds the local Desktop copy. |

## Build

```
./build/make.sh                      # rebuilds index.html from build/base/shared.html
python3 build/tests/smoke.py         # needs playwright + Chromium
```
Website pipeline (order matters):
`patch_local → patch_bans → patch_web → patch_accounts → patch_sharing → patch_mobile → patch_wish → patch_polish → patch_foil → patch_info → patch_links → patch_share_tidy → patch_decks_ui → patch_friends_ui → patch_shop → patch_offers → patch_shop_add → patch_uisize → patch_friends_size → patch_fixes → patch_chime → patch_offer_threads → patch_marketplace`

To change the site: edit the right patch (usually add to the latest one — `patch_info.py` for card/filter UI,
`patch_links.py` for sharing — or start a new `patch_<name>.py` appended to the end of the pipeline in
`make.sh`), run `make.sh`, run the tests, look at a screenshot at desktop (1400px) and phone (390px) widths, then commit
`index.html` together with the patch. Never hand-edit `index.html`; the next build would wipe it.

What each patch does: local = thumbnails + enlarged preview (lightbox) + image URLs; bans = Banned pills/chip;
web = website wording; accounts = Supabase sign-in + cloud save; sharing = shared decks + Friends tab; mobile = grid view,
pager, S/M/L sizes, phone layout; wish = Token filter + Wish List tab; polish = tab names, My Decks intro, deck import,
list sizes, Friends sections; foil = rainbow shine on foil-only cards; info = card info sheet in the preview, keyword
and tag filters, ability search, page-number box, Reset filters; links = private share links; share_tidy = no trades-contact field, share name = "Name This Shared Deck/Wishlist" (the title friends see, no "by …"), no sharing an empty wish list; decks_ui = My Decks workspace (I have taps change the collection; the Need − / + was removed in patch_marketplace, list/grid S-M-L via st.dview + st.size, rule checks, add a card); friends_ui = Friends card lines with picture, "you have N", tap to preview; shop = Shopping List tab (missing cards across decks, settings in wish._shop, shared as deck_id "__shop__"); offers = friends send offers on a shared shopping list (RPC make_offer, table shop_offers, needs supabase_offers.sql), owner sees them in Shopping List; shop_add = Add a Card box in Shopping List (wish._shop.extra {card id: copies}), CA + US prices on the list; uisize = Page size S/M/L (CSS zoom on body, localStorage rb-ui-size); friends_size = S-M-L card lines and a sort menu in Friends (st.size, st.frsort); fixes = small bug fixes (Friends buttons use frLast when frCache was cleared); chime = cute poro "brrr-eep!" + mystical "ca-ching" (synthesized, not a recording) + "New" tag for new offers, offers checked every minute (rb-offers-seen, rb-offer-sound); offer_threads = counter offers / replies (thread + status per offer), cards you'd trade in an offer, bad-word filter (badWords here = rb_bad_words in SQL, keep the patterns the same); offerers keep secret reply codes in rb-my-offers / wish._myoffers; marketplace = the Shopping List tab renamed Marketplace (still `t-shop`/`view-shop`/`renderShop` in code), laid out Incoming Offers → Shopping List Overview → Add a Card to Shopping List → "My Shopping List" header → one small box with filters (search/domain/type/rarity, not saved) + sort/size/layout → cards; each card has a To buy − / + (deck cards: wish._shop.adj offsets), Need/Have, its decks, and "+ Collected 1" (undoable: note with Undo + "↶ Undo Collected" by the header, `shUndo`/`undoCollected`, this visit only); shared shopping list name starts blank with a note; 🛒 Buy button beside ♡ Want on every card (`shopBtn`, each tap adds one more copy to wish._shop.extra, the button shows the count and a `#shop-toast` note pops up at the bottom; lowering/removing is done in Marketplace; `setShopN` updates the buttons in place). Marketplace headers fold (`mkFold`, localStorage rb-mk-fold). Friends' shopping lists live at the end of Marketplace ("Friends' Shopping Lists", own filters `mkf`), not in Friends: renderFriends still builds them in #fr-list and groupFriends moves them into #mk-frlist, so every #fr-list listener is registered on both via `frListen`. Their search matches card names and list/owner names. Each incoming offer folds by tapping the sender's name (`offFold`, rb-offer-fold). New-offer sound: `coinChime()` plays the picked one, `konbiniChime` (default, original konbini-style chime) or `poroCoin` (the old poro + ca-ching), chosen in a menu by Sound on/off (rb-offer-chime). The offer form has "Your Offer Preview" (`offerPreview`): pictures of the cards being given and traded.

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
local pipeline: `patch_local → patch_bans → patch_mobile → patch_wish → patch_polish → patch_foil → patch_info`) and copy the three
files from `build/out/` into that folder. Personal decks are never part of this repo or the build.

## Weekly refresh (already scheduled)

The site header says so ("updated every Monday", last and next update, `#c-sched` in patch_marketplace); if the
schedule changes, change that wording too.

A Claude scheduled task, "Riftbound card list and prices refresh", runs Mondays 8:47am Pacific. It re-fetches the
card list/images (Riftcodex), prices (tcgcsv.com, TCGplayer category 89) and the exchange rate, rebuilds `cards.js`
with `build.py`, publishes two claude.ai artifacts and pushes only `cards.js` here. It uses the Project copies of
`build.py` and `tcg/*`. The GitHub Action separately refreshes `text.js` every Monday.

## Pending / known gaps

- `supabase_links.sql` has been run (Oct 14, 2026). `supabase_offers.sql` has been run too. **Brandon must run `build/sql/supabase_offer_threads.sql`** for counter offers,
  trade cards and the server-side bad-word check; until then offers stay one-way and trade cards are refused.
- 26 printings have no text in `text.js` (Kennen – Heart of the Tempest, double-sided tokens like "Bird // Buff").
- The site is tested with a fake Supabase; real-database behaviour should be checked after SQL changes
  (share a deck, open its link in a private window).

## Conventions

- Commit as `itsbrandontryingthings`; fetch + rebase on `origin/main` before pushing (the Action and weekly task also push).
- Keep wording friendly and plain; headings in Title Case; tab names: Collection, Open Packs, My Decks, Wish List, Marketplace, Friends.
- On a Windows PC (Git for Windows + Python from python.org) there's no `python3`: run the build as
  `bash -c 'python3(){ python "$@"; }; export -f python3; ./build/make.sh'` and the tests with `python -X utf8`.
- After a change, tell Brandon in a couple of sentences what changed and where to see it.
