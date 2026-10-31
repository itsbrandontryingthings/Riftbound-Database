"""Price changes in the lists (website only, after patch_prices).

- Every list price (Collection list and grid, Wish List) gets a small change chip under it: "↑ 12% · 7d" in green,
  "↓ 70% · 7d" in red (the 7-day change from prices.js, else the 30-day one; `chgChip`).
- Collection's Filters panel gets a "Price change" menu (`#pchg`, `st.pchg`): Going up / Going down over 7 or 30 days.
  It keeps cards worth US $0.50 or more (a few cents' change looks huge on cheaper cards) and switches the sort to the
  biggest change first. Options for a period show only once prices.js has changes for it (30-day ones from ~Nov 29).
  It counts as a filter and Reset filters clears it.
- Sort menu: "biggest gains" / "biggest drops" for 7 and 30 days (cards without a change go last).
Usage: patch_trends.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

rep('.price .na{color:var(--muted);font-size:13px}', '''.price .na{color:var(--muted);font-size:13px}
.price small.pchg{font-weight:600;white-space:nowrap}
.price small.pchg.up{color:var(--ok)}
.price small.pchg.dn{color:#ef6b6b}
#pchg-note:empty{display:none}''')

# the chip under each list price
rep('''  return `<span class="price" title="TCGplayer market price${c.foil ? " (this printing only comes in foil)" : ""}"><b>${esc(one)}</b>${lines.map(l => `<small>${esc(l)}</small>`).join("")}</span>`;''',
    '''  return `<span class="price" title="TCGplayer market price${c.foil ? " (this printing only comes in foil)" : ""}"><b>${esc(one)}</b>${lines.map(l => `<small>${esc(l)}</small>`).join("")}${chgChip(c)}</span>`;''')
rep('function priceHTML(c, n){', '''// market price change: 7 days, else 30 days (prices.js)
const chgOf = (c, days) => c.px ? c.px[days === 30 ? 5 : 4] ?? null : null;
function chgChip(c){
  const d7 = chgOf(c, 7), v = d7 ?? chgOf(c, 30); if (v == null) return "";
  const per = d7 != null ? "7d" : "30d";
  return `<small class="pchg${v > 0 ? " up" : v < 0 ? " dn" : ""}" title="Market price change over the last ${d7 != null ? "7" : "30"} days">${v > 0 ? "↑" : v < 0 ? "↓" : "→"} ${Math.abs(v)}% · ${per}</small>`;
}
function priceHTML(c, n){''')

# the filter
rep('''      <select id="cset" aria-label="Set"><option value="">All sets</option></select>''',
    '''      <select id="cset" aria-label="Set"><option value="">All sets</option></select>
      <select id="pchg" aria-label="Price change"><option value="">Any price change</option><option value="up7">Price going up · 7 days</option><option value="dn7">Price going down · 7 days</option><option value="up30">Price going up · 30 days</option><option value="dn30">Price going down · 30 days</option></select>''')
rep('variants:true, only:false, sort:"set"', 'variants:true, only:false, pchg:"", sort:"set"')
rep('$("only").checked = !!st.only; $("sort").value = st.sort || "set";',
    '$("only").checked = !!st.only; $("pchg").value = st.pchg || ""; $("sort").value = st.sort || "set"; $("pchg-note").textContent = st.pchg ? "Cards worth US $0.50 or more, biggest change first." : "";')
rep('  if (st.only && !isVariant(c)) return false;', '''  if (st.only && !isVariant(c)) return false;
  if (st.pchg){ const v = chgOf(c, st.pchg.endsWith("30") ? 30 : 7); if (v == null || (c.price ?? 0) < 0.5 || (st.pchg.startsWith("up") ? v <= 0 : v >= 0)) return false; }''')
rep('(st.variants ? 0 : 1) + (st.only ? 1 : 0)', '(st.variants ? 0 : 1) + (st.only ? 1 : 0) + (st.pchg ? 1 : 0)', 2)
rep('show:"all", variants:true, only:false, limit:PAGE', 'show:"all", variants:true, only:false, pchg:"", sort: /^(gain|drop)/.test(st.sort || "") ? "set" : st.sort, limit:PAGE')
rep('''$("cset").addEventListener("change", e => { st.set = e.target.value; st.limit = PAGE; st.page = 0; render(); });''',
    '''$("cset").addEventListener("change", e => { st.set = e.target.value; st.limit = PAGE; st.page = 0; render(); });
// picking gains / drops also sorts by the biggest change; a period's options show once prices.js has changes for it
$("pchg").addEventListener("change", e => {
  st.pchg = e.target.value;
  if (st.pchg) st.sort = (st.pchg.startsWith("up") ? "gain" : "drop") + (st.pchg.endsWith("30") ? "30" : "7");
  else if (/^(gain|drop)/.test(st.sort || "")) st.sort = "set";
  st.limit = PAGE; st.page = 0; syncControls(); render();
});
for (const days of [7, 30]){
  const has = CARDS.some(c => chgOf(c, days) != null);
  document.querySelectorAll(`#pchg option[value$="${days}"], #sort option[value$="${days}"]`).forEach(o => o.hidden = !has);
}
if (!CARDS.some(c => chgOf(c, 7) != null || chgOf(c, 30) != null)) $("pchg").hidden = true;''')
rep('<label class="chk"><input type="checkbox" id="only"> Only alt arts, overnumbered and promos</label>',
    '<label class="chk"><input type="checkbox" id="only"> Only alt arts, overnumbered and promos</label>\n      <span class="meta" id="pchg-note" aria-live="polite"></span>')

# the sort
rep('<option value="name">Sort: name</option></select>',
    '<option value="name">Sort: name</option><option value="gain7">Sort: biggest gains · 7 days</option><option value="drop7">Sort: biggest drops · 7 days</option><option value="gain30">Sort: biggest gains · 30 days</option><option value="drop30">Sort: biggest drops · 30 days</option></select>')
rep('''  else if (st.sort === "name") shown.sort((a,b) => a.name.localeCompare(b.name));''',
    '''  else if (st.sort === "name") shown.sort((a,b) => a.name.localeCompare(b.name));
  else if (/^(gain|drop)(7|30)$/.test(st.sort || "")){
    const days = st.sort.endsWith("30") ? 30 : 7, up = st.sort.startsWith("gain"), key = c => { const v = chgOf(c, days); return v == null ? -Infinity : up ? v : -v; };
    shown.sort((a,b) => key(b) - key(a) || (b.price ?? -1) - (a.price ?? -1));
  }''')

open(out, "w", encoding="utf-8").write(h)
