#!/usr/bin/env python3
"""End-to-end check (fake Supabase): a friend makes an offer on a shared shopping list, then withdraws it.
The withdrawn offer must disappear for the friend (Your offers on this list) and for the list owner (Incoming Offers).
Run: python3 build/tests/offers_withdraw_test.py   (starts its own server on port 8767)"""
import asyncio, os, subprocess, sys, time
from playwright.async_api import async_playwright
S = os.path.dirname(os.path.abspath(__file__)) + "/"; ROOT = os.path.abspath(S + "../..")
BASE = "http://127.0.0.1:8767/index.html"
async def main():
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8767"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(); ctx = await b.new_context(viewport={"width": 1000, "height": 900}); errs = []
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
            async def signup(email):
                await pg.click("#acct-in"); await pg.click("#auth-switch"); await pg.fill("#auth-email", email); await pg.fill("#auth-pass", "secret12"); await pg.click("#auth-go"); await pg.wait_for_timeout(700)
            async def signin(email):
                await pg.click("#acct-in"); await pg.fill("#auth-email", email); await pg.fill("#auth-pass", "secret12"); await pg.click("#auth-go"); await pg.wait_for_timeout(900)
            # Alex puts a card on the shopping list and shares it
            await signup("alex@example.com")
            await pg.fill("#q", "Baccai Sandspinner"); await pg.wait_for_timeout(400)
            cid = await pg.get_attribute("#list button[data-shopadd]", "data-shopadd")
            await pg.click("#list button[data-shopadd]"); await pg.wait_for_timeout(200)
            await pg.click("#t-shop"); await pg.wait_for_timeout(400); await pg.click("#sh-share"); await pg.wait_for_timeout(300)
            if await pg.is_visible("#share-name"): await pg.fill("#share-name", "Alex's List")
            await pg.click("#share-go"); await pg.wait_for_timeout(1500)
            url = await pg.input_value("#share-url"); await pg.click("#share-ok"); await pg.click("#acct-out"); await pg.wait_for_timeout(400)
            # Amy (signed out, owns one copy of the card) opens the link, makes an offer, then withdraws it
            await pg.evaluate("id => localStorage.setItem('rb-counts', JSON.stringify({[id]: 1}))", cid)
            await pg.goto("about:blank"); await pg.goto(url); await pg.wait_for_timeout(1500); await pg.click("#t-shop"); await pg.wait_for_timeout(400)
            await pg.click(".of-pick"); await pg.wait_for_timeout(300)
            await pg.fill("[data-of=name]", "Amy"); await pg.fill("[data-of=offer]", "$5"); await pg.wait_for_timeout(100)
            await pg.click("[data-of=send]"); await pg.wait_for_timeout(1500)
            n_before = await pg.locator(".mo-card").count()   # shows straight away, no tab switch
            await pg.click("[data-mo=withdraw]"); await pg.wait_for_timeout(300)
            armed = await pg.text_content("[data-mo=withdraw]")
            await pg.click("[data-mo=withdraw]"); await pg.wait_for_timeout(1200)
            n_after = await pg.locator(".mo-card").count()
            toast = await pg.text_content("#shop-toast")
            status = await pg.evaluate("JSON.parse(localStorage.__db).shop_offers.map(o => o.status)")
            print("friend: offers shown before", n_before, "| armed:", armed, "| after withdraw", n_after, "| note:", toast, "| db:", status)
            ok = n_before == 1 and n_after == 0 and status == ["withdrawn"]
            # Alex no longer sees it under Incoming Offers
            await pg.goto(BASE); await pg.wait_for_timeout(600); await signin("alex@example.com")
            await pg.click("#t-shop"); await pg.wait_for_timeout(1200)
            owner_n = await pg.locator(".of-card, [data-ofid], .offer").count()
            inc = (await pg.inner_text("#view-shop"))[:400]
            print("owner: offer cards", owner_n, "| Amy mentioned:", "Amy" in inc, "| Withdrawn mentioned:", "Withdrawn" in inc)
            ok = ok and "Amy" not in inc and "Withdrawn" not in inc
            print("errors:", errs or "none"); print("PASS" if ok and not errs else "FAIL"); await b.close()
            return 0 if ok and not errs else 1
    finally:
        srv.terminate()
sys.exit(asyncio.run(main()))
