"""End-to-end test of private share links with the fake Supabase (tests/fake_supabase.js).
Serve the repo root first:  (cd <repo> && python3 -m http.server 8765)  then: python3 build/tests/links_test.py"""
import asyncio, re, os
from playwright.async_api import async_playwright
S=os.path.dirname(os.path.abspath(__file__))+"/"
BASE="http://127.0.0.1:8765/index.html"
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); ctx = await b.new_context(viewport={"width":1000,"height":900}); errs=[]
        await ctx.grant_permissions(["clipboard-read","clipboard-write"], origin="http://127.0.0.1:8765")
        async def h(r):
            u=r.request.url
            if "supabase-js" in u: return await r.fulfill(path=S+"fake_supabase.js", content_type="application/javascript")
            if "rgpub" in u or "tcgplayer-cdn" in u: return await r.fulfill(path=S+"ph.png")
            if "fonts.g" in u: return await r.abort()
            await r.continue_()
        await ctx.route("**/*", h)
        pg = await ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)+" @ "+(e.stack or "")[:300]))
        pg.on("dialog", lambda d: asyncio.ensure_future(d.accept()))   # "Are you sure you want to stop sharing?" -> OK
        await pg.goto(BASE); await pg.wait_for_timeout(500)
        async def signup(email):
            await pg.click("#acct-in"); await pg.click("#auth-switch"); await pg.fill("#auth-email",email); await pg.fill("#auth-pass","secret12"); await pg.click("#auth-go"); await pg.wait_for_timeout(700)
        async def signin(email):
            await pg.click("#acct-in"); await pg.fill("#auth-email",email); await pg.fill("#auth-pass","secret12"); await pg.click("#auth-go"); await pg.wait_for_timeout(900)
        # A shares a deck
        await signup("alex@example.com")
        await pg.click("#t-decks"); await pg.evaluate("document.getElementById('deck-add').open=true")
        await pg.fill("#dk-name","Jinx Aggro"); await pg.fill("#dk-list","Legend:\n1 Jinx, Loose Cannon\nMain deck:\n3 Get Excited!\n3 Gust\n2 Stacked Deck"); await pg.click("#dk-save"); await pg.wait_for_timeout(300)
        await pg.click("#dk-share"); await pg.fill("#share-name","Alex"); await pg.click("#share-go"); await pg.wait_for_timeout(1500)
        url = await pg.input_value("#share-url"); print("deck link:", url, "| done visible:", await pg.is_visible("#share-done"))
        await pg.screenshot(path=S+"link_dialog.png")
        await pg.click("#share-copy"); await pg.wait_for_timeout(200); print("clipboard:", await pg.evaluate("navigator.clipboard.readText()") == url)
        await pg.click("#share-ok")
        print("deck summary:", await pg.eval_on_selector("#deck-summary","e=>[...e.querySelectorAll('.tag.ok,button')].map(x=>x.textContent).join(' | ')"))
        # copy link again later shows the same link
        await pg.click("#dk-link"); await pg.wait_for_timeout(500); print("same link again:", await pg.input_value("#share-url") == url); await pg.click("#share-ok")
        # wish list share
        await pg.click("#t-collection"); await pg.wait_for_timeout(200)
        await pg.click("#list button[data-wish]"); await pg.click("#t-wish"); await pg.wait_for_timeout(300)
        await pg.click("#wish-share"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#share-go"): await pg.click("#share-go")
        await pg.wait_for_timeout(1500); wurl = await pg.input_value("#share-url"); print("wish link:", wurl[-45:], wurl != url); await pg.click("#share-ok")
        await pg.click("#acct-out"); await pg.wait_for_timeout(400)
        # B signs up: Friends tab is empty (can't browse)
        await signup("amy@example.com"); await pg.click("#t-friends"); await pg.wait_for_timeout(500)
        print("B friends before link:", (await pg.text_content("#fr-list"))[:70])
        # B opens the deck link
        await pg.goto(url); await pg.wait_for_timeout(1500)
        print("B after opening link:", await pg.eval_on_selector_all(".frdeck h3","e=>e.map(x=>x.textContent)"), "| highlighted:", await pg.eval_on_selector_all(".frdeck.new","e=>e.length"), "| open rows:", await pg.eval_on_selector_all(".frbody .frrow","e=>e.length"), "| url now:", pg.url[-25:])
        # paste the wish link
        await pg.fill("#fr-add", wurl); await pg.click("#fr-add-go"); await pg.wait_for_timeout(1000)
        print("after paste:", [x.strip() for x in await pg.eval_on_selector_all(".frsec","e=>e.map(x=>x.textContent)")], await pg.text_content("#fr-count"))
        await pg.fill("#fr-add","hello"); await pg.click("#fr-add-go"); print("bad paste msg:", await pg.text_content("#fr-add-msg"))
        await pg.fill("#fr-q","gust"); await pg.wait_for_timeout(400); print("search gust:", await pg.text_content("#fr-count"))
        await pg.fill("#fr-q",""); await pg.wait_for_timeout(300)
        await pg.screenshot(path=S+"links_friends.png", full_page=False)
        # B's links saved with account (wish._links)
        print("B cloud links:", await pg.evaluate("Object.values(JSON.parse(localStorage.__db).collections).map(c=>(c.wish||{})._links)"))
        await pg.click("#acct-out"); await pg.wait_for_timeout(400)
        # someone signed out with the link can still view it
        await pg.goto(url); await pg.wait_for_timeout(1500)
        print("signed-out viewer:", await pg.eval_on_selector_all(".frdeck h3","e=>e.map(x=>x.textContent)"))
        # A stops sharing -> link dies
        await pg.goto(BASE); await pg.wait_for_timeout(500)
        await signin("alex@example.com"); await pg.click("#t-decks"); await pg.wait_for_timeout(400)
        await pg.click("#dk-unshare"); await pg.wait_for_timeout(1500)
        print("rows left:", await pg.evaluate("JSON.parse(localStorage.__db).shared_decks.map(r=>r.deck_id)"))
        await pg.click("#acct-out"); await pg.wait_for_timeout(300)
        await signin("amy@example.com"); await pg.click("#t-friends"); await pg.wait_for_timeout(1200)
        print("B after A stopped:", await pg.eval_on_selector_all(".frdeck h3","e=>e.map(x=>x.textContent)"), "|", await pg.text_content("#fr-count"))
        await pg.click("#fr-prune"); await pg.wait_for_timeout(800); print("after prune:", await pg.text_content("#fr-count"))
        await pg.click(".frdeck [data-act=forget]"); await pg.wait_for_timeout(500); print("after forget:", (await pg.text_content("#fr-list"))[:50])
        print("errors", errs); await b.close()
asyncio.run(main())
