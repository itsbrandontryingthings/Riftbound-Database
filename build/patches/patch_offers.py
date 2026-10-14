#!/usr/bin/env python3
"""Offers on shared shopping lists (website; runs last, after patch_shop.py). Needs supabase_offers.sql.
- Friends view of a shopping list: each card shows its set and market price (cheapest printing). A viewer ticks
  "I have this", picks how many (up to what the list needs) and their price for each (starts at market price, in
  CAD unless they view prices in USD), adds their name and sends the offer (RPC make_offer; works signed out).
- Shopping List tab (owner): an Offers panel with who sent each offer, the cards, their price next to market price
  and the total; "Got them: add to my collection" adds the cards and clears the offer; "Remove offer" deletes it.
  The tab shows how many offers are waiting.
Usage: patch_offers.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

# ---------- owner: offers panel in the Shopping List tab
rep('''    <div class="panel" id="shop-summary"></div>''', '''    <div class="panel" id="shop-summary"></div>
    <div id="shop-offers"></div>''')
# the owner's grid tiles name the set too
rep('''<span class="tname">${name}</span><div class="tsub">${esc(codeOf(c))}</div><div class="dk-st">${status}</div>${decks}''',
    '''<span class="tname">${name}</span><div class="tsub">${esc(setName[c.set] || c.set)} · ${esc(codeOf(c))}</div><div class="dk-st">${status}</div>${decks}''')
rep('''  $("shop-body").innerHTML = tools + (items.length''', '''  renderOffers(); loadOffers();
  $("shop-body").innerHTML = tools + (items.length''')

rep('''function saveDeckView(){''', r'''// ---- offers on your shared shopping list (table shop_offers: only you can read or remove offers on your lists)
let offers = null, offersAt = 0, offersOff = false, offersBusy = false, offerArm = "";
const offerCur = () => FX && st.cur !== "usd" ? "CAD" : "USD";
const fmtOffer = (v, cur) => cur === "CAD" ? "CA " + fCAD.format(v || 0) : "US " + fUSD.format(v || 0);
const marketIn = (c, cur) => c && c.price != null ? Math.round((cur === "CAD" ? c.price * FX : c.price) * 100) / 100 : null;
async function loadOffers(force){
  if (!sb || !cloudUser){ offers = null; showOfferBadge(); return; }
  if (offersBusy || (!force && offers && Date.now() - offersAt < 60000)) return;
  offersBusy = true;
  const me = cloudUser, { data, error } = await sb.from("shop_offers").select("id, from_name, items, currency, total, created_at").order("created_at", { ascending: false }).limit(100);
  offersBusy = false; if (cloudUser !== me) return;
  if (error){ offersOff = /shop_offers|relation|does not exist|schema cache|permission/i.test(error.message || ""); offers = []; }
  else { offersOff = false; offers = data || []; }
  offersAt = Date.now(); showOfferBadge(); if (st.tab === "shop") renderOffers();
}
function showOfferBadge(){
  const n = offers ? offers.length : 0;
  $("t-shop").innerHTML = `Shopping List${n ? `<span class="fcount" title="${n} offer${n === 1 ? "" : "s"} waiting">${n}</span>` : ""}`;
}
function offerHTML(o){
  const cur = o.currency === "USD" ? "USD" : "CAD", items = Array.isArray(o.items) ? o.items : [], n = items.reduce((a, i) => a + (+i.q || 0), 0);
  return `<article class="of-card" data-offer="${esc(o.id)}">
    <div class="of-top"><div><b class="of-from">${esc(o.from_name)}</b> <span class="meta">sent ${esc(fmtDate(String(o.created_at).slice(0, 10)))}</span></div><span class="of-sum">${n} card${n === 1 ? "" : "s"} · <b>${esc(fmtOffer(+o.total || 0, cur))}</b></span></div>
    <div class="of-items">${items.map(i => { const key = norm(i.name), c = frCard(key), mk = marketIn(cheapestOf(key), cur);
      return `<div class="frrow"${c ? ` data-card="${esc(c.id)}"` : ""}>${frThumb(key)}<span class="q">${+i.q || 0}×</span><span class="frn">${esc(i.name)}<span class="of-sub">${c ? `<span class="dk-set" style="--sc:var(--${setCol[c.set] || "line"})">${esc(setName[c.set] || c.set)} · ${esc(codeOf(c))}</span>` : ""}${mk != null ? `<span class="of-mkt">market ${esc(fmtOffer(mk, cur))}</span>` : ""}</span></span><span class="of-each">${esc(fmtOffer(+i.price || 0, cur))} each</span></div>`; }).join("")}</div>
    <div class="frow"><button class="btn primary" data-ofa="accept" title="Adds these cards to your collection and removes the offer">Got them: add to my collection</button><button class="btn" data-ofa="dismiss">${offerArm === o.id ? "Tap again to remove" : "Remove offer"}</button><span class="meta" data-ofmsg aria-live="polite"></span></div>
  </article>`;
}
function renderOffers(){
  const box = $("shop-offers");
  if (!cloudUser || (!shopP().shared && !(offers && offers.length))){ box.innerHTML = ""; return; }
  if (offersOff){ box.innerHTML = `<div class="panel of-panel"><h3 class="of-h">Offers</h3><p class="meta">Offers need a quick database update before friends can send them. The site owner has the steps.</p></div>`; return; }
  if (!offers){ box.innerHTML = ""; return; }
  box.innerHTML = `<div class="panel of-panel"><div class="of-hrow"><h3 class="of-h">Offers <small>${offers.length}</small></h3><button class="btn" id="of-refresh">Check for new offers</button></div>
    ${offers.length ? offers.map(offerHTML).join("") : `<p class="meta">No offers yet. When a friend opens your shopping list link, they can tick the cards they have, set a price and send you an offer. It shows up here with their name.</p>`}</div>`;
}
$("shop-offers").addEventListener("click", async e => {
  if (e.target.id === "of-refresh"){ e.target.disabled = true; await loadOffers(true); return; }
  const a = e.target.closest("[data-ofa]");
  if (!a){ const row = e.target.closest(".frrow[data-card]"); if (row) openCard(byId[row.dataset.card]); return; }
  const card = a.closest("[data-offer]"), id = card.dataset.offer, o = (offers || []).find(x => x.id === id); if (!o) return;
  if (a.dataset.ofa === "dismiss" && offerArm !== id){ offerArm = id; renderOffers(); return; }
  if (a.dataset.ofa === "accept") for (const i of (Array.isArray(o.items) ? o.items : [])){ const key = norm(i.name), c = cheapestOf(key) || (groups[key] || [])[0]; if (c && +i.q > 0) adjust(c.id, Math.min(99, +i.q)); }
  a.disabled = true;
  const { error } = await sb.from("shop_offers").delete().eq("id", id);
  offerArm = "";
  if (error){ card.querySelector("[data-ofmsg]").textContent = "Couldn't remove the offer. Check your connection and try again."; a.disabled = false; return; }
  offers = offers.filter(x => x.id !== id); showOfferBadge(); renderShop();
});

// ---- making an offer on a friend's shopping list (Friends tab)
const offerSt = {};   // share token -> {sel: {card key: {q, price}}, name, msg}
const offerOf = tok => offerSt[tok] ||= { sel: {}, name: LS.get("rb-offer-name") || "", msg: "" };
const offerTotal = S => Object.values(S.sel).reduce((a, p) => a + p.q * (parseFloat(p.price) || 0), 0);
function frShopBody(r, rows, mine){
  const S = offerOf(r.share_token), cur = offerCur();
  const lines = rows.map(x => {
    const c = frCard(x.key), cheap = cheapestOf(x.key), own = ownedOf(x.key), pick = !mine && S.sel[x.key], mk = marketIn(cheap, cur);
    const set = c ? `<span class="dk-set" style="--sc:var(--${setCol[c.set] || "line"})">${esc(setName[c.set] || c.set)} · ${esc(codeOf(c))}</span>` : "";
    const ctl = mine || !groups[x.key] ? "" : `<div class="of-ctl"><label class="of-pick"><input type="checkbox" data-of="pick" ${pick ? "checked" : ""}> I have this</label>${pick ? `
      <span class="step" role="group" aria-label="How many ${esc(x.name)} you're offering"><button type="button" data-of="q" data-d="-1" aria-label="One fewer" ${pick.q > 1 ? "" : "disabled"}>−</button><output>${pick.q}</output><button type="button" data-of="q" data-d="1" aria-label="One more" ${pick.q < x.q ? "" : "disabled"}>+</button></span>
      <label class="of-price">${cur === "CAD" ? "CA $" : "US $"}<input type="text" inputmode="decimal" data-of="price" value="${esc(pick.price)}" aria-label="Your price for each ${esc(x.name)}"> each</label>` : ""}</div>`;
    return `<div class="frrow of-row${pick ? " on" : ""}" data-key="${esc(x.key)}" data-need="${x.q}"${frCardAttr(x.key)}>${frThumb(x.key)}<span class="q">${x.q}×</span><span class="frn">${esc(x.name)}<span class="of-sub">${set}${mk != null ? `<span class="of-mkt">${esc(fmtOffer(mk, cur))} each</span>` : '<span class="of-mkt">no price</span>'}</span></span><span class="${own ? "ok" : "no"}">${own ? `✓ you have ${own}` : "you don't have it"}</span>${ctl}</div>`;
  }).join("");
  const n = Object.keys(S.sel).length;
  const foot = mine ? `<p class="meta">This is your shopping list. Offers friends send show up in your Shopping List tab.</p>`
    : `<div class="of-foot"><label class="of-name">Your name <input data-of="name" maxlength="40" value="${esc(S.name)}" autocomplete="nickname" placeholder="So they know who it's from"></label>
        <span class="of-total" data-of-total>${n ? `${n} card${n === 1 ? "" : "s"} · <b>${esc(fmtOffer(offerTotal(S), cur))}</b>` : "Tick the cards you have to make an offer."}</span>
        <button type="button" class="btn primary" data-of="send" ${n ? "" : "disabled"}>Send offer</button>
        <p class="msg${S.ok ? " ok" : ""}" data-of-msg aria-live="polite">${esc(S.msg || "")}</p></div>`;
  return `<div class="frbody of-body" data-tok="${esc(r.share_token)}">${mine ? "" : `<p class="meta of-help">Have some of these? Tick <b>I have this</b>, choose how many and your price for each, add your name and send your offer. Only the owner of this list sees it.</p>`}${lines}${foot}</div>`;
}
function offerFoot(body){
  const S = offerOf(body.dataset.tok), n = Object.keys(S.sel).length, t = body.querySelector("[data-of-total]");
  if (t) t.innerHTML = n ? `${n} card${n === 1 ? "" : "s"} · <b>${esc(fmtOffer(offerTotal(S), offerCur()))}</b>` : "Tick the cards you have to make an offer.";
}
$("fr-list").addEventListener("change", e => {
  if (e.target.dataset.of !== "pick") return;
  const body = e.target.closest(".of-body"), row = e.target.closest(".of-row"), S = offerOf(body.dataset.tok), key = row.dataset.key, need = +row.dataset.need;
  if (e.target.checked) S.sel[key] = { q: Math.min(need, Math.max(1, ownedOf(key))), price: (marketIn(cheapestOf(key), offerCur()) ?? 0).toFixed(2) };
  else delete S.sel[key];
  S.msg = ""; S.ok = false; renderFriends();
});
$("fr-list").addEventListener("input", e => {
  const of = e.target.dataset.of; if (of !== "price" && of !== "name") return;
  const body = e.target.closest(".of-body"), S = offerOf(body.dataset.tok);
  if (of === "name") S.name = e.target.value;
  else { const p = S.sel[e.target.closest(".of-row").dataset.key]; if (p) p.price = e.target.value; offerFoot(body); }
});
$("fr-list").addEventListener("click", async e => {
  const b = e.target.closest("button[data-of]"); if (!b) return;
  const body = b.closest(".of-body"), tok = body.dataset.tok, S = offerOf(tok);
  if (b.dataset.of === "q"){ const row = b.closest(".of-row"), p = S.sel[row.dataset.key]; if (p){ p.q = Math.max(1, Math.min(+row.dataset.need, p.q + +b.dataset.d)); renderFriends(); } return; }
  if (b.dataset.of !== "send") return;
  const name = S.name.trim(), msg = body.querySelector("[data-of-msg]"), say = (t, ok) => { S.msg = t; S.ok = !!ok; msg.textContent = t; msg.className = "msg" + (ok ? " ok" : " err"); };
  const items = Object.entries(S.sel).map(([key, p]) => ({ name: (groups[key] || [])[0] ? groups[key][0].name : key, q: p.q, price: Math.round((parseFloat(String(p.price).replace(/[^0-9.]/g, "")) || 0) * 100) / 100 }));
  if (!name){ say("Add your name so they know who the offer is from."); body.querySelector('[data-of="name"]').focus(); return; }
  if (!items.length){ say("Tick at least one card you have."); return; }
  if (items.some(i => !(i.price >= 0) || i.price > 999999)){ say("Check your prices: each needs to be a number, like 2.50."); return; }
  if (!sb){ say("Couldn't connect. Check your connection and try again."); return; }
  b.disabled = true; say("Sending your offer…", true);
  const { error } = await sb.rpc("make_offer", { p_token: tok, p_name: name.slice(0, 40), p_items: items, p_currency: offerCur() });
  if (error){
    const m = error.message || "";
    say(/make_offer|function/i.test(m) && !/busy|link|item|name/i.test(m) ? "Offers aren't switched on yet. They need a quick database update." : /busy/.test(m) ? "This list has had a lot of offers in the last hour. Try again later." : /link/.test(m) ? "This shopping list isn't shared any more." : "Couldn't send your offer. Check your connection and try again.");
    b.disabled = false; return;
  }
  LS.set("rb-offer-name", name); S.sel = {}; S.msg = `Offer sent. They'll see it with your name, ${name}.`; S.ok = true; renderFriends();
});
function saveDeckView(){''')

# ---------- friends: a shopping list's body is the offer form
rep('''      const body = open ? `<div class="frbody">${rows.map(x => { const own = ownedOf(x.key);''',
    '''      const body = shop ? (open ? frShopBody(r, rows, mine) : "") : open ? `<div class="frbody">${rows.map(x => { const own = ownedOf(x.key);''')
rep('''<div class="frow"><button class="btn" data-act="toggle">${open ? "Hide list" : "Show list"}</button><button class="btn" data-act="forget">Remove from Friends</button></div>
        ${body}''',
    '''<div class="frow"><button class="btn${shop && !mine && !open ? " primary" : ""}" data-act="toggle">${open ? "Hide list" : shop && !mine ? "Show list and make an offer" : "Show list"}</button><button class="btn" data-act="forget">Remove from Friends</button></div>
        ${body}''')
# typing or ticking in the offer form must not open the card preview
rep('''if (!row || e.target.closest("a, button")) return;''', '''if (!row || e.target.closest("a, button, input, label, .of-ctl")) return;''')

# ---------- offers follow sign-in / sign-out
rep('''sb_onSignedIn = () => { loadShareProfile(); loadShareTokens();''', '''sb_onSignedIn = () => { loadShareProfile(); loadShareTokens(); loadOffers(true);''')
rep('''shareTok = {}; LS.set("rb-links", []);''', '''shareTok = {}; LS.set("rb-links", []); offers = null; showOfferBadge();''')

# ---------- styles
_i = h.rfind("</style>"); h = h[:_i] + """.of-sub{display:flex;flex-wrap:wrap;gap:4px 8px;align-items:center;margin-top:2px;font-size:12px}
.of-mkt{color:var(--muted);font-size:12px;font-variant-numeric:tabular-nums}
.frrow .frn{display:grid}
.of-row .of-ctl{grid-column:3/-1;display:flex;flex-wrap:wrap;gap:6px 12px;align-items:center;padding:2px 0 4px}
.of-row.on{background:color-mix(in srgb,var(--ok) 8%,var(--row));outline:1px solid color-mix(in srgb,var(--ok) 40%,var(--line))}
.of-pick{display:inline-flex;gap:6px;align-items:center;font-size:13.5px;cursor:pointer}
.of-pick input{width:18px;height:18px;accent-color:var(--ok)}
.of-ctl .step button{width:30px;height:30px}
.of-price{display:inline-flex;gap:4px;align-items:center;font-size:13.5px;color:var(--muted)}
.of-price input{width:78px;background:var(--bg);border:1px solid var(--line);border-radius:7px;padding:6px 8px;color:var(--fg);font-variant-numeric:tabular-nums;text-align:right}
.of-foot{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;border-top:1px solid var(--line);margin-top:6px;padding-top:10px}
.of-name{display:inline-flex;gap:6px;align-items:center;font-size:14px;color:var(--muted);flex:1 1 220px}
.of-name input{flex:1;min-width:0;background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:8px 10px;color:var(--fg)}
.of-total{font-size:14px;color:var(--muted)} .of-total b{color:var(--fg);font-family:var(--display);font-size:16px}
.of-foot .msg{flex-basis:100%;margin:0;font-size:13.5px} .of-foot .msg:empty{display:none}
.of-foot .msg.ok{color:var(--ok)} .of-foot .msg.err{color:var(--fury)}
.of-help{margin:0 0 4px}
.of-panel{display:grid;gap:10px}
.of-hrow{display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap}
.of-h{font-family:var(--display);font-size:19px;margin:0}
.of-h small{font-family:var(--body-font);font-size:14px;color:var(--muted);font-weight:500}
.of-card{background:var(--row);border:1px solid var(--line);border-radius:10px;padding:10px 12px;display:grid;gap:8px}
.of-top{display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;align-items:baseline}
.of-from{font-family:var(--display);font-size:16px}
.of-sum b{font-family:var(--display);font-size:16px;color:var(--ok)}
.of-items{display:grid;gap:2px}
.of-items .frrow[data-card]{cursor:zoom-in}
.of-items .frrow[data-card]:hover{background:var(--panel)}
.of-each{font-variant-numeric:tabular-nums;white-space:nowrap;justify-self:end;font-weight:600}
@media (max-width:520px){ .of-row .of-ctl{grid-column:1/-1} .of-each{grid-column:3;justify-self:start} }
""" + h[_i:]

open(out, "w", encoding="utf-8").write(h)
print("patch_offers: ok ->", out)
