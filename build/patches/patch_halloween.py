#!/usr/bin/env python3
"""Autumn / Halloween look (website; runs last, after patch_filters.py). Switches itself on and off by date:
- Autumn (Sep 22 - Nov 30, html.fall): pumpkin-orange accent colour and a warm orange glow over the top art strip
  and around the header panel.
- Halloween (Oct 1 - Nov 1, html.spooky, on top of autumn), with Teemo as the host: a garland of pumpkins, leaves
  and Teemo's mushrooms hanging off the header, a pumpkin after the page title, a "Happy Halloween" note from
  Teemo (his face in a round frame with a little witch hat), bats flying over the top art strip, and the
  bottom art strip becomes all Teemo cards with a pumpkin-and-mushroom patch along it.
Decoration only (aria-hidden, pointer-events:none). Cheap to draw: emoji moved with transform/opacity animations
only, no filters; nothing moves for people who ask for reduced motion. The Teemo strip's pictures load lazily and
only when it's shown. Try it any time of year with ?season=halloween or ?season=fall in the address
(?season=off turns it off).
Usage: patch_halloween.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

IMG = "https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/{}?accountingTag=RB&w=420&fm=webp&q=85"
TEEMO = [  # every Teemo printing's art, plus his Mushroom Pouch
    "4fd9e82cbd96010e2556430970d433022b541a51-1488x2078.png",  # Swift Scout, Signature
    "5e31f0ea037604aa531d84c1d56d26f255210b7c-744x1039.png",   # Strategist, Signature
    "ca8a2e11dd78dd09ad1c9ad3a23e5699254b947e-744x1039.png",   # Scout
    "ef5b3125fda91c0d0a02b7e6dfb7d3d5bafa8bd0-744x1039.png",   # Mushroom Pouch
    "0709ab02b75d9acc8f3c4037ec3a4140323150d8-744x1039.png",   # Strategist, Alternate Art
    "e2fbf10efaddbabe9241bd2c7b4d059accd1d5a7-1488x2078.png",  # Swift Scout, Overnumbered
    "404a8aa0061b58611bd913b58dd01d99fdb8087d-744x1039.png",   # Scout, Alternate Art
    "7f0962b840d228ad551fb9334fe9bdf76d209e7d-744x1039.png",   # Strategist, Overnumbered
]
FACE = IMG.format(TEEMO[0]).replace("w=420", "w=300")
GARLAND = "🍂🎃🍄🦇🍁🎃🍄🕸🍂🎃🍄🦇🍁🎃🍂"
BATS = '<span class="hw-bat" style="--y:18%;--d:0s;--w:14s">🦇</span><span class="hw-bat" style="--y:42%;--d:5s;--w:17s">🦇</span><span class="hw-bat" style="--y:28%;--d:10s;--w:12s">🦇</span>'
PATCH = "🎃🍄🎃🍂🍄🎃🍄🍁🎃🍄🍂🎃🍄🎃🍄"

# season switch: runs before the page is drawn, so there's no flash of the plain look
rep('<div class="wrap" id="app">', '''<script>(() => {
  const q = new URLSearchParams(location.search).get("season"), d = new Date(), md = (d.getMonth() + 1) * 100 + d.getDate();
  const fall = q ? q !== "off" : md >= 922 && md <= 1130, spooky = q ? q === "halloween" : md >= 1001 && md <= 1101;
  document.documentElement.classList.toggle("fall", fall); document.documentElement.classList.toggle("spooky", spooky);
})();</script>
<div class="wrap" id="app">''')
rep('<div class="art-band art-top" aria-hidden="true">', '<div class="art-band art-top" aria-hidden="true">' + BATS)
# Halloween: a Teemo strip takes the bottom strip's place
i = h.index('<div class="art-band art-bottom" aria-hidden="true">')
tiles = "".join(f'<span class="art-t"><img src="{IMG.format(f)}" alt="" width="420" height="586" referrerpolicy="no-referrer" decoding="async" loading="lazy"></span>' for f in TEEMO)
h = h[:i] + ('<div class="art-band art-bottom hw-teemo" aria-hidden="true"><span class="hw-patch">'
             + "".join(f"<span>{e}</span>" for e in PATCH) + '</span>' + tiles + '</div>\n  ') + h[i:]
rep('  <div class="top">\n', '  <div class="top">\n    <div class="hw-garland" aria-hidden="true">' + "".join(f"<span>{e}</span>" for e in GARLAND) + '</div>\n')
rep('<span>Riftbound Database</span></h1>', '''<span>Riftbound Database</span><span class="hw-pk" aria-hidden="true">🎃</span></h1>
    <div class="hw-hi" aria-hidden="true"><span class="hw-face"><span class="hw-ring"><img src="''' + FACE + '''" alt="" referrerpolicy="no-referrer" decoding="async" loading="lazy"></span><svg class="hw-hat" viewBox="0 0 40 34"><path d="M21 1C15 6 11 16 9 25h22C28 17 26 8 33 4c-4-1-9-2-12-3z" fill="#5b2a86"/><path d="M10 21h21v4H10z" fill="#ec8a3c"/><ellipse cx="20" cy="27" rx="19" ry="4.5" fill="#43206a"/></svg></span><span class="hw-bubble"><b>Happy Halloween from Captain Teemo!</b> Mind the mushrooms while you hunt for treats in the packs <span class="hw-shroom">🍄</span></span></div>''')

_i = h.rfind("</style>"); h = h[:_i] + """/* autumn / Halloween (patch_halloween) */
.hw-bat,.hw-garland,.hw-pk,.hw-hi,.hw-teemo{display:none}
html.fall{--accent:#ec8a3c}
html.fall .art-top::after{background:linear-gradient(180deg,rgb(120 50 10 / .22) 0%,rgb(40 18 10 / .35) 55%,var(--bg) 100%)}
html.fall .top{border-color:color-mix(in srgb,#ec8a3c 35%,var(--line));box-shadow:0 0 0 1px rgb(236 138 60 / .08),0 10px 30px -12px rgb(236 138 60 / .35)}
html.spooky .top{position:relative}
html.spooky .hw-garland{display:flex;justify-content:space-between;position:absolute;left:14px;right:14px;top:-15px;z-index:2;pointer-events:none;font-size:22px;line-height:1}
html.spooky .hw-garland::before{content:"";position:absolute;left:0;right:0;top:4px;height:10px;border-bottom:1.5px solid rgb(236 138 60 / .45);border-radius:0 0 50% 50%;z-index:-1}
.hw-garland span{display:block;transform-origin:50% 0}
.hw-garland span:nth-child(odd){transform:translateY(3px) rotate(-8deg)}
.hw-garland span:nth-child(even){transform:rotate(7deg)}
html.spooky .hw-pk{display:inline-block;font-size:.9em;margin-left:-2px;transform-origin:50% 90%;animation:hw-wobble 3.5s ease-in-out infinite}
@keyframes hw-wobble{0%,100%{transform:rotate(-6deg)}50%{transform:rotate(6deg)}}
/* Teemo's hello */
html.spooky .hw-hi{display:flex;align-items:center;gap:12px;pointer-events:none}
.hw-face{position:relative;flex:none;width:58px;height:58px}
.hw-ring{position:absolute;inset:0;border-radius:50%;overflow:hidden;border:2px solid #ec8a3c;box-shadow:0 0 14px rgb(236 138 60 / .45);background:var(--row)}
.hw-ring img{position:absolute;left:50%;top:50%;width:240%;max-width:none;height:auto;transform:translate(-50%,-31%)}
.hw-hat{position:absolute;left:4px;top:-22px;width:50px;height:auto;transform:rotate(-12deg)}
.hw-bubble{position:relative;background:color-mix(in srgb,#ec8a3c 12%,var(--row));border:1px solid color-mix(in srgb,#ec8a3c 40%,var(--line));border-radius:12px;padding:8px 12px;font-size:14px;line-height:1.35}
.hw-bubble::before{content:"";position:absolute;left:-7px;top:50%;width:12px;height:12px;margin-top:-6px;background:inherit;border:inherit;border-width:0 0 1px 1px;transform:rotate(45deg)}
.hw-bubble b{color:#f2a05a}
.hw-shroom{display:inline-block;transform-origin:50% 100%;animation:hw-wobble 2.6s ease-in-out infinite}
html.spooky .hw-bat{display:block;position:absolute;left:0;top:var(--y);z-index:2;font-size:30px;line-height:1;text-shadow:0 0 10px rgb(255 150 60 / .9),0 0 3px rgb(255 200 120 / .8);opacity:0;animation:hw-fly var(--w) linear var(--d) infinite}
@keyframes hw-fly{0%{transform:translate3d(-40px,0,0) scale(.8);opacity:0}6%{opacity:.85}25%{transform:translate3d(25vw,-14px,0) scale(.9)}50%{transform:translate3d(50vw,10px,0) scale(1)}75%{transform:translate3d(75vw,-10px,0) scale(.9)}94%{opacity:.85}100%{transform:translate3d(calc(100vw + 40px),0,0) scale(.8);opacity:0}}
/* bottom strip: all Teemo, with a pumpkin and mushroom patch along it */
html.spooky .art-bottom:not(.hw-teemo){display:none}
html.spooky .hw-teemo{display:flex}
.hw-teemo::after{background:linear-gradient(0deg,rgb(60 25 5 / .15) 0%,rgb(19 21 28 / .3) 45%,var(--bg) 100%)!important}
.hw-patch{display:flex;justify-content:space-around;align-items:flex-end;position:absolute;left:0;right:0;bottom:6px;z-index:2;font-size:30px;line-height:1;pointer-events:none}
@media (max-width:640px){
  html.spooky .hw-garland{font-size:16px;top:-11px;left:8px;right:8px}
  .hw-garland span:nth-child(n+10){display:none}
  html.spooky .hw-bat{font-size:20px}
  .hw-face{width:48px;height:48px}
  .hw-hat{width:42px;top:-19px;left:3px}
  .hw-bubble{font-size:13px;padding:7px 10px}
  .hw-patch{font-size:20px;bottom:4px}
  .hw-patch span:nth-child(n+10){display:none}
}
@media (prefers-reduced-motion:reduce){
  .hw-pk,.hw-bat,.hw-shroom{animation:none!important}
  html.spooky .hw-bat{opacity:.7}
  .hw-bat:nth-child(1){transform:translateX(18vw)}.hw-bat:nth-child(2){transform:translateX(52vw)}.hw-bat:nth-child(3){transform:translateX(80vw)}
}
""" + h[_i:]

open(out, "w", encoding="utf-8").write(h)
print("patch_halloween: ok ->", out)
