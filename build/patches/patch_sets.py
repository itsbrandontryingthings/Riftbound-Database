#!/usr/bin/env python3
"""Set filter everywhere (website only, last in the pipeline).
- Wish List, My Shopping List and Friends' Shopping Lists get a "Set" menu (All sets / Vendetta / Unleashed /
  Spiritforged / Origins…) before the Domain menu: `wlf.set`, `shf.set`, `mkf.set`, cleared by Reset filters.
- Collection's Filters panel gets the same menu (`#cset`), kept in step with the set buttons at the top (`st.set`).
Sets come from RB_META.sets (newest first), only ones with cards.
Usage: patch_sets.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

SEL = '<select id="{0}-set" aria-label="Set"><option value="">All sets</option></select>'

# menus
rep('<select id="type" aria-label="Card type">', '<select id="cset" aria-label="Set"><option value="">All sets</option></select>\n      <select id="type" aria-label="Card type">')
for k in ("wlf", "shf", "mkf"):
    rep(f'<select id="{k}-dom" aria-label="Domain">', SEL.format(k) + f'\n        <select id="{k}-dom" aria-label="Domain">')

# Collection: menu follows the set buttons, and picking one works like tapping its button
rep('function render(){ renderSummary();', 'function render(){ if ($("cset")) $("cset").value = st.set || ""; renderSummary();')
rep('$("sets").addEventListener("click", e => {',
    '''const setOpts = () => META.sets.filter(s => CARDS.some(c => c.set === s.code)).map(s => `<option value="${esc(s.code)}">${esc(s.name)}</option>`).join("");
$("cset").insertAdjacentHTML("beforeend", setOpts()); $("cset").value = st.set || "";
$("cset").addEventListener("change", e => { st.set = e.target.value; st.limit = PAGE; st.page = 0; render(); });
$("sets").addEventListener("click", e => {''')

# Wish List
rep('const wlf = {q: "", dom: "",', 'const wlf = {q: "", set: "", dom: "",')
rep('!!(wlf.q || wlf.dom', '!!(wlf.q || wlf.set || wlf.dom')
rep('  return (!wlf.dom || c.domains.includes(wlf.dom))', '  return (!wlf.set || c.set === wlf.set) && (!wlf.dom || c.domains.includes(wlf.dom))')
rep('  fill("wlf-dom", uniq(', '  $("wlf-set").insertAdjacentHTML("beforeend", setOpts());\n  fill("wlf-dom", uniq(')
rep('Object.assign(wlf, {q: "", dom: "",', 'Object.assign(wlf, {q: "", set: "", dom: "",')
rep('["dom", "type", "rar"].forEach(k => $("wlf-', '["set", "dom", "type", "rar"].forEach(k => $("wlf-', 2)

# Friends' Shopping Lists
rep('const mkf = {q: "", dom: "",', 'const mkf = {q: "", set: "", dom: "",')
rep('!!(mkf.q || mkf.dom', '!!(mkf.q || mkf.set || mkf.dom')
rep('if (!c) return nm && !mkf.dom', 'if (!c) return nm && !mkf.set && !mkf.dom')
rep('return nm && rngOK(c, "f") && (!mkf.dom', 'return nm && rngOK(c, "f") && (!mkf.set || c.set === mkf.set) && (!mkf.dom')
rep('Object.assign(mkf, {q: "", dom: "",', 'Object.assign(mkf, {q: "", set: "", dom: "",')
rep('["dom", "type", "rar"].forEach(k => $("mkf-', '["set", "dom", "type", "rar"].forEach(k => $("mkf-', 2)

# My Shopping List
rep('const shf = {q: "", dom: "",', 'const shf = {q: "", set: "", dom: "",')
rep('!!(shf.q || shf.dom', '!!(shf.q || shf.set || shf.dom')
rep('return rngOK(c, "s") && (!shf.q', 'return rngOK(c, "s") && (!shf.set || c.set === shf.set) && (!shf.q')
rep('  fill("shf-dom", uniq(', '  $("shf-set").insertAdjacentHTML("beforeend", setOpts()); $("mkf-set").insertAdjacentHTML("beforeend", setOpts());\n  fill("shf-dom", uniq(')
rep('Object.assign(shf, {q: "", dom: "",', 'Object.assign(shf, {q: "", set: "", dom: "",')
rep('["dom", "type", "rar"].forEach(k => $("shf-', '["set", "dom", "type", "rar"].forEach(k => $("shf-', 2)

open(out, "w", encoding="utf-8").write(h)
