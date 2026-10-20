#!/usr/bin/env python3
"""Collection filters (website and local copy; runs last in both pipelines).
- Domains: picking more than one shows only cards that have ALL of them (Calm + Order + Legend = Shen, Azir,
  Ivern, Leona…), instead of cards with any one of them. One domain works the same as before.
- Type: "Unit" is shown as "Regular Unit" (no champions), followed by "Champion Unit" (units whose supertype in
  text.js is Champion); "Spell" leaves out signature spells, which get their own "Signature Spell" choice after it.
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

# types: Regular Unit / Champion Unit, Spell / Signature Spell
rep('$("type").insertAdjacentHTML("beforeend", `<option value="__token">Token</option>`);',
    '''$("type").insertAdjacentHTML("beforeend", `<option value="__token">Token</option>`);
{ const u = $("type").querySelector('option[value="Unit"]'); if (u){ u.textContent = "Regular Unit"; u.insertAdjacentHTML("afterend", `<option value="__champ">Champion Unit</option>`); } }
{ const s = $("type").querySelector('option[value="Spell"]'); if (s) s.insertAdjacentHTML("afterend", `<option value="__sig">Signature Spell</option>`); }
const supOf = c => (txOf(c) && txOf(c).sup) || "";
const isChampUnit = c => c.type === "Unit" && supOf(c) === "Champion";
const isSigSpell = c => c.type === "Spell" && supOf(c) === "Signature";
const typeOK = c => st.type === "__token" ? !!c.token : st.type === "__champ" ? isChampUnit(c) : st.type === "__sig" ? isSigSpell(c)
  : st.type === "Unit" ? c.type === "Unit" && !isChampUnit(c) : st.type === "Spell" ? c.type === "Spell" && !isSigSpell(c) : !st.type || c.type === st.type;''')
rep('  if (st.type === "__token" ? !c.token : (st.type && c.type !== st.type)) return false;',
    '  if (!typeOK(c)) return false;')

open(out, "w", encoding="utf-8").write(h)
