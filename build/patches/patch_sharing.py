#!/usr/bin/env python3
"""Deck sharing for the website (needs accounts: run after patch_accounts.py, before patch_mobile.py).
- Deck checker: "Share with friends" on any deck (name friends see + optional contact); edits keep the shared copy
  up to date; "Stop sharing" removes it. Supabase table: shared_decks (see supabase_setup.sql).
- New "Friends' decks" tab: every shared deck, searchable by deck, player or card name, with what you already own
  and the cost to finish, plus "Copy to my decks". Signed-in people only.
Usage: patch_sharing.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:70]!r}, found {n}"
    h = h.replace(old, new)

# ---------- styles
rep("#auth .row{display:flex;", """.frbar{display:grid;gap:8px}
.frlist{display:grid;gap:10px}
.frdeck{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px;display:grid;gap:8px;min-width:0}
.frdeck h3{font-family:var(--display);font-size:16px;margin:0;overflow-wrap:anywhere}
.frhead{display:flex;justify-content:space-between;gap:8px;align-items:flex-start;flex-wrap:wrap}
.frhead .meta b{color:var(--fg)}
.frstats{display:flex;gap:6px 14px;flex-wrap:wrap;font-size:13.5px;color:var(--muted)}
.frstats b{color:var(--fg);font-variant-numeric:tabular-nums}
.frmatch{font-size:13px;color:var(--accent)}
.frbody{display:grid;gap:2px;border-top:1px solid var(--line);padding-top:8px}
.frbody h4{font-size:12px;text-transform:uppercase;letter-spacing:.1em;color:var(--accent);margin:8px 0 2px}
.frrow{display:flex;gap:8px;align-items:baseline;font-size:14px;flex-wrap:wrap}
.frrow .q{font-family:var(--display);min-width:2.2em;font-variant-numeric:tabular-nums}
.frrow .ok{color:var(--ok);font-size:12.5px} .frrow .no{color:var(--warn);font-size:12.5px}
#share label{display:grid;gap:4px;font-size:14px;color:var(--muted)}
#share input{background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:10px 12px;font:inherit;color:var(--fg)}
#share{border:1px solid var(--line);border-radius:12px;background:var(--panel);color:var(--fg);padding:18px;max-width:min(420px,calc(100vw - 32px));width:100%}
#share::backdrop{background:rgb(5 6 10 / .78)}
#share form{display:grid;gap:12px}
#share h2{font-family:var(--display);font-size:19px;margin:0}
#share .msg{font-size:13.5px;min-height:1.2em}
#share .msg.err{color:var(--fury)}
#auth .row{display:flex;""")

# ---------- new tab + section + share dialog
rep('<button role="tab" id="t-decks" aria-selected="false" aria-controls="view-decks">Deck checker</button>',
    '<button role="tab" id="t-decks" aria-selected="false" aria-controls="view-decks">Deck checker</button>\n'
    '    <button role="tab" id="t-friends" aria-selected="false" aria-controls="view-friends">Friends\' decks</button>')
rep('<section class="view" id="view-decks" role="tabpanel" aria-labelledby="t-decks" hidden>',
    '''<section class="view" id="view-friends" role="tabpanel" aria-labelledby="t-friends" hidden>
    <div class="panel frbar">
      <h2>Friends' decks</h2>
      <p class="meta">Decks other players have chosen to share. Search by deck name, player, or a card you're looking to trade for. Each deck shows how many of its cards you already own.</p>
      <input class="search" id="fr-q" type="search" placeholder="Search decks, players or cards, e.g. Jinx" aria-label="Search shared decks" autocomplete="off">
      <span class="meta" id="fr-count" aria-live="polite"></span>
    </div>
    <div class="frlist" id="fr-list"></div>
  </section>

  <dialog id="share" aria-labelledby="share-title"><form id="share-form" novalidate>
    <h2 id="share-title">Share this deck</h2>
    <p class="meta">Anyone signed in to this site can see a deck you share, under the name below. Your email is never shown.</p>
    <label>Name friends will see <input id="share-name" maxlength="40" autocomplete="nickname" required></label>
    <label>How to reach you for trades (optional) <input id="share-contact" maxlength="80" placeholder="e.g. Discord: brandon#1234"></label>
    <p class="msg" id="share-msg" aria-live="polite"></p>
    <div class="frow"><button type="submit" class="btn primary" id="share-go">Share deck</button><button type="button" class="btn" id="share-x">Cancel</button></div>
  </form></dialog>

  <section class="view" id="view-decks" role="tabpanel" aria-labelledby="t-decks" hidden>''')

# ---------- tabs know about "friends"
n = h.count('["collection","packs","decks"]')
assert n == 3, n
h = h.replace('["collection","packs","decks"]', '["collection","packs","decks","friends"]')
rep('  if (t === "decks") renderDecks();\n  LS.set("rb-filters"', '  if (t === "decks") renderDecks();\n  if (t === "friends") renderFriends();\n  LS.set("rb-filters"')

# ---------- share button in the deck summary; keep the shared flag through edits
rep('      <button class="btn" id="dk-edit">Edit deck</button>',
    '      <button class="btn" id="dk-edit">Edit deck</button>\n      ${d.shared ? `<span class="tag ok">✓ Shared with friends</span><button class="btn" id="dk-unshare">Stop sharing</button>` : `<button class="btn" id="dk-share">Share with friends</button>`}')
rep('    const d = {id:editingId, name, sub: old.sub || "Your deck", text};',
    '    const d = {id:editingId, name, sub: old.sub || "Your deck", text, shared: !!old.shared};')
rep('''  if (e.target.id === "dk-edit"){''', '''  if (e.target.id === "dk-share") openShare();
  if (e.target.id === "dk-unshare"){ const d = customDecks.find(x => x.id === curDeck); if (d){ d.shared = false; saveDecks(); renderDecks(); } }
  if (e.target.id === "dk-edit"){''')
# every deck save also refreshes what's shared
rep('function saveDecks(){\n  LS.set("rb-decks", customDecks); LS.set("rb-deck", curDeck); cloudSave();',
    'function saveDecks(){\n  LS.set("rb-decks", customDecks); LS.set("rb-deck", curDeck); cloudSave(); syncShared();')

# ---------- sharing logic (inserted before start-up)
rep('syncControls(); render(); showTab(["collection","packs","decks","friends"].includes(st.tab) ? st.tab : "collection"); connect(); cloudInit(); showAcct();',
    r'''// ---- deck sharing (table "shared_decks": everyone signed in can read; only the owner can change their rows)
let shareProfile = LS.get("rb-share-profile") || {name:"", contact:""};
let shareTimer = null, frCache = null, frLoadedAt = 0, frOpen = new Set();
function openShare(){
  if (!cloudUser){ $("acct-in").click(); return; }
  $("share-name").value = shareProfile.name || ""; $("share-contact").value = shareProfile.contact || ""; $("share-msg").textContent = "";
  try { $("share").showModal(); } catch(e){ $("share").setAttribute("open", ""); }
  $("share-name").focus();
}
$("share-x").addEventListener("click", () => $("share").close());
$("share-form").addEventListener("submit", e => {
  e.preventDefault();
  const name = $("share-name").value.trim(), contact = $("share-contact").value.trim();
  if (!name){ $("share-msg").textContent = "Add the name friends will see."; $("share-msg").className = "msg err"; return; }
  shareProfile = {name, contact}; LS.set("rb-share-profile", shareProfile);
  const d = customDecks.find(x => x.id === curDeck); if (d) d.shared = true;
  $("share").close(); saveDecks(); renderDecks();
});
function syncShared(){
  if (!sb || !cloudUser) return;
  clearTimeout(shareTimer);
  shareTimer = setTimeout(() => { shareTimer = null; pushShared(); }, 900);
}
async function flushShared(){ if (shareTimer){ clearTimeout(shareTimer); shareTimer = null; await pushShared(); } }
async function pushShared(){
  {
    const me = cloudUser; if (!me || !sb) return;
    const mine = customDecks.filter(d => d.shared);
    if (mine.length && shareProfile.name){
      const rows = mine.map(d => ({ owner: me.id, deck_id: d.id, owner_name: shareProfile.name.slice(0, 40), contact: (shareProfile.contact || "").slice(0, 80) || null, name: String(d.name).slice(0, 80), list: String(d.text).slice(0, 8000), updated_at: new Date().toISOString() }));
      const { error } = await sb.from("shared_decks").upsert(rows, { onConflict: "owner,deck_id" });
      if (error) setSync("Couldn't update your shared decks. They'll retry on your next change.", "warn");
    }
    // remove anything you've stopped sharing or deleted
    const { data } = await sb.from("shared_decks").select("deck_id").eq("owner", me.id);
    const keep = new Set(mine.map(d => d.id)), gone = (data || []).map(r => r.deck_id).filter(id => !keep.has(id));
    if (gone.length) await sb.from("shared_decks").delete().eq("owner", me.id).in("deck_id", gone);
    frCache = null;
  }
}
// when you sign in on a new device, pick up the sharing name you used before
async function loadShareProfile(){
  if (!sb || !cloudUser || shareProfile.name) return;
  const me = cloudUser; if (!me) return;
  const { data } = await sb.from("shared_decks").select("owner_name, contact").eq("owner", me.id).limit(1);
  if (data && data[0]){ shareProfile = {name: data[0].owner_name, contact: data[0].contact || ""}; LS.set("rb-share-profile", shareProfile); }
}
async function renderFriends(){
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
  if (!cloudUser) return renderFriends();
  const q = norm($("fr-q").value || ""), words = q ? q.split(" ") : [];
  const items = frCache.map(r => {
    const deck = { name: r.name, text: r.list };
    const secs = parseDeck(r.list), rows = secs.flatMap(s => s.rows);
    const hay = norm(r.name + " " + r.owner_name) + " " + rows.map(x => x.key).join(" | ");
    const hits = words.length ? rows.filter(x => words.every(w => x.key.includes(w))) : [];
    const ok = !words.length || words.every(w => hay.includes(w));
    return { r, deck, secs, rows, hits, ok };
  }).filter(x => x.ok);
  $("fr-count").textContent = frCache.length ? `${items.length} of ${frCache.length} shared deck${frCache.length===1?"":"s"}` : "";
  if (!frCache.length){ list.innerHTML = `<div class="empty">Nobody has shared a deck yet. Open Deck checker and tap <b>Share with friends</b> on one of yours to be the first.</div>`; return; }
  if (!items.length){ list.innerHTML = `<div class="empty">No shared decks match "${esc($("fr-q").value)}". Try a different card or player name.</div>`; return; }
  list.innerHTML = items.map(({ r, deck, secs, rows, hits }) => {
    const s = deckStats(deck), mine = !!cloudUser && r.owner === cloudUser.id;
    const legendSec = secs.find(x => /legend/i.test(x.label)), legend = legendSec && legendSec.rows[0] ? legendSec.rows[0].name : "";
    const banned = new Set(rows.filter(x => (groups[x.key]||[]).some(c => c.ban === "std")).map(x => x.key)).size;
    const open = frOpen.has(r.id);
    const body = open ? `<div class="frbody">${s.secs.map(sec => `<h4>${esc(sec.label)}</h4>${sec.rows.map(x => `<div class="frrow"><span class="q">${x.q}×</span><span>${esc(x.name)}</span>${banPill((groups[x.key]||[]).find(c => c.ban))}<span class="${x.miss ? "no" : "ok"}">${x.miss ? `you have ${x.h}` : "✓ you have it"}</span></div>`).join("")}`).join("")}</div>` : "";
    return `<article class="frdeck" data-id="${esc(r.id)}">
      <div class="frhead"><div><h3>${esc(r.name)}</h3><span class="meta">by <b>${esc(r.owner_name)}</b>${r.contact ? ` · ${esc(r.contact)}` : ""} · updated ${esc(fmtDate(String(r.updated_at).slice(0,10)))}</span></div>${mine ? '<span class="tag ok">Your deck</span>' : ""}${banned ? `<span class="tag ban">⚠ ${banned} banned</span>` : ""}</div>
      <div class="frstats">${legend ? `<span>Legend: <b>${esc(legend)}</b></span>` : ""}<span>You own <b>${s.have} / ${s.need}</b></span><span>${s.need - s.have ? `<b>${esc(money(s.cost))}</b> to finish` : "<b>You own every card</b>"}</span></div>
      ${hits.length ? `<div class="frmatch">Includes ${hits.slice(0, 4).map(x => `${x.q}× ${esc(x.name)}`).join(", ")}${hits.length > 4 ? "…" : ""}</div>` : ""}
      <div class="frow"><button class="btn" data-act="toggle">${open ? "Hide list" : "Show list"}</button>${mine ? "" : '<button class="btn" data-act="copy">Copy to my decks</button>'}<span class="meta" data-msg aria-live="polite"></span></div>
      ${body}
    </article>`;
  }).join("");
}
let frT; $("fr-q").addEventListener("input", () => { clearTimeout(frT); frT = setTimeout(renderFriends, 150); });
$("fr-list").addEventListener("click", e => {
  if (e.target.id === "fr-signin"){ $("acct-in").click(); return; }
  const b = e.target.closest("button[data-act]"); if (!b) return;
  const art = b.closest(".frdeck"), id = art.dataset.id, r = (frCache || []).find(x => x.id === id); if (!r) return;
  if (b.dataset.act === "toggle"){ frOpen.has(id) ? frOpen.delete(id) : frOpen.add(id); renderFriends(); }
  if (b.dataset.act === "copy"){
    customDecks.push({ id: "d" + Date.now().toString(36), name: `${r.name} (${r.owner_name})`.slice(0, 80), sub: `Copied from ${r.owner_name}`, text: r.list });
    saveDecks(); art.querySelector("[data-msg]").textContent = "Copied. It's in Deck checker now.";
  }
});
sb_onSignedIn = () => { loadShareProfile(); frCache = null; if (st.tab === "friends") renderFriends(); };
syncControls(); render(); showTab(["collection","packs","decks","friends"].includes(st.tab) ? st.tab : "collection"); connect(); cloudInit(); showAcct();''')

rep("  counts = {}; customDecks = []; LS.set(\"rb-counts\", counts); LS.set(\"rb-decks\", customDecks);",
    "  counts = {}; customDecks = []; LS.set(\"rb-counts\", counts); LS.set(\"rb-decks\", customDecks);\n  shareProfile = {name:\"\", contact:\"\"}; LS.set(\"rb-share-profile\", shareProfile); frCache = null; frOpen.clear();")

# hook: refresh sharing bits when someone signs in or out
rep("let sb = null, cloudUser = null,", "let sb_onSignedIn = () => {};\nlet sb = null, cloudUser = null,")
rep("    if (u && changed){ cloudReady = false; cloudLoad(); }",
    "    if (u && changed){ cloudReady = false; cloudLoad(); sb_onSignedIn(); }\n    if (!u && st.tab === \"friends\") renderFriends();")

rep("try { await cloudFlush(); } catch(e){}", "try { await cloudFlush(); await flushShared(); } catch(e){}")

open(out, "w", encoding="utf-8").write(h)
print("ok", len(h))
