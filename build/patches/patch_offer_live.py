#!/usr/bin/env python3
"""Offers: one sound, live updates, counter offers in Incoming Offers (website; runs last, after patch_withdrawn.py).
- The new-offer sound is always the poro coin (poroCoin); the konbini chime and the sound menu are gone.
- Offers are checked every 20 seconds while the page is open and showing (was every minute), and straight away when
  you come back to the page, so new offers, counter offers and replies show up (with "New" and the sound) without a refresh.
  The Incoming Offers panel redraws itself, except while you're typing in it (then it waits until you leave the box).
- Counter offers and answers on offers YOU made (signed in or not) show in Incoming Offers too, under
  "Counter Offers on Your Offers": the same card as under the friend's list (reply, accept their counter, revise,
  withdraw). They show while it's your turn (open, last message from the list owner) or while marked New.
Usage: patch_offer_live.py in.html out.html"""
import re, sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

# ---- one sound: the poro coin
rep('''function coinChime(){ (LS.get("rb-offer-chime") === "poro" ? poroCoin : konbiniChime)(); }''', '''function coinChime(){ poroCoin(); }''')
i, j = h.index("// konbini door chime:"), h.index("function poroCoin(){")
h = h[:i] + h[j:]
h, n = re.subn(r'<select id="of-chime".*?</select>', "", h, flags=re.S); assert n == 1, n
rep('''$("shop-offers").addEventListener("change", e => { if (e.target.id === "of-chime"){ LS.set("rb-offer-chime", e.target.value); coinChime(); } });\n''', "")
rep("#of-chime{padding:5px 8px;font-size:13px}\n", "")
assert "konbini" not in h.lower() and "of-chime" not in h

# ---- check more often, and when you come back to the page
rep('''setInterval(offerPoll, 60000);
document.addEventListener("visibilitychange", offerPoll);''', '''setInterval(offerPoll, 20000);
document.addEventListener("visibilitychange", offerPoll);
addEventListener("focus", offerPoll);''')
# the 60-second "don't ask again yet" limits would skip a poll, so polls always force; a stuck request can't block later ones
rep('''  if (offersBusy || (!force && offers && Date.now() - offersAt < 60000)) return;''',
    '''  if ((offersBusy && Date.now() - offersBusy < 30000) || (!force && offers && Date.now() - offersAt < 20000)) return;''')
rep('''  offersBusy = true;
  const me = cloudUser''', '''  offersBusy = Date.now();
  const me = cloudUser''')
rep('''  if (myOffersBusy || (!force && myOffers && Date.now() - myOffersAt < 60000)) return;
  myOffersBusy = true;''', '''  if ((myOffersBusy && Date.now() - myOffersBusy < 30000) || (!force && myOffers && Date.now() - myOffersAt < 20000)) return;
  myOffersBusy = Date.now();''')

# ---- redraw Incoming Offers when something changes, but not under someone's fingers
rep('''  offersAt = Date.now(); showOfferBadge(); if (st.tab === "shop") renderOffers();''',
    '''  offersAt = Date.now(); showOfferBadge(); offersRedraw();''')
rep('''  showFriendsBadge();
  if ((st.tab === "friends" || st.tab === "shop") && !document.activeElement?.closest?.(".of-body, .mo-card")) renderFriends();''',
    '''  showFriendsBadge(); offersRedraw();
  if ((st.tab === "friends" || st.tab === "shop") && !document.activeElement?.closest?.(".of-body, .mo-card")) renderFriends();''')

# ---- your offers: the same card, for one list or for the counter offers waiting on you
rep('''function myOffersHTML(listTok){
  const mine = (myOffers || []).filter(o => o.list_token === listTok);
  if (!mine.length) return "";
  return `<div class="mo-box"><span class="collect-k">Your offers on this list</span>${mine.map(o => {''',
    '''function myOffersHTML(listTok, pick){
  const mine = (myOffers || []).filter(pick || (o => o.list_token === listTok));
  if (!mine.length) return "";
  return `<div class="mo-box">${pick ? "" : '<span class="collect-k">Your offers on this list</span>'}${mine.map(o => {''')
rep('''      <div class="of-top"><div>${moNew.has(o.reply_token) ? '<span class="of-new">New</span>' : ""}${statusPill(o, false)}<span class="meta">sent ${esc(fmtWhen(o.created_at))}</span></div></div>''',
    '''      <div class="of-top"><div>${moNew.has(o.reply_token) ? '<span class="of-new">New</span>' : ""}${statusPill(o, false)}${pick ? `<b class="of-from">${esc(o.list_name || "A friend's shopping list")}</b> ` : ""}<span class="meta">sent ${esc(fmtWhen(o.created_at))}</span></div></div>''')
# the reply / accept / revise / withdraw buttons also work inside Incoming Offers
for t in ('frListen("input", e => { if (e.target.dataset.mo === "text")', 'frListen("keydown", e => { if (e.target.dataset.mo === "text"', '''frListen("click", async e => {
  const b = e.target.closest("button[data-mo]"); if (!b) return;'''):
    rep(t, t.replace("frListen(", "moListen(", 1))
rep('''  if (act === "withdraw" && moArm !== code){ moArm = code; renderFriends(); return; }''',
    '''  if (act === "withdraw" && moArm !== code){ moArm = code; renderFriends(); offersRedraw(true); return; }''')
rep('''function myOffersHTML(listTok, pick){''', r'''function moListen(type, fn){ frListen(type, fn); $("shop-offers").addEventListener(type, fn); }
// counter offers (and answers) on offers you made: your turn, or not looked at yet
function isCounter(o){ return (o.status === "open" && (o.thread[o.thread.length - 1] || {}).by === "owner") || moNew.has(o.reply_token); }
function myCounters(){ try { return (myOffers || []).filter(isCounter); } catch(e){ return []; } }   // myOffers / moNew are set up further down the page
var offersStale = false;
function offersRedraw(now){
  if (st.tab !== "shop") return;
  const a = document.activeElement;
  if (!now && a && a.closest && a.closest("#shop-offers") && /^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName)){ offersStale = true; return; }
  offersStale = false; renderOffers();
}
$("shop-offers").addEventListener("focusout", () => { if (offersStale) setTimeout(() => { if (!$("shop-offers").contains(document.activeElement)) offersRedraw(); }, 0); });
function myOffersHTML(listTok, pick){''')

# ---- Incoming Offers: counter offers on your offers, shown for everyone (signed in or not)
rep('''function renderOffers(){
  const box = $("shop-offers");''', '''function renderOffers(){
  renderOffers0();
  const cs = myCounters(), panel = $("shop-offers").querySelector(".of-panel"); if (!cs.length || !panel) return;
  const small = panel.querySelector(".of-h small"), n = (offers || []).length + cs.length;
  if (small) small.textContent = n; else panel.querySelector(".of-h .mk-fold, .of-h").insertAdjacentHTML("beforeend", ` <small>${n}</small>`);
  const html = `<div class="mo-in"><h3 class="mo-in-h">Counter Offers on Your Offers</h3><p class="meta">Answers from friends on offers you made. Reply, accept their counter or withdraw right here.</p>${myOffersHTML(null, isCounter)}</div>`;
  const after = panel.querySelector(".of-hrow") || panel.querySelector(".of-h");
  after.insertAdjacentHTML("afterend", html);
}
function renderOffers0(){
  const box = $("shop-offers");''')

_i = h.rfind("</style>"); h = h[:_i] + """.mo-in{display:grid;gap:8px;margin:6px 0 14px;padding-bottom:14px;border-bottom:1px solid var(--line)}
.mo-in-h{margin:0;font-size:15px;font-family:var(--display)}
.mo-in .meta{margin:0}
.mo-in .mo-box{display:grid;gap:10px}
.mo-in .of-from{margin-right:6px}
""" + h[_i:]

open(out, "w", encoding="utf-8").write(h)
print("ok")
