#!/usr/bin/env python3
"""Shopping List tab (website; runs last, after patch_friends_ui.py).
- New tab "Shopping List": every card your decks (My Decks) still need after your collection, with pictures that
  open the preview, which decks need it, cost at the cheapest printing, and "Bought 1" (adds that printing to your
  collection, like the deck I have buttons). Choose decks, count cards shared by decks once or add them up,
  include the sideboard or not, sort, list or grid at S-M-L, copy the list.
- Share by private link like decks and wish lists: row deck_id "__shop__", list = "N Card name" lines, kept up to
  date when your decks or collection change. Settings live in wish._shop {shared, name, skip:[deck ids], sum, noSide}
  (saved with the wish list, so they follow your account).
- Friends: a shared shopping list shows under "Shopping Lists" like a wish list (🛒, what you could trade them).
Usage: patch_shop.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

# ---------- tab + view
rep('''    <button role="tab" id="t-wish" aria-selected="false" aria-controls="view-wish">Wish List</button>''',
    '''    <button role="tab" id="t-wish" aria-selected="false" aria-controls="view-wish">Wish List</button>
    <button role="tab" id="t-shop" aria-selected="false" aria-controls="view-shop">Shopping List</button>''')
rep('''  <section class="view" id="view-decks" role="tabpanel" aria-labelledby="t-decks" hidden>''',
    '''  <section class="view" id="view-shop" role="tabpanel" aria-labelledby="t-shop" hidden>
    <div class="panel" id="shop-summary"></div>
    <div id="shop-body"></div>
  </section>

  <section class="view" id="view-decks" role="tabpanel" aria-labelledby="t-decks" hidden>''')
rep('''["collection","packs","decks","friends","wish"]''', '''["collection","packs","decks","friends","wish","shop"]''', count=3)
rep('''  if (t === "wish") renderWish();
  if (t === "friends") renderFriends();''', '''  if (t === "wish") renderWish();
  if (t === "shop") renderShop();
  if (t === "friends") renderFriends();''')
rep('''if (st.tab === "wish") renderWish(); LS.set("rb-filters"''', '''if (st.tab === "wish") renderWish(); if (st.tab === "shop") renderShop(); LS.set("rb-filters"''')
# collection changes keep the list (and a shared list) up to date
rep('''  renderSummary(); queueSave();
  if (st.tab === "decks") renderDecks();''', '''  renderSummary(); queueSave();
  if (st.tab === "decks") renderDecks();
  if (st.tab === "shop") renderShop();
  if (wish._shop && wish._shop.shared && typeof syncShared === "function") syncShared();''')

# ---------- shopping list logic + view (after the deck workspace helpers)
rep('''function saveDeckView(){''', r'''// ---- Shopping List: what your decks still need after your collection
const shopP = () => wish._shop || {};
function setShop(ch){ wish._shop = {...shopP(), ...ch}; saveWish(); renderShop(); }
function shopItems(){
  const P = shopP(), skip = new Set(P.skip || []), decks = allDecks().filter(d => !skip.has(d.id)), need = {}, by = {};
  let unknown = 0;
  for (const d of decks){
    const per = {};
    for (const s of parseDeck(d.text)) if (!P.noSide || !isSide(s)) for (const r of s.rows){ if (!groups[r.key]){ unknown++; continue; } per[r.key] = (per[r.key] || 0) + r.q; }
    for (const [k, q] of Object.entries(per)){ need[k] = P.sum ? (need[k] || 0) + q : Math.max(need[k] || 0, q); (by[k] ||= []).push({name: d.name, q}); }
  }
  const items = Object.entries(need).map(([key, q]) => {
    const owned = ownedOf(key), buy = Math.max(0, q - owned), cheap = cheapestOf(key), show = cheap || groups[key][0];
    return {key, name: groups[key][0].name, need: q, owned, buy, cheap, show, decks: by[key], cost: cheap ? buy * cheap.price : 0};
  }).filter(x => x.buy > 0);
  const sort = P.sort || "cost";
  items.sort(sort === "name" ? (a, b) => a.name.localeCompare(b.name) : sort === "set" ? (a, b) => CARDS.indexOf(a.show) - CARDS.indexOf(b.show) : (a, b) => b.cost - a.cost || a.name.localeCompare(b.name));
  return {items, decks, unknown};
}
const shopText = () => shopItems().items.map(x => `${x.buy} ${x.name}`).join("\n");
function shopRowHTML(x, view, size){
  const c = x.show, dom = c.domains && c.domains[0] ? `--dc:var(--${c.domains[0].toLowerCase()})` : "";
  const name = `<a href="${tcgURL(x.cheap || c)}" target="_blank" rel="noopener" title="Open ${esc(x.name)} on TCGplayer">${esc(x.name)}</a>`;
  const decks = `<span class="sh-decks">${x.decks.map(d => `<span>${esc(d.name)} <b>${d.q}</b></span>`).join("")}</span>`;
  const price = x.cheap ? `<span class="dk-price"><b>${esc(m1(x.cost))}</b>${FX && st.cur === "both" ? `<small>${esc(usd(x.cost))}</small>` : ""}<small>${x.buy} × ${esc(m1(x.cheap.price))}</small></span>` : `<span class="dk-price"><small>No price</small></span>`;
  const status = `<span class="dk-buy">buy ${x.buy}</span><span class="meta">need ${x.need} · have ${x.owned}</span>`;
  const bought = `<button class="btn sh-got" data-got="${esc(x.key)}" title="Adds 1 ${esc(c.name)} (${esc(codeOf(c))}) to your collection">+ Bought 1</button>`;
  const ban = banPill((groups[x.key] || []).find(z => z.ban));
  if (view === "grid") return `<div class="card tile dk-tile" style="${dom}">${thumbHTML(c, PHONE() && size === "s" ? 480 : 744)}
    <span class="tname">${name}</span><div class="tsub">${esc(codeOf(c))}</div><div class="dk-st">${status}</div>${decks}<div class="dk-st">${price}</div>${bought}</div>`;
  return `<div class="dk-card sh-card" style="${dom}">${thumbHTML(c, size === "s" ? 160 : 744)}
    <div class="dk-main"><div class="dk-top"><span class="name">${name}</span>${price}</div>
      <div class="dk-sub"><span class="dk-q">${x.buy}× <span>${esc(c.type)}</span></span><span class="dk-set" style="--sc:var(--${setCol[c.set] || "line"})">${esc(setName[c.set] || c.set)} · ${esc(codeOf(c))}</span>${ban}</div>
      <div class="dk-st">${status}</div>${decks}<div class="sh-act">${bought}</div></div></div>`;
}
function renderShop(){
  const P = shopP(), all = allDecks(), view = st.sview === "grid" ? "grid" : "list", size = ["s","m","l"].includes(st.size) ? st.size : "m";
  if (!all.length){
    $("shop-summary").innerHTML = `<h2>Shopping List</h2><p class="meta">Add a deck in <b>My Decks</b> and every card it still needs shows up here, after the cards in your collection.</p><div class="frow"><button class="btn primary" id="sh-go-decks">Go to My Decks</button></div>`;
    $("shop-body").innerHTML = ""; return;
  }
  const {items, decks, unknown} = shopItems(), skip = new Set(P.skip || []);
  const copies = items.reduce((a, x) => a + x.buy, 0), cost = items.reduce((a, x) => a + x.cost, 0), unpriced = items.filter(x => !x.cheap).length;
  const perDeck = d => { const s = dkStats(d); return s.need - s.have ? `${esc(m1(s.cost))} to finish` : "complete"; };
  $("shop-summary").innerHTML = `<h2>Shopping List</h2>
    <p class="meta">Every card your decks still need, after the cards in your collection. Tap a picture to see the card; tap <b>+ Bought 1</b> when you get one and it's added to your collection.</p>
    <div class="dk-tiles">
      <div class="dk-stat"><span class="collect-k">Cards to buy</span><span class="v">${copies}</span><small>${copies ? `cop${copies === 1 ? "y" : "ies"} across ${items.length} different card${items.length === 1 ? "" : "s"}` : "Nothing left to buy"}</small></div>
      <div class="dk-stat"><span class="collect-k">Total cost</span><span class="v${cost ? " warn" : ""}">${moneyHTML(cost)}</span><small>Cheapest printing of each${unpriced ? ` · ${unpriced} without a price` : ""}</small></div>
      <div class="dk-stat"><span class="collect-k">Decks included</span><span class="v">${decks.length} / ${all.length}</span><small>Tap a deck below to leave it out</small></div>
      <div class="dk-stat"><span class="collect-k">Biggest buy</span><span class="v sm">${items[0] && items[0].cheap ? `${esc(items[0].name)} ${esc(m1(items[0].cost))}` : "None"}</span><small>${items[0] && cost ? `About ${Math.round(items[0].cost / cost * 100)}% of the total` : "&nbsp;"}</small></div>
    </div>
    <div class="sh-decksel" role="group" aria-label="Decks to shop for">${all.map(d => `<button data-deck="${esc(d.id)}" aria-pressed="${!skip.has(d.id)}"><b>${esc(d.name)}</b><small>${perDeck(d)}</small></button>`).join("")}</div>
    <div class="frow">
      <button class="btn" id="sh-copy" ${items.length ? "" : "disabled"}>Copy shopping list</button>
      ${P.shared ? `<span class="tag ok">✓ Shared by link</span><button class="btn" id="sh-link">Copy share link</button><button class="btn" id="sh-unshare">Stop sharing</button>` : `<button class="btn" id="sh-share" ${items.length ? "" : "disabled"}>Share with friends</button>`}
    </div>
    ${unknown ? `<p class="meta">${unknown} card name${unknown === 1 ? " in your decks isn't" : "s in your decks aren't"} in the database, so ${unknown === 1 ? "it's" : "they're"} not on this list. Check the spelling in My Decks.</p>` : ""}`;
  const tools = `<div class="dk-tools" role="toolbar" aria-label="How to show the shopping list">
      <div class="seg" role="group" aria-label="Cards in more than one deck"><button id="sh-max" aria-pressed="${!P.sum}" title="A card in two decks is bought once, for the deck that needs the most">Shared cards once</button><button id="sh-sum" aria-pressed="${!!P.sum}" title="Buy enough to build every deck at the same time">Add up all decks</button></div>
      <div class="seg sizeseg" role="group" aria-label="Card size"><button id="shs-s" aria-pressed="${size==="s"}" title="Small cards">S</button><button id="shs-m" aria-pressed="${size==="m"}" title="Medium cards">M</button><button id="shs-l" aria-pressed="${size==="l"}" title="Large cards">L</button></div>
      <div class="seg" role="group" aria-label="Layout"><button id="shv-list" aria-pressed="${view==="list"}">List</button><button id="shv-grid" aria-pressed="${view==="grid"}">Grid</button></div>
      <select id="sh-sort" aria-label="Sort"><option value="cost" ${(P.sort || "cost") === "cost" ? "selected" : ""}>Sort: cost, high to low</option><option value="name" ${P.sort === "name" ? "selected" : ""}>Sort: name</option><option value="set" ${P.sort === "set" ? "selected" : ""}>Sort: set order</option></select>
      <label class="chk"><input type="checkbox" id="sh-side" ${P.noSide ? "" : "checked"}> Include sideboards</label>
    </div>`;
  $("shop-body").innerHTML = tools + (items.length
    ? `<div class="${view === "grid" ? `list grid dkg${size !== "s" ? " sz-" + size : ""}` : "dkl dkl-" + size}">${items.map(x => shopRowHTML(x, view, size)).join("")}</div>`
    : `<div class="empty">✓ You have every card ${decks.length === 1 ? "this deck needs" : decks.length ? "these decks need" : "… pick at least one deck above"}.</div>`);
}
$("shop-summary").addEventListener("click", e => {
  const id = e.target.id, dk = e.target.closest("[data-deck]");
  if (id === "sh-go-decks") return showTab("decks");
  if (dk){ const skip = new Set(shopP().skip || []); skip.has(dk.dataset.deck) ? skip.delete(dk.dataset.deck) : skip.add(dk.dataset.deck); return setShop({skip: [...skip]}); }
  if (id === "sh-copy"){ const {items} = shopItems(); copy(items.map(x => `${x.buy} ${x.name}` + (x.cheap ? ` — ${money(x.cost)} (${codeOf(x.cheap)})` : "")).join("\n") + `\n\nTotal: ${money(items.reduce((a, x) => a + x.cost, 0))}`, "shopping list"); }
  if (id === "sh-share" || id === "sh-link") openShare("shop");
  if (id === "sh-unshare") setShop({shared: false});
});
$("shop-body").addEventListener("click", e => {
  const id = e.target.id;
  if (id === "sh-max" || id === "sh-sum") return setShop({sum: id === "sh-sum"});
  if (/^shs-[sml]$/.test(id)){ st.size = id.slice(4); LS.set("rb-filters", {...st, doms:[...st.doms], limit:undefined}); return renderShop(); }
  if (id === "shv-list" || id === "shv-grid"){ st.sview = id === "shv-grid" ? "grid" : "list"; LS.set("rb-filters", {...st, doms:[...st.doms], limit:undefined}); return renderShop(); }
  const g = e.target.closest("[data-got]");
  if (g){ const c = cheapestOf(g.dataset.got) || groups[g.dataset.got][0]; adjust(c.id, 1); }
});
$("shop-body").addEventListener("change", e => {
  if (e.target.id === "sh-side") setShop({noSide: !e.target.checked});
  if (e.target.id === "sh-sort") setShop({sort: e.target.value});
});
function saveDeckView(){''')

# ---------- sharing: a third kind, "shop"
rep('''const curShareId = () => shareTarget === "wish" ? "__wish__" : curDeck;''',
    '''const curShareId = () => shareTarget === "wish" ? "__wish__" : shareTarget === "shop" ? "__shop__" : curDeck;''')
rep('''  $("share-done-title").textContent = shareTarget === "wish" ? "Your Wish List Link" : "Your Deck Link";''',
    '''  $("share-done-title").textContent = shareTarget === "wish" ? "Your Wish List Link" : shareTarget === "shop" ? "Your Shopping List Link" : "Your Deck Link";''')
rep('''  shareTarget = target === "wish" ? "wish" : "deck";
  $("share-title").textContent = shareTarget === "wish" ? "Share Your Wish List" : "Share This Deck";
  $("share-name-label").textContent = shareTarget === "wish" ? "Name This Shared Wishlist" : "Name This Shared Deck";''',
    '''  shareTarget = target === "wish" || target === "shop" ? target : "deck";
  $("share-title").textContent = shareTarget === "wish" ? "Share Your Wish List" : shareTarget === "shop" ? "Share Your Shopping List" : "Share This Deck";
  $("share-name-label").textContent = shareTarget === "wish" ? "Name This Shared Wishlist" : shareTarget === "shop" ? "Name This Shared Shopping List" : "Name This Shared Deck";''')
rep('''  const already = shareTarget === "wish" ? !!wish._shared : !!(customDecks.find(x => x.id === curDeck) || {}).shared;''',
    '''  const already = shareTarget === "wish" ? !!wish._shared : shareTarget === "shop" ? !!shopP().shared : !!(customDecks.find(x => x.id === curDeck) || {}).shared;''')
rep('''  $("share-name").value = shareTarget === "wish" ? (wish._shareName || "My Wish List") : (shareDeckName''',
    '''  $("share-name").value = shareTarget === "wish" ? (wish._shareName || "My Wish List") : shareTarget === "shop" ? (shopP().name || "My Shopping List") : (shareDeckName''')
rep('''$("share-msg").textContent = shareTarget === "wish" ? "Give your shared wish list a name." : "Give your shared deck a name.";''',
    '''$("share-msg").textContent = shareTarget === "wish" ? "Give your shared wish list a name." : shareTarget === "shop" ? "Give your shared shopping list a name." : "Give your shared deck a name.";''')
rep('''  if (shareTarget === "wish"){ wish._shared = true; wish._shareName = name; saveWish(); renderWish(); }
  else {''', '''  if (shareTarget === "wish"){ wish._shared = true; wish._shareName = name; saveWish(); renderWish(); }
  else if (shareTarget === "shop"){ setShop({shared: true, name}); }
  else {''')
rep('''[{ id: "__wish__", shareName: wish._shareName || "My Wish List", text: wishText() }] : []);''',
    '''[{ id: "__wish__", shareName: wish._shareName || "My Wish List", text: wishText() }] : [])
      .concat(shopP().shared ? (t => t ? [{ id: "__shop__", shareName: shopP().name || "My Shopping List", text: t }] : [])(shopText()) : []);''')

# ---------- Friends: shopping lists render like wish lists, in their own section
rep('''    if (r.deck_id === "__wish__"){''', '''    if (r.deck_id === "__wish__" || r.deck_id === "__shop__"){
      const shop = r.deck_id === "__shop__";''')
rep('''<h3>♥ ${esc(r.name)}</h3>''', '''<h3>${shop ? "🛒" : "♥"} ${esc(r.name)}</h3>''')
rep('''${mine ? '<span class="tag ok">Your wish list</span>' : ""}''', '''${mine ? `<span class="tag ok">Your ${shop ? "shopping" : "wish"} list</span>` : ""}''')
rep('''<span>Wants <b>${rows.length}</b> card${rows.length === 1 ? "" : "s"}</span>''',
    '''<span>${shop ? "Needs" : "Wants"} <b>${rows.length}</b> card${rows.length === 1 ? "" : "s"}${shop ? ` (${rows.reduce((a, x) => a + x.q, 0)} copies) for their decks` : ""}</span>''')
rep('''  const isWish = a => (a.querySelector("h3") || {}).textContent.trim().startsWith("♥");
  const wishes = arts.filter(isWish), decks = arts.filter(a => !isWish(a)), q = $("fr-q").value.trim();''',
    '''  const isWish = a => (a.querySelector("h3") || {}).textContent.trim().startsWith("♥"), isShop = a => (a.querySelector("h3") || {}).textContent.trim().startsWith("🛒");
  const wishes = arts.filter(isWish), shops = arts.filter(isShop), decks = arts.filter(a => !isWish(a) && !isShop(a)), q = $("fr-q").value.trim();''')
rep('''  section("Wish Lists", wishes, q ? "No shared wish lists match this search." : "No wish list links saved yet.");''',
    '''  section("Wish Lists", wishes, q ? "No shared wish lists match this search." : "No wish list links saved yet.");
  if (shops.length || !q) section("Shopping Lists", shops, q ? "No shared shopping lists match this search." : "No shopping list links saved yet.");''')

# ---------- styles
_i = h.rfind("</style>"); h = h[:_i] + """.sh-decksel{display:flex;flex-wrap:wrap;gap:6px}
.sh-decksel button{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:7px 12px;display:grid;gap:1px;text-align:left;color:var(--muted)}
.sh-decksel button b{font-family:var(--display);font-size:14px}
.sh-decksel button small{font-size:12px;font-variant-numeric:tabular-nums}
.sh-decksel button[aria-pressed="true"]{border-color:var(--accent);background:var(--row);color:var(--fg)}
.sh-decksel button[aria-pressed="false"] b{text-decoration:line-through}
.sh-decks{display:flex;flex-wrap:wrap;gap:4px 6px;font-size:12px;color:var(--muted)}
.sh-decks span{border:1px solid var(--line);border-radius:4px;padding:0 6px;line-height:18px}
.sh-decks b{color:var(--fg)}
.sh-act{display:flex;justify-content:flex-end}
.sh-got{padding:5px 10px;font-size:13px;border-color:color-mix(in srgb,var(--ok) 45%,var(--line));color:var(--ok)}
.sh-got:hover{background:color-mix(in srgb,var(--ok) 12%,transparent)}
#sh-sort{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:8px 10px;color:var(--fg)}
.dk-tile .sh-got{width:100%}
""" + h[_i:]

open(out, "w", encoding="utf-8").write(h)
print("patch_shop: ok ->", out)
