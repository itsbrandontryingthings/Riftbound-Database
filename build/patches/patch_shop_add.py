#!/usr/bin/env python3
"""Shopping List: add single cards, and CAD + USD everywhere (website; runs last, after patch_offers.py).
- "Add a Card" box in the Shopping List tab, like Open Packs: type part of a name, ↑ ↓ to pick a printing, Enter adds
  one copy. Added cards are saved in wish._shop.extra {card id: copies to buy}, show "Added by you" with − / + and
  Remove, are part of the shared list, and "+ Bought 1" adds that printing to your collection and takes one off.
- Every price on the Shopping List (each card, per deck, biggest buy) and in shopping-list offers shows CA and US,
  following the site's currency choice.
Usage: patch_shop_add.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

# ---------- add-a-card box (static, so typing keeps focus while the list redraws)
rep('''    <div id="shop-offers"></div>''', '''    <div class="panel sh-addp">
      <h3 class="of-h">Add a Card</h3>
      <p class="meta">Type part of a card name, then press Enter to add one copy to your shopping list. Use ↑ ↓ to pick a different printing.</p>
      <div class="qa-box">
        <input class="search" id="sh-q" type="search" placeholder="Start typing a card name…" aria-label="Card name to add to your shopping list" autocomplete="off" role="combobox" aria-expanded="false" aria-controls="sh-sug" aria-autocomplete="list">
        <ul class="sug" id="sh-sug" role="listbox" aria-label="Matching cards"></ul>
      </div>
      <p class="meta" id="sh-addmsg" aria-live="polite"></p>
    </div>
    <div id="shop-offers"></div>''')

# ---------- added cards join the list
rep('''  }).filter(x => x.buy > 0);''', '''  }).filter(x => x.buy > 0);
  for (const [id, q] of Object.entries(P.extra || {})){
    const c = byId[id]; if (!c || !(q > 0)) continue;
    items.push({key: norm(c.name), name: c.name, need: q, owned: counts[id] || 0, buy: q, cheap: c.price != null ? c : null, show: c, decks: [], extra: id, cost: c.price != null ? q * c.price : 0});
  }''')
rep('''  const decks = `<span class="sh-decks">${x.decks.map(d => `<span>${esc(d.name)} <b>${d.q}</b></span>`).join("")}</span>`;''',
    '''  const decks = `<span class="sh-decks">${x.extra ? `<span class="sh-mine">Added by you${c.variant ? ` · ${esc(c.variant)}` : ""}</span>` : ""}${x.decks.map(d => `<span>${esc(d.name)} <b>${d.q}</b></span>`).join("")}</span>`;''')
rep('''<small>${x.buy} × ${esc(m1(x.cheap.price))}</small>''', '''<small>${x.buy} × ${esc(money(x.cheap.price))}</small>''')
rep('''  const status = `<span class="dk-buy">buy ${x.buy}</span><span class="meta">need ${x.need} · have ${x.owned}</span>`;''',
    '''  const status = `<span class="dk-buy">buy ${x.buy}</span><span class="meta">${x.extra ? `you have ${x.owned} of this printing` : `need ${x.need} · have ${x.owned}`}</span>`;''')
rep('''  const bought = `<button class="btn sh-got" data-got="${esc(x.key)}" title="Adds 1 ${esc(c.name)} (${esc(codeOf(c))}) to your collection">+ Bought 1</button>`;''',
    '''  const bought = (x.extra ? `<span class="step sh-xq" role="group" aria-label="Copies of ${esc(c.name)} to buy"><button data-xq="-1" data-x="${esc(x.extra)}" aria-label="One fewer">−</button><output>${x.buy}</output><button data-xq="1" data-x="${esc(x.extra)}" aria-label="One more">+</button></span><button class="btn sh-rmx" data-xrm="${esc(x.extra)}">Remove</button>` : "")
    + `<button class="btn sh-got" ${x.extra ? `data-gotx="${esc(x.extra)}"` : `data-got="${esc(x.key)}"`} title="Adds 1 ${esc(c.name)} (${esc(codeOf(c))}) to your collection">+ Bought 1</button>`;''')
rep('''  if (!all.length){''', '''  if (!all.length && !Object.keys(P.extra || {}).length){''')
rep('''<p class="meta">Add a deck in <b>My Decks</b> and every card it still needs shows up here, after the cards in your collection.</p>''',
    '''<p class="meta">Add a deck in <b>My Decks</b> and every card it still needs shows up here, after the cards in your collection. You can also add single cards just below.</p>''')

# ---------- CA + US everywhere on the list
rep('''`${esc(m1(s.cost))} to finish`''', '''`${esc(money(s.cost))} to finish`''')
rep('''`${esc(items[0].name)} ${esc(m1(items[0].cost))}`''', '''`${esc(items[0].name)} ${esc(money(items[0].cost))}`''')
rep('''`market ${esc(m1(cheap.price))} each`''', '''`market ${esc(money(cheap.price))} each`''')
rep('''` · market ${esc(m1(worth))}`''', '''` · market ${esc(money(worth))}`''')

# ---------- added-card buttons
rep('''  const g = e.target.closest("[data-got]");''', '''  const xb = e.target.closest("[data-xq],[data-xrm],[data-gotx]");
  if (xb){
    const ex = {...(shopP().extra || {})}, id = xb.dataset.x || xb.dataset.xrm || xb.dataset.gotx;
    if (xb.dataset.gotx){ adjust(id, 1); ex[id] = (ex[id] || 0) - 1; }
    else if (xb.dataset.xrm) ex[id] = 0;
    else ex[id] = Math.max(0, Math.min(99, (ex[id] || 0) + +xb.dataset.xq));
    if (!(ex[id] > 0)) delete ex[id];
    return setShop({extra: ex});
  }
  const g = e.target.closest("[data-got]");''')

# ---------- the search box (same feel as Open Packs)
rep('''function saveDeckView(){''', r'''let shSug = [], shSel = 0;
function shSuggest(){
  const q = norm($("sh-q").value);
  if (!q) shSug = [];
  else {
    const words = q.split(" ");
    shSug = CARDS.filter(c => words.every(w => norm(c.name).includes(w)))
      .map(c => ({c, s: (norm(c.name) === q ? -5 : 0) + (norm(c.name).startsWith(q) ? 0 : 10) + (c.variant ? 3 : 0) + (c.token ? 6 : 0) + (["OPP","PR","JDG"].includes(c.set) ? 2 : 0) + META.sets.findIndex(x => x.code === c.set) * 0.1}))
      .sort((a, b) => a.s - b.s || a.c.name.localeCompare(b.c.name)).slice(0, 8).map(x => x.c);
  }
  shSel = 0; shDraw();
}
function shDraw(){
  const ex = shopP().extra || {};
  $("sh-q").setAttribute("aria-expanded", shSug.length > 0);
  $("sh-sug").innerHTML = shSug.map((c, i) => `<li role="option" id="shsug-${i}" data-i="${i}" aria-selected="${i === shSel}">
    ${thumbHTML(c, 100).replace("<button", "<span").replace("</button>", "</span>").replace(/ data-img="[^"]*"/, "")}
    <span class="code"><b>${c.set}</b>${esc(codeOf(c).split(" ")[1])}</span>
    <span class="info"><span class="name">${esc(c.name)}</span><span class="sub"><span class="r-${c.rarity}">${c.rarity}</span>${c.variant ? `<span class="pill var">${esc(c.variant)}</span>` : ""}${banPill(c)}<span>${c.price != null ? esc(money(c.price)) : "No price"}</span></span></span>
    <span class="own">${ex[c.id] ? `on list ${ex[c.id]}` : counts[c.id] ? `own ${counts[c.id]}` : ""}</span></li>`).join("");
  $("sh-q").setAttribute("aria-activedescendant", shSug.length ? "shsug-" + shSel : "");
}
function shAdd(i){
  const c = shSug[i]; if (!c) return;
  const ex = {...(shopP().extra || {})}; ex[c.id] = Math.min(99, (ex[c.id] || 0) + 1);
  setShop({extra: ex});
  $("sh-addmsg").textContent = `Added ${c.name} (${codeOf(c)}${c.variant ? ` · ${c.variant}` : ""}). You want ${ex[c.id]}.`;
  $("sh-q").value = ""; shSug = []; shDraw(); $("sh-q").focus();
}
$("sh-q").addEventListener("input", shSuggest);
$("sh-q").addEventListener("keydown", e => {
  if (e.key === "ArrowDown" && shSug.length){ shSel = (shSel + 1) % shSug.length; shDraw(); e.preventDefault(); }
  else if (e.key === "ArrowUp" && shSug.length){ shSel = (shSel - 1 + shSug.length) % shSug.length; shDraw(); e.preventDefault(); }
  else if (e.key === "Enter"){ shAdd(shSel); e.preventDefault(); }
  else if (e.key === "Escape"){ $("sh-q").value = ""; shSug = []; shDraw(); }
});
$("sh-q").addEventListener("blur", () => setTimeout(() => { shSug = []; shDraw(); }, 150));
$("sh-sug").addEventListener("mousedown", e => { const li = e.target.closest("li"); if (li){ e.preventDefault(); shAdd(+li.dataset.i); } });
function saveDeckView(){''')

# ---------- styles
_i = h.rfind("</style>"); h = h[:_i] + """.sh-addp{display:grid;gap:8px}
.sh-addp .meta{margin:0}
#sh-addmsg{color:var(--ok)} #sh-addmsg:empty{display:none}
.sh-mine{border-color:color-mix(in srgb,var(--accent) 55%,var(--line)) !important;color:var(--accent)}
.sh-act{gap:8px;flex-wrap:wrap;align-items:center}
.sh-xq button{width:30px;height:30px}
.sh-rmx{padding:5px 10px;font-size:13px;color:var(--muted)}
.sh-rmx:hover{color:var(--fury);border-color:var(--fury)}
.dk-tile .sh-xq{justify-content:space-between}
""" + h[_i:]

open(out, "w", encoding="utf-8").write(h)
print("patch_shop_add: ok ->", out)
