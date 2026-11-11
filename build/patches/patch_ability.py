"""Ability text filter (website only, after patch_search).

An "Ability text" box in Collection's Filters (`#ab`, `st.ab`) and in the Wish List's filters (`#wlf-ab`, `wlf.ab`)
searches only what cards do (their rules text), not names or tags. What's typed is matched as a phrase from the start
of a word ("draw 2" finds "Draw 2", "draw ca" finds "draw cards"); commas separate several ("deathknell, draw"), which
must all be there. Symbols count as words (`abOf`): ":rb_energy_2:" = "2 energy", might, exhaust, "calm rune",
"any rune". Capitals and punctuation don't matter (`fz`). It counts as a filter; Reset filters clears it.
Usage: patch_ability.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

rep('''function findOf(c){''', '''// a card's ability text as plain words, for the Ability text filter (symbols become words: ":rb_energy_2:" -> "2 energy")
function abOf(c){
  if (c._ab !== undefined) return c._ab;
  const t = txOf(c);
  return c._ab = t ? " " + fz(t.text.replace(/:rb_energy_(\\d+):/g, " $1 energy ").replace(/:rb_might:/g, " might ").replace(/:rb_exhaust:/g, " exhaust ")
    .replace(/:rb_rune_rainbow:/g, " any rune ").replace(/:rb_rune_([a-z]+):/g, " $1 rune ").replace(/:rb_[a-z0-9_]+:/g, " ")) + " " : " ";
}
// every comma-separated part is in the ability text, as a phrase starting at a word
const abOK = (c, q) => !q || q.split(/[,;]+/).every(p => { const f = fz(p); return !f || abOf(c).includes(" " + f); });
function findOf(c){''')
rep('.price .na{color:var(--muted);font-size:13px}', '''.price .na{color:var(--muted);font-size:13px}
#ab, #wlf-ab{flex:1 1 240px;min-width:0}''')

# Collection
rep('''      <select id="tg" aria-label="Champion or region tag"><option value="">All tags</option></select>''',
    '''      <select id="tg" aria-label="Champion or region tag"><option value="">All tags</option></select>
      <input class="search" id="ab" type="search" placeholder="Ability text, e.g. draw 2 or deathknell" aria-label="Ability text: search what cards do" autocomplete="off">''')
rep('only:false, pchg:"", sort:"set"', 'only:false, pchg:"", ab:"", sort:"set"')
rep('$("pchg").value = st.pchg || "";', '$("pchg").value = st.pchg || ""; $("ab").value = st.ab || "";')
rep('  if (st.kw && !kwOf(c).includes(st.kw)) return false;', '  if (st.kw && !kwOf(c).includes(st.kw)) return false;\n  if (st.ab && !abOK(c, st.ab)) return false;')
rep('(st.pchg ? 1 : 0)', '(st.pchg ? 1 : 0) + (st.ab ? 1 : 0)', 2)
rep('only:false, pchg:"", sort: /^(gain', 'only:false, pchg:"", ab:"", sort: /^(gain')
rep('''$("kw").addEventListener("change", e => {''', '''let abT; $("ab").addEventListener("input", e => { st.ab = e.target.value.trim(); clearTimeout(abT); abT = setTimeout(() => { st.limit = PAGE; st.page = 0; render(); }, 150); });
$("kw").addEventListener("change", e => {''')

# Wish List
rep('''        <select id="wlf-set" aria-label="Set"><option value="">All sets</option></select>''',
    '''        <input class="search" id="wlf-ab" type="search" placeholder="Ability text, e.g. draw 2" aria-label="Ability text: search what cards do" autocomplete="off">
        <select id="wlf-set" aria-label="Set"><option value="">All sets</option></select>''')
rep('const wlf = {q: "", set: "",', 'const wlf = {q: "", ab: "", set: "",')
rep('function wlfOn(){ return !!(wlf.q || wlf.set', 'function wlfOn(){ return !!(wlf.q || wlf.ab || wlf.set')
rep('  if (wlf.q && !hasWords(c.name + " " + c.id + " " + findOf(c), wlf.q)) return false;',
    '  if (wlf.q && !hasWords(c.name + " " + c.id + " " + findOf(c), wlf.q)) return false;\n  if (wlf.ab && !abOK(c, wlf.ab)) return false;')
rep('Object.assign(wlf, {q: "", set: "", dom: "", type: "", rar: "", own: ""}); $("wlf-q").value = "";',
    'Object.assign(wlf, {q: "", ab: "", set: "", dom: "", type: "", rar: "", own: ""}); $("wlf-q").value = ""; $("wlf-ab").value = "";')
rep('''let wlfT; $("wlf-q").addEventListener("input", e => {''', '''$("wlf-ab").addEventListener("input", e => { wlf.ab = e.target.value.trim(); wlfSync(); clearTimeout(wlfT); wlfT = setTimeout(renderWish, 120); });
let wlfT; $("wlf-q").addEventListener("input", e => {''')

open(out, "w", encoding="utf-8").write(h)
