#!/usr/bin/env python3
"""Friends tab S-M-L and sort (website; runs last, after patch_uisize.py).
- Sort menu (st.frsort): list order, set order, name A-Z, price high to low; applies inside friends' decks
  (per section), wish lists and shopping lists, offer form included.
- S / M / L buttons under the Friends search make each card line in friends' decks, wish lists and shopping lists
  (and the offer form) bigger: picture 38 / 64 / 104 px wide, with larger names and text. Uses the same st.size as
  the other tabs' S-M-L.
Usage: patch_friends_size.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

rep('''      <span class="meta" id="fr-count" aria-live="polite"></span>''',
    '''      <div class="frow fr-tools"><span class="meta">Card size</span><div class="seg sizeseg" role="group" aria-label="Card size"><button id="frs-s" aria-pressed="false" title="Small cards">S</button><button id="frs-m" aria-pressed="false" title="Medium cards">M</button><button id="frs-l" aria-pressed="false" title="Large cards">L</button></div></div>
      <span class="meta" id="fr-count" aria-live="polite"></span>''')

# ---------- sort the cards inside friends' decks, wish lists and shopping lists
rep('''<div class="seg sizeseg" role="group" aria-label="Card size"><button id="frs-s"''',
    '''<select id="fr-sort" aria-label="Sort the cards in friends' lists"><option value="">Sort: list order</option><option value="set">Sort: set order</option><option value="name">Sort: name A–Z</option><option value="price">Sort: price, high to low</option></select><span class="meta">Card size</span><div class="seg sizeseg" role="group" aria-label="Card size"><button id="frs-s"''')
rep('''<div class="frow fr-tools"><span class="meta">Card size</span>''', '''<div class="frow fr-tools">''')
rep('''<h4>${esc(sec.label)}</h4>${sec.rows.map(x =>''', '''<h4>${esc(sec.label)}</h4>${frSortRows(sec.rows).map(x =>''')
rep('''<div class="frbody">${rows.map(x => { const own = ownedOf(x.key);''', '''<div class="frbody">${frSortRows(rows).map(x => { const own = ownedOf(x.key);''')
rep('''  const lines = rows.map(x => {''', '''  const lines = frSortRows(rows).map(x => {''')

rep('''async function renderFriends(){ await renderFriendsList(); groupFriends(); }''',
    '''function frSortRows(rows){
  const by = st.frsort, cardIx = x => { const c = frCard(x.key); return c ? CARDS.indexOf(c) : 1e9; }, price = x => { const c = cheapestOf(x.key); return c ? c.price : -1; };
  if (by === "set") return rows.slice().sort((a, b) => cardIx(a) - cardIx(b));
  if (by === "name") return rows.slice().sort((a, b) => a.name.localeCompare(b.name));
  if (by === "price") return rows.slice().sort((a, b) => price(b) - price(a) || a.name.localeCompare(b.name));
  return rows;
}
$("fr-sort").addEventListener("change", e => { st.frsort = e.target.value; LS.set("rb-filters", {...st, doms:[...st.doms], limit:undefined}); renderFriends(); });
async function renderFriends(){ await renderFriendsList(); groupFriends(); }''')

rep('''async function renderFriends(){ await renderFriendsList(); groupFriends(); }''',
    '''function frSize(){
  const z = ["s","m","l"].includes(st.size) ? st.size : "m";
  $("fr-sort").value = st.frsort || "";
  ["s","m","l"].forEach(k => { $("frs-" + k).setAttribute("aria-pressed", k === z); $("fr-list").classList.toggle("frsz-" + k, k === z); });
}
["s","m","l"].forEach(k => $("frs-" + k).addEventListener("click", () => { st.size = k; LS.set("rb-filters", {...st, doms:[...st.doms], limit:undefined}); frSize(); }));
async function renderFriends(){ frSize(); await renderFriendsList(); groupFriends(); }''')

_i = h.rfind("</style>"); h = h[:_i] + """.fr-tools{gap:8px}
#fr-sort{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:8px 10px;color:var(--fg);margin-right:6px}
#fr-list.frsz-m .frrow{grid-template-columns:64px 2.4em minmax(0,1fr) auto auto;gap:6px 12px;padding:6px 8px}
#fr-list.frsz-m .frrow:not(:has(.pill.ban)){grid-template-columns:64px 2.4em minmax(0,1fr) auto}
#fr-list.frsz-m .frrow .frn{font-size:16px}
#fr-list.frsz-m .frrow .q{font-size:16px}
#fr-list.frsz-m .frrow .ok,#fr-list.frsz-m .frrow .no{font-size:13.5px}
#fr-list.frsz-l .frrow{grid-template-columns:104px 2.6em minmax(0,1fr) auto auto;gap:8px 14px;padding:8px 10px}
#fr-list.frsz-l .frrow:not(:has(.pill.ban)){grid-template-columns:104px 2.6em minmax(0,1fr) auto}
#fr-list.frsz-l .frrow .frn{font-size:18.5px;font-weight:600}
#fr-list.frsz-l .frrow .q{font-size:18px}
#fr-list.frsz-l .frrow .ok,#fr-list.frsz-l .frrow .no{font-size:14.5px}
#fr-list.frsz-l .of-sub,#fr-list.frsz-l .of-mkt{font-size:13.5px}
#fr-list.frsz-l .frdeck h3{font-size:19px}
#fr-list.frsz-l .frstats{font-size:15px}
@media (max-width:520px){
  #fr-list.frsz-m .frrow,#fr-list.frsz-m .frrow:not(:has(.pill.ban)){grid-template-columns:56px 2em minmax(0,1fr)}
  #fr-list.frsz-l .frrow,#fr-list.frsz-l .frrow:not(:has(.pill.ban)){grid-template-columns:84px 2.2em minmax(0,1fr)}
  #fr-list.frsz-l .frrow .frn{font-size:16.5px}
}
""" + h[_i:]

open(out, "w", encoding="utf-8").write(h)
print("patch_friends_size: ok ->", out)
