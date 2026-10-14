#!/usr/bin/env python3
"""Small fixes (website; runs last, after patch_friends_size.py).
- Friends: Show list / Hide list / Remove from Friends / Copy to my decks stopped working after any save to your
  account while the Friends tab was showing (opening another link, wanting a card...): the save clears the cached
  shared lists (frCache = null) so they reload next time, but the buttons looked the list up in that cache and found
  nothing until a page refresh. They now use the lists currently on screen (frLast) when the cache is empty.
Usage: patch_fixes.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

rep('''let shareTimer = null, frCache = null, frLoadedAt = 0, frOpen = new Set();''',
    '''let shareTimer = null, frCache = null, frLoadedAt = 0, frOpen = new Set(), frLast = [];   // frLast: the lists on screen''')
rep('''frCache = (data || []).sort((a, b) => tokens.indexOf(a.share_token) - tokens.indexOf(b.share_token)); frLoadedAt = Date.now();''',
    '''frCache = (data || []).sort((a, b) => tokens.indexOf(a.share_token) - tokens.indexOf(b.share_token)); frLoadedAt = Date.now(); frLast = frCache;''')
rep('''r = (frCache || []).find(x => x.id === id); if (!r) return;''', '''r = (frCache || frLast).find(x => x.id === id); if (!r) return;''')
rep('''frCache = frCache.filter(x => x !== r);''', '''frCache = (frCache || frLast).filter(x => x !== r); frLast = frCache;''')

open(out, "w", encoding="utf-8").write(h)
print("patch_fixes: ok ->", out)
