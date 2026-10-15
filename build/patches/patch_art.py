#!/usr/bin/env python3
"""Riftbound art banners at the top and bottom of the page (website; runs last, after patch_sliders.py).
- Top: a strip of card artwork (zoomed into the art, so the card frames and text don't show) that fades into the
  page; the header panel sits slightly over its lower edge. Bottom: a second strip with other champions after the
  last note, fading upward. Both are decoration only (aria-hidden), load from Riot's image server like the cards,
  and show fewer pieces on a phone. The bottom one loads lazily. Kept cheap to draw while scrolling: no blur, masks
  or filters (they made the page laggy on real screens); the fades are plain gradients on top; each strip is its own
  layer (contain:strict + translateZ) and the bottom one is skipped while off-screen (content-visibility:auto).
Usage: patch_art.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

IMG = "https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/{}?accountingTag=RB&w=420&fm=webp&q=85"
TOP = [  # (file, champion) - Signature / showcase art
    ("30bed82f66ce9e4eae260d029d92c9d8cb1588ab-1488x2078.png", "Jinx"),
    ("e5fe571a8f09c0a9e76345ec32b446480f54617c-1488x2078.png", "Ahri"),
    ("6a06599a299b15175984c1e38d27a3be21258fbe-1488x2078.png", "Yasuo"),
    ("8c234c7efc30a24dc50c4b76517857bff6e1f906-744x1039.png", "Shen"),
    ("ae8e68af43400f61f7391c0a6ee339fd718a7540-1488x2078.png", "Kai'Sa"),
    ("b4dfd543b1cfcdefba4568fe78146e0d6e46add7-1488x2078.png", "Lee Sin"),
    ("4fd9e82cbd96010e2556430970d433022b541a51-1488x2078.png", "Teemo"),
    ("e345a5fc347e6a5835f2afa33492058fdbfcb169-744x1039.png", "Viktor"),
]
BOTTOM = [  # other printings, so the two strips don't repeat
    ("dc89c6a2415debd5bf504ed46843f5dcc1d9b815-1488x2078.png", "Ahri"),
    ("f57c14381b126e9f5a7b5bc4913151cb24c14fc3-744x1039.png", "Jinx"),
    ("2c804ec513085702763a9145fac93a8adb6c4783-1488x2078.png", "Yasuo"),
    ("a576472c7bb00f475882ac814e1d8f9be233b402-744x1040.png", "Kai'Sa"),
    ("ffe064e002d3b9a366748eb85102a769b2545835-744x1039.png", "Lee Sin"),
    ("9723181e3392bb61c2aabc804a44f7b0558cedf1-744x1039.png", "Teemo"),
    ("913236dabf1e4f71650bbba46870fff8163e2eff-744x1039.png", "Viktor"),
    ("e7185deb46f17770802d06aeddfe3b929afff880-744x1039.png", "Garen"),
]

def strip(cards, cls, lazy):
    tiles = "".join(f'<span class="art-t"><img src="{IMG.format(f)}" alt="" width="420" height="586" referrerpolicy="no-referrer" decoding="async"{" loading=\"lazy\"" if lazy else ""}></span>' for f, _ in cards)
    return f'<div class="art-band {cls}" aria-hidden="true">{tiles}</div>'

rep('<div class="wrap" id="app">', '<div class="wrap" id="app">\n  ' + strip(TOP, "art-top", False))
# the bottom strip goes after the last note, just before the page's closing </div>
i = h.index('<p class="note">Riftbound Database is a free fan project.')
j = h.index('</p>\n</div>', i) + len('</p>\n')
h = h[:j] + '  ' + strip(BOTTOM, "art-bottom", True) + '\n' + h[j:]

_i = h.rfind("</style>"); h = h[:_i] + """.art-band{position:relative;display:flex;gap:4px;height:200px;border-radius:14px;overflow:hidden;pointer-events:none;contain:strict;transform:translateZ(0)}
/* side fades: plain gradients drawn on top (much cheaper while scrolling than a mask) */
.art-band::before{content:"";position:absolute;inset:0;z-index:1;pointer-events:none;background:linear-gradient(90deg,var(--bg) 0,transparent 7%,transparent 93%,var(--bg) 100%)}
.art-t{flex:1 1 0;min-width:96px;overflow:hidden;position:relative;background:var(--panel)}
.art-t img{position:absolute;left:50%;top:50%;width:215%;max-width:none;height:auto;transform:translate(-50%,-31%)}
.art-band::after{content:"";position:absolute;inset:0;z-index:1;pointer-events:none}
.art-top::after{background:linear-gradient(180deg,rgb(19 21 28 / .05) 0%,rgb(19 21 28 / .25) 55%,var(--bg) 100%)}
.art-top + .top{margin-top:-58px;position:relative;z-index:1}
.art-bottom{margin-top:6px;height:160px;content-visibility:auto;contain-intrinsic-size:auto 160px}
.art-bottom::after{background:linear-gradient(0deg,rgb(19 21 28 / .1) 0%,rgb(19 21 28 / .3) 45%,var(--bg) 100%)}
@media (max-width:640px){
  .art-band{height:120px;gap:3px}
  .art-t{min-width:78px}
  .art-top + .top{margin-top:-34px}
  .art-bottom{height:104px;contain-intrinsic-size:auto 104px}
}
""" + h[_i:]

open(out, "w", encoding="utf-8").write(h)
print("patch_art: ok ->", out)
