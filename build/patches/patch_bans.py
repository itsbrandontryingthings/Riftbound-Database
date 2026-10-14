#!/usr/bin/env python3
"""Show the competitive ban list on any version of the Riftbound tracker page (run after the other patches).
Card rows, pack adds and search suggestions get a red "Banned" tag; the deck checker flags banned cards in a deck.
Usage: patch_bans.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:70]!r}, found {n}"
    h = h.replace(old, new)

# fix: the "View card" link style (.view) also matched the tab sections (<section class="view">),
# which forced no-wrap text, green text and a green border onto the whole Collection section
rep('\n.view{color:var(--accent);text-decoration:none;', '\na.view{color:var(--accent);text-decoration:none;')
rep('\n.view:hover{', '\na.view:hover{')

rep('.pill.var{color:var(--warn);border-color:color-mix(in srgb,var(--warn) 40%,var(--line))}',
    '.pill.var{color:var(--warn);border-color:color-mix(in srgb,var(--warn) 40%,var(--line))}\n'
    '.pill.ban{color:var(--fury);border-color:color-mix(in srgb,var(--fury) 55%,var(--line));background:color-mix(in srgb,var(--fury) 12%,transparent);font-weight:600}\n'
    '.tag.ban{color:var(--fury)}\n'
    '.drow .banwarn{color:var(--fury);font-size:12px}')

rep('function cardHTML(c){', r'''// competitive ban list (from cards.js: ban = "std" for Standard + 2v2, "2v2" for 2v2 only)
const fmtDate = d => { try { return new Date(d + "T12:00:00").toLocaleDateString("en-CA", {year:"numeric", month:"short", day:"numeric"}); } catch(e){ return d; } };
function banPill(c){
  if (!c || !c.ban) return "";
  const what = c.ban === "2v2" ? "Banned in 2v2" : "Banned";
  const tip = (c.ban === "2v2" ? "Banned in 2v2 only; still legal in 1v1 Standard" : "Banned in competitive play (Standard and 2v2)") + (c.banSince ? `, since ${fmtDate(c.banSince)}` : "");
  return `<span class="pill ban" title="${esc(tip)}">${what}</span>`;
}
function cardHTML(c){''')

# tag in collection rows, pack adds, suggestions (and the enlarge view on the local copy)
V = '''<span class="r-${c.rarity}">${c.rarity}</span>${c.variant?`<span class="pill var">${esc(c.variant)}</span>`:""}'''
n = h.count(V)
assert n >= 3, n
h = h.replace(V, V + '${banPill(c)}')

# deck checker: per-row tag + warning in the summary
rep('${r.known ? `<span class="sub">', '${r.known ? `<span class="sub">${banPill((groups[r.key]||[]).find(x => x.ban))}')
rep('''${s.have===s.need?'<span class="tag ok">✓ You own every card</span>':""}</div>''',
    '''${s.have===s.need?'<span class="tag ok">✓ You own every card</span>':""}${(() => { const b = new Set(s.secs.flatMap(x => x.rows).filter(r => (groups[r.key]||[]).some(x => x.ban === "std")).map(r => r.key)); return b.size ? `<span class="tag ban">⚠ ${b.size} banned card${b.size===1?"":"s"}: not tournament legal</span>` : ""; })()}</div>''')

rep("Each card name opens its TCGplayer page.",
    "Each card name opens its TCGplayer page. Cards tagged <b>Banned</b> can't be played in competitive events (Riot's ban list as of September 18, 2026); <b>Banned in 2v2</b> cards are still legal in 1v1.")

# ---------- "Banned" filter chip beside the domain chips (combines with them: Banned + Fury = banned Fury cards)
rep('.dom button[aria-pressed="true"]{color:var(--fg);border-color:var(--muted);background:var(--row)}',
    '.dom button[aria-pressed="true"]{color:var(--fg);border-color:var(--muted);background:var(--row)}\n'
    '.dom button.banchip .dot{background:transparent;border:2px solid var(--fury);width:11px;height:11px}\n'
    '.dom button.banchip[aria-pressed="true"]{color:var(--fury);border-color:var(--fury);background:color-mix(in srgb,var(--fury) 12%,var(--row))}')
rep('<span class="dot" style="background:var(${v})"></span>${d}</button>`).join("");',
    '<span class="dot" style="background:var(${v})"></span>${d}</button>`).join("") + `<button class="banchip" data-ban="1" aria-pressed="false" title="Show only cards banned from competitive play"><span class="dot"></span>Banned</button>`;')
rep('document.querySelectorAll("#doms button").forEach(b => b.setAttribute("aria-pressed", st.doms.has(b.dataset.d)));',
    'document.querySelectorAll("#doms button").forEach(b => b.setAttribute("aria-pressed", b.dataset.ban ? !!st.banned : st.doms.has(b.dataset.d)));')
rep('  if (st.doms.size && !c.domains.some(d => st.doms.has(d))) return false;',
    '  if (st.doms.size && !c.domains.some(d => st.doms.has(d))) return false;\n  if (st.banned && !c.ban) return false;')
rep('$("doms").addEventListener("click", e => { const b = e.target.closest("button"); if (!b) return; const d',
    '$("doms").addEventListener("click", e => { const b = e.target.closest("button"); if (!b) return; if (b.dataset.ban){ st.banned = !st.banned; st.limit = PAGE; syncControls(); render(); return; } const d')

open(out, "w", encoding="utf-8").write(h)
print("ok", n, "row spots")
