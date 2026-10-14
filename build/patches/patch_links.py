#!/usr/bin/env python3
"""Private share links (website only; runs last, after patch_info.py). Needs supabase_links.sql.
- Sharing a deck or the wish list makes a secret link (rbdatabase.pages.dev/#share=<token>). Nothing is listed
  publicly; only people with the link can open it, signed in or not. Stop sharing deletes it, so the link stops working.
- Friends tab = the links you've been sent: opening a link saves it there (and to your account when signed in),
  or paste a link in. Still searchable by deck, player or card, split into Friends' Decks and Wish Lists.
Usage: patch_links.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

# ---------- share dialog: explain links, and a second step that shows the link
rep('<p class="meta">Anyone signed in to this site can see a deck you share, under the name below. Your email is never shown.</p>',
    '<p class="meta" id="share-intro">You\'ll get a private link to send to friends. Only people with the link can see it, under the name below. It isn\'t listed anywhere, and your email is never shown.</p>')
rep('''    <div class="frow"><button type="submit" class="btn primary" id="share-go">Share deck</button><button type="button" class="btn" id="share-x">Cancel</button></div>
  </form></dialog>''',
    '''    <div class="frow"><button type="submit" class="btn primary" id="share-go">Create link</button><button type="button" class="btn" id="share-x">Cancel</button></div>
  </form>
  <div id="share-done" hidden>
    <h2 id="share-done-title">Your Share Link</h2>
    <p class="meta">Send this link to the friends you want to see it. Anyone with the link can view it, so only share it with people you trust. Tap <b>Stop sharing</b> any time and the link stops working.</p>
    <div class="linkrow"><input id="share-url" readonly aria-label="Share link"><button type="button" class="btn primary" id="share-copy">Copy link</button></div>
    <p class="msg" id="share-done-msg" aria-live="polite"></p>
    <div class="frow"><button type="button" class="btn" id="share-ok">Done</button></div>
  </div></dialog>''')

# ---------- Friends tab: the links you've been sent
rep('''<p class="meta">Decks and wish lists other players have chosen to share. Search by deck name, player, or a card you're looking to trade for. Decks show how many of their cards you own; wish lists show which wanted cards you could trade.</p>''',
    '''<p class="meta">Decks and wish lists friends have sent you a link to. Open a link a friend sends you and it's saved here, or paste one below. Decks show how many of their cards you own; wish lists show which wanted cards you could trade.</p>
      <form class="linkrow" id="fr-add-form" novalidate><input id="fr-add" type="text" inputmode="url" placeholder="Paste a share link, e.g. https://rbdatabase.pages.dev/#share=…" aria-label="Paste a share link" autocomplete="off"><button class="btn primary" id="fr-add-go">Add</button></form>
      <p class="meta" id="fr-add-msg" aria-live="polite"></p>''')
rep('placeholder="Search decks, wish lists, players or cards, e.g. Jinx" aria-label="Search shared decks"',
    'placeholder="Search your friends\' decks and wish lists, e.g. Jinx" aria-label="Search shared decks"')
rep('''Only decks and wish lists you choose to share are visible, and only to people signed in to this site.''',
    '''Decks and wish lists you choose to share can only be seen by people you send the link to.''')

# ---------- deck + wish list buttons: copy the link
rep('${d.shared ? `<span class="tag ok">✓ Shared with friends</span><button class="btn" id="dk-unshare">Stop sharing</button>` : `<button class="btn" id="dk-share">Share with friends</button>`}',
    '${d.shared ? `<span class="tag ok">✓ Shared by link</span><button class="btn" id="dk-link">Copy share link</button><button class="btn" id="dk-unshare">Stop sharing</button>` : `<button class="btn" id="dk-share">Share with friends</button>`}')
rep('(wish._shared ? `<span class="tag ok">✓ Shared with friends</span><button class="btn" id="wish-unshare">Stop sharing</button>` : `<button class="btn" id="wish-share">Share with friends</button>`)',
    '(wish._shared ? `<span class="tag ok">✓ Shared by link</span><button class="btn" id="wish-link">Copy share link</button><button class="btn" id="wish-unshare">Stop sharing</button>` : `<button class="btn" id="wish-share">Share with friends</button>`)')
rep('  if (e.target.id === "dk-share") openShare("deck");', '  if (e.target.id === "dk-share" || e.target.id === "dk-link") openShare("deck");')
rep('  if (e.target.id === "wish-share" && typeof openShare === "function") openShare("wish");',
    '  if ((e.target.id === "wish-share" || e.target.id === "wish-link") && typeof openShare === "function") openShare("wish");')

# ---------- owner side: tokens, dialog flow
rep('// ---- deck sharing (table "shared_decks": everyone signed in can read; only the owner can change their rows)',
    '// ---- sharing by private link (table "shared_decks": owners manage their own rows; others open one only with its secret link, via get_shared)')
rep('let shareTarget = "deck";\nfunction openShare(target){',
    '''let shareTarget = "deck", shareTok = {}, linksOff = false;
const SHARE_BASE = location.origin + location.pathname;
const shareURL = t => `${SHARE_BASE}#share=${t}`;
const curShareId = () => shareTarget === "wish" ? "__wish__" : curDeck;
function showShareLink(){
  const t = shareTok[curShareId()];
  $("share-form").hidden = true; $("share-done").hidden = false;
  $("share-done-title").textContent = shareTarget === "wish" ? "Your Wish List Link" : "Your Deck Link";
  $("share-url").value = t ? shareURL(t) : "";
  $("share-copy").disabled = !t;
  $("share-done-msg").textContent = t ? "" : (linksOff ? "Share links need a quick database update before they work. The site owner has the steps." : "Making your link… if it doesn't appear, check your connection and try again.");
  $("share-done-msg").className = t ? "msg" : "msg err";
}
async function openShareLink(){
  try { $("share").showModal(); } catch(e){ $("share").setAttribute("open", ""); }
  showShareLink();
  if (!shareTok[curShareId()]){ await flushShared(); await pushShared(); showShareLink(); }
  if (shareTok[curShareId()]) $("share-copy").focus();
}
function openShare(target){''')
rep('''  if (!cloudUser){ $("acct-in").click(); return; }
  $("share-name").value = shareProfile.name || "";''',
    '''  if (!cloudUser){ $("acct-in").click(); return; }
  const already = shareTarget === "wish" ? !!wish._shared : !!(customDecks.find(x => x.id === curDeck) || {}).shared;
  if (already) return openShareLink();
  $("share-form").hidden = false; $("share-done").hidden = true;
  $("share-name").value = shareProfile.name || "";''')
rep('''  if (shareTarget === "wish"){ wish._shared = true; $("share").close(); saveWish(); renderWish(); return; }
  const d = customDecks.find(x => x.id === curDeck); if (d) d.shared = true;
  $("share").close(); saveDecks(); renderDecks();
});''',
    '''  if (shareTarget === "wish"){ wish._shared = true; saveWish(); renderWish(); }
  else { const d = customDecks.find(x => x.id === curDeck); if (d) d.shared = true; saveDecks(); renderDecks(); }
  $("share").close(); openShareLink();
});
$("share-copy").addEventListener("click", () => { if ($("share-url").value){ copy($("share-url").value, "share link"); $("share-done-msg").className = "msg"; $("share-done-msg").textContent = "Copied. Paste it in a message to your friends."; } });
$("share-url").addEventListener("focus", e => e.target.select());
$("share-ok").addEventListener("click", () => $("share").close());''')
# upsert returns each item's token; works (without links) before the database update is run
rep('''      const { error } = await sb.from("shared_decks").upsert(rows, { onConflict: "owner,deck_id" });''',
    '''      let { data: saved, error } = linksOff ? await sb.from("shared_decks").upsert(rows, { onConflict: "owner,deck_id" })
                                             : await sb.from("shared_decks").upsert(rows, { onConflict: "owner,deck_id" }).select("deck_id, share_token");
      if (error && !linksOff && /share_token/i.test(error.message || "")){ linksOff = true; ({ error } = await sb.from("shared_decks").upsert(rows, { onConflict: "owner,deck_id" })); }
      if (cloudUser !== me) return;
      (saved || []).forEach(r => { if (r.share_token) shareTok[r.deck_id] = r.share_token; });''')
rep('''    if (gone.length) await sb.from("shared_decks").delete().eq("owner", me.id).in("deck_id", gone);''',
    '''    if (gone.length){ await sb.from("shared_decks").delete().eq("owner", me.id).in("deck_id", gone); gone.forEach(id => delete shareTok[id]); }''')
# pick up your existing links on sign-in
rep('''sb_onSignedIn = () => { loadShareProfile(); frCache = null; if (st.tab === "friends") renderFriends(); };''',
    '''async function loadShareTokens(){
  if (!sb || !cloudUser || linksOff) return;
  const me = cloudUser, { data, error } = await sb.from("shared_decks").select("deck_id, share_token").eq("owner", me.id);
  if (error && /share_token/i.test(error.message || "")){ linksOff = true; return; }
  if (cloudUser === me) (data || []).forEach(r => { if (r.share_token) shareTok[r.deck_id] = r.share_token; });
}
sb_onSignedIn = () => { loadShareProfile(); loadShareTokens(); frCache = null; if (st.tab === "friends") renderFriends(); };''')
rep('''  shareProfile = {name:"", contact:""}; LS.set("rb-share-profile", shareProfile); frCache = null; frOpen.clear();''',
    '''  shareProfile = {name:"", contact:""}; LS.set("rb-share-profile", shareProfile); frCache = null; frOpen.clear(); shareTok = {}; LS.set("rb-links", []);''')

# ---------- Friends tab: only the links you've saved
rep('''async function renderFriendsList(){
  const list = $("fr-list");
  if (!cloudUser){
    $("fr-count").textContent = "";
    list.innerHTML = `<div class="empty">Sign in to see the decks your friends have shared, and to share your own.<br><br><button class="btn primary" id="fr-signin">Sign in or create an account</button></div>`;
    return;
  }
  if (!frCache || Date.now() - frLoadedAt > 60000){
    list.innerHTML = `<div class="empty">Loading shared decks…</div>`;
    const { data, error } = await sb.from("shared_decks").select("id, owner, deck_id, owner_name, contact, name, list, updated_at").order("updated_at", { ascending: false }).limit(500);
    if (error){ list.innerHTML = `<div class="empty">Couldn't load shared decks right now. Check your connection and open this tab again.</div>`; return; }
    frCache = data || []; frLoadedAt = Date.now();
  }
  if (!cloudUser) return renderFriends();''',
    '''// links you've opened or pasted: kept in this browser and, when signed in, with your account (inside the wish list row)
const TOKEN_RE = /^[A-Za-z0-9_-]{20,64}$/;
function savedLinks(){
  const a = LS.get("rb-links") || [], b = Array.isArray(wish._links) ? wish._links : [];
  return [...new Set([...a, ...b])].filter(t => TOKEN_RE.test(t)).slice(0, 200);
}
function setLinks(arr){
  arr = [...new Set(arr)].filter(t => TOKEN_RE.test(t)).slice(0, 200);
  LS.set("rb-links", arr);
  const before = JSON.stringify(wish._links || []);
  if (arr.length) wish._links = arr; else delete wish._links;
  if (JSON.stringify(wish._links || []) !== before) saveWish();
}
function tokenFrom(s){ s = String(s || "").trim(); const m = s.match(/[#?&]share=([A-Za-z0-9_-]{20,64})/); return m ? m[1] : (TOKEN_RE.test(s) ? s : ""); }
let frFocus = "", frMissing = [];
function addLink(t, focus){ const all = savedLinks(); if (!all.includes(t)) all.unshift(t); setLinks(all); frCache = null; if (focus) frFocus = t; }
async function renderFriendsList(){
  const list = $("fr-list"), tokens = savedLinks();
  setLinks(tokens);
  if (!tokens.length){
    $("fr-count").textContent = ""; frCache = [];
    list.innerHTML = `<div class="empty">No shared links yet. When a friend sends you a link to their deck or wish list, open it and it'll be saved here. You can also paste a link above.<br><br>To share your own, open a deck in My Decks, or your Wish List, and tap <b>Share with friends</b>.</div>`;
    return;
  }
  if (!sb){ list.innerHTML = `<div class="empty">Couldn't connect to load shared links. Check your connection and reload the page.</div>`; return; }
  if (!frCache || Date.now() - frLoadedAt > 60000){
    list.innerHTML = `<div class="empty">Loading shared links…</div>`;
    const { data, error } = await sb.rpc("get_shared", { p_tokens: tokens });
    if (error){ list.innerHTML = `<div class="empty">${/get_shared|function/i.test(error.message || "") ? "Shared links aren't switched on yet. They need a quick database update." : "Couldn't load shared links right now. Check your connection and open this tab again."}</div>`; return; }
    frCache = (data || []).sort((a, b) => tokens.indexOf(a.share_token) - tokens.indexOf(b.share_token)); frLoadedAt = Date.now();
    frMissing = tokens.filter(t => !frCache.some(r => r.share_token === t));
    if (frFocus){ const r = frCache.find(x => x.share_token === frFocus); if (r) frOpen.add(r.id); }
  }''')
rep('''  $("fr-count").textContent = frCache.length ? `${items.length} of ${frCache.length} shared list${frCache.length===1?"":"s"}` : "";
  if (!frCache.length){ list.innerHTML = `<div class="empty">Nobody has shared a deck yet. Open My Decks and tap <b>Share with friends</b> on one of yours to be the first.</div>`; return; }''',
    '''  const dead = frMissing.length ? `<span class="frdead">${frMissing.length} saved link${frMissing.length === 1 ? " no longer works" : "s no longer work"}. The owner stopped sharing ${frMissing.length === 1 ? "it" : "them"}. <button class="btn" id="fr-prune">Remove</button></span>` : "";
  $("fr-count").innerHTML = (frCache.length ? `${items.length} of ${frCache.length} shared list${frCache.length===1?"":"s"}` : "") + dead;
  if (!frCache.length){ list.innerHTML = `<div class="empty">None of your saved links work any more. Ask your friend for a new link.</div>`; return; }''')
# "mine" now comes from the server; each item can be removed from your list
rep('''      const mine = r.owner === (cloudUser && cloudUser.id), open = frOpen.has(r.id);''', '''      const mine = !!r.is_mine, open = frOpen.has(r.id);''')
rep('''    const s = deckStats(deck), mine = !!cloudUser && r.owner === cloudUser.id;''', '''    const s = deckStats(deck), mine = !!r.is_mine;''')
rep('''        <div class="frow"><button class="btn" data-act="toggle">${open ? "Hide list" : "Show list"}</button></div>''',
    '''        <div class="frow"><button class="btn" data-act="toggle">${open ? "Hide list" : "Show list"}</button><button class="btn" data-act="forget">Remove from Friends</button></div>''')
rep('''<div class="frow"><button class="btn" data-act="toggle">${open ? "Hide list" : "Show list"}</button>${mine ? "" : '<button class="btn" data-act="copy">Copy to my decks</button>'}<span class="meta" data-msg aria-live="polite"></span></div>''',
    '''<div class="frow"><button class="btn" data-act="toggle">${open ? "Hide list" : "Show list"}</button>${mine ? "" : '<button class="btn" data-act="copy">Copy to my decks</button>'}<button class="btn" data-act="forget">Remove from Friends</button><span class="meta" data-msg aria-live="polite"></span></div>''')
rep('''  if (b.dataset.act === "toggle"){ frOpen.has(id) ? frOpen.delete(id) : frOpen.add(id); renderFriends(); }''',
    '''  if (b.dataset.act === "toggle"){ frOpen.has(id) ? frOpen.delete(id) : frOpen.add(id); renderFriends(); }
  if (b.dataset.act === "forget"){ setLinks(savedLinks().filter(t => t !== r.share_token)); frCache = frCache.filter(x => x !== r); frOpen.delete(id); renderFriends(); }''')
rep('''$("fr-list").addEventListener("click", e => {
  if (e.target.id === "fr-signin"){ $("acct-in").click(); return; }''',
    '''$("fr-count").addEventListener("click", e => { if (e.target.id === "fr-prune"){ setLinks(savedLinks().filter(t => !frMissing.includes(t))); frMissing = []; frCache = null; renderFriends(); } });
$("fr-add-form").addEventListener("submit", e => {
  e.preventDefault();
  const t = tokenFrom($("fr-add").value);
  if (!t){ $("fr-add-msg").textContent = "That doesn't look like a share link. Copy the whole link your friend sent, starting with https://"; return; }
  $("fr-add-msg").textContent = savedLinks().includes(t) ? "You already have that link. It's highlighted below." : "Added.";
  $("fr-add").value = ""; addLink(t, true); renderFriends().then(() => { const a = document.querySelector(".frdeck.new"); if (a) a.scrollIntoView({block: "center"}); });
});
$("fr-list").addEventListener("click", e => {
  if (e.target.id === "fr-signin"){ $("acct-in").click(); return; }''')
# highlight the item from the link you just opened
rep('''      return `<article class="frdeck" data-id="${esc(r.id)}">
        <div class="frhead"><div><h3>♥''',
    '''      return `<article class="frdeck${r.share_token === frFocus ? " new" : ""}" data-id="${esc(r.id)}">
        <div class="frhead"><div><h3>♥''')
rep('''    return `<article class="frdeck" data-id="${esc(r.id)}">
      <div class="frhead"><div><h3>${esc(r.name)}</h3>''',
    '''    return `<article class="frdeck${r.share_token === frFocus ? " new" : ""}" data-id="${esc(r.id)}">
      <div class="frhead"><div><h3>${esc(r.name)}</h3>''')
rep('''section("Friends' Decks", decks, q ? "No shared decks match this search." : "No one has shared a deck yet.");
  section("Wish Lists", wishes, q ? "No shared wish lists match this search." : "No one has shared a wish list yet.");''',
    '''section("Friends' Decks", decks, q ? "No shared decks match this search." : "No deck links saved yet.");
  section("Wish Lists", wishes, q ? "No shared wish lists match this search." : "No wish list links saved yet.");''')

# ---------- opening a link: save it, show it in Friends, tidy the address bar
rep('''syncControls(); render(); showTab(["collection","packs","decks","friends","wish"].includes(st.tab) ? st.tab : "collection"); connect(); cloudInit(); showAcct();''',
    '''syncControls(); render(); showTab(["collection","packs","decks","friends","wish"].includes(st.tab) ? st.tab : "collection"); connect(); cloudInit(); showAcct();
function openSharedFromURL(){
  const t = tokenFrom(location.hash); if (!t) return;
  addLink(t, true);
  try { history.replaceState(null, "", location.pathname + location.search); } catch(e){}
  showTab("friends");
  renderFriends().then(() => { const a = document.querySelector(".frdeck.new"); if (a) a.scrollIntoView({block: "start", behavior: "smooth"}); });
}
openSharedFromURL();
addEventListener("hashchange", openSharedFromURL);''')

# ---------- styles
_i = h.rfind("</style>"); h = h[:_i] + """.linkrow{display:flex;gap:8px;align-items:center}
.linkrow input{flex:1;min-width:0;background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:9px 11px;font:inherit;font-size:14px;color:var(--fg)}
#share-done{display:grid;gap:12px}
#share-done h2{font-family:var(--display);font-size:19px;margin:0}
#share-done .msg{font-size:13.5px;min-height:1.2em}
#share-done .msg.err{color:var(--warn)}
#share{max-width:min(520px,calc(100vw - 32px))}
.frdeck.new{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent) inset}
.frdead{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:8px 0 0;color:var(--warn)}
#share-done .msg:empty{display:none}
#fr-add-msg:empty{display:none}
""" + h[_i:]

open(out, "w", encoding="utf-8").write(h)
print("patch_links: ok ->", out)
