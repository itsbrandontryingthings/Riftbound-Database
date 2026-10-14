#!/usr/bin/env python3
"""Offer conversations, trade cards and a bad-word filter (website; runs last, after patch_chime.py).
Needs supabase_offer_threads.sql (the site still works without it: offers just stay one-way).
- Bad words: names, offers and messages with swear words or slurs are refused, here (badWords) and in the database
  (rb_bad_words, same patterns). Numbers and symbols standing in for letters, repeated letters and dots between
  letters are caught.
- Offer form (Friends): "Cards you'd trade" picker (type, arrow keys, Enter), shown as chips with - / + / x. The offer
  text is optional when you add cards to trade. make_offer returns a secret reply code, kept in localStorage
  "rb-my-offers" (and in wish._myoffers when signed in).
- Friends: "Your offers" under each shopping list you offered on: status, the conversation, and when it's open:
  Accept their counter (if they countered), Reply, Withdraw. Counter offers play the chime and show "New".
- Shopping List (owner): each offer shows the cards they'd trade, the conversation and a status; Counter offer,
  Accept and Decline (RPC owner_reply). A reply from them plays the chime. "Got them" keeps adding the cards.
Usage: patch_offer_threads.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

BAD_SUB = "f+[._*-]*u+[._*-]*c+[._*-]*k+|b+[._*-]*i+[._*-]*t+[._*-]*c+[._*-]*h+|w+[._*-]*h+[._*-]*o+[._*-]*r+[._*-]*e+|s+[._*-]*l+[._*-]*u+[._*-]*t+|b+[._*-]*a+[._*-]*s+[._*-]*t+[._*-]*a+[._*-]*r+[._*-]*d+|a+[._*-]*s+[._*-]*s+[._*-]*h+[._*-]*o+[._*-]*l+[._*-]*e+|n+[._*-]*i+[._*-]*g+[._*-]*g+|f+[._*-]*a+[._*-]*g+[._*-]*g+[._*-]*o+[._*-]*t+|r+[._*-]*e+[._*-]*t+[._*-]*a+[._*-]*r+[._*-]*d+|m+[._*-]*o+[._*-]*t+[._*-]*h+[._*-]*e+[._*-]*r+[._*-]*f+|d+[._*-]*i+[._*-]*l+[._*-]*d+[._*-]*o+|p+[._*-]*u+[._*-]*s+[._*-]*s+[._*-]*y+|c+[._*-]*o+[._*-]*c+[._*-]*k+[._*-]*s+[._*-]*u+[._*-]*c+[._*-]*k+|t+[._*-]*w+[._*-]*a+[._*-]*t+|w+[._*-]*a+[._*-]*n+[._*-]*k+|j+[._*-]*i+[._*-]*z+[._*-]*z+|s+[._*-]*h+[._*-]*i[._*-]*t+"
BAD_WORD = "ass|asses|dick|dicks|cock|cocks|cum|tit|tits|piss|fag|fags|fuk|fck|hoe|hoes|kike|spic|spics|chink|tranny|rape|raping|rapist|nazi|porn|pedo|kys|nigga|niggas|cunt|cunts"

# ================= owner side (Shopping List > Offers)
OLD_LOAD = '''  const me = cloudUser, { data, error } = await sb.from("shop_offers").select("id, from_name, items, offer, created_at").order("created_at", { ascending: false }).limit(100);
  offersBusy = false; if (cloudUser !== me) return;
  if (error){ offersOff = /shop_offers|relation|does not exist|schema cache|permission/i.test(error.message || ""); offers = []; }
  else {
    offersOff = false; offers = data || [];
    const had = LS.get("rb-offers-seen"), seen = new Set(had || []), fresh = offers.filter(o => !seen.has(o.id));
    fresh.forEach(o => offersNew.add(o.id));
    if (fresh.length && had && offerSound()) coinChime();
    LS.set("rb-offers-seen", offers.map(o => o.id));
  }'''
NEW_LOAD = '''  const me = cloudUser, q = cols => sb.from("shop_offers").select(cols).order("created_at", { ascending: false }).limit(100);
  let { data, error } = await q("id, from_name, items, offer, trade, thread, status, created_at, updated_at");
  if (error && /column|trade|thread|status/i.test(error.message || "")){ threadsOff = true; ({ data, error } = await q("id, from_name, items, offer, created_at")); }
  else if (!error) threadsOff = false;
  offersBusy = false; if (cloudUser !== me) return;
  if (error){ offersOff = /shop_offers|relation|does not exist|schema cache|permission/i.test(error.message || ""); offers = []; }
  else {
    offersOff = false; offers = (data || []).map(o => ({...o, trade: Array.isArray(o.trade) ? o.trade : [], thread: Array.isArray(o.thread) ? o.thread : [], status: o.status || "open"}));
    // new = an offer you haven't seen, or a new message from them on one you have
    const old = LS.get("rb-offers-seen"), seen = Array.isArray(old) ? Object.fromEntries(old.map(id => [id, -1])) : (old || {}), first = !old;
    const fresh = offers.filter(o => !(o.id in seen) || (seen[o.id] >= 0 && o.thread.length > seen[o.id] && (o.thread[o.thread.length - 1] || {}).by === "them"));
    fresh.forEach(o => offersNew.add(o.id));
    if (fresh.length && !first && offerSound()) coinChime();
    LS.set("rb-offers-seen", Object.fromEntries(offers.map(o => [o.id, o.thread.length])));
  }'''
rep(OLD_LOAD, NEW_LOAD)
rep('''let offers = null, offersAt = 0, offersOff = false, offersBusy = false, offerArm = "";''',
    '''let offers = null, offersAt = 0, offersOff = false, offersBusy = false, offerArm = "", threadsOff = false;
const ownerDraft = {};   // offer id -> counter offer being typed''')
rep('''  const n = offers ? offers.length : 0;
  $("t-shop").innerHTML''', '''  const n = offers ? offers.filter(o => o.status === "open" && (o.thread[o.thread.length - 1] || {by: "them"}).by === "them").length : 0;
  $("t-shop").innerHTML''')

rep('''    <div class="of-said"><span class="collect-k">Their offer</span><span class="of-text">${esc(o.offer || "")}</span></div>
    <div class="of-items">''', '''    ${o.offer ? `<div class="of-said"><span class="collect-k">Their offer</span><span class="of-text">${esc(o.offer)}</span></div>` : ""}
    ${o.trade.length ? `<div class="of-trade-in"><span class="collect-k">They'd also trade you</span>${tradeRows(o.trade)}</div>` : ""}
    <span class="collect-k">Cards they have for you</span>
    <div class="of-items">''')
rep('''<div class="of-top"><div>${offersNew.has(o.id) ? '<span class="of-new">New</span>' : ""}<b class="of-from">${esc(o.from_name)}</b>''',
    '''<div class="of-top"><div>${offersNew.has(o.id) ? '<span class="of-new">New</span>' : ""}${threadsOff ? "" : statusPill(o, true)}<b class="of-from">${esc(o.from_name)}</b>''')
rep('''    <div class="frow"><button class="btn primary" data-ofa="accept" title="Adds these cards to your collection and removes the offer">Got them: add to my collection</button>''',
    '''    ${threadHTML(o.thread, true)}
    ${!threadsOff && o.status === "open" ? `<div class="of-reply"><input data-ofd="${esc(o.id)}" maxlength="200" value="${esc(ownerDraft[o.id] || "")}" placeholder="Counter offer, e.g. $25 or add your Jinx" aria-label="Your counter offer to ${esc(o.from_name)}"><button class="btn" data-ofa="counter">Send counter offer</button><button class="btn ok" data-ofa="oaccept">Accept</button><button class="btn" data-ofa="odecline">Decline</button></div>` : ""}
    <div class="frow"><button class="btn primary" data-ofa="got" title="Adds these cards to your collection and removes the offer">Got them: add to my collection</button>''')
rep('''  if (a.dataset.ofa === "accept") for (const i of''', '''  if (["counter", "oaccept", "odecline"].includes(a.dataset.ofa)){
    const text = (ownerDraft[id] || "").trim(), msg = card.querySelector("[data-ofmsg]"), act = {counter: "counter", oaccept: "accept", odecline: "decline"}[a.dataset.ofa];
    if (act === "counter" && !text){ msg.textContent = "Write your counter offer first."; card.querySelector("[data-ofd]").focus(); return; }
    if (badWords(text)){ msg.textContent = "Please keep it friendly: that has a word we don't allow."; return; }
    a.disabled = true; msg.textContent = "Sending…";
    const { error } = await sb.rpc("owner_reply", { p_id: id, p_action: act, p_text: text });
    if (error){ msg.textContent = offerErr(error); a.disabled = false; return; }
    delete ownerDraft[id]; await loadOffers(true); return;
  }
  if (a.dataset.ofa === "got") for (const i of''')
rep('''$("shop-offers").addEventListener("click", async e => {''', '''$("shop-offers").addEventListener("input", e => { if (e.target.dataset.ofd) ownerDraft[e.target.dataset.ofd] = e.target.value; });
$("shop-offers").addEventListener("keydown", e => { if (e.target.dataset.ofd && e.key === "Enter"){ e.preventDefault(); e.target.closest(".of-card").querySelector('[data-ofa="counter"]').click(); } });
$("shop-offers").addEventListener("click", async e => {''')

# ================= shared helpers + offerer side (Friends)
rep('''// ---- making an offer on a friend's shopping list (Friends tab)''', r'''// ---- bad words (same patterns as rb_bad_words in supabase_offer_threads.sql)
const BAD_SUB = new RegExp("__SUB__"), BAD_WORD = new RegExp("\\b(__WORD__)\\b"), LEET = {"0":"o","1":"i","3":"e","4":"a","5":"s","7":"t","@":"a","$":"s","!":"i"};
const badWords = t => { const n = String(t || "").toLowerCase().replace(/[013457@$!]/g, c => LEET[c]); return BAD_SUB.test(n) || BAD_WORD.test(n); };
const offerErr = error => { const m = (error && error.message) || "";
  return /words/.test(m) ? "Please keep it friendly: that has a word we don't allow."
    : /closed/.test(m) ? "This offer is already closed."
    : /busy/.test(m) ? "Too many messages on this offer. Try again later."
    : /link/.test(m) ? "This offer or list isn't available any more."
    : /function|schema cache/i.test(m) ? "Counter offers need a quick database update before they work."
    : "Couldn't send. Check your connection and try again."; };
// a list of cards with pictures (offer trades)
function tradeRows(list){
  return `<div class="of-items">${(list || []).map(i => { const c = i.id && byId[i.id] ? byId[i.id] : frCard(norm(i.name)), key = norm(i.name);
    return `<div class="frrow"${c ? ` data-card="${esc(c.id)}"` : ""}>${c ? thumbHTML(c, 160) : frThumb(key)}<span class="q">${+i.q || 0}×</span><span class="frn">${esc(i.name)}<span class="of-sub">${c ? `<span class="dk-set" style="--sc:var(--${setCol[c.set] || "line"})">${esc(setName[c.set] || c.set)} · ${esc(codeOf(c))}</span><span class="of-mkt">${c.price != null ? `market ${esc(money(c.price))} each` : "no price"}</span>` : ""}</span></span></div>`; }).join("")}</div>`;
}
const fmtWhen = s => { const d = new Date(s); return isNaN(d) ? "" : d.toLocaleString([], { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }); };
function threadHTML(thread, ownerView){
  if (!thread || !thread.length) return "";
  return `<div class="of-thread">${thread.map(m => { const mine = ownerView ? m.by === "owner" : m.by === "them";
    return `<div class="of-msg ${mine ? "me" : "them"}"><span class="of-who">${mine ? "You" : ownerView ? "Them" : "List owner"} <small>${esc(fmtWhen(m.at))}</small></span>${m.text ? `<span>${esc(m.text)}</span>` : ""}${m.trade && m.trade.length ? `<span class="of-who">Cards to trade:</span>${tradeRows(m.trade)}` : ""}</div>`; }).join("")}</div>`;
}
function statusPill(o, ownerView){
  const last = (o.thread[o.thread.length - 1] || {}).by;
  const [cls, label] = o.status === "accepted" ? ["ok", "Accepted"] : o.status === "declined" ? ["no", "Declined"] : o.status === "withdrawn" ? ["no", "Withdrawn"]
    : ownerView ? (last === "owner" ? ["wait", "Waiting for them"] : ["act", "Needs your answer"]) : (last === "owner" ? ["act", "Counter offer from them"] : ["wait", "Waiting for them"]);
  return `<span class="of-st ${cls}">${label}</span>`;
}
// offers you made: secret reply codes in this browser (and with your account when signed in)
let myOffers = null, myOffersAt = 0, myOffersOff = false, myOffersBusy = false, moArm = "";
const moDraft = {}, moNew = new Set();
const myReplyCodes = () => [...new Set([...(LS.get("rb-my-offers") || []), ...(Array.isArray(wish._myoffers) ? wish._myoffers : [])])].filter(t => /^[A-Za-z0-9_-]{20,64}$/.test(t)).slice(0, 100);
function addReplyCode(t){
  const all = [...new Set([t, ...myReplyCodes()])].slice(0, 100);
  LS.set("rb-my-offers", all);
  if (cloudUser){ wish._myoffers = all; saveWish(); }
}
async function loadMyOffers(force){
  const codes = myReplyCodes();
  if (!codes.length || !sb){ myOffers = []; showFriendsBadge(); return; }
  if (myOffersBusy || (!force && myOffers && Date.now() - myOffersAt < 60000)) return;
  myOffersBusy = true;
  const { data, error } = await sb.rpc("get_my_offers", { p_replies: codes });
  myOffersBusy = false;
  if (error){ myOffersOff = true; myOffers = []; showFriendsBadge(); return; }
  myOffersOff = false; myOffersAt = Date.now();
  myOffers = (data || []).map(o => ({...o, trade: Array.isArray(o.trade) ? o.trade : [], thread: Array.isArray(o.thread) ? o.thread : []}));
  const old = LS.get("rb-my-offers-seen"), seen = old || {};
  const fresh = myOffers.filter(o => o.thread.length > (seen[o.reply_token] || 0) && (o.thread[o.thread.length - 1] || {}).by === "owner");
  fresh.forEach(o => moNew.add(o.reply_token));
  if (fresh.length && old && offerSound()) coinChime();
  LS.set("rb-my-offers-seen", Object.fromEntries(myOffers.map(o => [o.reply_token, o.thread.length])));
  showFriendsBadge();
  if (st.tab === "friends" && !document.activeElement?.closest?.(".of-body, .mo-card")) renderFriends();
}
function showFriendsBadge(){
  const n = (myOffers || []).filter(o => o.status === "open" && (o.thread[o.thread.length - 1] || {}).by === "owner").length;
  $("t-friends").innerHTML = `Friends${n ? `<span class="fcount" title="${n} counter offer${n === 1 ? "" : "s"} waiting">${n}</span>` : ""}`;
}
function myOffersHTML(listTok){
  const mine = (myOffers || []).filter(o => o.list_token === listTok);
  if (!mine.length) return "";
  return `<div class="mo-box"><span class="collect-k">Your offers on this list</span>${mine.map(o => {
    const n = (o.items || []).reduce((a, i) => a + (+i.q || 0), 0), last = (o.thread[o.thread.length - 1] || {}).by, open = o.status === "open";
    return `<div class="mo-card" data-reply="${esc(o.reply_token)}">
      <div class="of-top"><div>${moNew.has(o.reply_token) ? '<span class="of-new">New</span>' : ""}${statusPill(o, false)}<span class="meta">sent ${esc(fmtWhen(o.created_at))}</span></div><span class="of-sum">${n} card${n === 1 ? "" : "s"}: ${esc((o.items || []).map(i => `${i.q}× ${i.name}`).join(", "))}</span></div>
      ${o.offer ? `<div class="of-said"><span class="collect-k">You offered</span><span class="of-text">${esc(o.offer)}</span></div>` : ""}
      ${o.trade.length ? `<span class="collect-k">Cards you'd trade</span>${tradeRows(o.trade)}` : ""}
      ${threadHTML(o.thread, false)}
      ${open ? `<div class="of-reply"><input data-mo="text" maxlength="200" value="${esc(moDraft[o.reply_token] || "")}" placeholder="${last === "owner" ? "Reply to their counter offer…" : "Add a message…"}" aria-label="Your reply"><button class="btn" data-mo="reply">Send reply</button>${last === "owner" ? '<button class="btn ok" data-mo="accept">Accept their counter</button>' : ""}<button class="btn" data-mo="withdraw">${moArm === o.reply_token ? "Tap again to withdraw" : "Withdraw"}</button></div><p class="msg" data-mo-msg aria-live="polite"></p>` : ""}
    </div>`; }).join("")}</div>`;
}
$("fr-list").addEventListener("input", e => { if (e.target.dataset.mo === "text") moDraft[e.target.closest(".mo-card").dataset.reply] = e.target.value; });
$("fr-list").addEventListener("keydown", e => { if (e.target.dataset.mo === "text" && e.key === "Enter"){ e.preventDefault(); e.target.closest(".mo-card").querySelector('[data-mo="reply"]').click(); } });
$("fr-list").addEventListener("click", async e => {
  const b = e.target.closest("button[data-mo]"); if (!b) return;
  const card = b.closest(".mo-card"), code = card.dataset.reply, act = b.dataset.mo, msg = card.querySelector("[data-mo-msg]"), text = (moDraft[code] || "").trim();
  if (act === "withdraw" && moArm !== code){ moArm = code; renderFriends(); return; }
  if (act === "reply" && !text){ msg.textContent = "Write your reply first."; card.querySelector('[data-mo="text"]').focus(); return; }
  if (badWords(text)){ msg.textContent = "Please keep it friendly: that has a word we don't allow."; return; }
  b.disabled = true; msg.textContent = "Sending…";
  const { error } = await sb.rpc("offer_reply", { p_reply: code, p_action: act, p_text: act === "withdraw" ? "" : text, p_trade: [] });
  moArm = "";
  if (error){ msg.textContent = offerErr(error); b.disabled = false; return; }
  delete moDraft[code]; moNew.delete(code); await loadMyOffers(true); renderFriends();
});

// ---- cards you'd trade (offer form)
function tradeSuggest(input){
  const S = offerOf(input.closest(".of-body").dataset.tok), q = norm(input.value), ul = input.parentElement.querySelector(".sug");
  if (!q) S.tsug = [];
  else {
    const words = q.split(" ");
    S.tsug = CARDS.filter(c => !c.token && words.every(w => norm(c.name).includes(w)))
      .map(c => ({c, s: (counts[c.id] ? -20 : 0) + (norm(c.name) === q ? -5 : 0) + (norm(c.name).startsWith(q) ? 0 : 10) + (c.variant ? 3 : 0) + META.sets.findIndex(x => x.code === c.set) * 0.1}))
      .sort((a, b) => a.s - b.s || a.c.name.localeCompare(b.c.name)).slice(0, 8).map(x => x.c);
  }
  S.tsel = 0; tradeDraw(input);
}
function tradeDraw(input){
  const S = offerOf(input.closest(".of-body").dataset.tok), ul = input.parentElement.querySelector(".sug"), sug = S.tsug || [];
  input.setAttribute("aria-expanded", sug.length > 0);
  ul.innerHTML = sug.map((c, i) => `<li role="option" data-i="${i}" aria-selected="${i === S.tsel}">
    ${thumbHTML(c, 100).replace("<button", "<span").replace("</button>", "</span>").replace(/ data-img="[^"]*"/, "")}
    <span class="code"><b>${c.set}</b>${esc(codeOf(c).split(" ")[1])}</span>
    <span class="info"><span class="name">${esc(c.name)}</span><span class="sub">${c.variant ? `<span class="pill var">${esc(c.variant)}</span>` : ""}<span>${c.price != null ? esc(money(c.price)) : "No price"}</span></span></span>
    <span class="own">${counts[c.id] ? `you have ${counts[c.id]}` : ""}</span></li>`).join("");
}
async function tradeAdd(input, i){
  const body = input.closest(".of-body"), tok = body.dataset.tok, S = offerOf(tok), c = (S.tsug || [])[i]; if (!c) return;
  S.trade ||= {}; S.trade[c.id] = Math.min(99, (S.trade[c.id] || 0) + 1); S.tsug = []; S.msg = ""; S.ok = false;
  await renderFriends();
  const again = document.querySelector(`.of-body[data-tok="${CSS.escape(tok)}"] [data-of="tq"]`); if (again) again.focus();
}
$("fr-list").addEventListener("input", e => { if (e.target.dataset.of === "tq") tradeSuggest(e.target); });
$("fr-list").addEventListener("keydown", e => {
  if (e.target.dataset.of !== "tq") return;
  const S = offerOf(e.target.closest(".of-body").dataset.tok), n = (S.tsug || []).length;
  if (e.key === "ArrowDown" && n){ S.tsel = (S.tsel + 1) % n; tradeDraw(e.target); e.preventDefault(); }
  else if (e.key === "ArrowUp" && n){ S.tsel = (S.tsel - 1 + n) % n; tradeDraw(e.target); e.preventDefault(); }
  else if (e.key === "Enter"){ e.preventDefault(); tradeAdd(e.target, S.tsel || 0); }
  else if (e.key === "Escape"){ e.target.value = ""; S.tsug = []; tradeDraw(e.target); }
});
$("fr-list").addEventListener("mousedown", e => { const li = e.target.closest(".of-trade .sug li"); if (li){ e.preventDefault(); tradeAdd(li.closest(".of-trade").querySelector('[data-of="tq"]'), +li.dataset.i); } });
$("fr-list").addEventListener("click", e => {
  const b = e.target.closest("button[data-tx]"); if (!b) return;
  const S = offerOf(b.closest(".of-body").dataset.tok), id = b.dataset.tx;
  S.trade[id] = b.dataset.d === "x" ? 0 : Math.max(0, Math.min(99, (S.trade[id] || 0) + +b.dataset.d));
  if (!S.trade[id]) delete S.trade[id];
  renderFriends();
});
function tradeChips(S){
  const ids = Object.keys(S.trade || {}).filter(id => byId[id]);
  return ids.length ? `<div class="of-chips">${ids.map(id => { const c = byId[id];
    return `<span class="of-chip">${thumbHTML(c, 100)}<span class="of-chn">${esc(c.name)}<small>${esc(codeOf(c))}${c.price != null ? ` · ${esc(money(c.price))}` : ""}</small></span><span class="step"><button type="button" data-tx="${esc(id)}" data-d="-1" aria-label="One fewer">−</button><output>${S.trade[id]}</output><button type="button" data-tx="${esc(id)}" data-d="1" aria-label="One more">+</button></span><button type="button" class="dk-rm" data-tx="${esc(id)}" data-d="x" aria-label="Remove ${esc(c.name)}">✕</button></span>`; }).join("")}</div>` : "";
}

// ---- making an offer on a friend's shopping list (Friends tab)''')
h = h.replace("__SUB__", BAD_SUB).replace("__WORD__", BAD_WORD)

# offer form: trade picker, optional text when trading, bad words, reply code
rep('''    : `<div class="of-foot"><label class="of-offer">Your offer <input data-of="offer" maxlength="200" value="${esc(S.offer)}" autocomplete="off" placeholder="Anything: $20, a trade, a McChicken…"></label>''',
    '''    : `<div class="of-foot"><div class="of-trade"><span class="of-lab">Cards you'd trade <small>(optional, your cards come up first)</small></span>
          <div class="qa-box"><input class="search" data-of="tq" placeholder="Add a card you'd trade, e.g. Jinx…" aria-label="Add a card you'd trade" autocomplete="off" role="combobox" aria-expanded="false"><ul class="sug" role="listbox" aria-label="Matching cards"></ul></div>
          ${tradeChips(S)}</div>
        <label class="of-offer">Your offer <input data-of="offer" maxlength="200" value="${esc(S.offer)}" autocomplete="off" placeholder="${Object.keys(S.trade || {}).length ? "Optional: add money or a note" : "Anything: $20, a trade, a McChicken…"}"></label>''')
rep('''  if (!offer){ say("Write your offer: money, a trade, anything."); body.querySelector('[data-of="offer"]').focus(); return; }
  if (!name){ say("Add your name so they know who the offer is from."); body.querySelector('[data-of="name"]').focus(); return; }''',
    '''  const trade = Object.entries(S.trade || {}).filter(([id]) => byId[id]).map(([id, q]) => ({ name: byId[id].name, q, id }));
  if (!offer && !trade.length){ say("Write your offer (money, anything) or add cards you'd trade."); body.querySelector('[data-of="offer"]').focus(); return; }
  if (!name){ say("Add your name so they know who the offer is from."); body.querySelector('[data-of="name"]').focus(); return; }
  if (badWords(name) || badWords(offer)){ say("Please keep it friendly: your name or offer has a word we don't allow."); return; }''')
rep('''  const { error } = await sb.rpc("make_offer", { p_token: tok, p_name: name.slice(0, 40), p_items: items, p_offer: offer.slice(0, 200) });''',
    '''  let { data: replyCode, error } = await sb.rpc("make_offer", { p_token: tok, p_name: name.slice(0, 40), p_items: items, p_offer: offer.slice(0, 200), p_trade: trade });
  if (error && trade.length && /function|schema cache/i.test(error.message || "")){ say("Offering your own cards needs a quick database update. Remove them, or put them in your offer text."); b.disabled = false; return; }''')
rep('''say(/make_offer|function/i.test(m) && !/busy|link|item|name|offer/i.test(m)''', '''say(/words/.test(m) ? "Please keep it friendly: your name or offer has a word we don't allow." : /make_offer|function/i.test(m) && !/busy|link|item|name|offer/i.test(m)''')
rep('''LS.set("rb-offer-name", name); S.sel = {}; S.offer = ""; S.msg''',
    '''if (typeof replyCode === "string" && replyCode.length >= 20){ addReplyCode(replyCode); loadMyOffers(true); }
  LS.set("rb-offer-name", name); S.sel = {}; S.trade = {}; S.offer = ""; S.msg''')
rep('''Tick <b>I have this</b> and choose how many, then write your offer (money, a trade, anything) and your name.''',
    '''Tick <b>I have this</b> and choose how many, then write your offer (money, anything) and/or add cards you'd trade, and your name. You can follow your offer here, and the owner can send you a counter offer.''')

# your offers appear under the list in Friends
rep('''        ${hits.length ? `<div class="frmatch">Wants ${hits.slice(0, 4).map(x => `${x.q}× ${esc(x.name)}`).join(", ")}${hits.length > 4 ? "…" : ""}</div>` : ""}''',
    '''        ${hits.length ? `<div class="frmatch">Wants ${hits.slice(0, 4).map(x => `${x.q}× ${esc(x.name)}`).join(", ")}${hits.length > 4 ? "…" : ""}</div>` : ""}
        ${shop && !mine ? myOffersHTML(r.share_token) : ""}''')
# typing in those boxes must not open the card preview (the row handler already skips inputs and buttons)

# polling + loading
rep('''const offerPoll = () => { if (cloudUser && sb && shopP().shared && document.visibilityState === "visible") loadOffers(true); };''',
    '''const offerPoll = () => {
  if (document.visibilityState !== "visible" || !sb) return;
  if (cloudUser && shopP().shared) loadOffers(true);
  if (myReplyCodes().length) loadMyOffers(true);
};
setTimeout(() => loadMyOffers(true), 1500);''')
rep('''sb_onSignedIn = () => { loadShareProfile(); loadShareTokens(); loadOffers(true);''', '''sb_onSignedIn = () => { loadShareProfile(); loadShareTokens(); loadOffers(true); setTimeout(() => loadMyOffers(true), 800);''')

# ---------- styles
_i = h.rfind("</style>"); h = h[:_i] + """.of-st{display:inline-block;font-size:11.5px;font-weight:700;border-radius:4px;padding:0 7px;line-height:19px;margin-right:6px;border:1px solid var(--line);vertical-align:1px}
.of-st.act{color:var(--bg);background:var(--warn);border-color:var(--warn)}
.of-st.wait{color:var(--muted)}
.of-st.ok{color:var(--ok);border-color:color-mix(in srgb,var(--ok) 50%,var(--line))}
.of-st.no{color:var(--muted);text-decoration:line-through}
.of-thread{display:grid;gap:6px;margin:4px 0}
.of-msg{display:grid;gap:2px;max-width:min(560px,92%);background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:7px 10px;font-size:14.5px;overflow-wrap:anywhere}
.of-msg.me{justify-self:end;border-color:color-mix(in srgb,var(--accent) 45%,var(--line));background:color-mix(in srgb,var(--accent) 7%,var(--panel))}
.of-who{font-size:12px;color:var(--muted);font-weight:600}
.of-who small{font-weight:400;margin-left:4px}
.of-reply{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.of-reply input{flex:1 1 240px;min-width:0;background:var(--bg);border:1px solid color-mix(in srgb,var(--accent) 45%,var(--line));border-radius:8px;padding:8px 10px;color:var(--fg)}
.btn.ok{color:var(--ok);border-color:color-mix(in srgb,var(--ok) 50%,var(--line))}
.of-trade-in{display:grid;gap:4px}
.of-trade{flex-basis:100%;display:grid;gap:6px}
.of-lab{font-size:14px;color:var(--fg);font-weight:600}
.of-lab small{color:var(--muted);font-weight:400}
.of-trade .qa-box .search{font-size:15px;padding:9px 12px}
.of-chips{display:flex;flex-wrap:wrap;gap:6px}
.of-chip{display:inline-grid;grid-template-columns:30px auto auto auto;gap:8px;align-items:center;background:var(--row);border:1px solid color-mix(in srgb,var(--accent) 40%,var(--line));border-radius:8px;padding:4px 6px}
.of-chn{display:grid;font-size:13.5px;line-height:1.2}
.of-chn small{font-size:11.5px;color:var(--muted)}
.of-chip .step button{width:28px;height:28px}
.mo-box{display:grid;gap:8px;border-top:1px solid var(--line);padding-top:8px}
.mo-card{display:grid;gap:8px;background:var(--row);border:1px solid var(--line);border-radius:10px;padding:10px 12px}
.mo-card .msg{margin:0;font-size:13.5px;color:var(--fury)} .mo-card .msg:empty{display:none}
""" + h[_i:]

open(out, "w", encoding="utf-8").write(h)
print("patch_offer_threads: ok ->", out)
