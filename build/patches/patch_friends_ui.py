#!/usr/bin/env python3
"""Friends tab card lines (website; runs last, after patch_decks_ui.py).
- Each card in a friend's deck or wish list shows a small picture, and the whole line opens the enlarged preview.
- Decks say "✓ you have N" in green (N = copies in your collection, any printing) instead of "✓ you have it";
  missing cards still say "you have N" in orange (N = copies left for that line after earlier lines of the deck).
Usage: patch_friends_ui.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

# wish lists
rep('''return `<div class="frrow"><span class="q">${x.q}×</span><span>${esc(x.name)}</span>${banPill''',
    '''return `<div class="frrow"${frCardAttr(x.key)}>${frThumb(x.key)}<span class="q">${x.q}×</span><span class="frn">${esc(x.name)}</span>${banPill''')
# decks
rep('''${sec.rows.map(x => `<div class="frrow"><span class="q">${x.q}×</span><span>${esc(x.name)}</span>${banPill((groups[x.key]||[]).find(c => c.ban))}<span class="${x.miss ? "no" : "ok"}">${x.miss ? `you have ${x.h}` : "✓ you have it"}</span></div>`).join("")}''',
    '''${sec.rows.map(x => `<div class="frrow"${frCardAttr(x.key)}>${frThumb(x.key)}<span class="q">${x.q}×</span><span class="frn">${esc(x.name)}</span>${banPill((groups[x.key]||[]).find(c => c.ban))}<span class="${x.miss ? "no" : "ok"}">${x.miss ? `you have ${x.h}` : `✓ you have ${ownedOf(x.key)}`}</span></div>`).join("")}''')

# helpers + tap a line to open the card (inserted before the Friends search box handler)
rep('''let frT; $("fr-q").addEventListener("input",''',
    '''const frCard = key => cheapestOf(key) || (groups[key] || [])[0] || CARDS.find(c => norm(c.name) === key) || null;   // tokens aren't in groups
const frCardAttr = key => { const c = frCard(key); return c ? ` data-card="${esc(c.id)}" title="Show ${esc(c.name)}"` : ""; };
const frThumb = key => { const c = frCard(key); return c ? thumbHTML(c, 160) : '<span class="thumb none" aria-hidden="true">No<br>image</span>'; };
$("fr-list").addEventListener("click", e => {
  const row = e.target.closest(".frrow[data-card]"); if (!row || e.target.closest("a, button")) return;
  openCard(byId[row.dataset.card]);
});
let frT; $("fr-q").addEventListener("input",''')

# ---------- styles
_i = h.rfind("</style>"); h = h[:_i] + """.frbody{gap:4px}
.frrow{display:grid;grid-template-columns:38px 2.2em minmax(0,1fr) auto auto;gap:4px 10px;align-items:center;padding:4px 6px;border-radius:8px}
.frrow[data-card]{cursor:zoom-in}
.frrow[data-card]:hover{background:var(--row)}
.frrow .frn{overflow-wrap:anywhere}
.frrow .ok,.frrow .no{white-space:nowrap;justify-self:end}
.frrow .pill.ban{justify-self:start}
.frrow:not(:has(.pill.ban)){grid-template-columns:38px 2.2em minmax(0,1fr) auto}
@media (max-width:520px){
  .frrow,.frrow:not(:has(.pill.ban)){grid-template-columns:34px 2em minmax(0,1fr)}
  .frrow .ok,.frrow .no,.frrow .pill.ban{grid-column:3;justify-self:start}
  .frrow .thumb{grid-row:span 2;align-self:start}
  .frrow .q{align-self:start;padding-top:2px}
  .frrow .frn{align-self:end}
}
""" + h[_i:]

open(out, "w", encoding="utf-8").write(h)
print("patch_friends_ui: ok ->", out)
