#!/usr/bin/env python3
"""Live offers check (fake Supabase), no page refreshes:
1. The list owner has the page open on Collection; a friend's offer arrives -> within ~10 s the Marketplace tab shows a
   count, the poro sound plays, and Incoming Offers shows it marked New.
2. The friend (signed out) has the page open; the owner sends a counter offer -> it shows in the friend's Incoming Offers
   under "Counter Offers on Your Offers" (New, sound), and replying from there works and moves it out.
"Another person" acts by writing straight into the fake database, like the real one would change on the server.
Run: python3 build/tests/offers_live_test.py   (starts its own server on port 8768; takes about 40 seconds)"""
import asyncio, os, subprocess, sys, time
from playwright.async_api import async_playwright
S = os.path.dirname(os.path.abspath(__file__)) + "/"; ROOT = os.path.abspath(S + "../..")
BASE = "http://127.0.0.1:8768/index.html"
# counts sounds that really play: the chime's <audio> element (not the silent unlock) or a live Web Audio chime
COUNT_SOUNDS = """window.__osc = 0;
const _p = HTMLMediaElement.prototype.play; HTMLMediaElement.prototype.play = function(){ const r = _p.call(this); if (!this.muted && r && r.then) r.then(() => window.__osc++, () => {}); return r; };
const _o = AudioContext.prototype.createOscillator; AudioContext.prototype.createOscillator = function(){ if (!(this instanceof OfflineAudioContext)) window.__osc++; return _o.call(this); };"""
TAP_FIRST = """window.__tapped = false; ["pointerdown", "keydown"].forEach(ev => addEventListener(ev, e => { if (e.isTrusted) window.__tapped = true; }, true));
const _pl = HTMLMediaElement.prototype.play; HTMLMediaElement.prototype.play = function(){ return window.__tapped ? _pl.call(this) : Promise.reject(new DOMException("needs a tap", "NotAllowedError")); };
const _A = AudioContext; window.AudioContext = class extends _A { constructor(...a){ super(...a); if (!window.__tapped) this.suspend(); }
  resume(){ return window.__tapped ? super.resume() : Promise.reject(new DOMException("needs a tap", "NotAllowedError")); } };"""
async def main():
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8768"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
    ok = True
    def check(name, cond, extra=""):
        nonlocal ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, extra)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch()   # normal sound rules: no sound until the page has had a click
            ctx = await b.new_context(viewport={"width": 1000, "height": 900}); errs = []
            await ctx.add_init_script(COUNT_SOUNDS)
            async def h(r):
                u = r.request.url
                if "supabase-js" in u: return await r.fulfill(path=S + "fake_supabase.js", content_type="application/javascript")
                if "rgpub" in u or "tcgplayer-cdn" in u: return await r.fulfill(path=S + "ph.png")
                if "fonts.g" in u: return await r.abort()
                await r.continue_()
            await ctx.route("**/*", h)
            pg = await ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.on("dialog", lambda d: asyncio.ensure_future(d.accept()))
            await pg.goto(BASE); await pg.wait_for_timeout(600)
            # Alex shares a shopping list
            await pg.click("#acct-in"); await pg.click("#auth-switch"); await pg.fill("#auth-email", "alex@example.com"); await pg.fill("#auth-pass", "secret12"); await pg.click("#auth-go"); await pg.wait_for_timeout(700)
            await pg.fill("#q", "Baccai Sandspinner"); await pg.wait_for_timeout(400)
            await pg.click("#list button[data-shopadd]"); await pg.click("#t-shop"); await pg.wait_for_timeout(400); await pg.click("#sh-share"); await pg.wait_for_timeout(300)
            if await pg.is_visible("#share-name"): await pg.fill("#share-name", "Alex's List")
            await pg.click("#share-go"); await pg.wait_for_timeout(1500); url = await pg.input_value("#share-url"); await pg.click("#share-ok")
            tok = url.split("#share=")[1]
            await pg.click("#t-collection"); await pg.mouse.click(5, 5); await pg.wait_for_timeout(2500)   # a click so sound is allowed
            before = await pg.evaluate("window.__osc")
            # 1. a friend's offer arrives in the database
            await pg.evaluate("""tok => { const d = JSON.parse(localStorage.__db), s = d.shared_decks.find(r => r.share_token === tok), now = new Date().toISOString();
              d.shop_offers.push({id: "o1", owner: s.owner, share_token: tok, from_name: "Sam", items: [{name: "Baccai Sandspinner", q: 1}], offer: "$3", trade: [], thread: [], status: "open", reply_token: "r".repeat(32), created_at: now, updated_at: now});
              localStorage.__db = JSON.stringify(d); }""", tok)
            await pg.wait_for_timeout(12000)
            tab = await pg.text_content("#t-shop")
            check("owner: Marketplace tab shows a count without refreshing", tab.strip() != "Marketplace", repr(tab))
            check("owner: the sound played", await pg.evaluate("window.__osc") > before)
            await pg.click("#t-shop"); await pg.wait_for_timeout(500)
            inc = await pg.inner_text("#shop-offers")
            check("owner: Incoming Offers shows Sam's offer marked New", "Sam" in inc and "NEW" in inc.upper())
            check("owner: no sound menu any more", await pg.locator("#of-chime").count() == 0)
            await pg.screenshot(path=S + "live_owner.png")
            # 2. the friend: signed out, has made an offer (reply code in this browser)
            await pg.click("#acct-out"); await pg.wait_for_timeout(500)
            await pg.evaluate("""() => { localStorage.setItem("rb-my-offers", JSON.stringify(["r".repeat(32)])); localStorage.setItem("rb-my-offers-seen", JSON.stringify({["r".repeat(32)]: 0})); }""")
            await pg.goto("about:blank"); await pg.goto(url); await pg.wait_for_timeout(2000); await pg.click("#t-collection"); await pg.mouse.click(5, 5); await pg.wait_for_timeout(500)
            before = await pg.evaluate("window.__osc")
            check("friend: nothing waiting yet", "Counter Offers" not in await pg.inner_text("#shop-offers"))
            await pg.evaluate("""() => { const d = JSON.parse(localStorage.__db), o = d.shop_offers.find(x => x.id === "o1");
              o.thread.push({by: "owner", text: "Would you do $5?", at: new Date().toISOString()}); localStorage.__db = JSON.stringify(d); }""")
            await pg.wait_for_timeout(12000)
            tab = await pg.text_content("#t-shop")
            check("friend: Marketplace tab shows a count without refreshing", tab.strip() != "Marketplace", repr(tab))
            check("friend: the sound played", await pg.evaluate("window.__osc") > before)
            await pg.click("#t-shop"); await pg.wait_for_timeout(600)
            inc = await pg.inner_text("#shop-offers")
            check("friend: counter offer shows in Incoming Offers", "Counter Offers on Your Offers" in inc and "Would you do $5?" in inc and "Alex's List" in inc and "NEW" in inc.upper())
            await pg.screenshot(path=S + "live_friend.png", full_page=False)
            await pg.set_viewport_size({"width": 390, "height": 844}); await pg.wait_for_timeout(300)
            await (await pg.query_selector("#shop-offers")).screenshot(path=S + "live_friend_phone.png")
            await pg.set_viewport_size({"width": 1000, "height": 900})
            # reply from Incoming Offers
            await pg.fill("#shop-offers [data-mo=text]", "Deal at $4?"); await pg.click("#shop-offers [data-mo=reply]"); await pg.wait_for_timeout(1500)
            thread = await pg.evaluate("JSON.parse(localStorage.__db).shop_offers[0].thread.map(m => m.by + ':' + m.text)")
            check("friend: reply sent from Incoming Offers", thread[-1] == "them:Deal at $4?", thread)
            check("friend: it leaves Incoming Offers (their turn now)", "Counter Offers on Your Offers" not in await pg.inner_text("#shop-offers"))
            # 3. nobody has tapped the page since it loaded: the browser blocks the sound, so a note says how to turn it on
            # (a fresh browser session with the same saved data: browsers remember clicks from earlier in a session)
            # the test browser doesn't enforce "no sound before a tap", so act like Chrome / Safari do
            ctx2 = await b.new_context(viewport={"width": 1000, "height": 900}, storage_state=await ctx.storage_state())
            await ctx2.add_init_script(TAP_FIRST); await ctx2.add_init_script(COUNT_SOUNDS); await ctx2.route("**/*", h)
            pg = await ctx2.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(BASE); await pg.wait_for_timeout(2500)
            await pg.evaluate("""() => { const d = JSON.parse(localStorage.__db), o = d.shop_offers.find(x => x.id === "o1");
              o.thread.push({by: "owner", text: "OK, $4.50?", at: new Date().toISOString()}); localStorage.__db = JSON.stringify(d); }""")
            await pg.wait_for_timeout(12000)
            note = (await pg.text_content("#shop-toast")) if await pg.locator("#shop-toast").count() else ""
            check("no tap yet: a note says to tap to turn on sounds", "Tap anywhere" in note, repr(note))
            await pg.mouse.click(5, 5); await pg.wait_for_timeout(300); before = await pg.evaluate("window.__osc")
            await pg.evaluate("""() => { const d = JSON.parse(localStorage.__db), o = d.shop_offers.find(x => x.id === "o1");
              o.thread.push({by: "owner", text: "Last offer: $4.25", at: new Date().toISOString()}); localStorage.__db = JSON.stringify(d); }""")
            await pg.wait_for_timeout(12000)
            check("after one tap: the next counter offer plays the sound", await pg.evaluate("window.__osc") > before)
            check("no JavaScript errors", not errs, errs)
            await b.close()
    finally:
        srv.terminate()
    print("ALL PASS" if ok else "SOME FAILED"); return 0 if ok else 1
sys.exit(asyncio.run(main()))
