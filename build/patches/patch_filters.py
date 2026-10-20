#!/usr/bin/env python3
"""Collection filters (website and local copy; runs last in both pipelines).
- Domains: picking more than one shows only cards that have ALL of them (Calm + Order + Legend = Shen, Azir,
  Ivern, Leona…), instead of cards with any one of them. One domain works the same as before.
- Type: a "Champion Unit" choice right after "Unit" (units whose supertype in text.js is Champion).
Usage: patch_filters.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

# domains: every picked domain must be on the card
rep('  if (st.doms.size && !c.domains.some(d => st.doms.has(d))) return false;',
    '  if (st.doms.size && ![...st.doms].every(d => c.domains.includes(d))) return false;')

# type: Champion Unit
rep('$("type").insertAdjacentHTML("beforeend", `<option value="__token">Token</option>`);',
    '$("type").insertAdjacentHTML("beforeend", `<option value="__token">Token</option>`);\n'
    '{ const u = $("type").querySelector(\'option[value="Unit"]\'); if (u) u.insertAdjacentHTML("afterend", `<option value="__champ">Champion Unit</option>`); }\n'
    'const isChampUnit = c => c.type === "Unit" && !!txOf(c) && txOf(c).sup === "Champion";')
rep('  if (st.type === "__token" ? !c.token : (st.type && c.type !== st.type)) return false;',
    '  if (st.type === "__token" ? !c.token : st.type === "__champ" ? !isChampUnit(c) : (st.type && c.type !== st.type)) return false;')

open(out, "w", encoding="utf-8").write(h)
