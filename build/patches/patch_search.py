"""Forgiving search (last in both pipelines).

Every search box matches the same way (`hasWords`): each word typed, or the start of one, appears somewhere in the card
(or list) name, in any order, ignoring capitals, accents, dashes, commas and apostrophes. "azir sovereign", "azir sov"
and "sovereign azir" all find "Azir - Sovereign"; "kaisa" finds "Kai'Sa". Before, Collection's and the Wish List's
filters needed the exact text (dash included), and the add-a-card boxes tripped on apostrophes.
Boxes: Collection and Wish List filters (name, code, rules text, tags), Open Packs, Wish List / Marketplace / offer
Add a Card, My Shopping List and Friends' Shopping Lists filters, Friends search, and My Decks' Add a Card, whose
suggestion list also lists the plain name (option label) and which takes a partly typed name when it fits one card.
Usage: patch_search.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1, need=True):
    global h
    n = h.count(old)
    if not need and n == 0: return
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

rep('''const norm = s => String(s).toLowerCase().replace(/[’`]/g,"'").replace(/\\s*[-,–—]\\s*/g," ").replace(/[!.]/g,"").replace(/\\s+/g," ").trim();''',
    '''const norm = s => String(s).toLowerCase().replace(/[’`]/g,"'").replace(/\\s*[-,–—]\\s*/g," ").replace(/[!.]/g,"").replace(/\\s+/g," ").trim();
// forgiving search: every word typed (or the start of one) appears somewhere, in any order, ignoring capitals, accents,
// dashes, commas and apostrophes ("azir sov" finds "Azir - Sovereign", "kaisa" finds "Kai'Sa")
const fz = s => String(s || "").toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g, "").replace(/['’`]/g, "").replace(/[^a-z0-9]+/g, " ").trim();
function hasWords(hay, q){
  const ws = fz(q).split(" ").filter(Boolean); if (!ws.length) return true;
  const t = fz(hay), joined = t.replace(/ /g, "");
  return ws.every(w => t.includes(w) || joined.includes(w));
}''')

# Collection and Wish List filters: name, card code, rules text and tags
rep('''  if (st.q){ const q = st.q.toLowerCase(); if (!(c.name.toLowerCase().includes(q) || c.id.includes(q) || findOf(c).includes(q))) return false; }''',
    '''  if (st.q && !hasWords(c.name + " " + c.id + " " + findOf(c), st.q)) return false;''')
rep('''  if (wlf.q){ const q = wlf.q.toLowerCase(); if (!(c.name.toLowerCase().includes(q) || c.id.includes(q) || findOf(c).includes(q))) return false; }''',
    '''  if (wlf.q && !hasWords(c.name + " " + c.id + " " + findOf(c), wlf.q)) return false;''', need=False)

# add-a-card suggestion boxes (Open Packs, Wish List, offers, Marketplace)
n = h.count('words.every(w => norm(c.name).includes(w))')
assert n >= 1, "no add-a-card boxes found"
h = h.replace('words.every(w => norm(c.name).includes(w))', 'hasWords(c.name, words.join(" "))')

# Marketplace filters and Friends search
rep('''nm = nameHit || !mkf.q || norm(x.name).includes(norm(mkf.q));''', '''nm = nameHit || !mkf.q || hasWords(x.name, mkf.q);''', need=False)
rep('''(!shf.q || norm(x.name).includes(norm(shf.q)))''', '''(!shf.q || hasWords(x.name, shf.q))''', need=False)
rep('''const nameHit = shop && !!mkf.q && norm(r.name + " " + (r.owner_name || "")).includes(norm(mkf.q));''',
    '''const nameHit = shop && !!mkf.q && hasWords(r.name + " " + (r.owner_name || ""), mkf.q);''', need=False)
rep('''    const hits = words.length ? rows.filter(x => words.every(w => x.key.includes(w))) : [];
    const ok = !words.length || words.every(w => hay.includes(w));''',
    '''    const hits = words.length ? rows.filter(x => hasWords(x.key, q)) : [];
    const ok = !words.length || hasWords(hay, q);''', need=False)

# My Decks' Add a Card: the browser's suggestion list also matches the plain name, and a partly typed name works
rep('''`<option value="${esc(g[0].name)}">`''', '''`<option value="${esc(g[0].name)}" label="${esc(fz(g[0].name))}">`''', need=False)
rep('''  const name = $("dk-addn").value.trim(), key = norm(name), q = Math.max''',
    '''  const name = $("dk-addn").value.trim(), key = dkFind(name), q = Math.max''', need=False)
rep('''function editableDeck(''', '''// the card a typed name means: exact, else the one card whose name has those words (the shortest name when several do)
function dkFind(name){
  const key = norm(name); if (groups[key] || !name) return key;
  const hits = Object.keys(groups).filter(k => hasWords(groups[k][0].name, name)).sort((a, b) => a.length - b.length);
  return hits.length && (hits.length === 1 || fz(groups[hits[0]][0].name).startsWith(fz(name))) ? hits[0] : key;
}
function editableDeck(''', need=False)

open(out, "w", encoding="utf-8").write(h)
