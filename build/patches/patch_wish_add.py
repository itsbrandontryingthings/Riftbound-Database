#!/usr/bin/env python3
"""Add wish-listed cards to your collection or your decks (website only, last; builds on patch_wish_lists.py).
- Every card in the Wish List tab gets a "+ Add to..." button beside "Lists". It opens a picker (#wa-dlg, `waOpen`):
  tick Collection and/or any of your decks (several at once is fine: "I got it, and it's for my Jinx deck"),
  choose how many copies (starts at the copies wanted), and "Take them off my wish list" (ticked when Collection is
  ticked, so a card you got leaves the list; untick to keep it). Collection adds use adjust() like the + button;
  deck adds go into the right section (Legend / Runes / Battlefields / Main deck) like My Decks' Add a Card.
- In a named wish list (st.wfold) only that list's copies are taken off.
- A note pops up with Undo (`waUndo`: puts the collection count, decks and wish list back as they were).
Usage: patch_wish_add.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

# ---------- the button on every wish list card (grid tile and list row)
rep("${wfTags(id, wsel)}${wfBtn(c)}", "${wfTags(id, wsel)}${wfBtn(c)}${waBtn(c)}", 2)

# ---------- styles
rep("#wf-dlg::backdrop{background:rgb(5 6 10 / .78)}", """#wf-dlg::backdrop{background:rgb(5 6 10 / .78)}
#wa-dlg{border:1px solid var(--line);border-radius:12px;background:var(--panel);color:var(--fg);padding:18px;max-width:min(460px,calc(100vw - 32px));width:100%}
#wa-dlg::backdrop{background:rgb(5 6 10 / .78)}
.wabtn{background:none;border:1px solid color-mix(in srgb,var(--ok) 45%,var(--line));border-radius:6px;padding:1px 8px;color:var(--ok);font-size:12.5px;white-space:nowrap}
.wabtn:hover{border-color:var(--ok);background:color-mix(in srgb,var(--ok) 10%,transparent)}
#wa-dlg .wfrow.on{border-color:color-mix(in srgb,var(--ok) 60%,var(--line));background:color-mix(in srgb,var(--ok) 10%,var(--bg))}
#wa-dlg .wfn small{display:block;font-weight:400}
.wa-q{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.wa-off{display:flex;align-items:center;gap:8px;font-size:14px}
.wa-off input{width:18px;height:18px;margin:0}""")

# ---------- the picker
rep('  <dialog id="share" aria-labelledby="share-title">', '''  <dialog id="wa-dlg" aria-labelledby="wa-title"><div class="wfd">
    <h2 id="wa-title">Add to Collection or a Deck</h2>
    <div class="wfd-card" id="wa-card"></div>
    <p class="meta">Pick where the card goes. You can pick more than one, like your collection and the deck it's for.</p>
    <div class="wfd-rows" id="wa-rows" role="group" aria-label="Where to add it"></div>
    <div class="wa-q"><span class="collect-k">Copies</span><span class="step" role="group" aria-label="Copies to add"><button type="button" id="wa-minus" aria-label="One fewer">−</button><output id="wa-n">1</output><button type="button" id="wa-plus" aria-label="One more">+</button></span></div>
    <label class="wa-off"><input type="checkbox" id="wa-off"> <span id="wa-offl">Take them off my wish list</span></label>
    <p class="msg" id="wa-msg" aria-live="polite"></p>
    <div class="frow"><button type="button" class="btn" id="wa-x">Cancel</button><span class="grow"></span><button type="button" class="btn primary" id="wa-go">Add</button></div>
  </div></dialog>
  <dialog id="share" aria-labelledby="share-title">''')

# ---------- the code
rep("// 🛒 on any card: every tap puts one more copy", r'''// ＋ Add to… on a wish list card: put it in your collection and/or any of your decks
const waBtn = c => `<button class="wabtn" data-waadd="${esc(c.id)}" aria-haspopup="dialog" title="Add ${esc(c.name)} to your collection or one of your decks" aria-label="Add ${esc(c.name)} to your collection or a deck">＋ Add to…</button>`;
let wa = {id: "", n: 1, to: new Set(), offSet: false}, waLast = null;
function waOpen(id){
  const c = byId[id]; if (!c) return;
  const ws = typeof wfSel === "function" ? wfSel() : null, want = ws ? wfIn(ws.fid, id) : (wish[id] || 0);
  wa = {id, n: Math.max(1, Math.min(99, want || 1)), to: new Set(["__col"]), offSet: false};
  $("wa-off").checked = true; $("wa-msg").textContent = ""; waDraw();
  const d = $("wa-dlg"); if (!d.open){ try { d.showModal(); } catch(e){ d.setAttribute("open", ""); } }
}
function waDeckN(d, key){ return parseDeck(d.text).reduce((a, s) => a + s.rows.filter(r => r.key === key).reduce((b, r) => b + r.q, 0), 0); }
function waDraw(){
  const c = byId[wa.id]; if (!c) return; const key = norm(c.name), want = wish[c.id] || 0;
  $("wa-card").innerHTML = `${thumbHTML(c, 160).replace("<button", "<span").replace("</button>", "</span>").replace(/ data-img="[^"]*"/, "")}<span class="info"><span class="name">${esc(c.name)}</span><span class="meta">${esc(codeOf(c))}${c.variant ? ` · ${esc(c.variant)}` : ""}${want ? ` · you want ${want}` : ""}</span></span>`;
  const have = counts[c.id] || 0, decks = customDecks;
  const row = (v, name, sub) => { const on = wa.to.has(v);
    return `<div class="wfrow${on ? " on" : ""}"><button type="button" class="wftog" data-wato="${esc(v)}" aria-pressed="${on}"><span class="wfchk" aria-hidden="true">${on ? "✓" : ""}</span><span class="wfn">${esc(name)}<small class="meta">${esc(sub)}</small></span></button></div>`; };
  $("wa-rows").innerHTML = row("__col", "My Collection", have ? `you have ${have} of this printing` : "you don't have it yet")
    + (decks.length ? decks.map(d => { const k = waDeckN(d, key); return row(d.id, d.name, k ? `${k} in this deck already` : "not in this deck yet"); }).join("")
      : `<p class="meta">No decks yet. Make one in My Decks and it'll show up here.</p>`);
  $("wa-n").textContent = wa.n; $("wa-minus").disabled = wa.n <= 1; $("wa-plus").disabled = wa.n >= 99;
  if (!wa.offSet) $("wa-off").checked = wa.to.has("__col");
  const ws = typeof wfSel === "function" ? wfSel() : null;
  $("wa-offl").textContent = `Take ${wa.n === 1 ? "it" : "them"} off my wish list${ws && ws.fid ? ` (${wfName(ws.fid)})` : ""}`;
  $("wa-off").parentElement.hidden = !want;
  $("wa-go").disabled = !wa.to.size;
  $("wa-go").textContent = wa.to.size ? `Add ${wa.n}` : "Pick where to add it";
}
$("wa-rows").addEventListener("click", e => { const b = e.target.closest("[data-wato]"); if (!b) return; const v = b.dataset.wato; if (wa.to.has(v)) wa.to.delete(v); else wa.to.add(v); $("wa-msg").textContent = ""; waDraw(); });
$("wa-minus").addEventListener("click", () => { wa.n = Math.max(1, wa.n - 1); waDraw(); });
$("wa-plus").addEventListener("click", () => { wa.n = Math.min(99, wa.n + 1); waDraw(); });
$("wa-off").addEventListener("change", () => { wa.offSet = true; });
$("wa-x").addEventListener("click", () => $("wa-dlg").close());
$("wa-dlg").addEventListener("click", e => { if (e.target === $("wa-dlg")) $("wa-dlg").close(); });
document.addEventListener("click", e => { const b = e.target.closest("button[data-waadd]"); if (b){ e.preventDefault(); waOpen(b.dataset.waadd); } });
function waToDeck(d, c, q){
  const key = norm(c.name), secs = parseDeck(d.text), kind = deckKind(key);
  let sec = secs.find(s => s.rows.some(r => r.key === key));
  if (!sec){
    const want = {legend: /legend/i, rune: /rune/i, battlefield: /battlefield/i}[kind];
    sec = want ? secs.find(s => want.test(s.label)) : secs.find(s => !/legend|champion|rune|battlefield|side/i.test(s.label));
    if (!sec){ sec = {label: {legend: "Legend", rune: "Runes", battlefield: "Battlefields"}[kind] || "Main deck", rows: []}; secs.push(sec); }
  }
  const ex = sec.rows.find(r => r.key === key);
  if (ex) ex.q += q; else sec.rows.push({name: c.name, q, key});
  d.text = deckToText(secs); delete d.own;
}
function waRedraw(){
  if (st.tab === "wish") renderWish(); if (st.tab === "decks") renderDecks();
  if (st.tab === "shop" && typeof renderShop === "function") renderShop();
}
$("wa-go").addEventListener("click", () => {
  const c = byId[wa.id]; if (!c || !wa.to.size) return;
  const q = wa.n, ws = typeof wfSel === "function" ? wfSel() : null;
  waLast = {id: c.id, have: counts[c.id] || 0, decks: JSON.stringify(customDecks), wish: JSON.stringify(wish)};
  const where = [];
  if (wa.to.has("__col")){ adjust(c.id, q); where.push("your collection"); }
  const dk = customDecks.filter(d => wa.to.has(d.id));
  dk.forEach(d => { waToDeck(d, c, q); where.push(d.name); });
  if (dk.length) saveDecks();
  let left = wish[c.id] || 0;
  if ($("wa-off").checked && left){
    if (ws && ws.fid) wfSet(ws.fid, c.id, Math.max(0, wfIn(ws.fid, c.id) - q));
    else { left = Math.max(0, left - q); if (left) wish[c.id] = left; else delete wish[c.id]; wfClean(); }
    saveWish(); wishBtnsRefresh(c.id);
  }
  left = wish[c.id] || 0;
  $("wa-dlg").close(); waRedraw();
  const list = where.length > 1 ? where.slice(0, -1).map(esc).join(", ") + " and " + esc(where[where.length - 1]) : esc(where[0]);
  toast(`✓ Added <b>${q} ${esc(c.name)}</b> to ${list}${left ? ` · still want ${left}` : ""}<button class="btn toast-undo" id="wa-undo" type="button">Undo</button>`, 6000);
});
function waUndo(){
  const u = waLast; if (!u) return; waLast = null;
  const d = u.have - (counts[u.id] || 0); if (d) adjust(u.id, d);
  customDecks = JSON.parse(u.decks); saveDecks();
  const w = JSON.parse(u.wish); Object.keys(wish).forEach(k => delete wish[k]); Object.assign(wish, w); saveWish(); wishBtnsRefresh(u.id);
  waRedraw(); toast("Took that back.", 2000);
}
document.addEventListener("click", e => { if (e.target.id === "wa-undo"){ e.preventDefault(); waUndo(); } });
// 🛒 on any card: every tap puts one more copy''')

open(out, "w", encoding="utf-8").write(h)
print("ok")
