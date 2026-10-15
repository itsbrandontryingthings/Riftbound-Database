#!/usr/bin/env python3
"""Energy and Might sliders in every filter area (website; runs last, after patch_social.py).
- Collection, Wish List, My Shopping List (Marketplace) and Friends' Shopping Lists each get two range sliders,
  Energy and Might, with a low and a high handle (0 to 12, the range in text.js). At 0-12 a slider shows "Any" and
  filters nothing; once narrowed, only cards whose Energy / Might (txOf: e / m) is in range show, so cards without
  that stat (runes, battlefields...) drop out.
- They count as filters: Reset filters clears them, Collection's "Reset filters (N)" counts them. This visit only.
- State: RNG = {c, w, s, f} (collection, wish, shop, friends), each {e: [lo, hi], m: [lo, hi]}.
Usage: patch_sliders.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

def sliders(g):
    one = lambda k, label: (f'<div class="rng" data-g="{g}" data-k="{k}"><span class="rng-l">{label} <b>Any</b></span>'
        f'<div class="rng-t"><i class="rng-fill"></i>'
        f'<input type="range" min="0" max="12" step="1" value="0" data-end="0" aria-label="Lowest {label.lower()}">'
        f'<input type="range" min="0" max="12" step="1" value="12" data-end="1" aria-label="Highest {label.lower()}"></div></div>')
    return f'<div class="frow rng-row">{one("e", "Energy")}{one("m", "Might")}</div>'

# ---------- the sliders in each filter area
rep('      <button class="btn reset" id="freset" type="button" disabled>Reset filters</button>\n    </div>',
    '      <button class="btn reset" id="freset" type="button" disabled>Reset filters</button>\n    </div>\n    ' + sliders("c"))
rep('        <select id="wlf-rar" aria-label="Rarity"><option value="">All rarities</option></select>\n      </div>',
    '        <select id="wlf-rar" aria-label="Rarity"><option value="">All rarities</option></select>\n      </div>\n      ' + sliders("w"))
rep('        <button class="btn reset" id="shf-reset" type="button" disabled>Reset filters</button>\n      </div>',
    '        <button class="btn reset" id="shf-reset" type="button" disabled>Reset filters</button>\n      </div>\n      ' + sliders("s"))
rep('          <button class="btn reset" id="mkf-reset" type="button" disabled>Reset filters</button>\n        </div>',
    '          <button class="btn reset" id="mkf-reset" type="button" disabled>Reset filters</button>\n        </div>\n        ' + sliders("f"))

# ---------- state, matching and the slider controls (early, so the first render can use them)
rep('const RBT = window.RB_TEXT || {n:{}, a:{}};', r'''const RBT = window.RB_TEXT || {n:{}, a:{}};
// ---- Energy / Might sliders: c = Collection, w = Wish List, s = My Shopping List, f = Friends' Shopping Lists
const RNG_MAX = 12, RNG = {}; for (const g of ["c", "w", "s", "f"]) RNG[g] = {e: [0, RNG_MAX], m: [0, RNG_MAX]};
const rngOn = g => ["e", "m"].some(k => RNG[g][k][0] > 0 || RNG[g][k][1] < RNG_MAX);
const rngCount = g => ["e", "m"].filter(k => RNG[g][k][0] > 0 || RNG[g][k][1] < RNG_MAX).length;
function rngOK(c, g){
  for (const k of ["e", "m"]){
    const [lo, hi] = RNG[g][k]; if (lo === 0 && hi === RNG_MAX) continue;
    const t = c && txOf(c), v = t ? t[k] : null;
    if (typeof v !== "number" || v < lo || v > hi) return false;
  }
  return true;
}
function rngDraw(box){
  const [lo, hi] = RNG[box.dataset.g][box.dataset.k], ins = box.querySelectorAll("input");
  ins[0].value = lo; ins[1].value = hi;
  ins[0].style.zIndex = lo > RNG_MAX / 2 ? 3 : 1;   // keep the low handle reachable when it's pushed to the right
  box.querySelector("b").textContent = lo === 0 && hi === RNG_MAX ? "Any" : lo === hi ? String(lo) : `${lo}–${hi}`;
  const f = box.querySelector(".rng-fill"); f.style.left = `calc(9px + (100% - 18px) * ${lo / RNG_MAX})`; f.style.width = `calc((100% - 18px) * ${(hi - lo) / RNG_MAX})`;
  box.classList.toggle("on", !(lo === 0 && hi === RNG_MAX));
}
function rngReset(g){ RNG[g].e = [0, RNG_MAX]; RNG[g].m = [0, RNG_MAX]; document.querySelectorAll(`.rng[data-g="${g}"]`).forEach(rngDraw); }
const rngT = {};
function rngApply(g){
  clearTimeout(rngT[g]);
  rngT[g] = setTimeout(() => {
    if (g === "c"){ st.limit = PAGE; st.page = 0; render(); }
    if (g === "w"){ wlfSync(); renderWish(); }
    if (g === "s"){ $("shf-reset").disabled = !shfOn(); renderShop(); }
    if (g === "f"){ $("mkf-reset").disabled = !mkfOn(); renderFriends(); }
  }, 90);
}
document.addEventListener("input", e => {
  const box = e.target.closest && e.target.closest(".rng"); if (!box || e.target.type !== "range") return;
  const r = RNG[box.dataset.g][box.dataset.k], v = +e.target.value;
  if (e.target.dataset.end === "0") r[0] = Math.min(v, r[1]); else r[1] = Math.max(v, r[0]);
  rngDraw(box); rngApply(box.dataset.g);
});
document.addEventListener("DOMContentLoaded", () => document.querySelectorAll(".rng").forEach(rngDraw));
setTimeout(() => document.querySelectorAll(".rng").forEach(rngDraw), 0);''')

# ---------- Collection
rep('  const n = counts[c.id]||0;\n  if (st.show==="have" && !n) return false;',
    '  if (!rngOK(c, "c")) return false;\n  const n = counts[c.id]||0;\n  if (st.show==="have" && !n) return false;')
rep('(st.variants ? 0 : 1); }', '(st.variants ? 0 : 1) + rngCount("c"); }')
rep('  Object.assign(st, {q:"", set:"", doms:new Set(), banned:false, type:"", rarity:"", kw:"", tg:"", show:"all", variants:true, limit:PAGE, page:0});\n  syncControls(); render();',
    '  Object.assign(st, {q:"", set:"", doms:new Set(), banned:false, type:"", rarity:"", kw:"", tg:"", show:"all", variants:true, limit:PAGE, page:0});\n  rngReset("c"); syncControls(); render();')
# ---------- Wish List
rep('function wlfOn(){ return !!(wlf.q || wlf.dom || wlf.type || wlf.rar || wlf.own); }',
    'function wlfOn(){ return !!(wlf.q || wlf.dom || wlf.type || wlf.rar || wlf.own) || rngOn("w"); }')
rep('  const c = byId[id], n = counts[id] || 0;\n', '  const c = byId[id], n = counts[id] || 0;\n  if (!rngOK(c, "w")) return false;\n')
rep('function wlfReset(){ Object.assign(wlf, {q: "", dom: "", type: "", rar: "", own: ""});',
    'function wlfReset(){ rngReset("w"); Object.assign(wlf, {q: "", dom: "", type: "", rar: "", own: ""});')
# ---------- My Shopping List
rep('function shfOn(){ return !!(shf.q || shf.dom || shf.type || shf.rar); }',
    'function shfOn(){ return !!(shf.q || shf.dom || shf.type || shf.rar) || rngOn("s"); }')
rep('function shfMatch(x){ const c = x.show;\n  return ', 'function shfMatch(x){ const c = x.show;\n  return rngOK(c, "s") && ')
rep('function shfReset(){ Object.assign(shf, {q: "", dom: "", type: "", rar: ""});',
    'function shfReset(){ rngReset("s"); Object.assign(shf, {q: "", dom: "", type: "", rar: ""});')
# ---------- Friends' Shopping Lists
rep('function mkfOn(){ return !!(mkf.q || mkf.dom || mkf.type || mkf.rar); }',
    'function mkfOn(){ return !!(mkf.q || mkf.dom || mkf.type || mkf.rar) || rngOn("f"); }')
rep('  if (!c) return nm && !mkf.dom && !mkf.type && !mkf.rar;\n  return nm && ',
    '  if (!c) return nm && !mkf.dom && !mkf.type && !mkf.rar && !rngOn("f");\n  return nm && rngOK(c, "f") && ')
rep('function mkfReset(){ Object.assign(mkf, {q: "", dom: "", type: "", rar: ""});',
    'function mkfReset(){ rngReset("f"); Object.assign(mkf, {q: "", dom: "", type: "", rar: ""});')

# ---------- styles
_i = h.rfind("</style>"); h = h[:_i] + """.rng-row{gap:10px 22px;align-items:flex-end}
.rng{display:grid;gap:2px;flex:1 1 200px;min-width:170px;max-width:320px}
.rng-l{font-size:13px;color:var(--muted)}
.rng-l b{color:var(--fg);font-variant-numeric:tabular-nums;margin-left:2px}
.rng.on .rng-l b{color:var(--accent)}
.rng-t{position:relative;height:28px}
.rng-t::before{content:"";position:absolute;left:9px;right:9px;top:12px;height:4px;border-radius:2px;background:var(--line)}
.rng-fill{position:absolute;top:12px;height:4px;border-radius:2px;background:var(--muted)}
.rng.on .rng-fill{background:var(--accent)}
.rng-t input{position:absolute;left:0;top:0;width:100%;height:28px;margin:0;background:none;pointer-events:none;-webkit-appearance:none;appearance:none;z-index:2}
.rng-t input:focus{outline:none}
.rng-t input::-webkit-slider-runnable-track{background:none;height:28px}
.rng-t input::-moz-range-track{background:none}
.rng-t input::-webkit-slider-thumb{-webkit-appearance:none;pointer-events:auto;width:18px;height:18px;margin-top:5px;border-radius:50%;background:var(--fg);border:2px solid var(--accent);cursor:pointer;box-shadow:0 1px 4px rgb(0 0 0 / .4)}
.rng-t input::-moz-range-thumb{pointer-events:auto;width:14px;height:14px;border-radius:50%;background:var(--fg);border:2px solid var(--accent);cursor:pointer}
.rng-t input:focus-visible::-webkit-slider-thumb{outline:2px solid var(--accent);outline-offset:2px}
""" + h[_i:]

open(out, "w", encoding="utf-8").write(h)
print("patch_sliders: ok ->", out)
