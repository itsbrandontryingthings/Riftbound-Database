#!/usr/bin/env python3
"""Marketplace tab (website; runs last, after patch_offer_threads.py).
- The Shopping List tab is now called Marketplace. Top to bottom: Incoming Offers (always shown, with a note when
  there are none yet), Shopping List Overview (cards to buy, total cost, decks, share), Add a Card, Filters (search,
  domain, type, rarity: not saved; then the sort / size / layout bar), then the My Shopping List header and the cards.
- Sharing a shopping list starts with a blank name and a note asking for one friends will recognise.
- Collection: a 🛒 Buy button next to ♡ Want on every card (list, grid and the enlarged preview). It adds one copy of
  that printing to the shopping list (wish._shop.extra, the same as Add a Card); tap again to take it off.
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
.sh-filt{display:grid;gap:8px}
.sh-filt .frow{margin:0}
.sh-filt .search{flex:1 1 220px;min-width:0}
#shop-body > .dk-tools{margin-top:0}
.shopbtn[aria-pressed="true"]{color:#5fd08a;border-color:color-mix(in srgb,#5fd08a 55%,var(--line));background:color-mix(in srgb,#5fd08a 12%,transparent)}
.wishbtn.shopbtn.over{right:46px;font-size:14px}
.wishbtn.shopbtn.over[aria-pressed="true"]{color:#5fd08a}
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
    <div class="panel sh-filt" role="search" aria-label="Filter your shopping list">
      <h3 class="of-h">Filters</h3>
      <div class="frow">
        <input class="search" id="shf-q" type="search" placeholder="Search your shopping list, e.g. Jinx" aria-label="Search your shopping list" autocomplete="off">
        <select id="shf-dom" aria-label="Domain"><option value="">All domains</option></select>
        <select id="shf-type" aria-label="Card type"><option value="">All types</option></select>
        <select id="shf-rar" aria-label="Rarity"><option value="">All rarities</option></select>
        <button class="btn reset" id="shf-reset" type="button" disabled>Reset filters</button>
      </div>
    </div>
    <div id="shop-body"></div>''')

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
    $("shop-body").innerHTML = shopHead(0, 0) + `<div class="empty">Your shopping list is empty.</div>`; renderOffers(); loadOffers(); return;''')
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
  $("shop-body").innerHTML = tools + shopHead(vis.length, items.length) + (items.length ? (vis.length
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

# ---------- 🛒 Buy button beside ♡ Want on every card
rep('''function wishBtn(c, over){ const on = !!wish[c.id];''', '''function shopBtn(c, over){ const on = !!(((wish._shop || {}).extra || {})[c.id] > 0);
  return `<button class="wishbtn shopbtn${over ? " over" : ""}" data-shopadd="${esc(c.id)}" aria-pressed="${on}" title="${on ? "On your shopping list (tap to remove)" : "Add to your shopping list"}" aria-label="${on ? "Remove " + esc(c.name) + " from" : "Add " + esc(c.name) + " to"} your shopping list">🛒${over ? "" : (on ? " On list" : " Buy")}</button>`; }
function wishBtn(c, over){ return wishBtn0(c, over) + shopBtn(c, over); }
function wishBtn0(c, over){ const on = !!wish[c.id];''')
rep('''x.outerHTML = wishBtn(byId[id], x.classList.contains("over")); });
  if (st.tab === "wish") renderWish();
}, true);''', '''x.outerHTML = wishBtn0(byId[id], x.classList.contains("over")); });
  if (st.tab === "wish") renderWish();
}, true);
// 🛒 on any card: one copy of that printing on the shopping list, or off again
document.addEventListener("click", e => {
  const b = e.target.closest("button[data-shopadd]"); if (!b) return;
  e.preventDefault(); e.stopPropagation();
  const id = b.dataset.shopadd, P = wish._shop || {}, ex = {...(P.extra || {})};
  if (ex[id] > 0) delete ex[id]; else ex[id] = 1;
  wish._shop = {...P, extra: ex}; saveWish();
  document.querySelectorAll(`button[data-shopadd="${CSS.escape(id)}"]`).forEach(x => { x.outerHTML = shopBtn(byId[id], x.classList.contains("over")); });
  if (st.tab === "shop") renderShop();
}, true);''')

open(out, "w", encoding="utf-8").write(h)
print("patch_marketplace: ok ->", out)
