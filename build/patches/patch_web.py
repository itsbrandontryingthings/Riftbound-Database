#!/usr/bin/env python3
"""Turn the local copy (built from the SHARED page, so no personal decks) into the public website version
for GitHub Pages. Run after patch_local.py and patch_bans.py. Usage: patch_web.py in.html out.html"""
import sys, re

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()
assert "Shen, Eye of Twilight" not in h and "Teemo, Swift Scout" not in h, "personal decks must not be on the website"

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:70]!r}, found {n}"
    h = h.replace(old, new)

h = re.sub(r"<title>[^<]*</title>", "<title>Riftbound Database</title>", h, count=1)
h = re.sub(r'<p class="localnote">.*?</p>',
    '<p class="localnote"><b>Your collection is private.</b> Cards and decks you enter save in this browser on this device, and nobody else who opens this site can see them. To move them to another phone or computer, use <b>Back up or move your collection</b> at the bottom of the page.</p>',
    h, count=1, flags=re.S)
rep('<p class="note">🔒 This file lives only on your computer. Nobody else can see what you enter here.</p>',
    '<p class="note">🔒 Everything you enter is saved only in your own browser. Nobody else, including whoever shared this link with you, can see your cards or decks.</p>')
rep("on this local copy your counts save in this browser, so use the backup code to move them between this page and your online one.",
    "your counts save in this browser, so use the backup code to move them to another device.")
rep('</div>\n\n<script src="cards.js"></script>',
    '''  <p class="note">Riftbound Database is a free fan project. It isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games and all associated properties are trademarks or registered trademarks of Riot Games, Inc. Card data from <a href="https://riftcodex.com" target="_blank" rel="noopener">Riftcodex</a>; prices from TCGplayer.</p>
</div>

<script src="cards.js"></script>''')
open(out, "w", encoding="utf-8").write(h)
print("ok", len(h))
