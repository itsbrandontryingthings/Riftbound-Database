#!/usr/bin/env python3
"""Special printings only (last in both pipelines).
Collection's Filters panel gets "Only alt arts, overnumbered and promos" (`#only`, `st.only`) under the existing
"Show alt arts, overnumbered and promos": it hides the regular cards (isVariant = a variant or a promo set). The two
stay in step: ticking Only ticks Show; unticking Show unticks Only. The owned/total counts and cost to complete follow
it, it counts as a filter, and Reset filters clears it.
Usage: patch_special.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

rep('<label class="chk"><input type="checkbox" id="variants" checked> Show alt arts, overnumbered and promos</label>',
    '<label class="chk"><input type="checkbox" id="variants" checked> Show alt arts, overnumbered and promos</label>\n'
    '      <label class="chk"><input type="checkbox" id="only"> Only alt arts, overnumbered and promos</label>')
rep('variants:true, sort:"set"', 'variants:true, only:false, sort:"set"')
rep('$("variants").checked = st.variants;', '$("variants").checked = st.variants; $("only").checked = !!st.only;')
rep('  if (!st.variants && isVariant(c)) return false;', '  if (!st.variants && isVariant(c)) return false;\n  if (st.only && !isVariant(c)) return false;')
rep('const pool = CARDS.filter(c => st.variants || !isVariant(c));', 'const pool = CARDS.filter(c => (st.variants || !isVariant(c)) && (!st.only || isVariant(c)));')
rep('(st.variants ? "" : " · counting standard printings only")', '(st.only ? " · counting alt arts, overnumbered and promos only" : st.variants ? "" : " · counting standard printings only")')
rep('(st.variants ? "" : " · standard printings only")', '(st.only ? " · alt arts, overnumbered and promos only" : st.variants ? "" : " · standard printings only")')
rep('(st.variants ? 0 : 1)', '(st.variants ? 0 : 1) + (st.only ? 1 : 0)', 2)
rep('show:"all", variants:true, limit:PAGE', 'show:"all", variants:true, only:false, limit:PAGE')
rep('$("variants").addEventListener("change", e => { st.variants = e.target.checked;',
    '$("only").addEventListener("change", e => { st.only = e.target.checked; if (st.only) st.variants = true; syncControls(); st.limit = PAGE; st.page = 0; render(); });\n'
    '$("variants").addEventListener("change", e => { st.variants = e.target.checked; if (!st.variants) { st.only = false; $("only").checked = false; }')

open(out, "w", encoding="utf-8").write(h)
