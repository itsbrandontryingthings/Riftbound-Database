#!/usr/bin/env python3
"""My Decks workspace (website; runs last, after patch_share_tidy.py).
- Deck header: rename in place, cards collected + progress, Show all / Hide cards I have, List or Grid at S-M-L,
  Include sideboard, tiles (deck value, cost to finish, cards to buy, biggest buys), deck rule checks
  (when the deck has a Legend), cards by set, and Copy decklist / shopping list.
- Every card: tap Need − / + to change how many the deck runs (rewrites the decklist; 0 or ✕ removes it) and tap
  I have 0…N. "I have" is your collection (any printing counts) and tapping it changes your collection: copies
  are added as the printing the deck prices (cheapest), and taken away from that printing first, then regular
  printings, then the cheapest others, so a pricey alt art you own is the last to go.
- Add a card: type a name (suggestions from every card), pick a section or let it choose by card type.
Usage: patch_decks_ui.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

# ---------- intro: mention the new controls
rep('''        <li><b>Tournament legality</b>: any banned card is flagged.</li>
      </ul>''',
    '''        <li><b>Tournament legality</b>: any banned card is flagged, and decks with a Legend are checked against the deck rules.</li>
        <li><b>Make it yours</b>: tap <b>Need</b> to change how many of a card the deck runs, tap <b>I have</b> to update your collection (it's the same count you see in Collection), add or remove cards, and switch between list and grid at S, M or L size.</li>
      </ul>''')

# ---------- replace the deck renderer (everything from renderDecks up to the deck-tab click handler)
start = h.index("function renderDecks(){\n  const decks = allDecks();")
end = h.index('$("deck-tabs").addEventListener("click"', start)
assert h.count("function renderDecks(){") == 1
h = h[:start] + r'''// ---- My Decks workspace
const m1 = v => FX && st.cur === "both" ? cad(v) : money(v);
const deckKind = key => { const c = (groups[key] || [])[0]; return !c ? "unknown" : c.type === "Legend" ? "legend" : c.type === "Rune" ? "rune" : c.type === "Battlefield" ? "battlefield" : "card"; };
const deckToText = secs => secs.filter(s => s.rows.length).map(s => `${s.label}:\n` + s.rows.map(r => `${r.q} ${r.name}`).join("\n")).join("\n\n");
function dkStats(d){
  const left = {};
  const secs = parseDeck(d.text).map((s, si) => ({label: s.label, si, side: isSide(s), rows: s.rows.map((r, ri) => {
    const known = !!groups[r.key], cheap = cheapestOf(r.key), show = cheap || (groups[r.key] || [])[0] || null;
    if (!(r.key in left)) left[r.key] = ownedOf(r.key);
    const hv = Math.min(r.q, left[r.key]); left[r.key] -= hv;
    return {...r, si, ri, known, cheap, show, h: hv, miss: r.q - hv, kind: deckKind(r.key)};
  })}));
  const counted = secs.filter(s => withSide || !s.side);
  let need = 0, have = 0, cost = 0, value = 0, unknown = 0;
  for (const s of counted) for (const r of s.rows){ need += r.q; have += r.h; if (!r.known) unknown++; if (r.cheap){ value += r.q * r.cheap.price; cost += r.miss * r.cheap.price; } }
  return {secs, counted, need, have, cost, value, unknown};
}
function dkChecks(S){
  const rows = S.secs.flatMap(s => s.rows.map(r => ({...r, side: s.side}))), sum = a => a.reduce((n, r) => n + r.q, 0);
  const legends = rows.filter(r => !r.side && r.kind === "legend");
  if (!legends.length) return null;
  const main = rows.filter(r => !r.side && (r.kind === "card" || r.kind === "unknown")), mainN = sum(main);
  const runes = sum(rows.filter(r => !r.side && r.kind === "rune"));
  const bfs = rows.filter(r => !r.side && r.kind === "battlefield"), bfN = sum(bfs), bfDiff = new Set(bfs.map(r => r.key)).size;
  const copies = {}; rows.filter(r => r.kind === "card").forEach(r => { copies[r.key] = (copies[r.key] || 0) + r.q; });
  const over = Object.keys(copies).filter(k => copies[k] > 3).map(k => groups[k][0].name);
  const doms = (groups[legends[0].key][0].domains || []), domSet = new Set(doms);
  const off = new Set(rows.filter(r => r.known && (r.kind === "card" || r.kind === "rune") && (groups[r.key][0].domains || []).some(x => !domSet.has(x))).map(r => r.key)).size;
  const banned = new Set(rows.filter(r => (groups[r.key] || []).some(c => c.ban === "std")).map(r => r.key)).size;
  const side = sum(rows.filter(r => r.side)), nLeg = sum(legends);
  const out = [
    {ok: nLeg === 1, t: nLeg === 1 ? "1 Legend" : `${nLeg} Legends (a deck has 1)`},
    {ok: mainN === 40, t: `${mainN}-card main deck` + (mainN === 40 ? "" : " (needs 40)")},
    {ok: !over.length, t: over.length ? `More than 3 copies: ${over.join(", ")}` : "Max 3 copies of any card"},
    {ok: runes === 12, t: `${runes} rune${runes === 1 ? "" : "s"}` + (runes === 12 ? "" : " (needs 12)")},
    {ok: bfN === 3 && bfDiff === 3, t: bfN === 3 && bfDiff === 3 ? "3 different battlefields" : `${bfN} battlefield${bfN === 1 ? "" : "s"}${bfDiff !== bfN ? `, ${bfDiff} different` : ""} (needs 3 different)`}
  ];
  if (doms.length) out.push({ok: !off, t: off ? `${off} card${off === 1 ? " isn't" : "s aren't"} ${doms.join(" or ")}` : `Every card is ${doms.join(" or ")}`});
  out.push({ok: !banned, t: banned ? `${banned} banned card${banned === 1 ? "" : "s"}` : "No banned cards"});
  if (side) out.push({info: true, t: `Sideboard: ${side} card${side === 1 ? "" : "s"}`});
  return {list: out, mainN};
}
// the deck you're looking at, as a deck you can change (a built-in deck is copied into your decks first)
function editableDeck(){
  let d = customDecks.find(x => x.id === curDeck);
  if (!d){ const b = allDecks().find(x => x.id === curDeck); if (!b) return null; d = {...b, sub: b.sub || "Your deck"}; customDecks.push(d); }
  return d;
}
function dkHaveCtl(r, grid){
  const lab = `<span class="dk-lab" title="Your collection: any printing counts. Tapping changes your collection.">I have</span>`;
  if (r.q <= 4) return `${lab}<span class="dk-have" role="group" aria-label="Copies of ${esc(r.name)} you have">${Array.from({length: r.q + 1}, (_, n) => `<button data-act="have" data-n="${n}" aria-pressed="${n === r.h}">${n}</button>`).join("")}</span>${grid ? "" : `<span class="meta">of ${r.q}</span>`}`;
  return `${lab}<span class="step" role="group" aria-label="Copies of ${esc(r.name)} you have"><button data-act="haveStep" data-d="-1" aria-label="One fewer" ${r.h ? "" : "disabled"}>−</button><output>${r.h}</output><button data-act="haveStep" data-d="1" aria-label="One more" ${r.h < r.q ? "" : "disabled"}>+</button></span><span class="meta">of ${r.q}</span>`;
}
function dkNeedCtl(r){
  return `<span class="dk-lab">Need</span><span class="step" role="group" aria-label="Copies of ${esc(r.name)} the deck needs"><button data-act="need" data-d="-1" aria-label="Need one fewer">−</button><output>${r.q}</output><button data-act="need" data-d="1" aria-label="Need one more">+</button></span>`;
}
function dkStatus(r){
  if (!r.known) return `<span class="unk">Not found in the database. Check the spelling.</span>`;
  return r.miss ? `<span class="dk-buy">buy ${r.miss}${r.cheap ? " · " + esc(m1(r.miss * r.cheap.price)) : ""}</span>` : `<span class="dk-got">got all ${r.q}</span>`;
}
function dkRowHTML(r, view, size){
  const c = r.show, dom = c && c.domains && c.domains[0] ? `--dc:var(--${c.domains[0].toLowerCase()})` : "";
  const thumb = c ? thumbHTML(c, view === "grid" ? (PHONE() && size === "s" ? 480 : 744) : (size === "s" ? 160 : 744)) : '<span class="thumb none" aria-hidden="true">No<br>image</span>';
  const name = r.cheap ? `<a href="${tcgURL(r.cheap)}" target="_blank" rel="noopener" title="Open ${esc(r.name)} on TCGplayer">${esc(c.name)}</a>` : esc(c ? c.name : r.name);
  const kind = c ? c.type + (c.champ ? " · Champion" : "") : "";
  const set = c ? `<span class="dk-set" style="--sc:var(--${(setCol[c.set] || "line")})">${esc(setName[c.set] || c.set)} · ${esc(codeOf(c))}</span>` : "";
  const ban = c ? banPill((groups[r.key] || []).find(x => x.ban)) : "";
  const price = r.cheap ? `<span class="dk-price"><b>${esc(m1(r.q * r.cheap.price))}</b>${FX && st.cur === "both" ? `<small>${esc(usd(r.q * r.cheap.price))}</small>` : ""}<small>${esc(m1(r.cheap.price))} ea</small></span>` : "";
  const ctl = `<div class="dk-ctl"><span class="dk-pair">${dkNeedCtl(r)}</span><span class="dk-pair">${r.known ? dkHaveCtl(r, view === "grid") : ""}</span></div>`;
  const rm = `<button class="dk-rm" data-act="rm" aria-label="Remove ${esc(r.name)} from this deck" title="Remove from this deck">✕</button>`;
  if (view === "grid") return `<div class="card tile dk-tile${r.miss ? "" : " done"}" data-s="${r.si}" data-r="${r.ri}" style="${dom}">${thumb}${c && (groups[r.key] || []).some(x => x.ban === "std") ? '<span class="tban">BANNED</span>' : ""}${rm}
    <span class="tname">${name}</span><div class="tsub"><b class="dk-q">${r.q}×</b> ${set || esc(r.name)}</div><div class="dk-st">${dkStatus(r)}${price}</div>${ctl}</div>`;
  return `<div class="dk-card${r.miss ? "" : " done"}" data-s="${r.si}" data-r="${r.ri}" style="${dom}">${thumb}
    <div class="dk-main"><div class="dk-top"><span class="name">${name}</span>${rm}</div>
      <div class="dk-sub"><span class="dk-q">${r.q}× <span>${esc(kind)}</span></span>${set}${ban}</div>
      <div class="dk-st">${dkStatus(r)}${price}</div>${ctl}</div></div>`;
}
const setCol = {VEN: "chaos", UNL: "fury", SFD: "mind", OGN: "body", OGS: "body", OPP: "order", PR: "order", JDG: "order"};
function renderDecks(){
  const decks = allDecks();
  if (!decks.length){
    $("deck-tabs").innerHTML = ""; $("deck-body").innerHTML = "";
    $("deck-summary").innerHTML = `<h2>No Decks Yet</h2><p class="meta">Paste a decklist below to see which cards you already own, what's missing, and what it would cost to finish. Your decks are private: nobody else who opens this page can see them.</p>`;
    $("deck-add").open = true; return;
  }
  if (!decks.find(d => d.id === curDeck)) curDeck = decks[0].id;
  $("deck-tabs").innerHTML = decks.map(d => { const s = dkStats(d); return `<button data-d="${esc(d.id)}" aria-pressed="${d.id===curDeck}"><b>${esc(d.name)}</b><small>${s.have}/${s.need} copies · ${s.need-s.have ? esc(money(s.cost))+" to finish" : "complete"}</small></button>`; }).join("");
  const d = decks.find(x => x.id === curDeck), S = dkStats(d), pct = S.need ? S.have / S.need * 100 : 0, custom = customDecks.some(x => x.id === d.id), isBuiltin = BUILTIN.some(b => b.id === d.id);
  const view = st.dview === "grid" ? "grid" : "list", size = ["s","m","l"].includes(st.size) ? st.size : "m", hide = !!st.dhide;
  const checks = dkChecks(S), all = S.counted.flatMap(s => s.rows);
  const buys = all.filter(r => r.miss && r.cheap).sort((a, b) => b.miss * b.cheap.price - a.miss * a.cheap.price);
  const buyCopies = all.reduce((a, r) => a + (r.known ? r.miss : 0), 0), buyKinds = new Set(all.filter(r => r.miss && r.known).map(r => r.key)).size;
  const top = buys.slice(0, 2), topShare = S.cost ? Math.round(top.reduce((a, r) => a + r.miss * r.cheap.price, 0) / S.cost * 100) : 0;
  const bySet = {}; all.forEach(r => { if (r.show) bySet[r.show.set] = (bySet[r.show.set] || 0) + r.q; });
  const banned = new Set(all.filter(r => (groups[r.key] || []).some(x => x.ban === "std")).map(r => r.key)).size;
  const legal = checks && checks.list.every(c => c.ok || c.info);
  const mainRows = all.filter(r => r.kind === "card" || r.kind === "unknown"), mainHave = mainRows.reduce((a, r) => a + r.h, 0);
  $("deck-summary").innerHTML = `<div class="eyebrow">Deck Workspace ${S.have === S.need && S.need ? '<span class="tag ok">✓ You own every card</span>' : ""}${checks ? (legal ? '<span class="tag ok">✓ Meets the deck rules</span>' : '<span class="tag warn">Doesn\'t meet the deck rules yet</span>') : ""}${banned ? `<span class="tag ban">⚠ ${banned} banned card${banned===1?"":"s"}: not tournament legal</span>` : ""}</div>
    <input class="dk-title" id="dk-rename" value="${esc(d.name)}" maxlength="80" aria-label="Deck name (tap to rename)" title="Tap to rename this deck">
    <div class="dk-prog"><span class="collect-k">Cards collected</span><span class="dk-big"><b>${S.have}</b> / ${S.need}</span><span class="meta">${S.need - S.have ? `${S.need - S.have} to go` : "complete"}${checks ? ` · main deck ${mainHave}/${checks.mainN}` : ""}</span></div>
    <div class="bar" role="progressbar" aria-label="Deck completion" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round(pct)}"><i style="width:${pct}%"></i></div>
    <div class="dk-tiles">
      <div class="dk-stat"><span class="collect-k">Full deck value</span><span class="v">${moneyHTML(S.value)}</span><small>Every card at its cheapest printing</small></div>
      <div class="dk-stat"><span class="collect-k">Cost to finish</span><span class="v${S.cost ? " warn" : ""}">${moneyHTML(S.cost)}</span><small>You have ${S.have} of ${S.need} cards</small></div>
      <div class="dk-stat"><span class="collect-k">Cards to buy</span><span class="v">${buyCopies}</span><small>${buyCopies ? `cop${buyCopies===1?"y":"ies"} across ${buyKinds} different card${buyKinds===1?"":"s"}` : "Nothing left to buy"}</small></div>
      <div class="dk-stat"><span class="collect-k">Biggest buys</span><span class="v sm">${top.length ? top.map(r => `${esc(r.name.split(/,|\s[-–—]\s/)[0].trim())} ${esc(m1(r.miss * r.cheap.price))}`).join(" · ") : "None"}</span><small>${top.length && S.cost ? `About ${topShare}% of what's left to spend` : "You own every priced card"}</small></div>
    </div>
    ${checks ? `<div class="dk-checks">${checks.list.map(c => `<span class="${c.info ? "info" : c.ok ? "ok" : "no"}">${c.info ? "" : c.ok ? "✓ " : "✗ "}${esc(c.t)}</span>`).join("")}</div>` : `<p class="meta">Add a Legend to this deck to check it against the deck rules (40-card main deck, 12 runes, 3 battlefields, up to 3 copies, Legend's domains).</p>`}
    ${Object.keys(bySet).length ? `<div class="dk-sets"><span>Cards by set:</span>${Object.entries(bySet).sort((a, b) => b[1] - a[1]).map(([k, n]) => `<span class="s" style="--sc:var(--${setCol[k] || "line"})">${esc(setName[k] || k)} ${n}</span>`).join("")}</div>` : ""}
    <div class="frow">
      <button class="btn" id="dk-copylist">Copy decklist</button>
      <button class="btn" id="dk-copy">Copy shopping list</button>
      <button class="btn" id="dk-edit">Edit list as text</button>
      ${d.shared ? `<span class="tag ok">✓ Shared by link</span><button class="btn" id="dk-link">Copy share link</button><button class="btn" id="dk-unshare">Stop sharing</button>` : `<button class="btn" id="dk-share">Share with friends</button>`}
      ${custom ? `<button class="btn danger" id="dk-del">${armDelete ? (isBuiltin ? "Tap again to restore the original list" : "Tap again to delete this deck") : (isBuiltin ? "Restore original list" : "Delete deck")}</button>` : ""}
    </div>
    <p class="meta">"I have" is your collection: any printing of a card counts, and tapping a number adds or removes copies in Collection too. New copies are added as the printing shown on the card. "Cost to finish" uses the cheapest printing of each missing card.${S.unknown ? ` ${S.unknown} card name${S.unknown===1?" isn't":"s aren't"} in the database, marked below.` : ""}</p>`;
  const gridCls = `list grid dkg${size !== "s" ? " sz-" + size : ""}`;
  const secOpts = S.secs.map(s => `<option value="${s.si}">${esc(s.label)}</option>`).join("");
  const tools = `<div class="dk-tools" role="toolbar" aria-label="How to show this deck's cards">
      <div class="seg" role="group" aria-label="Which cards to show"><button id="dk-all" aria-pressed="${!hide}">Show all cards</button><button id="dk-hide" aria-pressed="${hide}">Hide cards I have</button></div>
      <div class="seg sizeseg" role="group" aria-label="Card size"><button id="dks-s" aria-pressed="${size==="s"}" title="Small cards">S</button><button id="dks-m" aria-pressed="${size==="m"}" title="Medium cards">M</button><button id="dks-l" aria-pressed="${size==="l"}" title="Large cards">L</button></div>
      <div class="seg" role="group" aria-label="Layout"><button id="dkv-list" aria-pressed="${view==="list"}">List</button><button id="dkv-grid" aria-pressed="${view==="grid"}">Grid</button></div>
      <label class="chk"><input type="checkbox" id="dk-side" ${withSide?"checked":""}> Include sideboard</label>
    </div>`;
  $("deck-body").innerHTML = tools + S.counted.map(sec => {
    const sh = sec.rows.reduce((a, r) => a + r.h, 0), sn = sec.rows.reduce((a, r) => a + r.q, 0), rows = hide ? sec.rows.filter(r => r.miss || !r.known) : sec.rows;
    return `<section class="dk-sec"><div class="dk-sh"><h3>${esc(sec.label)}</h3><span class="dk-cnt${sh === sn ? " ok" : ""}" title="Copies you have / copies in this section">${sh}/${sn}</span></div>
      ${rows.length ? `<div class="${view === "grid" ? gridCls : "dkl dkl-" + size}">${rows.map(r => dkRowHTML(r, view, size)).join("")}</div>` : `<p class="meta dk-alldone">✓ You have ${sn === 1 ? "the 1 card" : `all ${sn} cards`} in this section.</p>`}</section>`;
  }).join("") + `<form class="panel dk-addc" id="dk-addc" novalidate><b>Add a Card</b>
      <input class="search" id="dk-addn" list="dk-names" placeholder="Card name, e.g. Gust" aria-label="Card name" autocomplete="off">
      <select id="dk-adds" aria-label="Section"><option value="auto">Best section for the card</option>${secOpts}</select>
      <input id="dk-addq" type="number" min="1" max="12" value="1" inputmode="numeric" aria-label="Copies">
      <button class="btn primary" id="dk-addgo">Add</button><span class="meta" id="dk-addmsg" aria-live="polite"></span></form>`;
  if (!$("dk-names")) document.body.insertAdjacentHTML("beforeend", `<datalist id="dk-names">${Object.values(groups).map(g => `<option value="${esc(g[0].name)}">`).join("")}</datalist>`);
}
function saveDeckView(){ LS.set("rb-filters", {...st, doms:[...st.doms], limit:undefined}); renderDecks(); }
$("deck-summary").addEventListener("change", e => {
  if (e.target.id !== "dk-rename") return;
  const v = e.target.value.trim(), d = editableDeck(); if (!d) return;
  if (!v){ e.target.value = d.name; return; }
  d.name = v.slice(0, 80); saveDecks(); renderDecks();
});
$("deck-summary").addEventListener("keydown", e => { if (e.target.id === "dk-rename" && e.key === "Enter") e.target.blur(); });
$("deck-summary").addEventListener("click", e => {
  const id = e.target.id;
  const d = allDecks().find(x => x.id === curDeck); if (!d) return;
  if (id === "dk-copylist") copy(d.text, "decklist");
});
// "I have" changes your collection: add as the deck's printing; remove that printing first, then regular
// printings, then the cheapest others (so an expensive alt art you own is the last to go)
function collectionChange(row, delta){
  if (!delta || !row.known) return;
  const base = row.show;
  if (delta > 0){ adjust(base.id, delta); }
  else {
    let left = -delta;
    const order = (groups[row.key] || []).filter(c => counts[c.id]).sort((a, b) => (b === base) - (a === base) || (!!a.variant) - (!!b.variant) || (a.price ?? 1e9) - (b.price ?? 1e9));
    for (const c of order){ if (!left) break; const take = Math.min(left, counts[c.id]); adjust(c.id, -take); left -= take; }
  }
  renderDecks();
}
$("deck-body").addEventListener("click", e => {
  const id = e.target.id;
  if (id === "dk-all" || id === "dk-hide"){ st.dhide = id === "dk-hide"; saveDeckView(); return; }
  if (/^dks-[sml]$/.test(id)){ st.size = id.slice(4); saveDeckView(); return; }
  if (id === "dkv-list" || id === "dkv-grid"){ st.dview = id === "dkv-grid" ? "grid" : "list"; saveDeckView(); return; }
  const b = e.target.closest("button[data-act]"); if (!b) return;
  const el = b.closest("[data-s]"), d = el && editableDeck(); if (!d) return;
  const si = +el.dataset.s, ri = +el.dataset.r, secs = parseDeck(d.text), sec = secs[si], r = sec && sec.rows[ri]; if (!r) return;
  const row = dkStats(d).secs[si].rows[ri], act = b.dataset.act;
  if (act === "have" || act === "haveStep"){
    const n = Math.max(0, Math.min(row.q, act === "have" ? +b.dataset.n : row.h + +b.dataset.d));
    collectionChange(row, n - row.h); return;
  }
  if (act === "need" || act === "rm"){
    r.q = act === "rm" ? 0 : Math.max(0, Math.min(99, r.q + +b.dataset.d));
    if (!r.q) sec.rows.splice(ri, 1);
    d.text = deckToText(secs); delete d.own;
  }
  saveDecks(); renderDecks();
});
$("deck-body").addEventListener("change", e => { if (e.target.id === "dk-side"){ withSide = e.target.checked; LS.set("rb-side", withSide); renderDecks(); } });
$("deck-body").addEventListener("submit", e => {
  if (e.target.id !== "dk-addc") return;
  e.preventDefault();
  const d = editableDeck(); if (!d) return;
  const name = $("dk-addn").value.trim(), key = norm(name), q = Math.max(1, Math.min(12, Math.floor(+$("dk-addq").value || 1))), msg = $("dk-addmsg");
  if (!groups[key]){ msg.textContent = name ? "Couldn't find that card. Pick a name from the suggestions." : "Type a card name first."; return; }
  const secs = parseDeck(d.text), kind = deckKind(key), pick = $("dk-adds").value;
  let sec = pick !== "auto" ? secs[+pick] : null;
  if (!sec){
    const want = {legend: /legend/i, rune: /rune/i, battlefield: /battlefield/i}[kind];
    sec = want ? secs.find(s => want.test(s.label)) : secs.find(s => !/legend|champion|rune|battlefield|side/i.test(s.label));
    if (!sec){ sec = {label: {legend: "Legend", rune: "Runes", battlefield: "Battlefields"}[kind] || "Main deck", rows: []}; secs.push(sec); }
  }
  const realName = groups[key][0].name, ex = sec.rows.find(r => r.key === key);
  if (ex) ex.q += q; else sec.rows.push({name: realName, q, key});
  d.text = deckToText(secs); saveDecks(); renderDecks();
  $("dk-addmsg").textContent = `Added ${q} ${realName} to ${sec.label}.`;
});
''' + h[end:]

# the old summary click handler still covers copy shopping list, edit, delete and sharing; the old dk-side change
# handler still covers the sideboard checkbox.

# ---------- styles
_i = h.rfind("</style>"); h = h[:_i] + """.dk-title{width:100%;min-width:0;background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:9px 12px;font-family:var(--display);font-size:24px;font-weight:700;color:var(--fg)}
.dk-title:hover{border-color:var(--muted)}
.dk-prog{display:flex;gap:6px 12px;align-items:baseline;flex-wrap:wrap}
.dk-big{font-family:var(--display);font-size:26px;font-weight:600;font-variant-numeric:tabular-nums}
.dk-big b{color:var(--ok)}
.dk-tools{display:flex;flex-wrap:wrap;gap:8px 10px;align-items:center;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin:14px 0 4px}
.dk-tiles{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}
@media (max-width:900px){.dk-tiles{grid-template-columns:repeat(2,minmax(0,1fr))}}
.dk-stat{background:var(--row);border:1px solid var(--line);border-radius:10px;padding:10px 12px;display:grid;gap:2px;align-content:start;min-width:0}
.dk-stat .v{font-family:var(--display);font-size:24px;font-weight:600;font-variant-numeric:tabular-nums;line-height:1.2;overflow-wrap:anywhere}
.dk-stat .v .alt{display:block;font-family:var(--body-font);font-size:13px;font-weight:500;color:var(--muted)}
.dk-stat .v.warn{color:var(--warn)}
.dk-stat .v.sm{font-size:17px}
.dk-stat small{color:var(--muted);font-size:12.5px}
.dk-checks{display:flex;flex-wrap:wrap;gap:4px 16px;font-size:13.5px}
.dk-checks .ok{color:var(--ok)} .dk-checks .no{color:var(--warn)} .dk-checks .info{color:var(--muted)}
.dk-sets{display:flex;flex-wrap:wrap;gap:6px;align-items:center;font-size:13px;color:var(--muted)}
.dk-sets .s{border:1px solid var(--line);border-left:3px solid var(--sc);border-radius:4px;padding:1px 8px;color:var(--fg)}
.dk-sec{display:grid;gap:8px;margin-top:8px}
.dk-sh{display:flex;justify-content:space-between;align-items:center;gap:8px;border-bottom:1px solid var(--line);padding-bottom:5px}
.dk-sh h3{font-size:12.5px;text-transform:uppercase;letter-spacing:.12em;color:var(--accent);margin:0;font-family:var(--body-font)}
.dk-cnt{font-family:var(--display);font-size:13px;border:1px solid var(--line);border-radius:6px;padding:1px 8px;font-variant-numeric:tabular-nums}
.dk-cnt.ok{color:var(--ok);border-color:color-mix(in srgb,var(--ok) 45%,var(--line))}
.dk-alldone{color:var(--ok);margin:0}
.dkl{display:grid;gap:8px;grid-template-columns:repeat(auto-fill,minmax(min(100%,330px),1fr))}
.dkl.dkl-m{grid-template-columns:repeat(auto-fill,minmax(min(100%,420px),1fr))}
.dkl.dkl-l{grid-template-columns:repeat(auto-fill,minmax(min(100%,540px),1fr))}
.dk-card{display:grid;grid-template-columns:56px minmax(0,1fr);gap:10px;align-items:start;background:var(--row);border:1px solid var(--line);border-left:4px solid var(--dc,var(--line));border-radius:10px;padding:8px 10px;min-width:0}
.dkl-m .dk-card{grid-template-columns:104px minmax(0,1fr);padding:10px 12px}
.dkl-l .dk-card{grid-template-columns:180px minmax(0,1fr);gap:14px;padding:12px 14px}
.dk-card.done,.dk-tile.done{background:var(--panel)}
.dk-card.done .name a,.dk-tile.done .tname a{color:var(--muted)}
.dk-main{display:grid;gap:6px;min-width:0}
.dk-top{display:flex;justify-content:space-between;align-items:flex-start;gap:8px}
.dk-top .name{font-weight:600;font-size:15px;overflow-wrap:anywhere}
.dkl-m .dk-top .name{font-size:16.5px} .dkl-l .dk-top .name{font-size:19px}
.dk-card .name a,.dk-tile .tname a{color:var(--fg);text-decoration:none}
.dk-card .name a:hover,.dk-tile .tname a:hover{text-decoration:underline;text-decoration-color:var(--accent)}
.dk-sub{display:flex;flex-wrap:wrap;gap:4px 8px;align-items:center;font-size:12.5px;color:var(--muted)}
.dk-q{font-family:var(--display);font-size:14px;color:var(--accent)} .dk-q span{font-family:var(--body-font);font-size:12.5px;color:var(--muted)}
.dk-set{border:1px solid var(--line);border-left:3px solid var(--sc);border-radius:4px;padding:0 6px;color:var(--fg);font-size:12px;line-height:18px;white-space:nowrap}
.dk-st{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;justify-content:space-between}
.dk-buy{color:var(--warn);border:1px solid color-mix(in srgb,var(--warn) 55%,var(--line));border-radius:999px;padding:0 9px;font-size:12.5px;line-height:20px;white-space:nowrap}
.dk-got{color:var(--ok);border:1px solid color-mix(in srgb,var(--ok) 45%,var(--line));border-radius:999px;padding:0 9px;font-size:12.5px;line-height:20px;white-space:nowrap}
.dk-price{display:grid;justify-items:end;font-variant-numeric:tabular-nums;line-height:1.2}
.dk-price b{font-family:var(--display);font-size:15px}
.dk-price small{font-size:11.5px;color:var(--muted)}
.dk-ctl{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center}
.dk-pair{display:inline-flex;gap:6px;align-items:center}
.dk-lab{font-size:12.5px;color:var(--muted)}
.dk-lab i{font-style:normal;color:var(--accent);margin-left:2px}
.dk-ctl .step button{width:32px;height:32px}
.dk-have{display:inline-flex;gap:4px}
.dk-have button{min-width:32px;height:32px;padding:0 6px;border:1px solid var(--line);border-radius:7px;background:var(--bg);color:var(--muted);font-family:var(--display);font-size:15px;font-variant-numeric:tabular-nums}
.dk-have button:hover{color:var(--fg);border-color:var(--muted)}
.dk-have button[aria-pressed="true"]{background:var(--ok);border-color:var(--ok);color:var(--bg);font-weight:700}
.dk-rm{background:none;border:1px solid transparent;border-radius:6px;width:28px;height:28px;flex:none;color:var(--muted);font-size:14px;line-height:1}
.dk-rm:hover{color:var(--fury);border-color:var(--fury)}
.dk-tile{border-left:4px solid var(--dc,var(--line))}
.dk-tile .dk-rm{position:absolute;top:10px;right:10px;z-index:1;background:rgb(0 0 0 / .72);color:#fff;border-color:transparent}
.dk-tile .tsub .dk-set{border:0;padding:0;font-size:inherit;color:inherit}
.dk-tile .dk-ctl{flex-direction:column;align-items:stretch;gap:6px}
.dk-tile .dk-pair{flex-direction:column;align-items:stretch;gap:3px}
.dk-tile .step{justify-content:space-between}
.dk-tile .dk-have{display:grid;grid-template-columns:repeat(auto-fit,minmax(26px,1fr));gap:4px}
.dk-tile .dk-have button{min-width:0;height:30px;padding:0;font-size:14px}
.dk-tile .dk-st{gap:4px}
.dk-addc{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:10px}
.dk-addc b{font-family:var(--display);flex-basis:100%}
.dk-addc .search{flex:1 1 220px;min-width:0}
.dk-addc select,.dk-addc input[type=number]{background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:9px 10px;color:var(--fg)}
.dk-addc input[type=number]{width:70px}
#dk-addmsg{flex-basis:100%}
#dk-addmsg:empty{display:none}
@media (max-width:640px){
  .dk-title{font-size:20px}
  .dkl-m .dk-card{grid-template-columns:84px minmax(0,1fr)}
  .dkl-l .dk-card{grid-template-columns:1fr}
  .dkl-l .dk-card .thumb{max-width:260px;justify-self:center}
  .dk-stat .v{font-size:19px}
}
""" + h[_i:]

open(out, "w", encoding="utf-8").write(h)
print("patch_decks_ui: ok ->", out)
