#!/usr/bin/env python3
"""Tidy sharing (website only; runs last, after patch_links.py).
- Removes the optional "How to reach you for trades" field. Shares now send no contact (clearing any saved one),
  and Friends no longer shows it.
- Wish list: "Share with friends" only shows once the list has a card (an empty list never gets a link).
- Share dialog: if a link couldn't be made, say so plainly instead of "Making your link…".
- The name field is "Name This Shared Deck" / "Name This Shared Wishlist": it names that shared item (saved as
  deck.shareName / wish._shareName, sent as name and owner_name) and is the title friends see, with no "by …" line.
Usage: patch_share_tidy.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

# ---------- no contact field
rep('''    <label>How to reach you for trades (optional) <input id="share-contact" maxlength="80" placeholder="e.g. Discord: brandon#1234"></label>\n''', '')
rep('''$("share-name").value = shareProfile.name || ""; $("share-contact").value = shareProfile.contact || "";''',
    '''$("share-name").value = shareProfile.name || "";''')
rep('''  const name = $("share-name").value.trim(), contact = $("share-contact").value.trim();''',
    '''  const name = $("share-name").value.trim();''')
rep('''  shareProfile = {name, contact}; LS.set("rb-share-profile", shareProfile);''',
    '''  shareProfile = {name}; LS.set("rb-share-profile", shareProfile);''')
rep('''{name:"", contact:""}''', '''{name:""}''', count=2)
rep('''contact: (shareProfile.contact || "").slice(0, 80) || null,''', '''contact: null,''')
rep('''  const { data } = await sb.from("shared_decks").select("owner_name, contact").eq("owner", me.id).limit(1);
  if (data && data[0]){ shareProfile = {name: data[0].owner_name, contact: data[0].contact || ""}; LS.set("rb-share-profile", shareProfile); }''',
    '''  const { data } = await sb.from("shared_decks").select("owner_name").eq("owner", me.id).limit(1);
  if (data && data[0]){ shareProfile = {name: data[0].owner_name}; LS.set("rb-share-profile", shareProfile); }''')
rep('''<span class="meta">${r.contact ? esc(r.contact) + " · " : ""}updated ''', '''<span class="meta">updated ''')
rep('''by <b>${esc(r.owner_name)}</b>${r.contact ? ` · ${esc(r.contact)}` : ""} · updated ''', '''by <b>${esc(r.owner_name)}</b> · updated ''')

# ---------- an empty wish list can't be shared
rep('''${typeof openShare === "function" ? (wish._shared ?''', '''${typeof openShare === "function" && ids.length ? (wish._shared ?''')

# ---------- clearer message when no link came back
rep('''function showShareLink(){''', '''function showShareLink(tried){''')
rep('''(linksOff ? "Share links need a quick database update before they work. The site owner has the steps." : "Making your link… if it doesn't appear, check your connection and try again.");''',
    '''(linksOff ? "Share links need a quick database update before they work. The site owner has the steps."
             : tried ? "Couldn't make your link right now. Check your connection, then tap Copy share link to try again."
             : "Making your link…");''')
rep('''  if (!shareTok[curShareId()]){ await flushShared(); await pushShared(); showShareLink(); }''',
    '''  if (!shareTok[curShareId()]){ await flushShared(); await pushShared(); showShareLink(true); }''')

# ---------- the name field names the shared deck / wish list (saved with each one), not the person
rep('''    <label>Name friends will see <input id="share-name" maxlength="40" autocomplete="nickname" required></label>''',
    '''    <label><span id="share-name-label">Name This Shared Deck</span> <input id="share-name" maxlength="40" autocomplete="off" required></label>''')
rep('''  $("share-title").textContent = shareTarget === "wish" ? "Share Your Wish List" : "Share This Deck";''',
    '''  $("share-title").textContent = shareTarget === "wish" ? "Share Your Wish List" : "Share This Deck";
  $("share-name-label").textContent = shareTarget === "wish" ? "Name This Shared Wishlist" : "Name This Shared Deck";''')
rep('''  $("share-name").value = shareProfile.name || "";''',
    '''  $("share-name").value = shareTarget === "wish" ? (wish._shareName || "My Wish List") : (shareDeckName(customDecks.find(x => x.id === curDeck)) || "");''')
rep('''if (!name){ $("share-msg").textContent = "Add the name friends will see.";''',
    '''if (!name){ $("share-msg").textContent = shareTarget === "wish" ? "Give your shared wish list a name." : "Give your shared deck a name.";''')
rep('''  shareProfile = {name}; LS.set("rb-share-profile", shareProfile);
  if (shareTarget === "wish"){ wish._shared = true; saveWish(); renderWish(); }
  else { const d = customDecks.find(x => x.id === curDeck); if (d) d.shared = true; saveDecks(); renderDecks(); }''',
    '''  if (shareTarget === "wish"){ wish._shared = true; wish._shareName = name; saveWish(); renderWish(); }
  else { const d = customDecks.find(x => x.id === curDeck); if (d){ d.shared = true; d.shareName = name; } saveDecks(); renderDecks(); }''')
rep('''let shareProfile = LS.get("rb-share-profile") || {name:""};''',
    '''let shareProfile = LS.get("rb-share-profile") || {name:""};
const shareDeckName = d => d ? String(d.shareName || d.name || "").trim() : "";''')
# keep the shared name when a deck is edited
rep('''    const d = {id:editingId, name, sub: old.sub || "Your deck", text, shared: !!old.shared};''',
    '''    const d = {id:editingId, name, sub: old.sub || "Your deck", text, shared: !!old.shared, shareName: old.shareName};''')
rep('''[{ id: "__wish__", name: "Wish list", text: wishText() }]''', '''[{ id: "__wish__", shareName: wish._shareName || "My Wish List", text: wishText() }]''')
rep('''    if (mine.length && shareProfile.name){
      const rows = mine.map(d => ({ owner: me.id, deck_id: d.id, owner_name: shareProfile.name.slice(0, 40), contact: null, name: String(d.name).slice(0, 80),''',
    '''    if (mine.length){
      const rows = mine.map(d => ({ owner: me.id, deck_id: d.id, owner_name: (shareDeckName(d) || "Shared").slice(0, 40), contact: null, name: (shareDeckName(d) || "Shared").slice(0, 80),''')
# what friends see: the shared name as the title, no "by …"
rep('''<h3>♥ ${esc(r.owner_name)}'s wish list</h3>''', '''<h3>♥ ${esc(r.name)}</h3>''')
rep('''<span class="meta">by <b>${esc(r.owner_name)}</b> · updated ''', '''<span class="meta">updated ''')
rep('''name: `${r.name} (${r.owner_name})`.slice(0, 80), sub: `Copied from ${r.owner_name}`,''',
    '''name: String(r.name).slice(0, 80), sub: "Copied from a friend's link",''')

open(out, "w", encoding="utf-8").write(h)
print("patch_share_tidy: ok ->", out)
