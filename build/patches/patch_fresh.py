"""Fresh start on a new visit (website only, last).

The site remembers Collection filters and the open tab in localStorage (rb-filters). Opening RBDB in a new
tab / window / browser session now drops those: every filter starts cleared (the same ones Reset filters clears,
plus the Wish List list chip) and the page opens on Collection. A refresh in the same tab keeps your place
(sessionStorage rb-visit marks the tab). Display choices (list/grid, sizes, sort, currency) are kept.
Usage: patch_fresh.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

rep('const savedF = LS.get("rb-filters"); if (savedF) {',
    'const savedF = LS.get("rb-filters");\n'
    'let rbFresh = true; try { rbFresh = !sessionStorage.getItem("rb-visit"); sessionStorage.setItem("rb-visit", "1"); } catch(e){}\n'
    'if (savedF && rbFresh) for (const k of ["q","set","doms","banned","type","rarity","kw","tg","show","variants","only","page","tab","wfold"]) delete savedF[k];\n'
    'if (savedF) {')

open(out, "w", encoding="utf-8").write(h)
