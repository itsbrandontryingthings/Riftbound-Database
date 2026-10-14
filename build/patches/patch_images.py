#!/usr/bin/env python3
"""Add a "Card image" link (official image, opens in a new tab) to each card row of the Riftbound tracker.
Artifact pages can't load images from outside hosts, so the image opens in its own tab instead of inline.
Usage: patch_images.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:70]!r}, found {n}"
    h = h.replace(old, new)

# style: same chip as "View card", in a neutral tone
rep(".view:hover{background:color-mix(in srgb,var(--accent) 14%,transparent)}",
    ".view:hover{background:color-mix(in srgb,var(--accent) 14%,transparent)}\n.view.img{color:var(--fg);border-color:var(--line)}\n.view.img:hover{background:var(--row);border-color:var(--muted)}\n.view.img.base{color:var(--warn)}")

# helper next to viewLink
rep("function viewLink(c, label){", r'''// card image: Riftcodex image (Riot CDN), else TCGplayer's product photo; opens in a new tab
const RC_IMG = "https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/";
function imgURL(c){
  if (!c) return "";
  if (c.img) return `${RC_IMG}${c.img}?accountingTag=RB`;
  if (c.imgTcg && c.tcg) return `https://tcgplayer-cdn.tcgplayer.com/product/${c.tcg}_in_1000x1000.jpg`;
  return "";
}
function imgLink(c, label){
  const u = imgURL(c); if (!u) return "";
  return c.imgBase
    ? `<a class="view img base" href="${u}" target="_blank" rel="noopener" title="No image of this exact printing yet; this is the regular printing's art" aria-label="Open the regular printing's art for ${esc(label || c.name)}">Base art ↗</a>`
    : `<a class="view img" href="${u}" target="_blank" rel="noopener" aria-label="Open the card image for ${esc(label || c.name)}">Card image ↗</a>`;
}
function viewLink(c, label){''')

# collection row
rep('''${c.variant?`<span class="pill var">${esc(c.variant)}</span>`:""}${viewLink(c)}</span></div>''',
    '''${c.variant?`<span class="pill var">${esc(c.variant)}</span>`:""}${imgLink(c)}${viewLink(c)}</span></div>''')
# pack log
rep('''${c.variant?`<span class="pill var">${esc(c.variant)}</span>`:""}${viewLink(c)}</span></span>''',
    '''${c.variant?`<span class="pill var">${esc(c.variant)}</span>`:""}${imgLink(c)}${viewLink(c)}</span></span>''')
# deck rows
rep('''<span class="sub">${viewLink(r.cheap || (groups[r.key]||[])[0], r.name)}</span>''',
    '''<span class="sub">${imgLink(r.cheap || (groups[r.key]||[])[0], r.name)}${viewLink(r.cheap || (groups[r.key]||[])[0], r.name)}</span>''')

rep("Each card name opens its TCGplayer page.</p>",
    "Each card name opens its TCGplayer page. <b>Card image</b> opens the official card image (via the Riftcodex card database) in a new tab; a few promo printings Riftcodex doesn't list use TCGplayer's photo, or the regular printing's art, marked <b>Base art</b>.</p>")

open(out, "w", encoding="utf-8").write(h)
print("ok", len(h))
