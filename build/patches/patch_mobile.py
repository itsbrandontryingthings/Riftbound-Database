#!/usr/bin/env python3
"""Phone-friendly layout for the versions that show card pictures (website + local copy).
- List / Grid switch (grid = card pictures, 3 across on phones; phones default to grid)
- Pages of cards with Prev / Next instead of one long "Show more" list
- On phones the sticky bar is just search + a Filters button; the rest opens on tap
- Sets become a sideways-scrolling strip on phones
- "Top" button after scrolling down
Run after patch_local.py and patch_bans.py (and patch_web/patch_accounts for the website).
Usage: patch_mobile.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:70]!r}, found {n}"
    h = h.replace(old, new)

# ---------- CSS
rep(".more{justify-self:center}", """.more{justify-self:center}
/* list bar, pager, grid tiles, filters toggle, top button */
.setbtn{min-width:0;overflow:hidden}
.setbtn .sn{min-width:0;overflow-wrap:anywhere}
.setbtn .sn small{flex:none}
.listbar{display:flex;gap:8px 12px;align-items:center;flex-wrap:wrap}
.listbar .grow{flex:1}
.pager{display:flex;gap:8px;align-items:center;justify-content:center;flex-wrap:wrap}
.pager:empty{display:none}
.pager .btn:disabled{opacity:.35;cursor:default}
.filters #count{display:none}
.ftoggle{display:none}
.fcount{display:inline-grid;place-items:center;min-width:20px;height:20px;padding:0 6px;margin-left:6px;border-radius:999px;background:var(--accent);color:var(--bg);font-size:12px;font-weight:700}
.fcount:empty{display:none}
/* card size S / M / L: columns by screen width (page sizes divide evenly by every count) */
.list.grid{--c:4;grid-template-columns:repeat(var(--c),minmax(0,1fr));gap:12px}
@media (min-width:1000px){.list.grid{--c:6}}
@media (min-width:1500px){.list.grid{--c:8}}
@media (max-width:699px){.list.grid{--c:3;gap:8px}}
.list.grid.sz-m{--c:3}
@media (min-width:1000px){.list.grid.sz-m{--c:4}}
@media (min-width:1500px){.list.grid.sz-m{--c:6}}
@media (max-width:699px){.list.grid.sz-m{--c:2}}
.list.grid.sz-l{--c:2}
@media (min-width:1000px){.list.grid.sz-l{--c:3}}
@media (min-width:1500px){.list.grid.sz-l{--c:4}}
@media (max-width:699px){.list.grid.sz-l{--c:1}}
body.gridview .wrap{max-width:none}
.sizeseg[hidden]{display:none!important}
.list.grid.sz-m .tname,.list.grid.sz-l .tname{font-size:15px}
.list.grid.sz-l .tname{font-size:16px}
.list.grid.sz-m .tile .price b,.list.grid.sz-l .tile .price b{font-size:16px}
.list.grid.sz-l .tsub{font-size:13px}
@media (min-width:700px){.tname{font-size:14px}.tsub{font-size:12px}.tile .price b{font-size:15px}.tile .price small{font-size:12px}.card.tile{padding:8px;gap:6px}}
.card.tile{display:flex;flex-direction:column;gap:5px;padding:6px;position:relative;align-items:stretch;min-width:0}
.tile .thumb{width:100%}
a.tname{color:var(--fg);text-decoration:none}
a.tname:hover,a.tname:focus-visible{text-decoration:underline;text-decoration-color:var(--accent)}
.tname{font-weight:600;font-size:13px;line-height:1.25;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:2.5em;overflow-wrap:anywhere}
.tsub{font-size:11px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tfoot{display:flex;flex-direction:column;gap:5px;margin-top:auto}
.tile .price{justify-items:start;min-width:0}
.tile .price small{font-size:11px;line-height:1.3}
.tile .price b{font-size:13.5px}
.tile .step{justify-content:space-between}
.tile .step button{width:32px;height:32px}
.tile .step output{min-width:18px;font-size:15px}
.tban{position:absolute;top:10px;left:10px;z-index:1;background:var(--fury);color:#fff;font-size:10.5px;font-weight:700;line-height:18px;padding:0 6px;border-radius:4px;letter-spacing:.02em;pointer-events:none}
.totop{position:fixed;right:16px;bottom:calc(16px + env(safe-area-inset-bottom, 0px));z-index:7;border-radius:999px;padding:10px 16px;background:var(--panel);border:1px solid var(--muted);box-shadow:0 6px 18px rgb(0 0 0 / .35)}
@media (max-width:640px){
  .ftoggle{display:inline-flex;align-items:center}
  .filters .frow:first-child .search{flex:1 1 0}
  .filters:not(.open) .showseg, .filters:not(.open) .fpanel{display:none}
  .filters.open{max-height:75vh;overflow:auto}
  .filters .frow:first-child .search{min-width:0}
  .filters.open .showseg{flex-basis:100%}
  .showseg button{flex:1}
  .top{padding:14px;gap:10px}
  .top h1{font-size:20px}
  .value-row{flex-wrap:nowrap;gap:14px}
  .value-row .vbox{flex:1 1 0;min-width:0}
  .vbig{font-size:22px}
  .vmid{font-size:18px}
  #c-updated{font-size:11.5px;line-height:1.35}
  .localnote{font-size:13px;padding:8px 10px}
  .sets{display:flex;overflow-x:auto;gap:8px;scroll-snap-type:x proximity;padding-bottom:4px}
  .setbtn{flex:0 0 150px;scroll-snap-align:start}
}""")

# ---------- markup: Filters button, collapsible panel, list bar, pager, top button
import re
h, n = re.subn(r'(<input class="search" id="q" [^>]*>)\n      <div class="seg" role="group" aria-label="Which cards to show">',
    lambda m: m.group(1) + '\n      <button class="btn ftoggle" id="ftoggle" aria-expanded="false" aria-controls="fpanel">Filters<span class="fcount" id="fcount"></span></button>\n      <div class="seg showseg" role="group" aria-label="Which cards to show">',
    h, count=1)
assert n == 1, "search row not found"
rep('''    </div>
    <div class="frow">
      <div class="dom" id="doms" role="group" aria-label="Filter by domain"></div>''',
    '''    </div>
    <div class="fpanel" id="fpanel" style="display:grid;gap:8px">
    <div class="frow">
      <div class="dom" id="doms" role="group" aria-label="Filter by domain"></div>''')
rep('''      <span class="meta" id="copied" aria-live="polite"></span>
    </div>
  </div>

  <div class="list" id="list" aria-live="polite"></div>''',
    '''      <span class="meta" id="copied" aria-live="polite"></span>
    </div>
    </div>
  </div>

  <div class="listbar"><span class="meta" id="count2"></span><span class="grow"></span><div class="seg sizeseg" id="sizeseg" role="group" aria-label="Card size"><button id="sz-s" aria-pressed="false" title="Small cards">S</button><button id="sz-m" aria-pressed="false" title="Medium cards">M</button><button id="sz-l" aria-pressed="false" title="Large cards">L</button></div><div class="seg" role="group" aria-label="Layout"><button id="v-list" aria-pressed="false">List</button><button id="v-grid" aria-pressed="false">Grid</button></div></div>
  <nav class="pager" id="pager-top" aria-label="Pages"></nav>
  <div class="list" id="list" aria-live="polite"></div>
  <nav class="pager" id="pager-bot" aria-label="Pages"></nav>
  <button class="btn totop" id="totop" hidden aria-label="Back to top">↑ Top</button>''')
# the inline display:grid on the panel would beat the phone rule; move it into CSS instead
h = h.replace('<div class="fpanel" id="fpanel" style="display:grid;gap:8px">', '<div class="fpanel" id="fpanel">')
rep(".ftoggle{display:none}", ".ftoggle{display:none}\n.fpanel{display:grid;gap:8px}")

# ---------- state: layout + page; phones start in grid
rep('let st = {set:"", q:"", show:"all", doms:new Set(), type:"", rarity:"", variants:true, sort:"set", cur:"both", limit:PAGE};',
    'let st = {set:"", q:"", show:"all", doms:new Set(), type:"", rarity:"", variants:true, sort:"set", cur:"both", limit:PAGE, view:"", page:0};')
rep('const savedF = LS.get("rb-filters"); if (savedF) { Object.assign(st, savedF, {doms:new Set(savedF.doms||[]), limit:PAGE}); }',
    'const savedF = LS.get("rb-filters"); if (savedF) { Object.assign(st, savedF, {doms:new Set(savedF.doms||[]), limit:PAGE}); }\n'
    'const PHONE = () => matchMedia("(max-width:640px)").matches;\n'
    'if (st.view !== "grid" && st.view !== "list") st.view = PHONE() ? "grid" : "list";')
# any filter change goes back to page 1
n = h.count("st.limit = PAGE;")
assert n >= 8, n
h = h.replace("st.limit = PAGE;", "st.limit = PAGE; st.page = 0;")

# ---------- grid tile + pager
rep("let shown = [];", r'''let gridCols = 0;
// if the window is resized across a column breakpoint, redo the page so rows stay full
addEventListener("resize", () => { clearTimeout(window.__rsz); window.__rsz = setTimeout(() => { if (st.view === "grid" && getComputedStyle($("list")).gridTemplateColumns.split(" ").filter(Boolean).length !== gridCols) renderList(); }, 200); });
function tileHTML(c){
  const n = counts[c.id]||0;
  return `<div class="card tile${n?" got":""}" data-id="${esc(c.id)}">
    ${thumbHTML(c, PHONE() && st.size === "s" ? 480 : 744)}${c.ban ? `<span class="tban">${c.ban === "2v2" ? "2v2 BAN" : "BANNED"}</span>` : ""}
    <a class="tname" href="${tcgURL(c)}" target="_blank" rel="noopener" title="Open ${esc(c.name)} on TCGplayer">${esc(c.name)}</a>
    <div class="tsub"><span class="r-${c.rarity}">${esc(codeOf(c))}</span>${c.variant ? ` · ${esc(c.variant)}` : ""}</div>
    <div class="tfoot">${priceHTML(c, n)}<div class="step" role="group" aria-label="Copies of ${esc(c.name)}">
      <button data-a="-1" aria-label="Remove one" ${n?"":"disabled"}>−</button><output>${n}</output><button data-a="1" aria-label="Add one">+</button>
    </div></div></div>`;
}
function renderPager(pages){
  const html = pages <= 1 ? "" : `<button class="btn" data-pg="-1" ${st.page ? "" : "disabled"}>‹ Prev</button><span class="meta">Page ${st.page + 1} of ${pages}</span><button class="btn" data-pg="1" ${st.page < pages - 1 ? "" : "disabled"}>Next ›</button>`;
  $("pager-top").innerHTML = html; $("pager-bot").innerHTML = html;
}
let shown = [];''')
rep("  const slice = shown.slice(0, st.limit);",
    '''  if (!["s","m","l"].includes(st.size)) st.size = "m";
  $("list").classList.toggle("grid", st.view === "grid"); document.body.classList.toggle("gridview", st.view === "grid");
  ["s","m","l"].forEach(z => { $("list").classList.toggle("sz-" + z, st.view === "grid" && st.size === z && z !== "s"); $("sz-" + z).setAttribute("aria-pressed", st.size === z); });
  $("sizeseg").hidden = st.view !== "grid";
  // page size always divides evenly by the column count: 8, 6 or 4 across -> 48 a page; 3 across (phones) -> 30
  const cols = st.view === "grid" ? (getComputedStyle($("list")).gridTemplateColumns.split(" ").filter(Boolean).length || 4) : 1;
  gridCols = cols;
  const PS = st.view === "grid" ? ({1:10, 2:24, 3:30}[cols] || 48) : 50;
  const pages = Math.max(1, Math.ceil(shown.length / PS)); st.page = Math.min(Math.max(0, st.page || 0), pages - 1);
  const slice = shown.slice(st.page * PS, st.page * PS + PS);''')
rep("slice.map(cardHTML).join(\"\")", "slice.map(st.view === \"grid\" ? tileHTML : cardHTML).join(\"\")")
rep("  $(\"more\").hidden = shown.length <= st.limit;", "  $(\"more\").hidden = true; renderPager(pages);")
rep("  $(\"more\").textContent = `Show ${Math.min(PAGE, shown.length - st.limit)} more`;",
    '''  $("v-list").setAttribute("aria-pressed", st.view === "list"); $("v-grid").setAttribute("aria-pressed", st.view === "grid");
  const nf = st.doms.size + (st.banned ? 1 : 0) + (st.type ? 1 : 0) + (st.rarity ? 1 : 0) + (st.show !== "all" ? 1 : 0) + (st.variants ? 0 : 1);
  $("fcount").textContent = nf ? nf : "";''')
rep('''$("more").addEventListener("click", () => { st.limit += PAGE; renderList(); });''',
    '''$("more").addEventListener("click", () => { st.limit += PAGE; renderList(); });
// count above the list mirrors the filter bar's count
new MutationObserver(() => { $("count2").textContent = $("count").textContent; }).observe($("count"), {childList:true, characterData:true, subtree:true});
["list","grid"].forEach(v => $("v-"+v).addEventListener("click", () => { if (st.view === v) return; st.view = v; st.page = 0; render(); }));
["s","m","l"].forEach(z => $("sz-"+z).addEventListener("click", () => { if (st.size === z) return; st.size = z; st.page = 0; render(); }));
document.querySelectorAll(".pager").forEach(p => p.addEventListener("click", e => {
  const b = e.target.closest("button[data-pg]"); if (!b || b.disabled) return;
  st.page += Number(b.dataset.pg); render();
  const top = document.querySelector(".listbar").getBoundingClientRect().top + scrollY - (document.querySelector(".filters").offsetHeight + 8);
  scrollTo({top: Math.max(0, top), behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth"});
}));
$("ftoggle").addEventListener("click", () => { const f = document.querySelector(".filters"); const open = !f.classList.contains("open"); f.classList.toggle("open", open); $("ftoggle").setAttribute("aria-expanded", open); });
addEventListener("scroll", () => { $("totop").hidden = scrollY < 1200; }, {passive:true});
$("totop").addEventListener("click", () => scrollTo({top:0, behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth"}));''')

open(out, "w", encoding="utf-8").write(h)
print("ok", len(h))
