#!/usr/bin/env python3
"""Token type filter + wish list. Run LAST (after patch_mobile.py) on the website and the local copy.
- Type dropdown gets "Token" (tokens are stored as Unit/Gear with a token flag)
- ♡ Want on every card (list rows and grid tiles); new "Wish list" tab with quantities, what you own, total cost
- Website extras (only if accounts/sharing are present): wish list saves to the account (collections.wish,
  falls back to this browser if that column doesn't exist yet) and can be shared; friends' wish lists show in the
  Friends tab (stored in shared_decks with deck_id "__wish__") and are searchable by card.
Usage: patch_wish.py in.html out.html"""
import sys, re

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()
WEB = "function cloudSave()" in h
SHARE = "function renderFriends()" in h

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:70]!r}, found {n}"
    h = h.replace(old, new)

# ---------- Token type filter
rep('types.forEach(t => $("type").insertAdjacentHTML("beforeend", `<option value="${esc(t)}">${esc(t)}</option>`));',
    'types.forEach(t => $("type").insertAdjacentHTML("beforeend", `<option value="${esc(t)}">${esc(t)}</option>`));\n'
    '$("type").insertAdjacentHTML("beforeend", `<option value="__token">Token</option>`);')
rep('  if (st.type && c.type !== st.type) return false;',
    '  if (st.type === "__token" ? !c.token : (st.type && c.type !== st.type)) return false;')

# ---------- styles
rep(".more{justify-self:center}", """.more{justify-self:center}
.wishbtn{background:none;border:1px solid var(--line);border-radius:4px;padding:0 7px;line-height:20px;font-size:12.5px;font-weight:600;color:var(--muted);white-space:nowrap}
.wishbtn:hover{color:var(--fg);border-color:var(--muted)}
.wishbtn[aria-pressed="true"]{color:#ff7a90;border-color:color-mix(in srgb,#ff7a90 55%,var(--line));background:color-mix(in srgb,#ff7a90 12%,transparent)}
.wishbtn.over{position:absolute;top:10px;right:10px;z-index:2;width:30px;height:30px;padding:0;border-radius:999px;font-size:16px;line-height:28px;background:rgb(10 12 18 / .72);border-color:transparent;color:#fff}
.wishbtn.over[aria-pressed="true"]{color:#ff7a90;background:rgb(10 12 18 / .85)}
.wsum{display:flex;gap:12px 32px;flex-wrap:wrap;align-items:flex-end}
.wlist{display:grid;gap:4px}
.wrow{display:grid;grid-template-columns:52px minmax(0,1fr) auto auto;gap:10px;align-items:center;background:var(--row);border:1px solid var(--line);border-radius:8px;padding:6px 10px}
.wrow .own{font-size:12.5px;color:var(--muted);white-space:nowrap}
.wrow .own.ok{color:var(--ok)}
.wrow .rm{background:none;border:1px solid var(--line);border-radius:6px;padding:4px 10px;color:var(--muted);font-size:13px}
.wrow .rm:hover{color:var(--fury);border-color:var(--fury)}
.tile .rm{background:none;border:1px solid var(--line);border-radius:6px;padding:4px 10px;color:var(--muted);font-size:13px}
.tile .rm:hover{color:var(--fury);border-color:var(--fury)}
.tile .own{font-size:12px;color:var(--muted)} .tile .own.ok{color:var(--ok)}
@media (max-width:640px){.wrow{grid-template-columns:44px minmax(0,1fr) auto}.wrow .wq{grid-column:2/4;justify-self:start;display:flex;gap:10px;align-items:center;flex-wrap:wrap}}""")

# ---------- state
rep('counts = LS.get("rb-counts") || {};',
    'counts = LS.get("rb-counts") || {};\n'
    'let wish = LS.get("rb-wish") || {};          // card id -> copies wanted; wish._shared = shared with friends\n'
    'const wishIds = () => Object.keys(wish).filter(k => k[0] !== "_" && wish[k] > 0);\n'
    'function saveWish(){ LS.set("rb-wish", wish); if (typeof cloudSave === "function") cloudSave(); if (typeof syncShared === "function") syncShared(); }\n'
    'function wishBtn(c, over){ const on = !!wish[c.id]; return `<button class="wishbtn${over ? " over" : ""}" data-wish="${esc(c.id)}" aria-pressed="${on}" title="${on ? "On your wish list (tap to remove)" : "Add to your wish list"}" aria-label="${on ? "Remove " + esc(c.name) + " from" : "Add " + esc(c.name) + " to"} your wish list">${on ? "♥" : "♡"}${over ? "" : (on ? " Wanted" : " Want")}</button>`; }')

# ---------- ♡ on list rows and grid tiles
rep('${banPill(c)}${viewLink(c)}</span></div>\n    <div class="right">',
    '${banPill(c)}${viewLink(c)}${wishBtn(c)}</span></div>\n    <div class="right">')
rep('${thumbHTML(c, PHONE() && st.size === "s" ? 480 : 744)}',
    '${thumbHTML(c, PHONE() && st.size === "s" ? 480 : 744)}${wishBtn(c, true)}')

# ---------- Wish list tab
tabs_old = re.search(r'<button role="tab" id="t-decks"[^\n]*\n', h).group(0)
rep(tabs_old, tabs_old + '    <button role="tab" id="t-wish" aria-selected="false" aria-controls="view-wish">Wish list</button>\n')
rep('<section class="view" id="view-decks" role="tabpanel" aria-labelledby="t-decks" hidden>',
    '''<section class="view" id="view-wish" role="tabpanel" aria-labelledby="t-wish" hidden>
    <div class="panel" id="wish-summary"></div>
    <div class="wlist" id="wish-list"></div>
  </section>

  <section class="view" id="view-decks" role="tabpanel" aria-labelledby="t-decks" hidden>''')
n = 0
for arr in ('["collection","packs","decks","friends"]', '["collection","packs","decks"]'):
    c = h.count(arr)
    if c:
        h = h.replace(arr, arr[:-1] + ',"wish"]'); n += c
assert n == 3, n
rep('  if (t === "decks") renderDecks();\n', '  if (t === "decks") renderDecks();\n  if (t === "wish") renderWish();\n')

share_btn = ('${typeof openShare === "function" ? (wish._shared ? `<span class="tag ok">✓ Shared with friends</span><button class="btn" id="wish-unshare">Stop sharing</button>` : `<button class="btn" id="wish-share">Share with friends</button>`) : ""}'
             if SHARE else "")
rep("let shown = [];", r'''function renderWish(){
  const ids = wishIds().filter(id => byId[id]).sort((a, b) => CARDS.indexOf(byId[a]) - CARDS.indexOf(byId[b]));
  const copies = ids.reduce((a, id) => a + wish[id], 0);
  const cost = ids.reduce((a, id) => a + wish[id] * (byId[id].price || 0), 0);
  const unpriced = ids.filter(id => byId[id].price == null).length;
  const wv = st.wview === "grid" || st.wview === "list" ? st.wview : (st.view === "grid" ? "grid" : "list");
  $("wish-summary").innerHTML = `<h2>Wish list</h2>
    <div class="wsum">
      <div class="vbox"><span class="collect-k">Cards wanted</span><span class="vmid">${ids.length} <small class="meta">(${copies} cop${copies === 1 ? "y" : "ies"})</small></span></div>
      <div class="vbox"><span class="collect-k">Cost to buy</span><span class="vbig">${moneyHTML(cost)}</span></div>
    </div>
    <div class="frow"><span class="meta">${ids.length ? "TCGplayer market prices" + (unpriced ? ` · ${unpriced} card${unpriced === 1 ? " has" : "s have"} no price yet` : "") : "Tap ♡ Want on any card in Collection to add it here, even if it's not in one of your decks."}</span><span style="flex:1"></span>
      ${ids.length ? `<div class="seg" role="group" aria-label="Wish list layout"><button id="wv-list" aria-pressed="${wv === "list"}">List</button><button id="wv-grid" aria-pressed="${wv === "grid"}">Grid</button></div><button class="btn" id="wish-copy">Copy wish list</button>` : ""}''' + share_btn + r'''</div>`;
  $("wish-list").className = wv === "grid" ? "list grid" + (st.size && st.size !== "s" ? " sz-" + st.size : "") : "wlist";
  $("wish-list").innerHTML = ids.map(id => { const c = byId[id], q = wish[id], have = counts[id] || 0;
    if (wv === "grid") return `<div class="card tile" data-id="${esc(id)}">${thumbHTML(c, PHONE() && st.size === "s" ? 480 : 744)}${c.ban ? `<span class="tban">${c.ban === "2v2" ? "2v2 BAN" : "BANNED"}</span>` : ""}
      <a class="tname" href="${tcgURL(c)}" target="_blank" rel="noopener" title="Open ${esc(c.name)} on TCGplayer">${esc(c.name)}</a>
      <div class="tsub"><span class="r-${c.rarity}">${esc(codeOf(c))}</span>${c.variant ? ` · ${esc(c.variant)}` : ""}</div>
      <div class="tsub"><span class="own${have ? " ok" : ""}">${have ? `you own ${have}` : "you don't own it"}</span></div>
      <div class="tfoot">${priceHTML(c, q)}<div class="step" role="group" aria-label="Copies of ${esc(c.name)} wanted"><button data-w="-1" aria-label="Want one fewer">−</button><output>${q}</output><button data-w="1" aria-label="Want one more">+</button></div>
      <button class="rm" data-w="rm" aria-label="Remove ${esc(c.name)} from your wish list">Remove</button></div></div>`;
    return `<div class="wrow" data-id="${esc(id)}">${thumbHTML(c, 160)}
      <span class="info"><span class="name"><a href="${tcgURL(c)}" target="_blank" rel="noopener">${esc(c.name)}</a></span><span class="sub"><span class="r-${c.rarity}">${esc(codeOf(c))}</span>${c.variant ? `<span class="pill var">${esc(c.variant)}</span>` : ""}${banPill(c)}<span class="own${have ? " ok" : ""}">${have ? `you own ${have}` : "you don't own it"}</span></span></span>
      <span class="wq">${priceHTML(c, q)}<span class="step" role="group" aria-label="Copies of ${esc(c.name)} wanted"><button data-w="-1" aria-label="Want one fewer">−</button><output>${q}</output><button data-w="1" aria-label="Want one more">+</button></span></span>
      <button class="rm" data-w="rm" aria-label="Remove ${esc(c.name)} from your wish list">Remove</button></div>`; }).join("");
}
function wishText(){
  return wishIds().filter(id => byId[id]).map(id => { const c = byId[id]; return `${wish[id]} ${c.name} [${codeOf(c)}${c.variant ? ` · ${c.variant}` : ""}]`; }).join("\n");
}
$("wish-list").addEventListener("click", e => {
  const b = e.target.closest("button[data-w]"); if (!b) return;
  const id = b.closest("[data-id]").dataset.id;
  if (b.dataset.w === "rm") delete wish[id]; else { const q = (wish[id] || 0) + Number(b.dataset.w); if (q > 0) wish[id] = q; else delete wish[id]; }
  saveWish(); renderWish();
});
// the enlarged card view must not live inside a tab: opened from a hidden tab it was invisible but blocked every click
document.body.appendChild($("lb"));
$("wish-summary").addEventListener("click", e => {
  if (e.target.id === "wv-list" || e.target.id === "wv-grid"){ st.wview = e.target.id === "wv-grid" ? "grid" : "list"; LS.set("rb-filters", {...st, doms:[...st.doms], limit:undefined}); renderWish(); return; }
  if (e.target.id === "wish-copy"){ const ids = wishIds().filter(id => byId[id]); copy(wishText() + `\n\nTotal: ${money(ids.reduce((a, id) => a + wish[id] * (byId[id].price || 0), 0))}`, "wish list"); }
  if (e.target.id === "wish-share" && typeof openShare === "function") openShare("wish");
  if (e.target.id === "wish-unshare"){ delete wish._shared; saveWish(); renderWish(); }
});
// ♡ / ♥ on any card
document.addEventListener("click", e => {
  const b = e.target.closest("button[data-wish]"); if (!b) return;
  e.preventDefault(); e.stopPropagation();
  const id = b.dataset.wish;
  if (wish[id]) delete wish[id]; else wish[id] = 1;
  saveWish();
  document.querySelectorAll(`button[data-wish="${CSS.escape(id)}"]`).forEach(x => { x.outerHTML = wishBtn(byId[id], x.classList.contains("over")); });
  if (st.tab === "wish") renderWish();
}, true);
let shown = [];''')

# the main refresh also refreshes the wish list tab (sign-in load, restore, currency switch)
rep('if (st.tab === "decks") renderDecks(); if (st.tab === "packs") renderPack();', 'if (st.tab === "decks") renderDecks(); if (st.tab === "packs") renderPack(); if (st.tab === "wish") renderWish();')

# ---------- backup code carries the wish list
rep('JSON.stringify({v:1, counts, decks:customDecks})', 'JSON.stringify({v:1, counts, decks:customDecks, wish})')
rep('  customDecks = Array.isArray(data.decks) ? data.decks.filter(d => d && d.name && d.text) : [];',
    '  customDecks = Array.isArray(data.decks) ? data.decks.filter(d => d && d.name && d.text) : [];\n'
    '  wish = {}; if (data.wish && typeof data.wish === "object") for (const [k, v] of Object.entries(data.wish)) if (byId[k] && v > 0) wish[k] = Math.floor(v);\n'
    '  LS.set("rb-wish", wish);')

if WEB:
    # saved with the account; works before the "wish" column exists (falls back to this browser)
    rep('let sb = null, cloudUser = null,', 'let noWishCol = false;\nconst cloudRow = me => Object.assign({ id: me.id, counts, decks: customDecks, updated_at: new Date().toISOString() }, noWishCol ? {} : { wish });\nlet sb = null, cloudUser = null,')
    rep('    const { error } = await sb.from("collections").upsert({ id: me.id, counts, decks: customDecks, updated_at: new Date().toISOString() });',
        '    let { error } = await sb.from("collections").upsert(cloudRow(me));\n'
        '    if (error && !noWishCol && /wish/i.test(error.message || "")){ noWishCol = true; ({ error } = await sb.from("collections").upsert(cloudRow(me))); }')
    rep('  await sb.from("collections").upsert({ id: cloudUser.id, counts, decks: customDecks, updated_at: new Date().toISOString() });',
        '  await sb.from("collections").upsert(cloudRow(cloudUser));')
    rep('  const { data, error } = await sb.from("collections").select("counts, decks").eq("id", cloudUser.id).maybeSingle();',
        '  let { data, error } = await sb.from("collections").select(noWishCol ? "counts, decks" : "counts, decks, wish").eq("id", cloudUser.id).maybeSingle();\n'
        '  if (error && !noWishCol && /wish/i.test(error.message || "")){ noWishCol = true; ({ data, error } = await sb.from("collections").select("counts, decks").eq("id", cloudUser.id).maybeSingle()); }')
    rep('    counts = data.counts || {}; customDecks = Array.isArray(data.decks) ? data.decks : [];',
        '    counts = data.counts || {}; customDecks = Array.isArray(data.decks) ? data.decks : [];\n'
        '    if (!noWishCol && data.wish && typeof data.wish === "object"){ wish = data.wish; LS.set("rb-wish", wish); }')
    rep('  counts = {}; customDecks = []; LS.set("rb-counts", counts); LS.set("rb-decks", customDecks);',
        '  counts = {}; customDecks = []; wish = {}; LS.set("rb-counts", counts); LS.set("rb-decks", customDecks); LS.set("rb-wish", wish);')

if SHARE:
    rep('<p class="note">🔒 Everything you enter is saved only in your own browser. Nobody else, including whoever shared this link with you, can see your cards or decks.</p>',
        '<p class="note">🔒 Your cards, decks and wish list are private. They save to your account when you\'re signed in, or in this browser when you\'re not. Only decks and wish lists you choose to share are visible, and only to people signed in to this site.</p>')
    # share dialog serves decks and the wish list
    rep('function openShare(){', 'let shareTarget = "deck";\nfunction openShare(target){\n  shareTarget = target === "wish" ? "wish" : "deck";\n  $("share-title").textContent = shareTarget === "wish" ? "Share your wish list" : "Share this deck";')
    rep('  const d = customDecks.find(x => x.id === curDeck); if (d) d.shared = true;\n  $("share").close(); saveDecks(); renderDecks();',
        '  if (shareTarget === "wish"){ wish._shared = true; $("share").close(); saveWish(); renderWish(); return; }\n'
        '  const d = customDecks.find(x => x.id === curDeck); if (d) d.shared = true;\n  $("share").close(); saveDecks(); renderDecks();')
    rep('if (e.target.id === "dk-share") openShare();', 'if (e.target.id === "dk-share") openShare("deck");')
    rep('    const mine = customDecks.filter(d => d.shared);',
        '    const mine = customDecks.filter(d => d.shared).concat(wish._shared && wishIds().length ? [{ id: "__wish__", name: "Wish list", text: wishText() }] : []);')
    # Friends tab shows wish lists too
    rep('''<button role="tab" id="t-friends" aria-selected="false" aria-controls="view-friends">Friends' decks</button>''',
        '''<button role="tab" id="t-friends" aria-selected="false" aria-controls="view-friends">Friends</button>''')
    rep("<h2>Friends' decks</h2>", "<h2>Friends' decks and wish lists</h2>")
    rep("Decks other players have chosen to share. Search by deck name, player, or a card you're looking to trade for. Each deck shows how many of its cards you already own.",
        "Decks and wish lists other players have chosen to share. Search by deck name, player, or a card you're looking to trade for. Decks show how many of their cards you own; wish lists show which wanted cards you could trade.")
    rep('placeholder="Search decks, players or cards, e.g. Jinx"', 'placeholder="Search decks, wish lists, players or cards, e.g. Jinx"')
    rep('`${items.length} of ${frCache.length} shared deck${frCache.length===1?"":"s"}`', '`${items.length} of ${frCache.length} shared list${frCache.length===1?"":"s"}`')
    rep('  list.innerHTML = items.map(({ r, deck, secs, rows, hits }) => {',
        r'''  list.innerHTML = items.map(({ r, deck, secs, rows, hits }) => {
    if (r.deck_id === "__wish__"){
      const mine = r.owner === (cloudUser && cloudUser.id), open = frOpen.has(r.id);
      const canGive = rows.filter(x => ownedOf(x.key) > 0);
      const body = open ? `<div class="frbody">${rows.map(x => { const own = ownedOf(x.key); return `<div class="frrow"><span class="q">${x.q}×</span><span>${esc(x.name)}</span>${banPill((groups[x.key]||[]).find(c => c.ban))}<span class="${own ? "ok" : "no"}">${own ? `✓ you have ${own}` : "you don't have it"}</span></div>`; }).join("")}</div>` : "";
      return `<article class="frdeck" data-id="${esc(r.id)}">
        <div class="frhead"><div><h3>♥ ${esc(r.owner_name)}'s wish list</h3><span class="meta">${r.contact ? esc(r.contact) + " · " : ""}updated ${esc(fmtDate(String(r.updated_at).slice(0,10)))}</span></div>${mine ? '<span class="tag ok">Your wish list</span>' : ""}</div>
        <div class="frstats"><span>Wants <b>${rows.length}</b> card${rows.length === 1 ? "" : "s"}</span><span>${canGive.length ? `You have <b>${canGive.length}</b> of them to trade` : "You don't have any of them yet"}</span></div>
        ${hits.length ? `<div class="frmatch">Wants ${hits.slice(0, 4).map(x => `${x.q}× ${esc(x.name)}`).join(", ")}${hits.length > 4 ? "…" : ""}</div>` : ""}
        <div class="frow"><button class="btn" data-act="toggle">${open ? "Hide list" : "Show list"}</button></div>
        ${body}
      </article>`;
    }''')

open(out, "w", encoding="utf-8").write(h)
print("ok", len(h), "web" if WEB else "", "share" if SHARE else "")
