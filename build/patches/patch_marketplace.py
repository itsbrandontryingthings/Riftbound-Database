#!/usr/bin/env python3
"""Marketplace tab (website; runs last, after patch_offer_threads.py).
- The Shopping List tab is now called Marketplace. Top to bottom: Incoming Offers (always shown, with a note when
  there are none yet), Shopping List Overview (cards to buy, total cost, decks, share), Add a Card to Shopping List,
  the My Shopping List header, one small box with the filters (search, domain, type, rarity: not saved) and the
  sort / size / layout buttons, then the cards. The tab's click / change listeners sit on #shop-wrap around all three.
- Sharing a shopping list starts with a blank name and a note asking for one friends will recognise.
- Collection: a 🛒 Buy button next to ♡ Want on every card (list, grid and the enlarged preview). It adds one copy of
  that printing to the shopping list (wish._shop.extra, the same as Add a Card); every tap adds one more (up to 99) and
  the button shows how many are on the list, and a note pops up at the bottom ("✓ Gust added to your shopping list ·
  3 on it", updated on each tap). Lower or remove it in Marketplace.
- Each shopping list card: "To buy" − / + (deck cards keep the change in wish._shop.adj), "Need N · Have N", the decks
  that use it with their counts, and "+ Collected 1" (was "+ Bought 1"), which adds one to your collection and takes
  one off "to buy"; the collection, totals, decks and shared list all update from that.
- My Decks: the Need − / + on each deck card is gone; only "I have" stays.
- Marketplace headers (Incoming Offers, Shopping List Overview, My Shopping List, Friends' Shopping Lists) fold up when
  tapped (localStorage "rb-mk-fold").
- Friends' Shopping Lists: moved from the Friends tab to the end of Marketplace, with their own filters (search,
  domain, type, rarity) plus sort and size. renderFriends still builds them in #fr-list; groupFriends moves them to
  #mk-frlist, and every #fr-list listener is on both (frListen). Opening or pasting a shopping list link goes there.
  Its search matches card names and the list's name (or owner's name: then the whole list shows).
- Each incoming offer folds to its top line by tapping the sender's name (localStorage "rb-offer-fold").
- Making an offer: "Your Offer Preview" shows pictures of the cards you're giving (ticked) and trading, with counts;
  the trade chips' pictures are bigger.
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
.shopq.over.on .wishbtn.shopbtn{width:auto;padding:0 9px}
#shop-toast{position:fixed;left:50%;bottom:22px;transform:translate(-50%,16px);z-index:1000;width:max-content;max-width:calc(100vw - 32px);box-sizing:border-box;text-align:center;background:#14231a;color:#e8f6ec;border:1px solid #5fd08a;border-radius:10px;padding:10px 16px;font-size:14px;box-shadow:0 10px 28px rgb(0 0 0 / .5);opacity:0;pointer-events:none;transition:opacity .2s,transform .2s}
#shop-toast.show{opacity:1;transform:translate(-50%,0)}
#shop-toast.bump{animation:shopbump .25s}
#shop-toast b{color:#5fd08a}
@keyframes shopbump{40%{transform:translate(-50%,0) scale(1.04)}}
@media (prefers-reduced-motion: reduce){#shop-toast,#shop-toast.bump{transition:none;animation:none}}
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

# ---------- 🛒 Buy button beside ♡ Want on every card: each tap adds one more copy (change or remove in Marketplace)
rep('''function wishBtn(c, over){ const on = !!wish[c.id];''', '''const shopN = id => +(((wish._shop || {}).extra || {})[id]) || 0;
const shopLbl = (n, over) => over ? (n ? `🛒 ${n}` : "🛒") : n ? `🛒 ${n} on list` : "🛒 Buy";
const shopTip = n => (n ? `${n} on your shopping list. ` : "") + "Tap to add one more. Change how many in Marketplace.";
function shopBtn(c, over){ const n = shopN(c.id);
  return `<span class="shopq${over ? " over" : ""}${n ? " on" : ""}" data-sq="${esc(c.id)}"><button class="wishbtn shopbtn${over ? " over" : ""}" data-shopadd="${esc(c.id)}" aria-pressed="${n > 0}" title="${shopTip(n)}" aria-label="Add one ${esc(c.name)} to your shopping list${n ? ` (${n} on it now)` : ""}">${shopLbl(n, over)}</button></span>`; }
function wishBtn(c, over){ return wishBtn0(c, over) + shopBtn(c, over); }
function wishBtn0(c, over){ const on = !!wish[c.id];''')
rep('''x.outerHTML = wishBtn(byId[id], x.classList.contains("over")); });
  if (st.tab === "wish") renderWish();
}, true);''', '''x.outerHTML = wishBtn0(byId[id], x.classList.contains("over")); });
  if (st.tab === "wish") renderWish();
}, true);
// 🛒 on any card: every tap puts one more copy of that printing on the shopping list (up to 99)
function setShopN(id, q){
  const P = wish._shop || {}, ex = {...(P.extra || {})}, c = byId[id];
  if (q > 0) ex[id] = Math.min(99, q); else delete ex[id];
  wish._shop = {...P, extra: ex}; saveWish();
  const n = shopN(id);
  document.querySelectorAll(`.shopq[data-sq="${CSS.escape(id)}"]`).forEach(w => {
    const b = w.querySelector("[data-shopadd]"); w.classList.toggle("on", n > 0);
    b.setAttribute("aria-pressed", n > 0); b.title = shopTip(n); b.textContent = shopLbl(n, w.classList.contains("over"));
    b.setAttribute("aria-label", `Add one ${c.name} to your shopping list${n ? ` (${n} on it now)` : ""}`);
  });
  if (st.tab === "shop") renderShop();
}
// a small note at the bottom of the screen; tapping again updates it and keeps it up
let shopToastT = 0;
function shopToast(c, n){
  let t = $("shop-toast");
  if (!t){ document.body.insertAdjacentHTML("beforeend", '<div id="shop-toast" role="status" aria-live="polite"></div>'); t = $("shop-toast"); }
  t.innerHTML = `✓ <b>${esc(c.name)}</b> added to your shopping list · <b>${n}</b> on it`;
  t.classList.remove("bump"); void t.offsetWidth; t.classList.add("show", "bump");
  clearTimeout(shopToastT); shopToastT = setTimeout(() => t.classList.remove("show"), 2500);
}
document.addEventListener("click", e => {
  const b = e.target.closest("button[data-shopadd]"); if (!b) return;
  e.preventDefault(); e.stopPropagation();
  const id = b.dataset.shopadd; setShopN(id, shopN(id) + 1); shopToast(byId[id], shopN(id));
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

# Collection + / −: each card now also holds the 🛒 − n + box, so "the first <output>" on a card is that box, not
# your count. Point at the count's own stepper (the one with the data-a buttons).
rep('''row.querySelector("output").textContent = n; row.querySelector('button[data-a="-1"]').disabled = !n;''',
    '''row.querySelector('button[data-a="-1"]').parentElement.querySelector("output").textContent = n; row.querySelector('button[data-a="-1"]').disabled = !n;''')

# ---------- My Decks: no Need − / + on deck cards, just "I have 0 1 2 …" (the "3×" still shows what the deck runs;
# change it with Edit list as text)
rep('''const ctl = `<div class="dk-ctl"><span class="dk-pair">${dkNeedCtl(r)}</span><span class="dk-pair">${r.known ? dkHaveCtl(r, view === "grid") : ""}</span></div>`;''',
    '''const ctl = r.known ? `<div class="dk-ctl"><span class="dk-pair">${dkHaveCtl(r, view === "grid")}</span></div>` : "";''')
rep('''tap <b>Need</b> to change how many of a card the deck runs, tap <b>I have</b> to update your collection (it's the same count you see in Collection), add or remove cards,''',
    '''tap <b>I have</b> to update your collection (it's the same count you see in Collection), add or remove cards, change how many of a card the deck runs with <b>Edit list as text</b>,''')

# ---------- Marketplace headers fold up (Incoming Offers, Shopping List Overview, My Shopping List, Friends' Shopping
# Lists); which ones are folded is kept in localStorage "rb-mk-fold"
rep('''<h2 class="of-h mk-h">Incoming Offers</h2>''', '''<h2 class="of-h mk-h">${mkFoldBtn("offers", "Incoming Offers")}</h2>''')
rep('''<h2 class="of-h mk-h">Incoming Offers <small>${offers.length}</small></h2>''', '''<h2 class="of-h mk-h">${mkFoldBtn("offers", `Incoming Offers <small>${offers.length}</small>`)}</h2>''')
rep('''<h3 class="of-h">Shopping List Overview</h3>''', '''<h3 class="of-h">${mkFoldBtn("overview", "Shopping List Overview")}</h3>''', 2)
rep('''<h2 class="mk-h">My Shopping List</h2>''', '''<h2 class="mk-h">${mkFoldBtn("list", "My Shopping List")}</h2>''')
rep('''// ---- Marketplace filters for your shopping list (this visit only, not saved)''', '''// ---- Marketplace: fold / unfold a section by tapping its header
const mkFold = Object.assign({}, LS.get("rb-mk-fold") || {});
function mkFoldBtn(k, html){ return `<button type="button" class="mk-fold" data-fold="${k}" aria-expanded="${!mkFold[k]}"><span class="mk-car" aria-hidden="true"></span>${html}</button>`; }
function mkFoldSync(){
  const v = $("view-shop");
  ["offers", "overview", "list", "friends"].forEach(k => { v.classList.toggle("fold-" + k, !!mkFold[k]); v.querySelectorAll(`[data-fold="${k}"]`).forEach(b => b.setAttribute("aria-expanded", !mkFold[k])); });
}
$("view-shop").addEventListener("click", e => { const b = e.target.closest("[data-fold]"); if (!b) return; mkFold[b.dataset.fold] = !mkFold[b.dataset.fold]; LS.set("rb-mk-fold", mkFold); mkFoldSync(); });
mkFoldSync();
// ---- Marketplace: friends' shopping lists. They're built by the Friends tab code (renderFriends), then moved here, so
// every listener that used to sit on #fr-list sits on both lists (frListen).
function frListen(type, fn, opt){ ["fr-list", "mk-frlist"].forEach(id => $(id).addEventListener(type, fn, opt)); }
const mkf = {q: "", dom: "", type: "", rar: ""};
function mkfOn(){ return !!(mkf.q || mkf.dom || mkf.type || mkf.rar); }
function mkfMatch(x){ const c = frCard(x.key), nm = !mkf.q || norm(x.name).includes(norm(mkf.q));
  if (!c) return nm && !mkf.dom && !mkf.type && !mkf.rar;
  return nm && (!mkf.dom || (c.domains || []).includes(mkf.dom)) && (!mkf.type || c.type === mkf.type) && (!mkf.rar || c.rarity === mkf.rar); }
function mkFriendsFill(shops){
  const box = $("mk-frlist"); box.innerHTML = "";
  if (shops.length) shops.forEach(a => box.append(a));
  else box.innerHTML = mkfOn() ? `<div class="empty">No friends' shopping lists or cards match these filters. <button class="btn" id="mkf-clear">Reset filters</button></div>`
    : `<div class="empty">No friends' shopping lists yet. When a friend sends you a link to their shopping list, open it (or paste it in the <b>Friends</b> tab) and it shows up here, where you can send them an offer.</div>`;
  $("mkf-count").textContent = shops.length ? `${shops.length} list${shops.length === 1 ? "" : "s"}` : "";
}
function mkfReset(){ Object.assign(mkf, {q: "", dom: "", type: "", rar: ""}); $("mkf-q").value = ""; ["dom", "type", "rar"].forEach(k => $("mkf-" + k).value = ""); $("mkf-reset").disabled = true; renderFriends(); }
let mkfT; $("mkf-q").addEventListener("input", e => { mkf.q = e.target.value.trim(); $("mkf-reset").disabled = !mkfOn(); clearTimeout(mkfT); mkfT = setTimeout(renderFriends, 150); });
["dom", "type", "rar"].forEach(k => $("mkf-" + k).addEventListener("change", e => { mkf[k] = e.target.value; $("mkf-reset").disabled = !mkfOn(); renderFriends(); }));
$("mkf-reset").addEventListener("click", mkfReset);
$("mk-frlist").addEventListener("click", e => { if (e.target.id === "mkf-clear") mkfReset(); });
$("mkf-sort").addEventListener("change", e => { st.frsort = e.target.value; LS.set("rb-filters", {...st, doms:[...st.doms], limit:undefined}); renderFriends(); });
["s","m","l"].forEach(k => $("mkfs-" + k).addEventListener("click", () => { st.size = k; LS.set("rb-filters", {...st, doms:[...st.doms], limit:undefined}); frSize(); }));
// ---- Marketplace filters for your shopping list (this visit only, not saved)''')
rep('''  fill("shf-rar", RAR.filter(r => CARDS.some(c => c.rarity === r)));''', '''  fill("shf-rar", RAR.filter(r => CARDS.some(c => c.rarity === r)));
  fill("mkf-dom", uniq(c => c.domains || [])); fill("mkf-type", uniq(c => [c.type])); fill("mkf-rar", RAR.filter(r => CARDS.some(c => c.rarity === r)));''')
rep('''    <div id="shop-body"></div>
    </div>
  </section>''', '''    <div id="shop-body"></div>
    </div>
    <div id="mk-friends">
      <div class="mk-hrow"><h2 class="mk-h"><button type="button" class="mk-fold" data-fold="friends" aria-expanded="true"><span class="mk-car" aria-hidden="true"></span>Friends' Shopping Lists</button></h2><span class="meta" id="mkf-count"></span></div>
      <div class="panel sh-filt" id="mkf-filtp" role="search" aria-label="Filter your friends' shopping lists">
        <div class="frow">
          <input class="search" id="mkf-q" type="search" placeholder="Search your friends' shopping lists, e.g. Jinx" aria-label="Search your friends' shopping lists" autocomplete="off">
          <select id="mkf-dom" aria-label="Domain"><option value="">All domains</option></select>
          <select id="mkf-type" aria-label="Card type"><option value="">All types</option></select>
          <select id="mkf-rar" aria-label="Rarity"><option value="">All rarities</option></select>
          <button class="btn reset" id="mkf-reset" type="button" disabled>Reset filters</button>
        </div>
        <div class="frow"><select id="mkf-sort" aria-label="Sort the cards in friends' shopping lists"><option value="">Sort: list order</option><option value="set">Sort: set order</option><option value="name">Sort: name A–Z</option><option value="price">Sort: price, high to low</option></select><span class="meta">Card size</span><div class="seg sizeseg" role="group" aria-label="Card size"><button id="mkfs-s" aria-pressed="false" title="Small cards">S</button><button id="mkfs-m" aria-pressed="false" title="Medium cards">M</button><button id="mkfs-l" aria-pressed="false" title="Large cards">L</button></div></div>
      </div>
      <div class="frlist" id="mk-frlist"></div>
    </div>
  </section>''')
h = h.replace('$("fr-list").addEventListener(', 'frListen(')
assert 'frListen("click"' in h
h = h.replace('#fr-list.frsz', ':is(#fr-list,#mk-frlist).frsz')
rep('''["s","m","l"].forEach(k => { $("frs-" + k).setAttribute("aria-pressed", k === z); $("fr-list").classList.toggle("frsz-" + k, k === z); });''',
    '''["s","m","l"].forEach(k => { $("frs-" + k).setAttribute("aria-pressed", k === z); $("fr-list").classList.toggle("frsz-" + k, k === z); $("mkfs-" + k).setAttribute("aria-pressed", k === z); $("mk-frlist").classList.toggle("frsz-" + k, k === z); });
  $("mkf-sort").value = st.frsort || "";''')
# Friends tab search doesn't hide shopping lists (they have their own filters in Marketplace)
rep('''  }).filter(x => x.ok);''', '''  }).filter(x => x.ok || x.r.deck_id === "__shop__");''')
rep('''      const mine = !!r.is_mine, open = frOpen.has(r.id);
      const canGive = rows.filter(x => ownedOf(x.key) > 0);
      const body = shop ? (open ? frShopBody(r, rows, mine) : "") :''', '''      const fRows = shop && mkfOn() ? rows.filter(mkfMatch) : rows;
      if (shop && mkfOn() && !fRows.length) return "";
      const mine = !!r.is_mine, open = frOpen.has(r.id) || (shop && mkfOn());
      const canGive = rows.filter(x => ownedOf(x.key) > 0);
      const body = shop ? (open ? frShopBody(r, fRows, mine) : "") :''')
rep('''  const list = $("fr-list"), arts = [...list.querySelectorAll(":scope > article.frdeck")];
  if (!arts.length) return;
  const isWish = a => (a.querySelector("h3") || {}).textContent.trim().startsWith("♥"), isShop = a => (a.querySelector("h3") || {}).textContent.trim().startsWith("🛒");
  const wishes = arts.filter(isWish), shops = arts.filter(isShop), decks = arts.filter(a => !isWish(a) && !isShop(a)), q = $("fr-q").value.trim();
  list.innerHTML = "";''', '''  const list = $("fr-list"), arts = [...list.querySelectorAll(":scope > article.frdeck")];
  const isWish = a => (a.querySelector("h3") || {}).textContent.trim().startsWith("♥"), isShop = a => (a.querySelector("h3") || {}).textContent.trim().startsWith("🛒");
  const wishes = arts.filter(isWish), shops = arts.filter(isShop), decks = arts.filter(a => !isWish(a) && !isShop(a)), q = $("fr-q").value.trim();
  // two renders can overlap (e.g. opening a link); if an earlier one already sorted this list, leave it alone
  if (!arts.length && list.querySelector(":scope > .frsec")) return;
  mkFriendsFill(shops);
  if (!arts.length) return;
  list.innerHTML = "";''')
rep('''  if (shops.length || !q) section("Shopping Lists", shops, q ? "No shared shopping lists match this search." : "No shopping list links saved yet.");''',
    '''  if (shops.length){ const p = document.createElement("p"); p.className = "meta frnone"; p.innerHTML = `Your friends' shopping lists (${shops.length}) are in the <b>Marketplace</b> tab, where you can send them offers.`; list.append(p); }''')
rep('''  if (t === "shop") renderShop();
  if (t === "friends") renderFriends();''', '''  if (t === "shop"){ renderShop(); renderFriends(); }
  if (t === "friends") renderFriends();''')
rep('''frCache = null; if (st.tab === "friends") renderFriends(); };''', '''frCache = null; if (st.tab === "friends" || st.tab === "shop") renderFriends(); };''')
# a friend's shopping list link (opened or pasted) goes to Marketplace
rep('''  showTab("friends");
  renderFriends().then(() => { const a = document.querySelector(".frdeck.new"); if (a) a.scrollIntoView({block: "start", behavior: "smooth"}); });''',
    '''  showTab("friends");
  renderFriends().then(() => { const a = document.querySelector(".frdeck.new"); if (a && a.closest("#mk-frlist")) return mkGoFriend(); if (a) a.scrollIntoView({block: "start", behavior: "smooth"}); });''')
rep('''$("fr-add").value = ""; addLink(t, true); renderFriends().then(() => { const a = document.querySelector(".frdeck.new"); if (a) a.scrollIntoView({block: "center"}); });''',
    '''$("fr-add").value = ""; addLink(t, true); renderFriends().then(() => { const a = document.querySelector(".frdeck.new"); if (a && a.closest("#mk-frlist")){ $("fr-add-msg").textContent = "Added. It's a shopping list, so it's in the Marketplace tab."; return; } if (a) a.scrollIntoView({block: "center"}); });''')
rep('''function frListen(type, fn, opt){''', '''function mkGoFriend(){
  if (mkFold.friends){ mkFold.friends = false; LS.set("rb-mk-fold", mkFold); mkFoldSync(); }
  showTab("shop"); setTimeout(() => { const b = document.querySelector("#mk-frlist .frdeck.new"); if (b) b.scrollIntoView({block: "start", behavior: "smooth"}); }, 400);
}
function frListen(type, fn, opt){''')
rep('</style>\n\n<div class="wrap" id="app">', '''.mk-fold{all:unset;cursor:pointer;display:inline-flex;align-items:center;gap:8px;border-radius:4px}
.mk-fold:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
.mk-fold:hover{color:var(--accent)}
.mk-car::before{content:"▾";display:inline-block;width:1em;font-size:.8em;color:var(--muted)}
.mk-fold[aria-expanded="false"] .mk-car::before{content:"▸"}
#view-shop.fold-offers #shop-offers .of-panel > :not(:first-child){display:none}
#view-shop.fold-offers #shop-offers .of-hrow > :not(:first-child){display:none}
#view-shop.fold-overview #shop-summary > :not(:first-child){display:none}
#view-shop.fold-list #sh-filtp,#view-shop.fold-list #shop-body{display:none}
#view-shop.fold-friends #mkf-filtp,#view-shop.fold-friends #mk-frlist{display:none}
#mk-friends{margin-top:8px}
#mk-friends .mk-hrow{margin-top:22px}
</style>

<div class="wrap" id="app">''')

# ---------- Incoming Offers: each offer folds to its top line by tapping the sender's name (localStorage "rb-offer-fold")
rep('''<article class="of-card" data-offer="${esc(o.id)}">''', '''<article class="of-card${offFold.has(o.id) ? " folded" : ""}" data-offer="${esc(o.id)}">''')
rep('''<b class="of-from">${esc(o.from_name)}</b> <span class="meta">sent''',
    '''<button type="button" class="mk-fold" data-offold="${esc(o.id)}" aria-expanded="${!offFold.has(o.id)}" title="Show or hide this offer"><span class="mk-car" aria-hidden="true"></span><b class="of-from">${esc(o.from_name)}</b></button> <span class="meta">sent''')
rep('''// ---- Marketplace: fold / unfold a section by tapping its header''', '''// ---- Marketplace: each incoming offer folds by tapping the sender's name
const offFold = new Set(Array.isArray(LS.get("rb-offer-fold")) ? LS.get("rb-offer-fold") : []);
$("shop-offers").addEventListener("click", e => {
  const b = e.target.closest("[data-offold]"); if (!b) return;
  const id = b.dataset.offold, art = b.closest(".of-card");
  offFold.has(id) ? offFold.delete(id) : offFold.add(id);
  if (offers) [...offFold].forEach(x => { if (!offers.some(o => o.id === x)) offFold.delete(x); });   // forget removed offers
  LS.set("rb-offer-fold", [...offFold]); art.classList.toggle("folded", offFold.has(id)); b.setAttribute("aria-expanded", !offFold.has(id));
}, true);
// ---- Marketplace: fold / unfold a section by tapping its header''')

# ---------- Friends' shopping lists: bigger pictures on "Cards you'd trade", and an offer preview with the cards you'd give
rep('''.of-chip{display:inline-grid;grid-template-columns:30px auto auto auto;''', '''.of-chip{display:inline-grid;grid-template-columns:48px auto auto auto;''')
rep('''          ${tradeChips(S)}</div>''', '''          ${tradeChips(S)}</div>
        ${offerPreview(S)}''')
rep('''function tradeChips(S){''', '''// the cards in your offer, as pictures: the ones you ticked (a printing you own, if you have one) and the ones you'd trade
function offerPreview(S){
  const give = Object.entries(S.sel || {}).map(([key, p]) => ({c: (groups[key] || []).find(c => counts[c.id]) || frCard(key), q: p.q})).filter(x => x.c);
  const trade = Object.entries(S.trade || {}).filter(([id]) => byId[id]).map(([id, q]) => ({c: byId[id], q}));
  if (!give.length && !trade.length) return "";
  const tiles = list => `<div class="of-pv">${list.map(x => `<span class="of-pvc">${thumbHTML(x.c, 480)}<span class="of-pvq">${x.q}×</span><small>${esc(x.c.name)}</small></span>`).join("")}</div>`;
  return `<div class="of-preview"><span class="of-lab">Your Offer Preview <small>(tap a card to see it bigger)</small></span>${give.length ? `<span class="collect-k">Cards you're giving them</span>${tiles(give)}` : ""}${trade.length ? `<span class="collect-k">Cards you'd trade them</span>${tiles(trade)}` : ""}</div>`;
}
function tradeChips(S){''')

# ---------- Friends' shopping lists search also matches the list's name (and its owner's name): then every card in it shows
rep('''      const fRows = shop && mkfOn() ? rows.filter(mkfMatch) : rows;''',
    '''      const nameHit = shop && !!mkf.q && norm(r.name + " " + (r.owner_name || "")).includes(norm(mkf.q));
      const fRows = shop && mkfOn() ? rows.filter(x => mkfMatch(x, nameHit)) : rows;''')
rep('''function mkfMatch(x){ const c = frCard(x.key), nm = !mkf.q || norm(x.name).includes(norm(mkf.q));''',
    '''function mkfMatch(x, nameHit){ const c = frCard(x.key), nm = nameHit || !mkf.q || norm(x.name).includes(norm(mkf.q));''')
rep('''placeholder="Search your friends' shopping lists, e.g. Jinx" aria-label="Search your friends' shopping lists"''',
    '''placeholder="Search a list name or card, e.g. Sam or Jinx" aria-label="Search your friends' shopping lists by list name or card"''')

rep('</style>\n\n<div class="wrap" id="app">', '''.of-card.folded > :not(.of-top){display:none}
.of-preview{flex-basis:100%;display:grid;gap:6px;background:color-mix(in srgb,var(--accent) 6%,var(--row));border:1px solid color-mix(in srgb,var(--accent) 35%,var(--line));border-radius:10px;padding:10px 12px}
.of-pv{display:grid;grid-template-columns:repeat(auto-fill,minmax(92px,1fr));gap:10px}
.of-pvc{position:relative;display:grid;gap:4px;align-content:start}
.of-pvc small{font-size:12px;line-height:1.25;color:var(--fg)}
.of-pvq{position:absolute;top:6px;left:6px;z-index:3;background:rgb(10 12 18 / .85);color:#fff;font-weight:700;font-size:13px;border-radius:6px;padding:1px 7px;pointer-events:none}
@media (max-width:520px){.of-pv{grid-template-columns:repeat(3,minmax(0,1fr))}}
</style>

<div class="wrap" id="app">''')

open(out, "w", encoding="utf-8").write(h)
print("patch_marketplace: ok ->", out)
