#!/usr/bin/env python3
"""Foil shine: cards that only come as foil (c.foil from cards.js: Rares, Epics, Showcase and most promos)
get a moving rainbow sheen on their picture, like riftbound.gg. In the enlarged preview the shine and a
small tilt follow the mouse/finger. Runs last, on both the website and the local copy.
Usage: patch_foil.py in.html out.html"""
import sys

src, dst = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def sub(old, new, count=1):
    global h
    if old not in h:
        sys.exit("patch_foil: not found: " + old[:80])
    h = h.replace(old, new, count)

# 1) thumbnails: mark foil printings and add the sheen layer
sub('''return `<button class="thumb" data-img="${esc(c.id)}"''',
    '''return `<button class="thumb${c.foil ? " foil" : ""}" data-img="${esc(c.id)}"''')
sub('''referrerpolicy="no-referrer">${c.imgBase ? '<span class="bm">BASE ART</span>' : ""}</button>`;''',
    '''referrerpolicy="no-referrer">${c.foil ? '<span class="sheen" aria-hidden="true"></span>' : ""}${c.imgBase ? '<span class="bm">BASE ART</span>' : ""}</button>`;''')

# 2) enlarged preview: wrap the picture so the sheen can sit on top of it
sub('''<img class="lbimg" id="lb-img" alt="" referrerpolicy="no-referrer">''',
    '''<div class="lbwrap" id="lb-fx"><img class="lbimg" id="lb-img" alt="" referrerpolicy="no-referrer"><span class="sheen" aria-hidden="true"></span><span class="glare" aria-hidden="true"></span></div>''')
sub('''$("lb-link").innerHTML = viewLink(c);''',
    '''$("lb-link").innerHTML = viewLink(c);
  $("lb-fx").classList.toggle("foil", !!c.foil); $("lb-fx").style.transform = ""; $("lb-fx").classList.remove("live");''')

# 3) the shine follows the pointer in the preview, with a gentle tilt
JS = r'''
// foil preview: the light moves with the mouse or finger, and the card tilts slightly toward it
(function(){
  const fx = $("lb-fx"); if (!fx) return;
  const calm = matchMedia("(prefers-reduced-motion: reduce)");
  function move(e){
    if (!fx.classList.contains("foil")) return;
    const r = fx.getBoundingClientRect();
    const x = Math.min(1, Math.max(0, (e.clientX - r.left) / r.width)), y = Math.min(1, Math.max(0, (e.clientY - r.top) / r.height));
    fx.classList.add("live");
    fx.style.setProperty("--mx", (x * 100).toFixed(1) + "%");
    fx.style.setProperty("--my", (y * 100).toFixed(1) + "%");
    fx.style.transform = calm.matches ? "" : `perspective(900px) rotateY(${((x - .5) * 10).toFixed(2)}deg) rotateX(${((.5 - y) * 10).toFixed(2)}deg)`;
  }
  function leave(){ fx.classList.remove("live"); fx.style.transform = ""; }
  fx.addEventListener("pointermove", move);
  fx.addEventListener("pointerleave", leave);
  fx.addEventListener("pointercancel", leave);
})();
'''
sub('''$("lb-x").addEventListener("click", () => $("lb").close());''',
    '''$("lb-x").addEventListener("click", () => $("lb").close());''' + JS)

CSS = '''
/* foil shine (cards that only come as foil) */
@keyframes foilmove{0%,100%{background-position:0% 50%}50%{background-position:100% 50%}}
.thumb .sheen,.lbwrap .sheen{position:absolute;inset:0;z-index:2;pointer-events:none;border-radius:inherit;mix-blend-mode:color-dodge;opacity:.55;
  background-image:linear-gradient(115deg,transparent 0%,rgb(255 0 150 / .24) 18%,rgb(255 220 0 / .24) 30%,rgb(0 255 170 / .24) 42%,rgb(0 180 255 / .24) 54%,rgb(150 80 255 / .24) 66%,rgb(255 0 150 / .24) 78%,transparent 100%);
  background-size:300% 300%;animation:foilmove 7s ease-in-out infinite}
.thumb.foil:hover .sheen{opacity:.8}
.lbwrap{position:relative;width:fit-content;max-width:100%;margin:0 auto;border-radius:10px;overflow:hidden;transition:transform .25s ease-out;will-change:transform;touch-action:pinch-zoom}
.lbwrap .sheen,.lbwrap .glare{display:none}
.lbwrap.foil .sheen{display:block;opacity:.6}
.lbwrap.foil.live .sheen{animation:none;opacity:.75;background-position:var(--mx,50%) var(--my,50%);transition:background-position .08s linear}
.lbwrap .glare{position:absolute;inset:0;z-index:3;pointer-events:none;border-radius:inherit;mix-blend-mode:overlay;opacity:0;transition:opacity .2s;
  background:radial-gradient(circle at var(--mx,50%) var(--my,50%),rgb(255 255 255 / .55),rgb(255 255 255 / 0) 45%)}
.lbwrap.foil .glare{display:block}
.lbwrap.foil.live .glare{opacity:1}
.lbwrap.foil.live{transition:transform .08s linear}
@media (prefers-reduced-motion:reduce){.thumb .sheen,.lbwrap .sheen{animation:none;background-position:50% 50%}}
'''
i = h.rfind("</style>")
if i < 0:
    sys.exit("patch_foil: no </style>")
h = h[:i] + CSS + h[i:]

open(dst, "w", encoding="utf-8").write(h)
print("patch_foil: ok ->", dst)
