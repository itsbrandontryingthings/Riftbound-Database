#!/usr/bin/env python3
"""Tab names + title-case headings, a clearer My Decks intro, total deck value, RiftDecks export
instructions, and (website only) importing a decklist from a link via /api/import.
Run LAST, after patch_wish.py, on the website and the local copy. Usage: patch_polish.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()
WEB = "function cloudSave()" in h
SHARE = "function renderFriends()" in h

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:70]!r}, found {n}"
    h = h.replace(old, new)

# ---------- tab names
rep('aria-controls="view-packs">Open packs<', 'aria-controls="view-packs">Open Packs<')
rep('aria-controls="view-decks">Deck checker<', 'aria-controls="view-decks">My Decks<')
rep('aria-controls="view-wish">Wish list<', 'aria-controls="view-wish">Wish List<')
if SHARE:
    rep('aria-controls="view-friends">Friends<', 'aria-controls="view-friends">Friends\' Decks<')

# ---------- headings in title case
rep('<h2>Open packs</h2>', '<h2>Open Packs</h2>')
rep('<h2>Wish list</h2>', '<h2>Wish List</h2>')
rep('<h2>No decks yet</h2>', '<h2>No Decks Yet</h2>')
rep('<summary id="dk-title">Add a deck</summary>', '<summary id="dk-title">Add a Deck</summary>')
rep('"Add a deck"', '"Add a Deck"')
rep('`Edit deck: ${d.name}`', '`Edit Deck: ${d.name}`')
rep('<summary>Back up or move your collection</summary>', '<summary>Back Up or Move Your Collection</summary>')
h = h.replace("<b>Back up or move your collection</b>", "<b>Back Up or Move Your Collection</b>")
if WEB:
    rep('<h2 id="auth-title">Sign in</h2>', '<h2 id="auth-title">Sign In</h2>')
    rep('$("auth-title").textContent = m === "in" ? "Sign in" : "Create an account";', '$("auth-title").textContent = m === "in" ? "Sign In" : "Create an Account";')
if SHARE:
    rep("<h2>Friends' decks and wish lists</h2>", "<h2>Friends' Decks and Wish Lists</h2>")
    rep('<h2 id="share-title">Share this deck</h2>', '<h2 id="share-title">Share This Deck</h2>')
    rep('"Share your wish list" : "Share this deck"', '"Share Your Wish List" : "Share This Deck"')
# the old tab name in messages
h = h.replace("Deck checker", "My Decks").replace("Open packs", "Open Packs")

# ---------- My Decks intro
share_line = " Copy a shopping list of what's missing, edit the deck any time, or share it with friends." if SHARE else " Copy a shopping list of what's missing, or edit the deck any time."
rep('<section class="view" id="view-decks" role="tabpanel" aria-labelledby="t-decks" hidden>',
    '''<section class="view" id="view-decks" role="tabpanel" aria-labelledby="t-decks" hidden>
    <div class="panel deckintro">
      <h2>My Decks</h2>
      <p>Add any decklist and it's checked against your collection automatically. For each deck you'll see:</p>
      <ul>
        <li><b>Cards you own</b>: any printing of a card counts toward the deck, including alt arts and promos.</li>
        <li><b>What's missing</b>: every card you still need, and how many copies.</li>
        <li><b>Cost to finish</b>: what the missing cards cost, using the cheapest printing of each, in CAD and USD.</li>
        <li><b>Total deck value</b>: what the whole deck is worth at TCGplayer market prices.</li>
        <li><b>Tournament legality</b>: any banned card is flagged.</li>
      </ul>
      <p class="meta">''' + share_line.strip() + ''' Add a deck at the bottom of this page.</p>
    </div>''')
rep(".more{justify-self:center}", """.more{justify-self:center}
.deckintro ul{margin:0;padding-left:20px;display:grid;gap:4px}
.deckintro p{margin:0;max-width:75ch}
.howto{background:var(--row);border:1px solid var(--line);border-radius:8px;padding:10px 12px;font-size:14px;display:grid;gap:6px}
.howto ol{margin:0;padding-left:20px;display:grid;gap:3px}
.howto b{color:var(--fg)}
.howto.flash{border-color:var(--accent);box-shadow:0 0 0 3px color-mix(in srgb,var(--accent) 30%,transparent)}
.howto code{font-family:ui-monospace,Consolas,monospace;font-size:13px;background:var(--bg);border:1px solid var(--line);border-radius:4px;padding:0 4px}
.imp{display:flex;gap:8px;flex-wrap:wrap}
.imp .search{flex:1 1 260px}
#dk-imp-msg.err{color:var(--fury)} #dk-imp-msg.ok{color:var(--ok)}""")

# ---------- total deck value
rep("let need = 0, have = 0, cost = 0, unknown = 0;", "let need = 0, have = 0, cost = 0, unknown = 0, value = 0;")
rep("if (miss && cheap) cost += miss * cheap.price;", "if (miss && cheap) cost += miss * cheap.price;\n    if (cheap) value += r.q * cheap.price;")
rep("return {secs:out, need, have, cost, unknown};", "return {secs:out, need, have, cost, unknown, value};")
rep('<span class="collect-k">Cost to finish</span><span class="vbig">${moneyHTML(s.cost)}</span></div>',
    '<span class="collect-k">Cost to finish</span><span class="vbig">${moneyHTML(s.cost)}</span></div>\n      <div class="vbox"><span class="collect-k">Total deck value</span><span class="vmid">${moneyHTML(s.value)}</span></div>')

# ---------- add-a-deck: link import (website) + how to export from RiftDecks
link_ui = ('''        <div class="add-grid"><span class="meta"><b>Paste a deck link</b> from a deck site such as Piltover Archive, then tap Import to fill in the list. RiftDecks doesn't allow this, so for RiftDecks decks use the steps below.</span>
          <div class="imp"><input class="search" id="dk-url" type="url" inputmode="url" placeholder="https://piltoverarchive.com/decks/view/…" aria-label="Deck link"><button class="btn primary" id="dk-import" type="button">Import</button></div>
          <span class="meta" id="dk-imp-msg" aria-live="polite"></span></div>
''' if WEB else "")
howto = '''        <div class="howto" id="dk-howto">
          <b>Copying a deck from RiftDecks.com</b>
          <ol>
            <li>Open the deck on riftdecks.com.</li>
            <li>Click <b>Export this Deck</b>, then <b>Export TXT</b>.</li>
            <li>Click inside the box of text, select all of it (<code>Ctrl + A</code> on Windows, <code>⌘ + A</code> on Mac, or long-press → Select all on a phone) and copy it.</li>
            <li>Paste it into the Decklist box below and tap <b>Save deck</b>.</li>
          </ol>
          <span class="meta">From any other site, copy the decklist text: each line needs the number of copies and the card name, like <code>3 Gust</code>. Lines like <code>Sideboard:</code> start a new section.</span>
        </div>
'''
rep('<details class="panel" id="deck-add">\n      <summary id="dk-title">Add a Deck</summary>\n      <div class="add-grid">\n',
    '<details class="panel" id="deck-add">\n      <summary id="dk-title">Add a Deck</summary>\n      <div class="add-grid">\n' + link_ui + howto)
h = h.replace('<p class="meta">Paste a list from RiftDecks or anywhere else. A line ending in a colon (like "Sideboard:" or "Runes:") starts a new section.</p>', '')

if WEB:
    rep('$("dk-cancel").addEventListener("click",', r'''// import a decklist from a link (server helper at /api/import reads the page)
async function importDeck(url){
  const msg = $("dk-imp-msg"), go = $("dk-import");
  url = (url || "").trim();
  if (!/^https?:\/\/\S+$/i.test(url)){ msg.textContent = "Paste the full link to the deck page, starting with https://"; msg.className = "meta err"; return; }
  if (/(^|\/\/|\.)riftdecks\.com/i.test(url)){
    msg.textContent = "RiftDecks doesn't let other websites read its decks. Copy the list instead, using the steps just below (Export this Deck → Export TXT).";
    msg.className = "meta err"; $("dk-howto").scrollIntoView({behavior:"smooth", block:"center"}); $("dk-howto").classList.add("flash"); setTimeout(() => $("dk-howto").classList.remove("flash"), 1600); return;
  }
  go.disabled = true; msg.textContent = "Reading the deck…"; msg.className = "meta";
  try {
    const r = await fetch("/api/import?url=" + encodeURIComponent(url));
    const j = await r.json().catch(() => ({ error: "Couldn't read that page." }));
    if (!r.ok || j.error){ msg.textContent = j.error || "Couldn't read that page."; msg.className = "meta err"; }
    else {
      $("dk-list").value = j.text;
      if (!$("dk-name").value.trim() && j.name) $("dk-name").value = j.name;
      const rows = parseDeck(j.text).flatMap(s => s.rows), copies = rows.reduce((a, x) => a + x.q, 0), unknown = rows.filter(x => !groups[x.key]).length;
      msg.textContent = `Imported ${copies} cards from ${j.source}.` + (unknown ? (unknown === 1 ? " 1 card name wasn't recognized; check it in the list." : ` ${unknown} card names weren't recognized; check them in the list.`) : "") + " Check the name and list, then tap Save deck.";
      msg.className = "meta ok";
    }
  } catch(e){ msg.textContent = "Couldn't reach the import service. Check your connection, or copy the list and paste it instead."; msg.className = "meta err"; }
  go.disabled = false;
}
$("dk-import").addEventListener("click", () => importDeck($("dk-url").value));
$("dk-url").addEventListener("keydown", e => { if (e.key === "Enter"){ e.preventDefault(); importDeck($("dk-url").value); } });
// a link pasted straight into the Decklist box is imported too
$("dk-list").addEventListener("paste", e => { const t = (e.clipboardData && e.clipboardData.getData("text") || "").trim(); if (/^https?:\/\/\S+$/i.test(t) && !$("dk-list").value.trim()){ e.preventDefault(); $("dk-url").value = t; importDeck(t); } });
$("dk-cancel").addEventListener("click",''')

# ---------- bigger list view: the S / M / L size switch also sets the picture size in list rows
rep('  $("sizeseg").hidden = st.view !== "grid";',
    '  $("sizeseg").hidden = false;\n  ["m","l"].forEach(z => $("list").classList.toggle("lsz-" + z, st.view === "list" && st.size === z));')
rep('\n    ${thumbHTML(c)}\n', '\n    ${thumbHTML(c, st.size === "m" || st.size === "l" ? 744 : 160)}\n')
rep('${thumbHTML(c, 160)}\n', '${thumbHTML(c, st.size === "m" || st.size === "l" ? 744 : 160)}\n')
rep(': "wlist";', ': "wlist" + (st.size === "m" || st.size === "l" ? " lsz-" + st.size : "");')
rep(".more{justify-self:center}", """.more{justify-self:center}
/* list view picture sizes (M / L); S keeps the compact 60px rows */
.list.lsz-m .card:not(.tile){grid-template-columns:170px 72px minmax(0,1fr) auto;gap:14px;padding:10px 12px}
.list.lsz-l .card:not(.tile){grid-template-columns:280px 72px minmax(0,1fr) auto;gap:16px;padding:12px 14px}
.wlist.lsz-m .wrow{grid-template-columns:170px minmax(0,1fr) auto auto;gap:14px;padding:10px 12px}
.wlist.lsz-l .wrow{grid-template-columns:280px minmax(0,1fr) auto auto;gap:16px;padding:12px 14px}
.list.lsz-m .name,.list.lsz-l .name,.wlist.lsz-m .name,.wlist.lsz-l .name{font-size:17px}
.list.lsz-l .name,.wlist.lsz-l .name{font-size:19px}
@media (max-width:640px){
  .list.lsz-m .card:not(.tile){grid-template-columns:96px minmax(0,1fr) auto;gap:10px;padding:8px}
  .list.lsz-l .card:not(.tile){grid-template-columns:150px minmax(0,1fr);gap:10px;padding:8px}
  .list.lsz-m .card:not(.tile) .code,.list.lsz-l .card:not(.tile) .code{display:none}
  .list.lsz-l .card:not(.tile) .right{grid-column:1/-1;flex-direction:row;justify-content:space-between;align-items:center}
  .wlist.lsz-m .wrow{grid-template-columns:96px minmax(0,1fr) auto}
  .wlist.lsz-l .wrow{grid-template-columns:150px minmax(0,1fr)}
  .wlist.lsz-l .wrow .wq,.wlist.lsz-l .wrow .rm{grid-column:1/-1}
  .list.lsz-m .name,.list.lsz-l .name,.wlist.lsz-m .name,.wlist.lsz-l .name{font-size:15px}
}""")

# ---------- Friends tab: name, and separate Friends' Decks / Wish Lists sections
if SHARE:
    rep("aria-controls=\"view-friends\">Friends' Decks<", 'aria-controls="view-friends">Friends<')
    rep("<h2>Friends' Decks and Wish Lists</h2>", "<h2>Friends</h2>")
    rep(".more{justify-self:center}", ".more{justify-self:center}\n.frsec{font-family:var(--display);font-size:19px;margin:10px 0 0;display:flex;gap:8px;align-items:baseline}\n.frsec small{font-family:var(--body-font);font-size:14px;color:var(--muted);font-weight:500}\n.frlist > .frnone{margin:0}")
    rep("async function renderFriends(){", r"""// split the shared lists into "Friends' Decks" and "Wish Lists"
function groupFriends(){
  const list = $("fr-list"), arts = [...list.querySelectorAll(":scope > article.frdeck")];
  if (!arts.length) return;
  const isWish = a => (a.querySelector("h3") || {}).textContent.trim().startsWith("♥");
  const wishes = arts.filter(isWish), decks = arts.filter(a => !isWish(a)), q = $("fr-q").value.trim();
  list.innerHTML = "";
  const section = (title, items, none) => {
    const h = document.createElement("h2"); h.className = "frsec"; h.innerHTML = `${title} <small>${items.length}</small>`; list.append(h);
    if (items.length) items.forEach(a => list.append(a));
    else { const p = document.createElement("p"); p.className = "meta frnone"; p.textContent = none; list.append(p); }
  };
  section("Friends' Decks", decks, q ? "No shared decks match this search." : "No one has shared a deck yet.");
  section("Wish Lists", wishes, q ? "No shared wish lists match this search." : "No one has shared a wish list yet.");
}
async function renderFriends(){ await renderFriendsList(); groupFriends(); }
async function renderFriendsList(){""")

open(out, "w", encoding="utf-8").write(h)
print("ok", len(h), "web" if WEB else "")
