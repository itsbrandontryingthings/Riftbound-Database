"""Pick several in the filter menus (website only, last).

Set, Type, Rarity, Keyword and Tag in Collection's Filters, and Set, Domain, Type and Rarity in the Wish List, My Shopping
List and Friends' Shopping Lists, become pick-several menus (`multiSel`): a button that opens checkboxes (a sheet at
the bottom of the screen on phones), with Clear and Done. The <select> stays, hidden, and keeps the value, several
picks joined with "|" ("Unit|__champ"); `many(v)` splits it, and `msVal(select, v)` sets one (code must use it instead
of `.value =`, so the button's label follows). Picks in one menu widen the results (Champion Unit + Regular Unit = both);
domains in the other areas must all be on the card, like Collection's domain buttons. The set buttons at the top still
pick one set (Ctrl/Shift-click adds one), and show every picked set as pressed.
Usage: patch_multi.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

rep('select{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:8px 10px}', '''select{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:8px 10px}
.msel{position:relative;display:inline-flex;min-width:0}
.msel-b{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:8px 30px 8px 12px;min-width:150px;width:100%;text-align:left;position:relative;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.msel-b::after{content:"▾";position:absolute;right:11px;top:50%;transform:translateY(-50%);color:var(--muted)}
.msel-b.on{border-color:var(--accent)}
.msel-p{position:absolute;top:100%;left:0;z-index:40;margin-top:4px;min-width:240px;max-width:min(360px,calc(100vw - 32px));max-height:340px;overflow:auto;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:6px;box-shadow:0 12px 32px rgb(0 0 0 / .45);display:grid;gap:2px}
.msel-p[hidden]{display:none}
.msel-o{display:flex;gap:9px;align-items:center;padding:7px 9px;border-radius:6px;cursor:pointer;font-size:14px}
.msel-o:hover{background:var(--row)}
.msel-o input{width:17px;height:17px;flex:none;accent-color:var(--accent)}
.msel-h{font-size:12px;color:var(--muted);padding:4px 9px 2px}
.msel-f{position:sticky;bottom:-6px;background:var(--panel);display:flex;gap:6px;justify-content:flex-end;padding:6px 0 0;border-top:1px solid var(--line);margin-top:4px}
@media (max-width:640px){
  .msel-p{position:fixed;left:12px;right:12px;bottom:12px;top:auto;max-width:none;min-width:0;max-height:62vh;margin:0}
}''')

rep('''function txOf(c){''', '''// ---- pick-several menus: a <select> becomes a button that opens checkboxes; several picks are kept joined with "|"
function many(v){ return v ? String(v).split("|") : []; }
let msOpen = null;
function msVal(sel, v){                          // set a menu's value, one or several picks
  if (!sel) return;
  v = v || "";
  if (v && ![...sel.options].some(o => o.value === v)){ const o = new Option("", v); o.dataset.multi = "1"; o.hidden = true; sel.add(o); }
  sel.value = v; msLabel(sel);
}
function msLabel(sel){
  const m = sel._ms; if (!m) return;
  const vs = many(sel.value), opts = [...sel.options], name = v => ((opts.find(o => o.value === v && !o.dataset.multi) || {}).textContent || v).replace(/\\s*\\(\\d+\\)$/, "");
  m.btn.textContent = !vs.length ? opts[0].textContent : vs.length === 1 ? name(vs[0]) : `${name(vs[0])} +${vs.length - 1}`;
  m.btn.title = vs.map(name).join(", ");
  m.btn.classList.toggle("on", vs.length > 0);
}
function msClose(w){ if (!w) return; w._ms.pop.hidden = true; w._ms.btn.setAttribute("aria-expanded", "false"); if (msOpen === w) msOpen = null; }
function multiSel(sel){
  if (!sel || sel._ms) return;
  const wrap = document.createElement("div"), btn = document.createElement("button"), pop = document.createElement("div");
  wrap.className = "msel"; btn.type = "button"; btn.className = "msel-b"; pop.className = "msel-p"; pop.hidden = true;
  btn.setAttribute("aria-haspopup", "true"); btn.setAttribute("aria-expanded", "false"); btn.setAttribute("aria-label", (sel.getAttribute("aria-label") || "") + ": pick one or more");
  pop.setAttribute("role", "group"); pop.setAttribute("aria-label", sel.getAttribute("aria-label") || "");
  sel.before(wrap); wrap.append(btn, pop, sel); sel.hidden = true; sel._ms = wrap._ms = {btn, pop};
  const fire = () => sel.dispatchEvent(new Event("change", {bubbles: true}));
  const open = () => {
    const vs = many(sel.value), opts = [...sel.options].filter(o => o.value && !o.hidden && !o.dataset.multi);
    pop.innerHTML = `<div class="msel-h">Pick one or more</div>` + opts.map(o => `<label class="msel-o"><input type="checkbox" value="${esc(o.value)}"${vs.includes(o.value) ? " checked" : ""}>${esc(o.textContent)}</label>`).join("")
      + `<div class="msel-f"><button type="button" class="btn" data-clear>Clear</button><button type="button" class="btn primary" data-done>Done</button></div>`;
    pop.hidden = false; btn.setAttribute("aria-expanded", "true"); msOpen = wrap;
    // near the right edge, open to the left (phones use a sheet at the bottom instead)
    pop.style.left = pop.style.right = "";
    if (!matchMedia("(max-width:640px)").matches && pop.getBoundingClientRect().right > innerWidth - 8){ pop.style.left = "auto"; pop.style.right = "0"; }
  };
  btn.addEventListener("click", () => { if (pop.hidden){ msClose(msOpen); open(); } else msClose(wrap); });
  pop.addEventListener("change", () => { msVal(sel, [...pop.querySelectorAll("input:checked")].map(i => i.value).join("|")); fire(); });
  pop.addEventListener("click", e => {
    if (e.target.closest("[data-done]")){ msClose(wrap); btn.focus(); }
    else if (e.target.closest("[data-clear]")){ pop.querySelectorAll("input").forEach(i => i.checked = false); msVal(sel, ""); fire(); }
  });
  msLabel(sel);
}
document.addEventListener("click", e => { if (msOpen && !msOpen.contains(e.target)) msClose(msOpen); });
document.addEventListener("keydown", e => { if (e.key === "Escape" && msOpen){ const w = msOpen; msClose(w); w._ms.btn.focus(); } });
function txOf(c){''')

# Collection: matching
rep('''const typeOK = c => st.type === "__token" ? !!c.token : TYPE_SUB[st.type] ? subOf(c) === st.type : !st.type || (c.type === st.type && !subOf(c));''',
    '''const typeOK = c => !st.type || many(st.type).some(t => t === "__token" ? !!c.token : TYPE_SUB[t] ? subOf(c) === t : c.type === t && !subOf(c));''')
rep('''  if (!ignoreSet && st.set && c.set !== st.set) return false;''', '''  if (!ignoreSet && st.set && !many(st.set).includes(c.set)) return false;''')
rep('''  if (st.rarity && c.rarity !== st.rarity) return false;''', '''  if (st.rarity && !many(st.rarity).includes(c.rarity)) return false;''')
rep('''  if (st.kw && !kwOf(c).includes(st.kw)) return false;''', '''  if (st.kw && !many(st.kw).some(k => kwOf(c).includes(k))) return false;''')
rep('''  if (st.tg && !(txOf(c) && txOf(c).tags.includes(st.tg))) return false;''', '''  if (st.tg && !(txOf(c) && many(st.tg).some(g => txOf(c).tags.includes(g)))) return false;''')
rep('''  const scope = pool.filter(c => !st.set || c.set === st.set);''', '''  const scope = pool.filter(c => !st.set || many(st.set).includes(c.set));''')
rep('''st.set ? `Cost to complete ${setName[st.set]}` : "Cost to complete everything";''', '''st.set ? `Cost to complete ${many(st.set).map(s => setName[s]).join(" + ")}` : "Cost to complete everything";''')
rep('''data-set="${s.code}" aria-pressed="${st.set===s.code}"''', '''data-set="${s.code}" aria-pressed="${many(st.set).includes(s.code)}"''')
rep('''(st.set ? ` in ${setName[st.set]}` : "")''', '''(st.set ? ` in ${many(st.set).map(s => setName[s]).join(" + ")}` : "")''')
rep('''counts[c.id] > 0 && (!st.set || c.set===st.set));''', '''counts[c.id] > 0 && (!st.set || many(st.set).includes(c.set)));''')
rep('''$("sets").addEventListener("click", e => { const b = e.target.closest(".setbtn"); if (!b) return; st.set = b.dataset.set;''',
    '''$("sets").addEventListener("click", e => { const b = e.target.closest(".setbtn"); if (!b) return;
  // a tap picks that set; Ctrl/Shift-click adds or removes it
  if ((e.ctrlKey || e.metaKey || e.shiftKey) && b.dataset.set){ const v = many(st.set), i = v.indexOf(b.dataset.set); if (i < 0) v.push(b.dataset.set); else v.splice(i, 1); st.set = v.join("|"); }
  else st.set = b.dataset.set;''')

# Collection: writing the menus
rep('''$("type").value = st.type; $("rarity").value = st.rarity; $("kw").value = st.kw || ""; $("tg").value = st.tg || "";''',
    '''msVal($("type"), st.type); msVal($("rarity"), st.rarity); msVal($("kw"), st.kw); msVal($("tg"), st.tg);''')
rep('''if ($("cset")) $("cset").value = st.set || "";''', '''if ($("cset")) msVal($("cset"), st.set);''')
rep('''$("cset").insertAdjacentHTML("beforeend", setOpts()); $("cset").value = st.set || "";''', '''$("cset").insertAdjacentHTML("beforeend", setOpts()); msVal($("cset"), st.set);''')

# Wish List, My Shopping List, Friends' Shopping Lists
for f in ("wlf", "mkf", "shf"):
    rep(f'''$("{f}-" + k).value = ""''', f'''msVal($("{f}-" + k), "")''')
rep('''(!wlf.set || c.set === wlf.set) && (!wlf.dom || c.domains.includes(wlf.dom)) && (!wlf.type || c.type === wlf.type) && (!wlf.rar || c.rarity === wlf.rar)''',
    '''(!wlf.set || many(wlf.set).includes(c.set)) && many(wlf.dom).every(d => c.domains.includes(d)) && (!wlf.type || many(wlf.type).includes(c.type)) && (!wlf.rar || many(wlf.rar).includes(c.rarity))''')
rep('''(!mkf.set || c.set === mkf.set) && (!mkf.dom || (c.domains || []).includes(mkf.dom)) && (!mkf.type || c.type === mkf.type) && (!mkf.rar || c.rarity === mkf.rar)''',
    '''(!mkf.set || many(mkf.set).includes(c.set)) && many(mkf.dom).every(d => (c.domains || []).includes(d)) && (!mkf.type || many(mkf.type).includes(c.type)) && (!mkf.rar || many(mkf.rar).includes(c.rarity))''')
rep('''(!shf.set || c.set === shf.set) && (!shf.q || hasWords(x.name, shf.q)) && (!shf.dom || (c.domains || []).includes(shf.dom)) && (!shf.type || c.type === shf.type) && (!shf.rar || c.rarity === shf.rar)''',
    '''(!shf.set || many(shf.set).includes(c.set)) && (!shf.q || hasWords(x.name, shf.q)) && many(shf.dom).every(d => (c.domains || []).includes(d)) && (!shf.type || many(shf.type).includes(c.type)) && (!shf.rar || many(shf.rar).includes(c.rarity))''')

# turn the menus into pick-several menus once their options are in
rep('''syncControls(); render(); showTab(''', '''["cset", "type", "rarity", "kw", "tg"].concat(...["wlf", "shf", "mkf"].map(f => ["set", "dom", "type", "rar"].map(k => f + "-" + k))).forEach(id => multiSel($(id)));
syncControls(); render(); showTab(''')

open(out, "w", encoding="utf-8").write(h)
