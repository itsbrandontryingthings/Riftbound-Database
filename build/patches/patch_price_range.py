#!/usr/bin/env python3
"""Price slider beside Energy and Might (website only, last; builds on patch_sliders.py).
- Every filter area (Collection, Wish List, My Shopping List, Friends' Shopping Lists) gets a third two-handle slider,
  "Price (US $)", from $0 to $20K+. The steps grow as they go ($0, 25c, 50c, $1, $2 ... $1K ... $20K), because most cards
  cost under $5 and only a few cost thousands; a straight 0-20,000 line would put every cheap card on one pixel.
- Uses the card's market price (c.price, today's from prices.js). The top step means "no upper limit".
  Once narrowed, cards without a price drop out. Counts as a filter; Reset filters clears it; this visit only.
- State: RNG[g].p = [low step, high step] (indexes into RNG_PX).
Usage: patch_price_range.py in.html out.html"""
import re, sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

PX = [0, 0.25, 0.5, 1, 2, 3, 5, 10, 15, 20, 30, 50, 75, 100, 150, 200, 300, 500, 750,
      1000, 1500, 2000, 3000, 5000, 7500, 10000, 15000, 20000]
TOP = len(PX) - 1

# ---------- the slider, after Might in each of the four rows
def add(m):
    g = m.group(1)
    return (m.group(0)[:-len("</div>")] +
        f'<div class="rng rng-px" data-g="{g}" data-k="p"><span class="rng-l">Price (US $) <b>Any</b></span>'
        f'<div class="rng-t"><i class="rng-fill"></i>'
        f'<input type="range" min="0" max="{TOP}" step="1" value="0" data-end="0" aria-label="Lowest price">'
        f'<input type="range" min="0" max="{TOP}" step="1" value="{TOP}" data-end="1" aria-label="Highest price"></div></div></div>')
h, n = re.subn(r'<div class="rng" data-g="(\w)" data-k="m">.*?aria-label="Highest might"></div></div></div>', add, h)
assert n == 4, f"expected 4 slider rows, found {n}"

# ---------- state, labels and matching
rep('const RNG_MAX = 12, RNG = {}; for (const g of ["c", "w", "s", "f"]) RNG[g] = {e: [0, RNG_MAX], m: [0, RNG_MAX]};\n'
    'const rngOn = g => ["e", "m"].some(k => RNG[g][k][0] > 0 || RNG[g][k][1] < RNG_MAX);\n'
    'const rngCount = g => ["e", "m"].filter(k => RNG[g][k][0] > 0 || RNG[g][k][1] < RNG_MAX).length;',
    f'const RNG_MAX = 12, RNG_PX = {PX}, RNG = {{}};\n'
    'const rngTop = k => k === "p" ? RNG_PX.length - 1 : RNG_MAX, RNG_K = ["e", "m", "p"];\n'
    'for (const g of ["c", "w", "s", "f"]) RNG[g] = {e: [0, RNG_MAX], m: [0, RNG_MAX], p: [0, rngTop("p")]};\n'
    'const rngNarrow = (g, k) => RNG[g][k][0] > 0 || RNG[g][k][1] < rngTop(k);\n'
    'const rngOn = g => RNG_K.some(k => rngNarrow(g, k));\n'
    'const rngCount = g => RNG_K.filter(k => rngNarrow(g, k)).length;\n'
    'const rngUsd = v => v >= 1000 ? `$${v / 1000}K` : v > 0 && v < 1 ? `${Math.round(v * 100)}¢` : `$${v}`;\n'
    'function rngLabel(k, lo, hi){\n'
    '  const T = rngTop(k); if (lo === 0 && hi === T) return "Any";\n'
    '  if (k !== "p") return lo === hi ? String(lo) : `${lo}–${hi}`;\n'
    '  const a = RNG_PX[lo], b = RNG_PX[hi];\n'
    '  if (hi === T) return `${rngUsd(a)}+`;\n'
    '  if (lo === 0) return `Up to ${rngUsd(b)}`;\n'
    '  return lo === hi ? rngUsd(a) : `${rngUsd(a)}–${rngUsd(b)}`;\n'
    '}')
rep('''    if (typeof v !== "number" || v < lo || v > hi) return false;
  }
  return true;
}''', '''    if (typeof v !== "number" || v < lo || v > hi) return false;
  }
  const [pl, ph] = RNG[g].p, PT = rngTop("p");
  if (pl > 0 || ph < PT){
    const v = c && c.price;
    if (typeof v !== "number" || !(v > 0)) return false;
    if (v < RNG_PX[pl] || (ph < PT && v > RNG_PX[ph])) return false;
  }
  return true;
}''')
rep('''  ins[0].style.zIndex = lo > RNG_MAX / 2 ? 3 : 1;   // keep the low handle reachable when it's pushed to the right
  box.querySelector("b").textContent = lo === 0 && hi === RNG_MAX ? "Any" : lo === hi ? String(lo) : `${lo}–${hi}`;
  const f = box.querySelector(".rng-fill"); f.style.left = `calc(9px + (100% - 18px) * ${lo / RNG_MAX})`; f.style.width = `calc((100% - 18px) * ${(hi - lo) / RNG_MAX})`;
  box.classList.toggle("on", !(lo === 0 && hi === RNG_MAX));''',
'''  const k = box.dataset.k, T = rngTop(k);
  ins[0].style.zIndex = lo > T / 2 ? 3 : 1;   // keep the low handle reachable when it's pushed to the right
  box.querySelector("b").textContent = rngLabel(k, lo, hi);
  const f = box.querySelector(".rng-fill"); f.style.left = `calc(9px + (100% - 18px) * ${lo / T})`; f.style.width = `calc((100% - 18px) * ${(hi - lo) / T})`;
  box.classList.toggle("on", !(lo === 0 && hi === T));''')
rep('function rngReset(g){ RNG[g].e = [0, RNG_MAX]; RNG[g].m = [0, RNG_MAX];',
    'function rngReset(g){ RNG[g].e = [0, RNG_MAX]; RNG[g].m = [0, RNG_MAX]; RNG[g].p = [0, rngTop("p")];')

open(out, "w", encoding="utf-8").write(h)
print("patch_price_range: ok ->", out)
