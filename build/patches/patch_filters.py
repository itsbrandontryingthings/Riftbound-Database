#!/usr/bin/env python3
"""Collection filters (website and local copy; runs last in both pipelines).
- Domains: picking more than one shows only cards that have ALL of them (Calm + Order + Legend = Shen, Azir,
  Ivern, Leona…), instead of cards with any one of them. One domain works the same as before.
- Type: "Unit" is shown as "Regular Unit" (no champion or signature units), followed by "Champion Unit" and
  "Signature Unit" (supertype in text.js); "Spell" and "Gear" leave out signature cards, which get their own
  "Signature Spell" / "Signature Gear" choice right after them.
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

# types: Regular / Champion / Signature Unit, Spell / Signature Spell, Gear / Signature Gear
rep('$("type").insertAdjacentHTML("beforeend", `<option value="__token">Token</option>`);',
    '''$("type").insertAdjacentHTML("beforeend", `<option value="__token">Token</option>`);
const TYPE_SUB = {__champ: ["Unit", "Champion", "Champion Unit"], __sigunit: ["Unit", "Signature", "Signature Unit"],
  __sig: ["Spell", "Signature", "Signature Spell"], __siggear: ["Gear", "Signature", "Signature Gear"]};
Object.entries(TYPE_SUB).reverse().forEach(([v, [t, , label]]) => { const o = $("type").querySelector(`option[value="${t}"]`); if (o) o.insertAdjacentHTML("afterend", `<option value="${v}">${label}</option>`); });
{ const u = $("type").querySelector('option[value="Unit"]'); if (u) u.textContent = "Regular Unit"; }
const supOf = c => (txOf(c) && txOf(c).sup) || "";
const subOf = c => Object.keys(TYPE_SUB).find(v => TYPE_SUB[v][0] === c.type && TYPE_SUB[v][1] === supOf(c)) || "";
const typeOK = c => st.type === "__token" ? !!c.token : TYPE_SUB[st.type] ? subOf(c) === st.type : !st.type || (c.type === st.type && !subOf(c));''')
rep('  if (st.type === "__token" ? !c.token : (st.type && c.type !== st.type)) return false;',
    '  if (!typeOK(c)) return false;')

open(out, "w", encoding="utf-8").write(h)
