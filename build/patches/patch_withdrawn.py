#!/usr/bin/env python3
"""Withdrawn offers disappear (website; runs last, after patch_wish_lists.py).
- Offers you made: once you withdraw one it's gone from "Your offers on this list" (a note says "Offer withdrawn").
- Offers on your shopping list: ones the sender withdrew aren't shown (and don't count as new or play the chime).
  The row stays in shop_offers (status 'withdrawn'); it's only hidden, so no SQL change.
- An offer you just sent shows up under "Your offers on this list" straight away (before, only after switching tabs).
Usage: patch_withdrawn.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

# owner side: drop withdrawn offers before "new" / chime are worked out
rep('''offers = (data || []).map(o => ({...o, trade: Array.isArray(o.trade) ? o.trade : [], thread: Array.isArray(o.thread) ? o.thread : [], status: o.status || "open"}));''',
    '''offers = (data || []).map(o => ({...o, trade: Array.isArray(o.trade) ? o.trade : [], thread: Array.isArray(o.thread) ? o.thread : [], status: o.status || "open"})).filter(o => o.status !== "withdrawn");''')
# offers you made
rep('''myOffers = (data || []).map(o => ({...o, trade: Array.isArray(o.trade) ? o.trade : [], thread: Array.isArray(o.thread) ? o.thread : []}));''',
    '''myOffers = (data || []).map(o => ({...o, trade: Array.isArray(o.trade) ? o.trade : [], thread: Array.isArray(o.thread) ? o.thread : []})).filter(o => o.status !== "withdrawn");''')
rep('''  delete moDraft[code]; moNew.delete(code); await loadMyOffers(true); renderFriends();''',
    '''  delete moDraft[code]; moNew.delete(code);
  if (act === "withdraw"){ myOffers = (myOffers || []).filter(o => o.reply_token !== code); toast("Offer withdrawn."); }
  await loadMyOffers(true); renderFriends();''')

rep('''addReplyCode(replyCode); loadMyOffers(true); }''', '''addReplyCode(replyCode); await loadMyOffers(true); }''')

open(out, "w", encoding="utf-8").write(h)
print("ok")
