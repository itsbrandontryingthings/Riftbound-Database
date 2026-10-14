#!/usr/bin/env python3
"""Tidy sharing (website only; runs last, after patch_links.py).
- Removes the optional "How to reach you for trades" field. Shares now send no contact (clearing any saved one),
  and Friends no longer shows it.
- Wish list: "Share with friends" only shows once the list has a card (an empty list never gets a link).
- Share dialog: if a link couldn't be made, say so plainly instead of "Making your link…".
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

open(out, "w", encoding="utf-8").write(h)
print("patch_share_tidy: ok ->", out)
