#!/usr/bin/env python3
"""My Decks: sort the cards in each section (website; runs last, after patch_art.py).
- A Sort menu in the deck toolbar: Set order (default: like Collection, newest set first then card number, by the
  printing shown on the card), Deck list order (as pasted), Name A-Z, Energy low to high, Price high to low.
  Sorts within each section (Legend, Main deck, Sideboard...), only on screen: the decklist text isn't changed.
  Saved as st.dsort ("" = set order).
Usage: patch_deck_sort.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

rep('''      <label class="chk"><input type="checkbox" id="dk-side" ${withSide?"checked":""}> Include sideboard</label>
    </div>`;''', '''      <select id="dk-sort" aria-label="Sort the cards in each section">${[["", "Sort: set order"], ["list", "Sort: deck list order"], ["name", "Sort: name A–Z"], ["energy", "Sort: energy, low to high"], ["price", "Sort: price, high to low"]].map(([v, t]) => `<option value="${v}" ${(st.dsort || "") === v ? "selected" : ""}>${t}</option>`).join("")}</select>
      <label class="chk"><input type="checkbox" id="dk-side" ${withSide?"checked":""}> Include sideboard</label>
    </div>`;''')
rep('${rows.map(r => dkRowHTML(r, view, size)).join("")}', '${dkSortRows(rows).map(r => dkRowHTML(r, view, size)).join("")}')
rep('function saveDeckView(){', r'''// sort a deck section's cards for display (the decklist itself keeps its order)
function dkSortRows(rows){
  const by = st.dsort || "", ix = r => r.show ? CARDS.indexOf(r.show) : 1e9, en = r => { const t = r.show && txOf(r.show); return t && typeof t.e === "number" ? t.e : 99; };
  if (by === "list") return rows;
  const out = rows.slice();
  if (by === "name") out.sort((a, b) => (a.show ? a.show.name : a.name).localeCompare(b.show ? b.show.name : b.name));
  else if (by === "energy") out.sort((a, b) => en(a) - en(b) || ix(a) - ix(b));
  else if (by === "price") out.sort((a, b) => (b.cheap ? b.cheap.price : -1) - (a.cheap ? a.cheap.price : -1) || ix(a) - ix(b));
  else out.sort((a, b) => ix(a) - ix(b));
  return out;
}
$("deck-body").addEventListener("change", e => { if (e.target.id === "dk-sort"){ st.dsort = e.target.value; saveDeckView(); } });
function saveDeckView(){''')

_i = h.rfind("</style>"); h = h[:_i] + """#dk-sort{background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:8px 10px;color:var(--fg)}
""" + h[_i:]

open(out, "w", encoding="utf-8").write(h)
print("patch_deck_sort: ok ->", out)
