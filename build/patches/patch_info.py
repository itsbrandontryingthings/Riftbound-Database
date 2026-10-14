#!/usr/bin/env python3
"""Card info sheet + keyword filter. Runs after patch_foil on both the website and the local copy.
- The enlarged preview becomes an info sheet: the card (still tilting with the pointer, foils still shine)
  beside legality, set, Energy / Might / Power, domain, type, rarity, the effect with keyword badges and
  symbols, flavour, tags, artist, price and your copies / wish list.
- New "All keywords" filter (Action, Reaction, Temporary, Accelerate, Deathknell, ...).
- Search also matches keywords, rules text and tags (e.g. "deathknell", "draw 2", "Yordle").
Card text comes from text.js (window.RB_TEXT, built from Riftcodex by tools/fetch_text.py); without it the
sheet shows what cards.js has and the keyword filter is hidden.
Usage: patch_info.py in.html out.html"""
import sys

src, dst = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def sub(old, new, count=1):
    global h
    if old not in h:
        sys.exit("patch_info: not found: " + old[:90])
    h = h.replace(old, new, count)

# --- load text.js (missing file is fine)
sub('<script src="cards.js"></script>', '<script src="cards.js"></script>\n<script src="text.js"></script>')

# --- keyword filter control
sub('''<select id="rarity" aria-label="Rarity"><option value="">All rarities</option></select>''',
    '''<select id="rarity" aria-label="Rarity"><option value="">All rarities</option></select>
      <select id="kw" aria-label="Keyword"><option value="">All keywords</option></select>
      <select id="tg" aria-label="Champion or region tag"><option value="">All tags</option></select>''')
sub('''$("q").value = st.q; $("type").value = st.type; $("rarity").value = st.rarity;''',
    '''$("q").value = st.q; $("type").value = st.type; $("rarity").value = st.rarity; $("kw").value = st.kw || ""; $("tg").value = st.tg || "";''')
sub('''  if (st.rarity && c.rarity !== st.rarity) return false;''',
    '''  if (st.rarity && c.rarity !== st.rarity) return false;
  if (st.kw && !kwOf(c).includes(st.kw)) return false;
  if (st.tg && !(txOf(c) && txOf(c).tags.includes(st.tg))) return false;''')
sub('''if (!(c.name.toLowerCase().includes(q) || c.id.includes(q))) return false; }''',
    '''if (!(c.name.toLowerCase().includes(q) || c.id.includes(q) || findOf(c).includes(q))) return false; }''')
sub('''(st.rarity ? 1 : 0) +''', '''(st.rarity ? 1 : 0) + (st.kw ? 1 : 0) + (st.tg ? 1 : 0) +''')
sub('''$("rarity").addEventListener("change", e => {''',
    '''$("tg").addEventListener("change", e => { st.tg = e.target.value; st.limit = PAGE; st.page = 0; render(); });
$("kw").addEventListener("change", e => { st.kw = e.target.value; st.limit = PAGE; st.page = 0; render(); });
$("rarity").addEventListener("change", e => {''')
import re as _re
h, _n = _re.subn(r'(id="q" type="search" placeholder=")[^"]*"', r'\1Search name, keyword or ability, e.g. Jinx, Deathknell, draw"', h)
if not _n: sys.exit("patch_info: search box not found")

# --- card text helpers (before the static controls are built)
HELPERS = r'''
// ---- card text (text.js from Riftcodex): stats, rules text, keywords
const RBT = window.RB_TEXT || {n:{}, a:{}};
const TXNORM = n => n.replace(/\s*\((Alternate Art|Overnumbered|Signature|Metal|Starter|GG EZ|Launch Exclusive|Ultimate|Special)\)\s*$/, "").toLowerCase().replace(", ", " - ").replace(/[^a-z0-9]+/g, " ").trim();
function txOf(c){
  if (c._tx !== undefined) return c._tx;
  const r = RBT.n[TXNORM(c.name)] || RBT.n[TXNORM(c.name.split(" // ")[0])];
  const art = RBT.a[c.id.split("~")[0]] || (c.tcg && RBT.a["tcg:" + c.tcg]) || "";
  return c._tx = r ? {e:r[0], m:r[1], p:r[2], text:r[3] || "", fl:r[4] || "", tags:r[5] ? r[5].split(",") : [], sup:r[6] || "", art} : (art ? {text:"", fl:"", tags:[], sup:"", art} : null);
}
const KW_SKIP = new Set(["Add", "ADD", ">", ">>", "NO TEXT"]);
function kwOf(c){
  if (c._kw) return c._kw;
  const t = txOf(c), out = [];
  if (t) for (const m of t.text.matchAll(/\[([A-Za-z][A-Za-z' -]*?)(?:\s+\d+)?\]/g)) { const k = m[1].trim(); if (!KW_SKIP.has(k) && !out.includes(k)) out.push(k); }
  return c._kw = out;
}
function findOf(c){
  if (c._find !== undefined) return c._find;
  const t = txOf(c);
  return c._find = t ? (t.text.replace(/:rb_[a-z0-9_]+:/g, " ").replace(/[\[\]]/g, "") + " " + t.tags.join(" ") + " " + t.sup).toLowerCase() : "";
}
const KW_TIMING = new Set(["Action", "Reaction", "Hidden", "Quick-Draw"]), KW_DEATH = new Set(["Temporary", "Deathknell"]);
const kwClass = k => KW_TIMING.has(k) ? "kw t" : KW_DEATH.has(k) ? "kw d" : "kw";
function rulesHTML(s){
  // reminder text "(...)" is marked first, before symbols add their own markup
  return esc(s).replace(/\(([^()]{3,})\)/g, "\u0001($1)\u0002")
    .replace(/\[(&gt;)+\]/g, '<span class="sym arr" title="then">➜</span>')
    .replace(/\[(Add|ADD)\]/g, "<b>Add</b>")
    .replace(/\[([A-Za-z][A-Za-z' -]*?(?:\s+\d+)?)\]/g, (m, k) => `<span class="${kwClass(k.replace(/\s+\d+$/, ""))}">${k}</span>`)
    .replace(/:rb_energy_(\d+):/g, '<span class="sym en" title="$1 Energy">$1</span>')
    .replace(/:rb_might:/g, '<span class="sym mi" title="Might">⚔</span>')
    .replace(/:rb_exhaust:/g, '<span class="sym ex" title="Exhaust">⟳</span>')
    .replace(/:rb_rune_rainbow:/g, '<span class="sym rn any" title="Rune of any domain"></span>')
    .replace(/:rb_rune_([a-z]+):/g, (m, d) => `<span class="sym rn" title="${d[0].toUpperCase() + d.slice(1)} rune" style="background:var(--${d})"></span>`)
    .replace(/:rb_[a-z0-9_]+:/g, "")
    .replace(/\u0001/g, '<i class="rem">').replace(/\u0002/g, "</i>")
    .replace(/\n/g, "<br>");
}
'''
sub('// ---- static controls', HELPERS + '\n// ---- static controls')

# keyword options, most common first
sub('''$("type").insertAdjacentHTML("beforeend", `<option value="__token">Token</option>`);''',
    '''$("type").insertAdjacentHTML("beforeend", `<option value="__token">Token</option>`);
{ const kc = {}; CARDS.forEach(c => kwOf(c).forEach(k => kc[k] = (kc[k] || 0) + 1));
  const ks = Object.keys(kc).sort((a, b) => a.localeCompare(b));
  ks.forEach(k => $("kw").insertAdjacentHTML("beforeend", `<option value="${esc(k)}">${esc(k)} (${kc[k]})</option>`));
  if (!ks.length) $("kw").hidden = true;
  const tc = {}; CARDS.forEach(c => { const t = txOf(c); if (t) t.tags.forEach(g => tc[g] = (tc[g] || 0) + 1); });
  const ts = Object.keys(tc).sort((a, b) => a.localeCompare(b));
  ts.forEach(g => $("tg").insertAdjacentHTML("beforeend", `<option value="${esc(g)}">${esc(g)} (${tc[g]})</option>`));
  if (!ts.length) $("tg").hidden = true; }''')

# --- the info sheet layout
sub('''<div class="lbwrap" id="lb-fx">''', '''<div class="lbbody"><div class="lbleft"><div class="lbwrap" id="lb-fx">''')
sub('''<span class="glare" aria-hidden="true"></span></div><div class="lbf"><span class="meta" id="lb-note"></span><span style="flex:1"></span><span id="lb-link"></span></div>''',
    '''<span class="glare" aria-hidden="true"></span></div><div class="lbf"><span class="meta" id="lb-note"></span><span id="lb-link" hidden></span></div></div><div class="lbinfo" id="lb-info"></div></div>''')
sub('''  $("lb-fx").classList.toggle("foil", !!c.foil);''', '''  renderInfo(c); $("lb-info").scrollTop = 0;
  $("lb-fx").classList.toggle("foil", !!c.foil);''')
sub(''': c.imgTcg ? "Image: TCGplayer" : "Image: Riot Games, via Riftcodex";''', ''': "";''')
# every card tilts toward the pointer; only foils get the shine and glare
sub('''    if (!fx.classList.contains("foil")) return;\n''', '')

INFO = r'''
// flavour: a quote with "\n— Speaker" gets quote marks and the speaker underneath; other lines show as written
function flavHTML(f){
  const i = f.lastIndexOf("\n— "), who = i >= 0 ? f.slice(i + 3) : "", q = (i >= 0 ? f.slice(0, i) : f).replace(/^["“”]+|["“”]+$/g, "");
  return `<div class="flav">${who ? "“" : ""}${esc(q).replace(/\n/g, "<br>")}${who ? "”" : ""}</div>${who ? `<div class="who">— ${esc(who)}</div>` : ""}`;
}
// ---- info sheet beside the enlarged card
let lbCard = null;
function renderInfo(c){
  lbCard = c;
  const t = txOf(c) || {text:"", fl:"", tags:[], sup:"", art:""}, n = counts[c.id] || 0;
  $("lb-sub").innerHTML = esc(c.type + (t.sup ? " · " + t.sup : "") + (c.token ? " · Token" : ""));
  const legal = (fmt, banned) => `<span class="lgl${banned ? " no" : ""}">${fmt}: ${banned ? "Banned" : "Legal"}</span>`;
  const legality = c.token || c.type === "Token" ? "" : legal("Standard", c.ban === "std") + legal("2v2", !!c.ban);
  const stat = (k, v, icon) => v == null ? "" : `<div class="st"><span class="k">${k}</span><span class="v">${icon}${esc(String(v))}</span></div>`;
  const dom = c.domains.length ? c.domains.map(d => `<span class="dot" style="background:var(--${d.toLowerCase()})"></span>${esc(d)}`).join(" ") : "Colorless";
  const stats = stat("Energy", t.e, '<span class="sym en big"></span>') + stat("Might", t.m, '<span class="sym mi">⚔</span>') + stat("Power", t.p, '<span class="sym rn' + (c.domains.length === 1 ? '" style="background:var(--' + c.domains[0].toLowerCase() + ')"' : ' any"') + '></span>');
  const kws = kwOf(c);
  const priceBox = `<div class="ibox"><div class="ih"><span>Market</span><span>TCGplayer</span></div>
      ${c.price != null ? `<div class="ip">${moneyHTML(c.price)}</div>${c.foil ? '<div class="meta">This printing only comes in foil</div>' : ""}` : '<div class="meta">No recent sales yet</div>'}
      <a class="ibuy" href="${tcgURL(c)}" target="_blank" rel="noopener">View on TCGplayer ↗</a></div>`;
  const mine = `<div class="ibox"><div class="ih"><span>My Collection</span></div>
      <div class="iown"><span>You own <b id="lb-n">${n}</b></span><div class="step" role="group" aria-label="Copies of ${esc(c.name)}"><button data-lbadj="-1" aria-label="Remove one" ${n ? "" : "disabled"}>−</button><output>${n}</output><button data-lbadj="1" aria-label="Add one">+</button></div></div>
      ${wishBtn(c)}</div>`;
  $("lb-info").innerHTML = `
    ${legality ? `<div class="lgls">${legality}</div>` : ""}
    <div class="iset"><b>${esc(codeOf(c))}</b> · <span>${esc(c.set)} – ${esc(setName[c.set] || c.set)}</span>${c.variant ? ` <span class="pill var">${esc(c.variant)}</span>` : ""}</div>
    ${stats ? `<div class="istats">${stats}</div>` : ""}
    <div class="istats three"><div class="st"><span class="k">Domain</span><span class="v sm">${dom}</span></div><div class="st"><span class="k">Type</span><span class="v sm">${esc(c.type)}</span></div><div class="st"><span class="k">Rarity</span><span class="v sm r-${c.rarity}">${esc(c.rarity)}</span></div></div>
    ${t.text ? `<div class="isec"><div class="k">Effect</div><div class="rules">${rulesHTML(t.text)}</div></div>` : (RBT.updated ? "" : `<div class="isec meta">Card text isn't loaded yet.</div>`)}
    ${t.fl ? `<div class="isec"><div class="k">Flavor</div>${flavHTML(t.fl)}</div>` : ""}
    ${kws.length ? `<div class="isec"><div class="k">Keywords</div><div class="kws">${kws.map(k => `<button class="${kwClass(k)}" data-kwf="${esc(k)}" title="Show every card with ${esc(k)}">${esc(k)}</button>`).join("")}</div></div>` : ""}
    ${t.tags.length ? `<div class="isec"><div class="k">Tags</div><div class="kws">${t.tags.map(g => `<button class="tagc" data-tgf="${esc(g)}" title="Show every card tagged ${esc(g)}">${esc(g)}</button>`).join("")}</div></div>` : ""}
    <div class="iboxes">${priceBox}${mine}</div>`;
}
document.addEventListener("click", e => {
  const b = e.target.closest("[data-lbadj]");
  if (b && lbCard){ const n = adjust(lbCard.id, Number(b.dataset.lbadj)); const box = b.closest(".iown"); box.querySelector("output").textContent = n; box.querySelector("#lb-n").textContent = n; box.querySelector('[data-lbadj="-1"]').disabled = !n; if (st.tab === "wish") renderWish(); return; }
  const k = e.target.closest("[data-kwf],[data-tgf]");
  if (k){ if (k.dataset.kwf) { st.kw = k.dataset.kwf; st.tg = ""; } else { st.tg = k.dataset.tgf; st.kw = ""; } st.q = ""; st.limit = PAGE; st.page = 0; $("lb").close(); if (st.tab !== "collection" && typeof showTab === "function") showTab("collection"); syncControls(); render(); $("list").scrollIntoView({behavior: "smooth", block: "start"}); }
});
'''
sub('''document.addEventListener("click", e => { const t = e.target.closest("button.thumb[data-img]");''',
    INFO + '''document.addEventListener("click", e => { const t = e.target.closest("button.thumb[data-img]");''')


# --- type a page number to jump straight to it
sub('<span class="meta">Page ${st.page + 1} of ${pages}</span>',
    '<label class="meta pgjump">Page <input class="pgin" type="number" min="1" max="${pages}" value="${st.page + 1}" inputmode="numeric" enterkeyhint="go" aria-label="Page number, out of ${pages}"> of ${pages}</label>')
PGJS = r"""document.querySelectorAll(".pager").forEach(p => p.addEventListener("change", e => {
  const inp = e.target.closest(".pgin"); if (!inp) return;
  const max = Number(inp.max) || 1, v = Math.round(Number(inp.value));
  if (!v){ inp.value = st.page + 1; return; }
  const pg = Math.min(max, Math.max(1, v)) - 1;
  if (pg === st.page){ inp.value = pg + 1; return; }
  st.page = pg; render();
  const top = document.querySelector(".listbar").getBoundingClientRect().top + scrollY - (document.querySelector(".filters").offsetHeight + 8);
  scrollTo({top: Math.max(0, top), behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth"});
}));
document.querySelectorAll(".pager").forEach(p => p.addEventListener("keydown", e => { if (e.key === "Enter" && e.target.closest(".pgin")) e.target.blur(); }));
document.querySelectorAll(".pager").forEach(p => p.addEventListener("focusin", e => { if (e.target.closest(".pgin")) e.target.select(); }));
"""
PGOLD = 'document.querySelectorAll(".pager").forEach(p => p.addEventListener("click", e => {'
sub(PGOLD, PGJS + PGOLD)
h = h.replace("</style>", """.pgjump{display:inline-flex;align-items:center;gap:6px}
.pgin{width:3.6em;padding:4px 6px;text-align:center;font:inherit;color:var(--fg);background:var(--bg);border:1px solid var(--line);border-radius:6px;-moz-appearance:textfield}
.pgin:focus{outline:2px solid var(--accent);outline-offset:1px}
.pgin::-webkit-outer-spin-button,.pgin::-webkit-inner-spin-button{-webkit-appearance:none;margin:0}
</style>""", 1)


# --- reset filters button
sub('<label class="chk"><input type="checkbox" id="variants" checked> Show alt arts, overnumbered and promos</label>',
    '<label class="chk"><input type="checkbox" id="variants" checked> Show alt arts, overnumbered and promos</label>\n      <button class="btn reset" id="freset" type="button" disabled>Reset filters</button>')
RSJS = r"""
// ---- reset filters: search, set, domains, banned, type, rarity, keyword, tag, All/I have/Missing, alt arts
function activeFilters(){ return (st.q ? 1 : 0) + (st.set ? 1 : 0) + st.doms.size + (st.banned ? 1 : 0) + (st.type ? 1 : 0) + (st.rarity ? 1 : 0) + (st.kw ? 1 : 0) + (st.tg ? 1 : 0) + (st.show !== "all" ? 1 : 0) + (st.variants ? 0 : 1); }
function syncReset(){ const n = activeFilters(), b = $("freset"); if (!b) return; b.disabled = !n; b.textContent = n ? `Reset filters (${n})` : "Reset filters"; }
$("freset").addEventListener("click", () => {
  Object.assign(st, {q:"", set:"", doms:new Set(), banned:false, type:"", rarity:"", kw:"", tg:"", show:"all", variants:true, limit:PAGE, page:0});
  syncControls(); render();
});
"""
sub('let qT; $("q").addEventListener("input"', RSJS + 'let qT; $("q").addEventListener("input"')
sub('$("fcount").textContent = nf ? nf : "";', '$("fcount").textContent = nf ? nf : ""; syncReset();')
h = h.replace("</style>", """.btn.reset{border-color:color-mix(in srgb,var(--fury) 45%,var(--line));color:var(--fg)}
.btn.reset:not(:disabled):hover{background:color-mix(in srgb,var(--fury) 14%,transparent)}
.btn.reset:disabled{opacity:.4;cursor:default;border-color:var(--line)}
</style>""", 1)

CSS = '''
/* card info sheet */
#lb{max-width:min(1060px,calc(100vw - 24px))}
#lb .lbbody{display:grid;grid-template-columns:auto minmax(280px,1fr);gap:18px;align-items:start}
#lb .lbleft{min-width:0}
#lb .lbimg{width:min(420px,calc(100vw - 420px),(100dvh - 130px) * 0.716)}
#lb .lbimg.land{width:min(560px,calc(100vw - 420px),(100dvh - 130px) * 1.396)}
#lb .lbinfo{min-width:0;max-height:calc(100dvh - 120px);overflow:auto;padding-right:2px;font-size:14px;line-height:1.45}
#lb .lgls{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px}
#lb .lgl{font-size:12px;font-weight:600;padding:2px 8px;border-radius:5px;color:var(--ok);border:1px solid color-mix(in srgb,var(--ok) 55%,var(--line));background:color-mix(in srgb,var(--ok) 12%,transparent)}
#lb .lgl.no{color:var(--fury);border-color:color-mix(in srgb,var(--fury) 55%,var(--line));background:color-mix(in srgb,var(--fury) 12%,transparent)}
#lb .iset{color:var(--muted);margin-bottom:10px}#lb .iset b{color:var(--fg)}#lb .iset span:not(.pill){color:var(--body)}
#lb .istats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;border-top:1px solid var(--line);padding:10px 0}
#lb .st{display:flex;flex-direction:column;gap:2px;min-width:0}
#lb .k{font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
#lb .st .v{font-family:var(--display);font-size:22px;font-weight:700;display:flex;align-items:center;gap:6px}
#lb .st .v.sm{font-size:15px;font-weight:600;flex-wrap:wrap;gap:4px}
#lb .isec{border-top:1px solid var(--line);padding:9px 0}
#lb .isec .k{margin-bottom:4px}
#lb .rules{font-size:15px;line-height:1.6}
#lb .rem{color:var(--muted)}
#lb .flav{font-style:italic;color:var(--muted)}
#lb .who{color:var(--muted);font-size:13px;margin-top:2px;text-align:right}
.kw{display:inline-block;font-family:var(--display);font-weight:700;font-size:12.5px;line-height:1.5;padding:0 7px;border-radius:4px;color:#fff;background:#4a6fb5;vertical-align:1px;border:0}
.kw.t{background:#2f9a55}.kw.d{background:#8d4bb8}
button.kw{cursor:pointer;font-size:13.5px;padding:2px 9px}button.kw:hover{filter:brightness(1.15)}
#lb .kws{display:flex;gap:6px;flex-wrap:wrap}
#lb .tagc{border:1px solid var(--line);border-radius:12px;padding:2px 10px;font-size:13px;color:var(--fg);background:var(--row);cursor:pointer}
#lb .lbleft .lbf:has(#lb-note:empty){display:none}
#lb .tagc:hover{border-color:var(--accent);color:var(--accent)}
.sym{display:inline-grid;place-items:center;vertical-align:-3px;font-style:normal}
.sym.en{width:19px;height:19px;border-radius:50%;background:#f1f1f1;color:#111;font:700 11.5px/1 var(--display)}
.sym.en.big{display:none}
.sym.mi{color:#e8c37a;font-size:15px}
.sym.ex{width:18px;height:18px;border-radius:4px;background:#3b4153;color:#fff;font-size:12px}
.sym.rn{width:13px;height:13px;border-radius:50%;border:1px solid rgb(255 255 255 / .35)}
.sym.rn.any{background:conic-gradient(var(--fury),var(--order),var(--calm),var(--mind),var(--chaos),var(--body),var(--fury))}
.sym.arr{color:var(--accent);font-size:13px;margin:0 2px}
#lb .iboxes{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:8px}
#lb .ibox{border:1px solid var(--line);border-radius:8px;padding:10px;background:var(--bg);display:flex;flex-direction:column;gap:8px}
#lb .ih{display:flex;justify-content:space-between;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
#lb .ip{font-family:var(--display);font-size:22px;font-weight:700}#lb .ip small{display:block;font-size:12px;color:var(--muted);font-weight:500}
#lb .ibuy{display:block;text-align:center;background:#e9973a;color:#1b1206;font-weight:700;border-radius:6px;padding:6px 8px;text-decoration:none}
#lb .iown{display:flex;justify-content:space-between;align-items:center;gap:8px}
#lb .ibox .wishbtn{align-self:flex-start}
@media (max-width:760px){
  #lb .lbbody{grid-template-columns:1fr}
  #lb .lbimg{width:min(360px,calc(100vw - 60px),(100dvh - 160px) * 0.716)}
  #lb .lbimg.land{width:min(520px,calc(100vw - 60px))}
  #lb .lbinfo{max-height:none;overflow:visible}
  #lb .iboxes{grid-template-columns:1fr}
}
'''
i = h.rfind("</style>")
h = h[:i] + CSS + h[i:]
open(dst, "w", encoding="utf-8").write(h)
print("patch_info: ok ->", dst)
