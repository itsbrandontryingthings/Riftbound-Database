#!/usr/bin/env python3
"""Wish List folders ("lists") (website; runs last, after patch_deck_sort.py).
- People make their own named lists inside the Wish List, e.g. "Master Yi Deck", "Art Deck", "Collectibles".
- Saved inside the wish row (no SQL change): wish._folders = [{id, name}], wish._wf = {list id: {card id: copies}}.
  wish[card id] is still the TOTAL wanted, so sharing, Friends trade matching, offers and old saves keep working;
  copies that aren't in any list are "General" (wfIn("", id) = total - copies in lists).
- ♡ Want / ♥ Wanted on any card opens a picker (#wf-dlg): tick the lists the card goes in, change copies per list,
  make a new list, or remove the card from the wish list.
- Wish List tab: a row of list chips (All, General, each list, + New List) above the cards; picking a list shows
  only its cards (copies, cost, copy-to-clipboard and Add a Card all follow the list). Rename / Delete list
  (deleting keeps the cards, under General). Each card shows which lists it's in and a "Lists" button.
  The chosen list is st.wfold ("" = All, "~gen" = General).
Usage: patch_wish_lists.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

# ---- data helpers
rep('''const wishIds = () => Object.keys(wish).filter(k => k[0] !== "_" && wish[k] > 0);''', r'''const wishIds = () => Object.keys(wish).filter(k => k[0] !== "_" && wish[k] > 0);
// ---- wish lists (folders): wish._folders = [{id, name}], wish._wf = {list id: {card id: copies}}. wish[card id] stays the
// total wanted; copies that aren't in any list are "General" (list id "").
const wFolders = () => Array.isArray(wish._folders) ? wish._folders.filter(f => f && f.id && f.name) : [];
const wfMap = () => wish._wf && typeof wish._wf === "object" ? wish._wf : {};
const wfSum = id => wFolders().reduce((a, f) => a + (+((wfMap()[f.id] || {})[id]) || 0), 0);
function wfIn(fid, id){ return fid ? (+((wfMap()[fid] || {})[id]) || 0) : Math.max(0, (wish[id] || 0) - wfSum(id)); }
const wfName = fid => fid ? ((wFolders().find(f => f.id === fid) || {}).name || "List") : "General";
function wfSel(){ const v = st.wfold || ""; if (v === "~gen" && wFolders().length) return {fid: ""}; if (v && wFolders().some(f => f.id === v)) return {fid: v}; return null; }
const wq = id => { const s = wfSel(); return s ? wfIn(s.fid, id) : (wish[id] || 0); };
function wfClean(){
  const fs = wFolders(), m = wfMap(), o = {};
  for (const f of fs){ o[f.id] = {}; for (const [id, n] of Object.entries(m[f.id] || {})) if (wish[id] > 0 && +n > 0) o[f.id][id] = Math.min(99, Math.floor(+n)); }
  // a list can't hold more copies than the total wanted: trim from the newest list first
  for (const id of wishIds()){ let over = fs.reduce((a, f) => a + (o[f.id][id] || 0), 0) - wish[id]; for (let i = fs.length - 1; over > 0 && i >= 0; i--){ const x = o[fs[i].id], t = Math.min(over, x[id] || 0); if (t){ x[id] -= t; over -= t; if (!x[id]) delete x[id]; } } }
  if (fs.length){ wish._folders = fs; wish._wf = o; } else { delete wish._folders; delete wish._wf; }
}
// set how many copies of a card are in one list (fid "" = General); the total follows
function wfSet(fid, id, n){
  n = Math.max(0, Math.min(99, Math.floor(n) || 0));
  const tot = Math.min(99, (wish[id] || 0) - wfIn(fid, id) + n);
  if (fid){ const m = {...wfMap()}; m[fid] = {...(m[fid] || {})}; if (n) m[fid][id] = n; else delete m[fid][id]; wish._wf = m; }
  if (tot > 0) wish[id] = tot; else delete wish[id];
  wfClean();
}
function wfNew(name){
  name = String(name || "").replace(/\s+/g, " ").trim().slice(0, 40); if (!name) return null;
  const fs = wFolders(), same = fs.find(f => f.name.toLowerCase() === name.toLowerCase()); if (same) return same.id;
  if (fs.length >= 30) return null;
  const id = "f" + Date.now().toString(36) + Math.random().toString(36).slice(2, 5);
  wish._folders = fs.concat([{id, name}]); wish._wf = {...wfMap(), [id]: {}}; return id;
}
function wishBtnsRefresh(id){
  document.querySelectorAll(`button[data-wish="${CSS.escape(id)}"]`).forEach(x => { if (byId[id]) x.outerHTML = wishBtn0(byId[id], x.classList.contains("over")); });
}''')

rep('''title="${on ? "On your wish list (tap to remove)" : "Add to your wish list"}" aria-label="${on ? "Remove " + esc(c.name) + " from" : "Add " + esc(c.name) + " to"} your wish list">''',
    '''aria-haspopup="dialog" title="${on ? "On your wish list (tap to change lists or remove)" : "Add to a wish list"}" aria-label="${on ? "Change wish lists for " + esc(c.name) : "Add " + esc(c.name) + " to a wish list"}">''')

# ---- Wish List tab: list chips, per-list view
rep('''function renderWish(){
  const ids = wishIds().filter(id => byId[id])''', '''function renderWish(){
  const wsel = wfSel(); if (!wsel && st.wfold) st.wfold = "";
  const ids = wishIds().filter(id => byId[id] && (!wsel || wfIn(wsel.fid, id) > 0))''')
rep('''  const copies = ids.reduce((a, id) => a + wish[id], 0);
  const cost = ids.reduce((a, id) => a + wish[id] * (byId[id].price || 0), 0);''', '''  const copies = ids.reduce((a, id) => a + wq(id), 0);
  const cost = ids.reduce((a, id) => a + wq(id) * (byId[id].price || 0), 0);''')
rep('''$("wish-summary").innerHTML = `<h2>Wish List</h2>''', '''$("wish-summary").innerHTML = `<h2>Wish List</h2>${wfBarHTML(wsel)}''')
rep('''"Tap ♡ Want on any card in Collection, or add one just below. It doesn't have to be in one of your decks."''',
    '''(wsel ? "Nothing in this list yet. Tap ♡ Want on any card in Collection and pick this list, or add one just below." : "Tap ♡ Want on any card in Collection, or add one just below. It doesn't have to be in one of your decks.")''')
rep('''${ids.length ? `<button class="btn" id="wish-copy">Copy wish list</button>` : ""}${typeof openShare === "function" && ids.length ?''',
    '''${ids.length ? `<button class="btn" id="wish-copy">Copy ${wsel ? "this list" : "wish list"}</button>` : ""}${typeof openShare === "function" && ids.length && !wsel ?''')
rep('''<h2 class="mk-h">My Wish List</h2>''', '''<h2 class="mk-h">${wsel ? esc(wfName(wsel.fid)) : "My Wish List"}</h2>''')
rep('''    + vis.map(id => { const c = byId[id], q = wish[id], have = counts[id] || 0;''', '''    + vis.map(id => { const c = byId[id], q = wq(id), have = counts[id] || 0;''')
# which lists a card is in + a Lists button (grid tile and list row)
rep('''<div class="tsub"><span class="own${have ? " ok" : ""}">${have ? `you own ${have}` : "you don't own it"}</span></div>''',
    '''<div class="tsub"><span class="own${have ? " ok" : ""}">${have ? `you own ${have}` : "you don't own it"}</span></div><div class="tsub wftags">${wfTags(id, wsel)}${wfBtn(c)}</div>''')
rep('''<span class="own${have ? " ok" : ""}">${have ? `you own ${have}` : "you don't own it"}</span></span></span>''',
    '''<span class="own${have ? " ok" : ""}">${have ? `you own ${have}` : "you don't own it"}</span>${wfTags(id, wsel)}${wfBtn(c)}</span></span>''')
rep('''function wishText(){''', r'''let wfEdit = "";   // "new" or "ren" while the name box is open in the Wish List tab
function wfBarHTML(ws){
  const fs = wFolders(), all = wishIds().filter(id => byId[id]), cur = ws ? (ws.fid || "~gen") : "";
  const n = fid => all.filter(id => wfIn(fid, id) > 0).length;
  const chip = (v, name, k) => `<button class="wfchip" data-wf="${esc(v)}" aria-pressed="${cur === v}">${esc(name)} <small>${k}</small></button>`;
  const form = wfEdit ? `<form class="wfform" id="wf-form"><input id="wf-name" maxlength="40" autocomplete="off" placeholder="List name, e.g. Master Yi Deck, Art Deck, Collectibles" aria-label="List name" value="${wfEdit === "ren" && ws ? esc(wfName(ws.fid)) : ""}"><button class="btn primary" type="submit">${wfEdit === "ren" ? "Save name" : "Create list"}</button><button class="btn" type="button" id="wf-cancel">Cancel</button><span class="meta" id="wf-msg" aria-live="polite"></span></form>` : "";
  return `<div class="wfbar" role="group" aria-label="Your wish lists"><span class="collect-k">Lists</span>${chip("", "All", all.length)}${fs.length ? chip("~gen", "General", n("")) : ""}${fs.map(f => chip(f.id, f.name, n(f.id))).join("")}<button class="wfchip wfnew" id="wf-new" aria-expanded="${wfEdit === "new"}">+ New List</button>${ws && ws.fid ? `<span class="grow"></span><button class="btn sm" id="wf-ren">Rename</button><button class="btn sm" id="wf-del">Delete list</button>` : ""}</div>
    ${fs.length ? "" : `<p class="meta wfhint">Sort your wish list into lists, like "Master Yi Deck", "Art Deck" or "Collectibles". Tap + New List to start one.</p>`}${form}`;
}
function wfTags(id, ws){
  if (ws) return ""; const fs = wFolders(); if (!fs.length) return "";
  return fs.filter(f => wfIn(f.id, id) > 0).map(f => { const k = wfIn(f.id, id); return `<span class="wftag">${esc(f.name)}${k > 1 ? ` ×${k}` : ""}</span>`; }).join("");
}
const wfBtn = c => `<button class="wfbtn" data-wfpick="${esc(c.id)}" aria-haspopup="dialog" title="Choose which wish lists ${esc(c.name)} is in" aria-label="Wish lists for ${esc(c.name)}">📁 Lists</button>`;
function wishText(){''')

# +/- and Remove change the list you're looking at (All = the totals)
rep('''  if (b.dataset.w === "rm") delete wish[id]; else { const q = (wish[id] || 0) + Number(b.dataset.w); if (q > 0) wish[id] = q; else delete wish[id]; }
  saveWish(); renderWish();''', '''  const ws = wfSel();
  if (ws) wfSet(ws.fid, id, b.dataset.w === "rm" ? 0 : wfIn(ws.fid, id) + Number(b.dataset.w));
  else { if (b.dataset.w === "rm") delete wish[id]; else { const q = Math.min(99, (wish[id] || 0) + Number(b.dataset.w)); if (q > 0) wish[id] = q; else delete wish[id]; } wfClean(); }
  saveWish(); wishBtnsRefresh(id); renderWish();''')
rep('''  if (e.target.id === "wish-copy"){ const ids = wishIds().filter(id => byId[id]); copy(wishText() + `\\n\\nTotal: ${money(ids.reduce((a, id) => a + wish[id] * (byId[id].price || 0), 0))}`, "wish list"); }''',
    r'''  if (e.target.id === "wish-copy"){ const ws = wfSel(), ids = wishIds().filter(id => byId[id] && (!ws || wfIn(ws.fid, id) > 0));
    copy((ws ? wfName(ws.fid) + "\n" : "") + ids.map(id => { const c = byId[id]; return `${wq(id)} ${c.name} [${codeOf(c)}${c.variant ? ` · ${c.variant}` : ""}]`; }).join("\n") + `\n\nTotal: ${money(ids.reduce((a, id) => a + wq(id) * (byId[id].price || 0), 0))}`, ws ? "list" : "wish list"); }''')

# the list chips, + New List, Rename, Delete
rep('''// ♡ / ♥ on any card''', r'''$("wish-summary").addEventListener("click", e => {
  const chip = e.target.closest("[data-wf]");
  if (chip){ st.wfold = chip.dataset.wf; wfEdit = ""; LS.set("rb-filters", {...st, doms:[...st.doms], limit:undefined}); renderWish(); return; }
  const id = e.target.id, ws = wfSel();
  if (id === "wf-new" || id === "wf-ren"){ wfEdit = id === "wf-new" ? (wfEdit === "new" ? "" : "new") : "ren"; renderWish(); if ($("wf-name")){ $("wf-name").focus(); $("wf-name").select(); } }
  else if (id === "wf-cancel"){ wfEdit = ""; renderWish(); }
  else if (id === "wf-del" && ws && ws.fid){
    if (!confirm(`Delete the list "${wfName(ws.fid)}"?\n\nThe cards in it stay on your wish list, under General.`)) return;
    wish._folders = wFolders().filter(f => f.id !== ws.fid); const m = {...wfMap()}; delete m[ws.fid]; wish._wf = m; wfClean();
    st.wfold = ""; LS.set("rb-filters", {...st, doms:[...st.doms], limit:undefined}); saveWish(); renderWish();
  }
});
$("wish-summary").addEventListener("submit", e => {
  if (e.target.id !== "wf-form") return; e.preventDefault();
  const name = $("wf-name").value.replace(/\s+/g, " ").trim(), ws = wfSel();
  if (!name){ $("wf-msg").textContent = "Give your list a name."; return; }
  if (wfEdit === "ren" && ws && ws.fid){
    if (wFolders().some(f => f.id !== ws.fid && f.name.toLowerCase() === name.toLowerCase())){ $("wf-msg").textContent = "You already have a list with that name."; return; }
    wish._folders = wFolders().map(f => f.id === ws.fid ? {...f, name: name.slice(0, 40)} : f);
  } else {
    if (wFolders().length >= 30){ $("wf-msg").textContent = "You can have up to 30 lists."; return; }
    st.wfold = wfNew(name); LS.set("rb-filters", {...st, doms:[...st.doms], limit:undefined});
  }
  wfEdit = ""; saveWish(); renderWish();
});
// ♡ / ♥ on any card''')

# ♡ / ♥ opens the list picker instead of switching straight on/off
rep('''  const id = b.dataset.wish;
  if (wish[id]) delete wish[id]; else wish[id] = 1;
  saveWish();
  document.querySelectorAll(`button[data-wish="${CSS.escape(id)}"]`).forEach(x => { x.outerHTML = wishBtn0(byId[id], x.classList.contains("over")); });
  if (st.tab === "wish") renderWish();
}, true);''', r'''  wfOpen(b.dataset.wish);
}, true);
document.addEventListener("click", e => { const b = e.target.closest("button[data-wfpick]"); if (b){ e.preventDefault(); wfOpen(b.dataset.wfpick); } });
// ---- the "which wish list?" picker
let wfCard = null;
function wfOpen(id){
  if (!byId[id]) return; wfCard = id; $("wf-dname").value = ""; $("wf-dmsg").textContent = ""; wfDraw();
  const d = $("wf-dlg"); if (!d.open){ try { d.showModal(); } catch(e){ d.setAttribute("open", ""); } }
}
function wfDraw(){
  const c = byId[wfCard]; if (!c) return; const on = (wish[c.id] || 0) > 0;
  $("wf-title").textContent = on ? "Your Wish Lists" : "Add to a Wish List";
  $("wf-card").innerHTML = `${thumbHTML(c, 160).replace("<button", "<span").replace("</button>", "</span>").replace(/ data-img="[^"]*"/, "")}<span class="info"><span class="name">${esc(c.name)}</span><span class="meta">${esc(codeOf(c))}${c.variant ? ` · ${esc(c.variant)}` : ""}${on ? ` · you want ${wish[c.id]}` : ""}</span></span>`;
  const rows = [{id: "", name: "General"}].concat(wFolders());
  $("wf-rows").innerHTML = rows.map(f => { const n = wfIn(f.id, c.id);
    return `<div class="wfrow${n ? " on" : ""}"><button type="button" class="wftog" data-wfr="${esc(f.id)}" aria-pressed="${n > 0}"><span class="wfchk" aria-hidden="true">${n ? "✓" : ""}</span><span class="wfn">${esc(f.name)}${f.id ? "" : ` <small class="meta">(not in a list)</small>`}</span></button>${n ? `<span class="step" role="group" aria-label="Copies in ${esc(f.name)}"><button type="button" data-wfq="${esc(f.id)}" data-d="-1" aria-label="One fewer">−</button><output>${n}</output><button type="button" data-wfq="${esc(f.id)}" data-d="1" aria-label="One more">+</button></span>` : ""}</div>`; }).join("");
  $("wf-drm").hidden = !on;
}
function wfChanged(){ saveWish(); wishBtnsRefresh(wfCard); if (st.tab === "wish") renderWish(); wfDraw(); }
$("wf-rows").addEventListener("click", e => {
  const t = e.target.closest("[data-wfr]"), q = e.target.closest("[data-wfq]"); if (!wfCard) return;
  if (t){ const f = t.dataset.wfr; wfSet(f, wfCard, wfIn(f, wfCard) ? 0 : 1); wfChanged(); }
  else if (q){ const f = q.dataset.wfq; wfSet(f, wfCard, wfIn(f, wfCard) + Number(q.dataset.d)); wfChanged(); }
});
$("wf-dnew").addEventListener("submit", e => {
  e.preventDefault(); const name = $("wf-dname").value.replace(/\s+/g, " ").trim();
  if (!name){ $("wf-dmsg").textContent = "Type a name for the new list first."; return; }
  if (wFolders().length >= 30 && !wFolders().some(f => f.name.toLowerCase() === name.toLowerCase())){ $("wf-dmsg").textContent = "You can have up to 30 lists."; return; }
  const fid = wfNew(name); if (!fid) return;
  if (!wfIn(fid, wfCard)) wfSet(fid, wfCard, 1);
  $("wf-dname").value = ""; $("wf-dmsg").textContent = `Added to ${wfName(fid)}.`; wfChanged();
});
$("wf-drm").addEventListener("click", () => { if (!wfCard) return; delete wish[wfCard]; wfClean(); wfChanged(); $("wf-dlg").close(); });
$("wf-dok").addEventListener("click", () => $("wf-dlg").close());
$("wf-dlg").addEventListener("click", e => { if (e.target === $("wf-dlg")) $("wf-dlg").close(); });''')

# Add a Card (in the Wish List tab) goes into the list you're looking at
rep('''  wish[c.id] = Math.min(99, (wish[c.id] || 0) + 1); saveWish(); renderWish();''',
    '''  const ws = wfSel(), wf = ws ? ws.fid : ""; wfSet(wf, c.id, wfIn(wf, c.id) + 1); saveWish(); renderWish();''')
rep('''). You want ${wish[c.id]}.`;''', ''')${ws ? ` to ${wfName(wf)}` : ""}. You want ${wish[c.id]}${ws ? " in all" : ""}.`;''')
rep('''wish[b] * Math.max(0, p(b)) - wish[a] * Math.max(0, p(a))''', '''wq(b) * Math.max(0, p(b)) - wq(a) * Math.max(0, p(a))''')

# a restored backup keeps its lists
rep('''if (byId[k] && v > 0) wish[k] = Math.floor(v);
  LS.set("rb-wish", wish);''', '''if (byId[k] && v > 0) wish[k] = Math.floor(v);
  if (data.wish && Array.isArray(data.wish._folders)){ wish._folders = data.wish._folders; wish._wf = data.wish._wf || {}; wfClean(); }
  LS.set("rb-wish", wish);''')

# ---- the picker dialog
rep('''  <dialog id="share" aria-labelledby="share-title">''', '''  <dialog id="wf-dlg" aria-labelledby="wf-title"><div class="wfd">
    <h2 id="wf-title">Add to a Wish List</h2>
    <div class="wfd-card" id="wf-card"></div>
    <p class="meta">Tap a list to put the card in it, tap again to take it out. A card can be in more than one list.</p>
    <div class="wfd-rows" id="wf-rows"></div>
    <form class="wfform" id="wf-dnew" novalidate><input id="wf-dname" maxlength="40" autocomplete="off" placeholder="New list, e.g. Master Yi Deck" aria-label="New list name"><button class="btn" type="submit">Create &amp; add</button></form>
    <p class="msg" id="wf-dmsg" aria-live="polite"></p>
    <div class="frow"><button type="button" class="btn" id="wf-drm" hidden>Remove from wish list</button><span class="grow"></span><button type="button" class="btn primary" id="wf-dok">Done</button></div>
  </div></dialog>
  <dialog id="share" aria-labelledby="share-title">''')

_i = h.rfind("</style>"); h = h[:_i] + """.wfbar{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:10px 0 6px}
.wfbar .collect-k{margin-right:2px}
.wfbar .grow{flex:1}
.wfchip{background:var(--bg);border:1px solid var(--line);border-radius:999px;padding:6px 12px;color:var(--muted);font-size:13.5px;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.wfchip small{opacity:.7;margin-left:2px;font-variant-numeric:tabular-nums}
.wfchip:hover{color:var(--fg)}
.wfchip[aria-pressed="true"]{color:var(--fg);border-color:color-mix(in srgb,#ff7a90 60%,var(--line));background:color-mix(in srgb,#ff7a90 14%,transparent)}
.wfchip.wfnew{border-style:dashed;color:var(--accent)}
.btn.sm{padding:5px 10px;font-size:13px}
.wfhint{margin:2px 0 4px}
.wfform{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:6px 0}
.wfform input{flex:1 1 220px;min-width:0;background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:9px 12px;font:inherit;color:var(--fg)}
.wfform .meta:empty{display:none}
.wftag{font-size:12px;border:1px solid color-mix(in srgb,#ff7a90 40%,var(--line));color:#ffb3c0;border-radius:999px;padding:0 7px;white-space:nowrap}
.wfbtn{background:none;border:1px solid var(--line);border-radius:6px;padding:1px 8px;color:var(--muted);font-size:12.5px;white-space:nowrap}
.wfbtn:hover{color:var(--fg);border-color:var(--muted)}
.tsub.wftags{display:flex;flex-wrap:wrap;gap:4px;align-items:center}
#wf-dlg{border:1px solid var(--line);border-radius:12px;background:var(--panel);color:var(--fg);padding:18px;max-width:min(460px,calc(100vw - 32px));width:100%}
#wf-dlg::backdrop{background:rgb(5 6 10 / .78)}
.wfd{display:grid;gap:12px}
.wfd h2{font-family:var(--display);font-size:19px;margin:0}
.wfd .msg{font-size:13.5px;color:var(--ok)}
.wfd .msg:empty{display:none}
.wfd .grow{flex:1}
.wfd-card{display:flex;gap:12px;align-items:center}
.wfd-card .thumb{width:52px;flex:0 0 auto}
.wfd-card .info{display:grid;gap:2px;min-width:0}
.wfd-card .name{font-weight:600}
.wfd-rows{display:grid;gap:6px;max-height:45vh;overflow:auto}
.wfrow{display:flex;align-items:center;gap:8px;border:1px solid var(--line);border-radius:10px;padding:2px 6px 2px 2px;background:var(--bg)}
.wfrow.on{border-color:color-mix(in srgb,#ff7a90 55%,var(--line));background:color-mix(in srgb,#ff7a90 10%,var(--bg))}
.wftog{flex:1;min-width:0;display:flex;gap:10px;align-items:center;background:none;border:0;padding:10px 8px;color:var(--fg);text-align:left;font:inherit}
.wfn{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.wfchk{width:20px;height:20px;border:1.5px solid var(--muted);border-radius:5px;display:inline-grid;place-items:center;font-size:13px;font-weight:700;flex:0 0 auto}
.wfrow.on .wfchk{background:#ff7a90;border-color:#ff7a90;color:#14151b}
.wfrow .step button{width:30px;height:30px}
""" + h[_i:]

open(out, "w", encoding="utf-8").write(h)
print("ok")
