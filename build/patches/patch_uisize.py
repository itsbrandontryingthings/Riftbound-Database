#!/usr/bin/env python3
"""Page size S-M-L (website; runs last, after patch_shop_add.py).
- A "Page size" S / M / L switch in the top panel makes the whole site bigger (text, buttons, cards, pictures,
  but not pop-ups, which already fill the screen) using CSS zoom on <body>, undone on each <dialog>: S = 100% (the original look), M = 115%, L = 130%. Remembered per device in
  localStorage "rb-ui-size". Layout reflows because zoom shrinks the usable width, so phones stay one column.
Usage: patch_uisize.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

rep('''    <div class="eyebrow">Collection tracker <span class="tag" id="sync">Loading your collection…</span></div>''',
    '''    <div class="eyebrow">Collection tracker <span class="tag" id="sync">Loading your collection…</span><span class="uisize"><span>Page size</span><span class="seg" role="group" aria-label="Page size"><button id="ui-s" aria-pressed="true" title="Normal size">S</button><button id="ui-m" aria-pressed="false" title="Bigger">M</button><button id="ui-l" aria-pressed="false" title="Biggest">L</button></span></span></div>''')

rep('''function saveDeckView(){''', r'''// ---- page size: zooms the whole site (S = normal)
const UI_ZOOM = {s: 1, m: 1.15, l: 1.3};
function setUiSize(z, save){
  if (!UI_ZOOM[z]) z = "s";
  document.body.style.zoom = UI_ZOOM[z] === 1 ? "" : String(UI_ZOOM[z]);
  // pop-ups (card view, sign-in, share) are sized to the screen already; keep them at normal size so they fit
  document.querySelectorAll("dialog").forEach(d => { d.style.zoom = UI_ZOOM[z] === 1 ? "" : String(1 / UI_ZOOM[z]); });
  ["s","m","l"].forEach(k => $("ui-" + k).setAttribute("aria-pressed", k === z));
  if (save) LS.set("rb-ui-size", z);
}
["s","m","l"].forEach(k => $("ui-" + k).addEventListener("click", () => { setUiSize(k, true); if (st.view === "grid" && st.tab === "collection") renderList(); }));
setUiSize(LS.get("rb-ui-size") || "s");
function saveDeckView(){''')

_i = h.rfind("</style>"); h = h[:_i] + """.uisize{margin-left:auto;display:inline-flex;gap:8px;align-items:center;text-transform:none;letter-spacing:.02em;font-family:var(--body-font);font-size:13px}
.uisize .seg button{padding:4px 10px;font-size:13px;font-family:var(--display)}
""" + h[_i:]

open(out, "w", encoding="utf-8").write(h)
print("patch_uisize: ok ->", out)
