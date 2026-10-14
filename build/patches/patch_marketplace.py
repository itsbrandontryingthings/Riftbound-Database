#!/usr/bin/env python3
"""Marketplace tab (website; runs last, after patch_offer_threads.py).
- The Shopping List tab is now called Marketplace. Top to bottom: Incoming Offers (always shown, with a note when
  there are none yet), Shopping List Overview (cards to buy, total cost, decks, share), Add a Card to Shopping List,
  the My Shopping List header, one small box with the filters (search, domain, type, rarity: not saved) and the
  sort / size / layout buttons, then the cards. The tab's click / change listeners sit on #shop-wrap around all three.
- Sharing a shopping list starts with a blank name and a note asking for one friends will recognise.
- Collection: a 🛒 Buy button next to ♡ Want on every card (list, grid and the enlarged preview). It adds one copy of
  that printing to the shopping list (wish._shop.extra, the same as Add a Card); tap again to take it off. Hovering it
  shows − n + to pick how many (on phones, which can't hover, − n + shows once the card is on the list).
- Each shopping list card: "To buy" − / + (deck cards keep the change in wish._shop.adj), "Need N · Have N", the decks
  that use it with their counts, and "+ Collected 1" (was "+ Bought 1"), which adds one to your collection and takes
  one off "to buy"; the collection, totals, decks and shared list all update from that.
- My Decks: the Need − / + on each deck card is gone; only "I have" stays.
Usage: patch_marketplace.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

# ---------- styles
rep('</style>\n\n<div class="wrap" id="app">', '''.mk-h{font-family:var(--display);font-size:22px;margin:0}
.of-panel > .mk-h{margin-bottom:6px}
.mk-hrow{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin:18px 0 6px}
.sh-filt{display:grid;gap:8px;padding:10px 12px;margin:0 0 12px}
.sh-filt .frow{margin:0;gap:8px}
.sh-filt .search{flex:1 1 220px;min-width:0}
.sh-filt[hidden]{display:none}
.sh-filt .dk-tools{background:none;border:0;padding:0;margin:0}
#shop-head .mk-hrow{margin-top:18px}
.shopbtn[aria-pressed="true"]{color:#5fd08a;border-color:color-mix(in srgb,#5fd08a 55%,var(--line));background:color-mix(in srgb,#5fd08a 12%,transparent)}
.shopq{position:relative;display:inline-flex;align-items:center;vertical-align:middle}
.shopq.over{position:absolute;top:10px;right:46px;z-index:3}
.shopq .wishbtn.shopbtn.over{position:static;font-size:14px}
.wishbtn.shopbtn.over[aria-pressed="true"]{color:#5fd08a}
.shopstep{display:none;position:absolute;left:0;top:100%;z-index:6;background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:2px;box-shadow:0 6px 18px rgb(0 0 0 / .45);white-space:nowrap}
.shopstep button{width:26px;height:26px}
.shopstep output{min-width:22px;text-align:center}
.shopq.over .shopstep{left:auto;right:calc(100% + 2px);top:0}
.shopq:hover .shopstep,.shopq:focus-within .shopstep{display:inline-flex;align-items:center}
@media (hover:none){.shopq.on .shopstep{display:inline-flex;align-items:center;position:static;box-shadow:none;margin-left:4px}.shopq.over.on .shopstep{order:-1;margin:0 4px 0 0;background:rgb(10 12 18 / .85)}}
</style>

<div class="wrap" id="app">''')

# ---------- tab name
rep('aria-controls="view-shop">Shopping List</button>', 'aria-controls="view-shop">Marketplace</button>')
rep('$("t-shop").innerHTML = `Shopping List${n ?', '$("t-shop").innerHTML = `Marketplace${n ?')
rep('Offers friends send show up in your Shopping List tab.', 'Offers friends send show up in your Marketplace tab.')

# ---------- page layout: offers first, then overview, add a card, filters, then the list under its header
rep('''    <div class="panel" id="shop-summary"></div>
    <div class="panel sh-addp">''', '''    <div id="shop-offers"></div>
    <div class="panel" id="shop-summary"></div>
    <div class="panel sh-addp">''')
rep('''      <p class="meta" id="sh-addmsg" aria-live="polite"></p>
    </div>
    <div id="shop-offers"></div>
    <div id="shop-body"></div>''', '''      <p class="meta" id="sh-addmsg" aria-live="polite"></p>
    </div>
    <div id="shop-wrap">
    <div id="shop-head"></div>
    <div class="panel sh-filt" id="sh-filtp" role="search" aria-label="Filter and sort your shopping list">
      <div class="frow">
        <input class="search" id="shf-q" type="search" placeholder="Search your shopping list, e.g. Jinx" aria-label="Search your shopping list" autocomplete="off">
        <select id="shf-dom" aria-label="Domain"><option value="">All domains</option></select>
        <select id="shf-type" aria-label="Card type"><option value="">All types</option></select>
        <select id="shf-rar" aria-label="Rarity"><option value="">All rarities</option></select>
        <button class="btn reset" id="shf-reset" type="button" disabled>Reset filters</button>
      </div>
      <div id="shop-tools"></div>
    </div>
    <div id="shop-body"></div>
    </div>''')
rep('<h3 class="of-h">Add a Card</h3>', '<h3 class="of-h">Add a Card to Shopping List</h3>')
# the sort / size / layout buttons now live in #shop-tools, so listen on the wrapper around head, filters and list
rep('''$("shop-body").addEventListener("click", e => {
  const id = e.target.id;''', '''$("shop-wrap").addEventListener("click", e => {
  const id = e.target.id;''')
rep('''$("shop-body").addEventListener("change", e => {''', '''$("shop-wrap").addEventListener("change", e => {''')

# filters (kept for this visit only, not saved)
rep('''// ---- Shopping List: what your decks still need after your collection''', '''// ---- Marketplace filters for your shopping list (this visit only, not saved)
const shf = {q: "", dom: "", type: "", rar: ""};
function shfOn(){ return !!(shf.q || shf.dom || shf.type || shf.rar); }
function shfMatch(x){ const c = x.show;
  return (!shf.q || norm(x.name).includes(norm(shf.q))) && (!shf.dom || (c.domains || []).includes(shf.dom)) && (!shf.type || c.type === shf.type) && (!shf.rar || c.rarity === shf.rar); }
let shfReady = false;
function shfOpts(){
  if (shfReady) return; shfReady = true;
  const uniq = f => [...new Set(CARDS.flatMap(f))].filter(Boolean).sort();
  const fill = (id, vals) => $(id).insertAdjacentHTML("beforeend", vals.map(v => `<option value="${esc(v)}">${esc(v)}</option>`).join(""));
  fill("shf-dom", uniq(c => c.domains || [])); fill("shf-type", uniq(c => [c.type]));
  fill("shf-rar", RAR.filter(r => CARDS.some(c => c.rarity === r)));
}
function shopHead(n, all){ return `<div class="mk-hrow"><h2 class="mk-h">My Shopping List</h2>${all && shfOn() ? `<span class="meta">Showing ${n} of ${all} card${all === 1 ? "" : "s"}</span>` : ""}</div>`; }
function shfReset(){ Object.assign(shf, {q: "", dom: "", type: "", rar: ""}); $("shf-q").value = ""; ["dom", "type", "rar"].forEach(k => $("shf-" + k).value = ""); $("shf-reset").disabled = true; renderShop(); }
$("shf-q").addEventListener("input", e => { shf.q = e.target.value.trim(); $("shf-reset").disabled = !shfOn(); renderShop(); });
["dom", "type", "rar"].forEach(k => $("shf-" + k).addEventListener("change", e => { shf[k] = e.target.value; $("shf-reset").disabled = !shfOn(); renderShop(); }));
$("shf-reset").addEventListener("click", shfReset);
$("shop-body").addEventListener("click", e => { if (e.target.id === "shf-clear") shfReset(); });
// ---- Shopping List: what your decks still need after your collection''')

# overview: same tiles, new heading; empty list still shows the header and offers
rep('''$("shop-summary").innerHTML = `<h2>Shopping List</h2><p class="meta">Add a deck in <b>My Decks</b> and every card it still needs shows up here, after the cards in your collection. You can also add single cards just below.</p><div class="frow"><button class="btn primary" id="sh-go-decks">Go to My Decks</button></div>`;
    $("shop-body").innerHTML = ""; return;''',
    '''$("shop-summary").innerHTML = `<h3 class="of-h">Shopping List Overview</h3><p class="meta">Add a deck in <b>My Decks</b> and every card it still needs goes on your shopping list, after the cards in your collection. You can also add single cards just below, or tap <b>🛒 Buy</b> on any card in Collection.</p><div class="frow"><button class="btn primary" id="sh-go-decks">Go to My Decks</button></div>`;
    $("shop-head").innerHTML = shopHead(0, 0); $("shop-tools").innerHTML = ""; $("sh-filtp").hidden = true;
    $("shop-body").innerHTML = `<div class="empty">Your shopping list is empty.</div>`; renderOffers(); loadOffers(); return;''')
rep('''$("shop-summary").innerHTML = `<h2>Shopping List</h2>
    <p class="meta">Every card your decks still need, after the cards in your collection.''',
    '''$("shop-summary").innerHTML = `<h3 class="of-h">Shopping List Overview</h3>
    <p class="meta">Every card your decks still need, after the cards in your collection, plus cards you added.''')
rep('''<button class="btn" id="sh-share" ${items.length ? "" : "disabled"}>Share with friends</button>''',
    '''<button class="btn primary" id="sh-share" ${items.length ? "" : "disabled"}>Share my shopping list</button>''')
rep('''  renderOffers(); loadOffers();
  $("shop-body").innerHTML = tools + (items.length
    ? `<div class="${view === "grid" ? `list grid dkg${size !== "s" ? " sz-" + size : ""}` : "dkl dkl-" + size}">${items.map(x => shopRowHTML(x, view, size)).join("")}</div>`
    : `''', '''  renderOffers(); loadOffers(); shfOpts();
  const vis = items.filter(shfMatch);
  $("shop-head").innerHTML = shopHead(vis.length, items.length); $("shop-tools").innerHTML = tools; $("sh-filtp").hidden = false;
  $("shop-body").innerHTML = (items.length ? (vis.length
    ? `<div class="${view === "grid" ? `list grid dkg${size !== "s" ? " sz-" + size : ""}` : "dkl dkl-" + size}">${vis.map(x => shopRowHTML(x, view, size)).join("")}</div>`
    : `<div class="empty">No cards on your shopping list match these filters. <button class="btn" id="shf-clear">Reset filters</button></div>`)
    : `''')

# incoming offers: always a panel, first on the page
rep('''  if (!cloudUser || (!shopP().shared && !(offers && offers.length))){ box.innerHTML = ""; return; }
  if (offersOff){ box.innerHTML = `<div class="panel of-panel"><h3 class="of-h">Offers</h3><p class="meta">Offers need a quick database update before friends can send them. The site owner has the steps.</p></div>`; return; }
  if (!offers){ box.innerHTML = ""; return; }
  box.innerHTML = `<div class="panel of-panel"><div class="of-hrow"><h3 class="of-h">Offers <small>${offers.length}</small></h3>''',
    '''  const note = t => `<div class="panel of-panel"><h2 class="of-h mk-h">Incoming Offers</h2><p class="meta">${t}</p></div>`;
  if (!cloudUser){ box.innerHTML = note("Sign in and share your shopping list, and friends can send you offers on the cards you need. They show up here."); return; }
  if (!shopP().shared && !(offers && offers.length)){ box.innerHTML = note("No offers yet. Share your shopping list (below) and friends can tick the cards they have and send you an offer: money, a trade, anything. It shows up here with their name."); return; }
  if (offersOff){ box.innerHTML = note("Offers need a quick database update before friends can send them. The site owner has the steps."); return; }
  if (!offers){ box.innerHTML = note("Checking for offers…"); return; }
  box.innerHTML = `<div class="panel of-panel"><div class="of-hrow"><h2 class="of-h mk-h">Incoming Offers <small>${offers.length}</small></h2>''')

# ---------- share dialog: blank name for a shopping list, with a note
rep('''<label><span id="share-name-label">Name This Shared Deck</span> <input id="share-name" maxlength="40" autocomplete="off" required></label>''',
    '''<label><span id="share-name-label">Name This Shared Deck</span> <input id="share-name" maxlength="40" autocomplete="off" required></label>
    <p class="meta" id="share-name-note" hidden>Name your shopping list so your friends can easily tell whose it is, e.g. "Sam's Kai'Sa Deck".</p>''')
rep('''shareTarget === "shop" ? (shopP().name || "My Shopping List") : (shareDeckName(customDecks.find(x => x.id === curDeck)) || ""); $("share-msg").textContent = "";''',
    '''shareTarget === "shop" ? (shopP().name || "") : (shareDeckName(customDecks.find(x => x.id === curDeck)) || ""); $("share-msg").textContent = "";
  $("share-name").placeholder = shareTarget === "shop" ? "Name your shopping list" : ""; $("share-name-note").hidden = shareTarget !== "shop";''')

# ---------- 🛒 Buy button beside ♡ Want on every card; hover it (or, on a phone, once it's on the list) for − n +
rep('''function wishBtn(c, over){ const on = !!wish[c.id];''', '''const shopN = id => +(((wish._shop || {}).extra || {})[id]) || 0;
const shopLbl = (n, over) => over ? "🛒" : n ? `🛒 ${n} on list` : "🛒 Buy";
const shopTip = n => n ? `${n} on your shopping list (tap to remove, or use − + to change)` : "Add to your shopping list (hover for − + to pick how many)";
function shopBtn(c, over){ const n = shopN(c.id);
  return `<span class="shopq${over ? " over" : ""}${n ? " on" : ""}" data-sq="${esc(c.id)}"><button class="wishbtn shopbtn${over ? " over" : ""}" data-shopadd="${esc(c.id)}" aria-pressed="${n > 0}" title="${shopTip(n)}" aria-label="${n ? "Remove " + esc(c.name) + " from" : "Add " + esc(c.name) + " to"} your shopping list">${shopLbl(n, over)}</button><span class="step shopstep" role="group" aria-label="Copies of ${esc(c.name)} on your shopping list"><button data-shopq="-1" aria-label="One fewer" ${n ? "" : "disabled"}>−</button><output>${n}</output><button data-shopq="1" aria-label="One more" ${n >= 99 ? "disabled" : ""}>+</button></span></span>`; }
function wishBtn(c, over){ return wishBtn0(c, over) + shopBtn(c, over); }
function wishBtn0(c, over){ const on = !!wish[c.id];''')
rep('''x.outerHTML = wishBtn(byId[id], x.classList.contains("over")); });
  if (st.tab === "wish") renderWish();
}, true);''', '''x.outerHTML = wishBtn0(byId[id], x.classList.contains("over")); });
  if (st.tab === "wish") renderWish();
}, true);
// 🛒 on any card: tap = one copy of that printing on the shopping list (or off again); − / + = how many.
// The buttons are updated in place (not redrawn) so the − + box stays open under the pointer.
function setShopN(id, q){
  const P = wish._shop || {}, ex = {...(P.extra || {})}, c = byId[id];
  if (q > 0) ex[id] = Math.min(99, q); else delete ex[id];
  wish._shop = {...P, extra: ex}; saveWish();
  const n = shopN(id);
  document.querySelectorAll(`.shopq[data-sq="${CSS.escape(id)}"]`).forEach(w => {
    const b = w.querySelector("[data-shopadd]"); w.classList.toggle("on", n > 0);
    b.setAttribute("aria-pressed", n > 0); b.title = shopTip(n); b.textContent = shopLbl(n, w.classList.contains("over"));
    b.setAttribute("aria-label", `${n ? "Remove " + c.name + " from" : "Add " + c.name + " to"} your shopping list`);
    w.querySelector("output").textContent = n; w.querySelector('[data-shopq="-1"]').disabled = !n; w.querySelector('[data-shopq="1"]').disabled = n >= 99;
  });
  if (st.tab === "shop") renderShop();
}
document.addEventListener("click", e => {
  const b = e.target.closest("button[data-shopadd],button[data-shopq]"); if (!b) return;
  e.preventDefault(); e.stopPropagation();
  const id = b.closest("[data-sq]").dataset.sq, n = shopN(id);
  setShopN(id, b.dataset.shopq ? n + +b.dataset.shopq : (n ? 0 : 1));
}, true);''')

# ---------- My Shopping List cards: − / + for how many to buy, Need / Have, decks, "+ Collected 1"
# Deck cards: wish._shop.adj {card key: n} moves the number to buy up or down from what the decks need (buy = need -
# owned + n, 0 to 99). At 0 the card stays on the list, dimmed, so + can bring it back; copy / share leave it out.
rep('''    const owned = ownedOf(key), buy = Math.max(0, q - owned), cheap = cheapestOf(key), show = cheap || groups[key][0];
    return {key, name: groups[key][0].name, need: q, owned, buy, cheap, show, decks: by[key], cost: cheap ? buy * cheap.price : 0};
  }).filter(x => x.buy > 0);''', '''    const owned = ownedOf(key), base = Math.max(0, q - owned), adj = (P.adj || {})[key] || 0, buy = Math.max(0, Math.min(99, base + adj)), cheap = cheapestOf(key), show = cheap || groups[key][0];
    return {key, name: groups[key][0].name, need: q, owned, base, adj, buy, cheap, show, decks: by[key], cost: cheap ? buy * cheap.price : 0};
  }).filter(x => x.buy > 0 || (x.adj < 0 && x.base > 0));''')
rep('''const shopText = () => shopItems().items.map(''', '''const shopText = () => shopItems().items.filter(x => x.buy > 0).map(''')
rep('''if (id === "sh-copy"){ const {items} = shopItems(); copy(items.map(''', '''if (id === "sh-copy"){ const items = shopItems().items.filter(x => x.buy > 0); copy(items.map(''')
rep('''cop${copies === 1 ? "y" : "ies"} across ${items.length} different card${items.length === 1 ? "" : "s"}''',
    '''cop${copies === 1 ? "y" : "ies"} across ${items.filter(x => x.buy).length} different card${items.filter(x => x.buy).length === 1 ? "" : "s"}''')
rep('''Tap a picture to see the card; tap <b>+ Bought 1</b> when you get one and it's added to your collection.</p>''',
    '''Use <b>−</b> and <b>+</b> to change how many to buy. Tap <b>+ Collected 1</b> when you get one: it's added to your collection and comes off this list.</p>''')
rep('''  const status = `<span class="dk-buy">buy ${x.buy}</span><span class="meta">${x.extra ? `you have ${x.owned} of this printing` : `need ${x.need} · have ${x.owned}`}</span>`;
  const bought = (x.extra ? `<span class="step sh-xq" role="group" aria-label="Copies of ${esc(c.name)} to buy"><button data-xq="-1" data-x="${esc(x.extra)}" aria-label="One fewer">−</button><output>${x.buy}</output><button data-xq="1" data-x="${esc(x.extra)}" aria-label="One more">+</button></span><button class="btn sh-rmx" data-xrm="${esc(x.extra)}">Remove</button>` : "")
    + `<button class="btn sh-got" ${x.extra ? `data-gotx="${esc(x.extra)}"` : `data-got="${esc(x.key)}"`} title="Adds 1 ${esc(c.name)} (${esc(codeOf(c))}) to your collection">+ Bought 1</button>`;''',
    '''  const status = `<span class="sh-nh" title="${x.extra ? "Copies you added · copies of this printing you have" : "Most copies a deck needs · copies you have (any printing)"}">Need <b>${x.need}</b> · Have <b>${x.owned}</b></span>`;
  const step = `<span class="sh-tb"><span class="meta">To buy</span><span class="step sh-xq" role="group" aria-label="Copies of ${esc(c.name)} to buy">` + (x.extra
      ? `<button data-xq="-1" data-x="${esc(x.extra)}" aria-label="Buy one fewer">−</button><output>${x.buy}</output><button data-xq="1" data-x="${esc(x.extra)}" aria-label="Buy one more">+</button>`
      : `<button data-adj="-1" data-k="${esc(x.key)}" aria-label="Buy one fewer" ${x.buy ? "" : "disabled"}>−</button><output>${x.buy}</output><button data-adj="1" data-k="${esc(x.key)}" aria-label="Buy one more" ${x.buy >= 99 ? "disabled" : ""}>+</button>`) + `</span></span>`;
  const bought = step + (x.extra ? `<button class="btn sh-rmx" data-xrm="${esc(x.extra)}">Remove</button>` : "")
    + `<button class="btn sh-got" ${x.extra ? `data-gotx="${esc(x.extra)}"` : `data-got="${esc(x.key)}"`} title="Adds 1 ${esc(c.name)} (${esc(codeOf(c))}) to your collection">+ Collected 1</button>`;''')
rep('''if (view === "grid") return `<div class="card tile dk-tile" style="${dom}">''', '''if (view === "grid") return `<div class="card tile dk-tile${x.buy ? "" : " sh-zero"}" style="${dom}">''')
rep('''return `<div class="dk-card sh-card" style="${dom}">''', '''return `<div class="dk-card sh-card${x.buy ? "" : " sh-zero"}" style="${dom}">''')
rep('''<span class="dk-q">${x.buy}× <span>${esc(c.type)}</span></span>''', '''<span class="dk-q"><span>${esc(c.type)}</span></span>''')
rep('''    if (xb.dataset.gotx){ adjust(id, 1); ex[id] = (ex[id] || 0) - 1; }''',
    '''    if (xb.dataset.gotx){ ex[id] = (ex[id] || 0) - 1; if (!(ex[id] > 0)) delete ex[id]; wish._shop = {...shopP(), extra: ex}; saveWish(); adjust(id, 1); return; }''')
rep('''  const g = e.target.closest("[data-got]");
  if (g){ const c = cheapestOf(g.dataset.got) || groups[g.dataset.got][0]; adjust(c.id, 1); }''', '''  const ad = e.target.closest("[data-adj]");
  if (ad){
    const x = shopItems().items.find(i => !i.extra && i.key === ad.dataset.k); if (!x) return;
    const a = {...(shopP().adj || {})}; a[x.key] = Math.max(0, Math.min(99, x.buy + +ad.dataset.adj)) - x.base; if (!a[x.key]) delete a[x.key];
    return setShop({adj: a});
  }
  const g = e.target.closest("[data-got]");
  if (g){
    // collecting one always takes one off "to buy": when the decks are already covered, it comes off the extra copies
    const x = shopItems().items.find(i => !i.extra && i.key === g.dataset.got);
    if (x && x.base === 0 && x.adj > 0){ const a = {...(shopP().adj || {})}; a[x.key] = x.adj - 1; if (!a[x.key]) delete a[x.key]; wish._shop = {...shopP(), adj: a}; saveWish(); }
    const c = cheapestOf(g.dataset.got) || groups[g.dataset.got][0]; adjust(c.id, 1);
  }''')
rep('</style>\n\n<div class="wrap" id="app">', '''.sh-nh{font-size:13px;color:var(--muted);white-space:nowrap}
.sh-nh b{color:var(--fg)}
.sh-tb{display:inline-flex;align-items:center;gap:6px}
.sh-zero{opacity:.55}
</style>

<div class="wrap" id="app">''')

# ---------- My Decks: no Need − / + on deck cards, just "I have 0 1 2 …" (the "3×" still shows what the deck runs;
# change it with Edit list as text)
rep('''const ctl = `<div class="dk-ctl"><span class="dk-pair">${dkNeedCtl(r)}</span><span class="dk-pair">${r.known ? dkHaveCtl(r, view === "grid") : ""}</span></div>`;''',
    '''const ctl = r.known ? `<div class="dk-ctl"><span class="dk-pair">${dkHaveCtl(r, view === "grid")}</span></div>` : "";''')
rep('''tap <b>Need</b> to change how many of a card the deck runs, tap <b>I have</b> to update your collection (it's the same count you see in Collection), add or remove cards,''',
    '''tap <b>I have</b> to update your collection (it's the same count you see in Collection), add or remove cards, change how many of a card the deck runs with <b>Edit list as text</b>,''')

open(out, "w", encoding="utf-8").write(h)
print("patch_marketplace: ok ->", out)
