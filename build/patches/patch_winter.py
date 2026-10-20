#!/usr/bin/env python3
"""Winter / Christmas look (website; runs last, after patch_halloween.py). Takes over from autumn on Nov 2 and runs
to Jan 6 (html.winter); autumn now ends on Nov 1.
- Icy blue accent colour and a cool glow over the top art strip and around the header panel.
- Snow piled along the top of the header panel with a string of twinkling Christmas lights hanging under it, a
  🎄 after the page title, a few twinkling snowflakes over the top art strip, a holiday note from Captain Teemo
  (same round frame as at Halloween, in a Santa hat and beard) and a row of presents, trees and snowmen along the bottom strip.
Decoration only (aria-hidden, pointer-events:none). Light snowfall: 9 slow, faint flakes (5 on a phone) drawn behind the
page content so they never cover cards or text boxes. Only opacity/transform animations, none for reduced motion. ?season=winter previews it.
Usage: patch_winter.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

LIGHTS = "".join(f'<i style="--c:{c};--d:{i * 0.37 % 2:.2f}s"></i>' for i, c in enumerate(["#ff5a5a", "#ffd34d", "#5ad17a", "#5aaaff"] * 6))
FLAKES = "".join(f'<span class="xm-flake" style="left:{x}%;top:{y}%;font-size:{s}px;--d:{d}s">❄</span>' for x, y, s, d in [
    (6, 14, 16, 0), (19, 46, 12, 1.4), (33, 20, 18, .7), (47, 52, 13, 2.1), (58, 16, 15, 1.1), (71, 40, 18, .3), (84, 18, 13, 1.8), (93, 48, 16, .9)])
GIFTS = "".join(f"<span>{e}</span>" for e in ["🎁", "🎄", "⛄", "🎁", "🦌", "🎄", "🎁", "⛄", "🎄", "🎁", "🦌", "🎄", "⛄", "🎁", "🎄"])
FACE = "https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/4fd9e82cbd96010e2556430970d433022b541a51-1488x2078.png?accountingTag=RB&w=300&fm=webp&q=85"
SANTA = ('<svg class="xm-hat" viewBox="0 0 44 36"><path d="M6 27C10 14 18 5 30 4c6 0 9 5 10 11-3-3-7-4-10-2-4 3-5 9-6 14z" fill="#d93636"/>'
         '<rect x="3" y="24" width="28" height="8" rx="4" fill="#f4f6fb"/><circle cx="40" cy="17" r="4" fill="#f4f6fb"/></svg>'
         '<svg class="xm-beard" viewBox="0 0 60 34"><path d="M3 4c4 3 9 4 14 3 4 5 9 6 13 6s9-1 13-6c5 1 10 0 14-3 1 9-2 16-7 20-3 6-8 9-14 9-3 1-6 1-9 0-6 0-11-3-14-9C5 20 2 13 3 4z" fill="#f4f6fb"/>'
         '<path d="M22 13c3-2 5-2 8 0 3-2 5-2 8 0-2 3-5 4-8 3-3 1-6 0-8-3z" fill="#dfe6f2"/></svg>')

# season switch: autumn ends Nov 1, winter runs Nov 2 - Jan 6
rep('''  const fall = q ? q !== "off" : md >= 922 && md <= 1130, spooky = q ? q === "halloween" : md >= 1001 && md <= 1101;
  document.documentElement.classList.toggle("fall", fall); document.documentElement.classList.toggle("spooky", spooky);''',
    '''  const fall = q ? q === "fall" || q === "halloween" : md >= 922 && md <= 1101, spooky = q ? q === "halloween" : md >= 1001 && md <= 1101;
  const winter = q ? q === "winter" : md >= 1102 || md <= 106;
  document.documentElement.classList.toggle("fall", fall); document.documentElement.classList.toggle("spooky", spooky);
  document.documentElement.classList.toggle("winter", winter);''')
rep('<div class="art-band art-top" aria-hidden="true">', '<div class="art-band art-top" aria-hidden="true">' + FLAKES)
# light snowfall: a few slow flakes drawn BEHIND the page (z-index -1), so they only show in the gaps and never cover cards or text boxes
SNOW = "".join(f'<i style="left:{x}%;font-size:{s}px;--d:-{d}s;--w:{w}s;--dx:{dx}px">❄</i>' for x, s, d, w, dx in [
    (3, 12, 0, 26, 30), (14, 9, 9, 31, -20), (26, 14, 17, 28, 25), (38, 10, 4, 33, -30), (50, 12, 21, 29, 20),
    (61, 9, 12, 32, -25), (72, 13, 6, 27, 30), (83, 10, 15, 34, -20), (94, 12, 2, 30, 20)])
rep('<div class="wrap" id="app">', '<div class="xm-fall" aria-hidden="true">' + SNOW + '</div>\n<div class="wrap" id="app">')
rep('<div class="art-band art-bottom" aria-hidden="true">', '<div class="art-band art-bottom" aria-hidden="true"><span class="xm-gifts">' + GIFTS + '</span>')
rep('  <div class="top">\n', '  <div class="top">\n    <div class="xm-snow" aria-hidden="true"></div><div class="xm-lights" aria-hidden="true">' + LIGHTS + '</div>\n')
rep('<span class="hw-pk" aria-hidden="true">🎃</span></h1>', '<span class="hw-pk" aria-hidden="true">🎃</span><span class="xm-tree" aria-hidden="true">🎄</span></h1>')
rep('<div class="hw-hi" aria-hidden="true">', '<div class="xm-hi" aria-hidden="true"><span class="hw-face"><span class="hw-ring"><img src="' + FACE + '" alt="" referrerpolicy="no-referrer" decoding="async" loading="lazy"></span>' + SANTA
    + '</span><span class="hw-bubble"><b>Happy Holidays from Captain Teemo!</b> Hope you find something shiny in your packs this winter <span class="hw-shroom">✨</span></span></div>\n    <div class="hw-hi" aria-hidden="true">')

_i = h.rfind("</style>"); h = h[:_i] + """/* winter / Christmas (patch_winter) */
.xm-snow,.xm-lights,.xm-tree,.xm-hi,.xm-flake,.xm-gifts,.xm-fall{display:none}
html.winter .xm-fall{display:block;position:fixed;inset:0;z-index:-1;pointer-events:none;overflow:hidden}
.xm-fall i{position:absolute;top:0;font-style:normal;line-height:1;color:#dcecff;opacity:0;animation:xm-drop var(--w) linear var(--d) infinite;will-change:transform}
@keyframes xm-drop{0%{transform:translate3d(0,-30px,0) rotate(0);opacity:0}10%{opacity:.45}50%{transform:translate3d(var(--dx),50vh,0) rotate(90deg)}90%{opacity:.4}100%{transform:translate3d(0,105vh,0) rotate(180deg);opacity:0}}
html.winter{--accent:#7cc4ee}
html.winter .art-top::after{background:linear-gradient(180deg,rgb(40 80 140 / .2) 0%,rgb(15 25 45 / .35) 55%,var(--bg) 100%)}
html.winter .top{position:relative;padding-top:38px;border-color:color-mix(in srgb,#7cc4ee 35%,var(--line));box-shadow:0 0 0 1px rgb(124 196 238 / .08),0 10px 30px -12px rgb(124 196 238 / .35)}
/* snow piled on the header: soft white bumps drawn with gradients */
html.winter .xm-snow{display:block;position:absolute;left:-1px;right:-1px;top:-9px;height:20px;z-index:2;pointer-events:none;border-radius:10px 10px 0 0;
  background:radial-gradient(14px 11px at 14px 11px,#f4f7fc 98%,transparent) 0 0/34px 20px repeat-x,radial-gradient(20px 10px at 12px 13px,#e8eef8 98%,transparent) 17px 0/41px 20px repeat-x,linear-gradient(#f4f7fc,#f4f7fc) 0 11px/100% 9px no-repeat}
html.winter .xm-lights{display:flex;justify-content:space-between;position:absolute;left:18px;right:18px;top:8px;height:22px;z-index:2;pointer-events:none}
html.winter .xm-lights::before{content:"";position:absolute;left:-6px;right:-6px;top:-4px;height:12px;border-bottom:1.5px solid rgb(40 60 50 / .9);border-radius:0 0 50% 50%}
.xm-lights i{position:relative;display:block;width:8px;height:12px;margin-top:8px;border-radius:50% 50% 50% 50% / 60% 60% 40% 40%;background:var(--c);box-shadow:0 0 8px 2px var(--c);animation:xm-twinkle 2s ease-in-out var(--d) infinite}
.xm-lights i::before{content:"";position:absolute;left:1px;right:1px;top:-3px;height:4px;border-radius:1px;background:#3a4a40}
.xm-lights i:nth-child(odd){margin-top:5px}
@keyframes xm-twinkle{0%,100%{opacity:1}50%{opacity:.35}}
html.winter .xm-tree{display:inline-block;font-size:.9em;margin-left:-2px}
html.winter .xm-hi{display:flex;align-items:center;gap:12px;pointer-events:none;margin:14px 0 8px}
html.winter .xm-hi .hw-ring{border-color:#7cc4ee;box-shadow:0 0 14px rgb(124 196 238 / .45)}
html.winter .xm-hi .hw-bubble{background:color-mix(in srgb,#7cc4ee 12%,var(--row));border-color:color-mix(in srgb,#7cc4ee 40%,var(--line))}
html.winter .xm-hi .hw-bubble b{color:#9fd6f4}
.xm-hat{position:absolute;overflow:visible;left:2px;top:-20px;width:54px;height:auto;transform:rotate(-14deg)}
.xm-beard{position:absolute;left:-1px;bottom:-12px;width:60px;height:auto}
html.winter .xm-flake{display:block;position:absolute;z-index:2;line-height:1;color:#eaf4ff;text-shadow:0 0 8px rgb(170 215 255 / .9);animation:xm-twinkle 3s ease-in-out var(--d) infinite}
html.winter .xm-gifts{display:flex;justify-content:space-around;align-items:flex-end;position:absolute;left:0;right:0;bottom:6px;z-index:2;font-size:30px;line-height:1;pointer-events:none}
@media (max-width:640px){
  html.winter .xm-lights{left:10px;right:10px}
  .xm-lights i:nth-child(n+15){display:none}
  .xm-hat{width:46px;top:-17px}
  .xm-beard{width:50px;bottom:-10px}
  html.winter .xm-gifts{font-size:20px;bottom:4px}
  .xm-gifts span:nth-child(n+10){display:none}
}
@media (max-width:640px){.xm-fall i:nth-child(even){display:none}}
@media (prefers-reduced-motion:reduce){.xm-lights i,.xm-flake{animation:none!important}html.winter .xm-fall{display:none}}
""" + h[_i:]

open(out, "w", encoding="utf-8").write(h)
print("patch_winter: ok ->", out)
