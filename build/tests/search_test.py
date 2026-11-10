#!/usr/bin/env python3
"""Forgiving search test: names typed without dashes or apostrophes, half typed, or in another order must still find the
card in Collection, Open Packs and the Wish List's Add a Card, and My Decks' Add a Card must take a half-typed name.
Run: python3 build/tests/search_test.py   (needs playwright + Chromium; no internet)"""
import asyncio, os, subprocess, sys, time
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PH = os.path.join(HERE, "ph.png")
if not os.path.exists(PH):
    from PIL import Image; Image.new("RGB", (744, 1039), (60, 70, 110)).save(PH)
# (typed, a card name that must be among the results)
CASES = [("azir sovereign", "Azir - Sovereign"), ("azir sov", "Azir - Sovereign"), ("sovereign azir", "Azir - Sovereign"),
         ("AZIR-SOVEREIGN", "Azir - Sovereign"), ("kaisa", "Kai'Sa - Daughter of the Void"), ("kai sa daughter", "Kai'Sa - Daughter of the Void"),
         ("miss fort bounty", "Miss Fortune - Bounty Hunter"), ("jinx loose", "Jinx - Loose Cannon"), ("portal rescue", "Portal Rescue")]

async def main():
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8775"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
    bad = []
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(); pg = await b.new_page(viewport={"width": 1400, "height": 900}); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("dialog", lambda d: asyncio.ensure_future(d.accept()))
            async def h(r):
                u = r.request.url
                if "supabase-js" in u: return await r.fulfill(path=os.path.join(HERE, "fake_supabase.js"), content_type="application/javascript")
                if "rgpub" in u or "tcgplayer-cdn" in u: return await r.fulfill(path=PH)
                if "fonts.g" in u: return await r.abort()
                await r.continue_()
            await pg.route("**/*", h)
            await pg.goto("http://127.0.0.1:8775/index.html"); await pg.wait_for_timeout(800)
            names = lambda sel: pg.evaluate(f"[...document.querySelectorAll('{sel}')].map(e => e.textContent.trim())")
            for typed, want in CASES:
                await pg.fill("#q", typed); await pg.wait_for_timeout(350)
                got = await names("#list .card .name, #list .card .tname"); ok = want in got
                print(f"Collection   {'OK  ' if ok else 'MISS'} {typed!r:22} -> {await pg.text_content('#count')}{'' if ok else ' ' + str(got[:3])}")
                if not ok: bad.append(("collection", typed))
            await pg.fill("#q", "deathknell"); await pg.wait_for_timeout(350); print("Collection   rules text 'deathknell' ->", await pg.text_content("#count"))
            await pg.fill("#q", "")
            await pg.click("#t-packs")
            for typed, want in CASES:
                await pg.fill("#qa-q", typed); await pg.wait_for_timeout(200)
                got = await names("#qa-sug .name"); ok = want in got
                print(f"Open Packs   {'OK  ' if ok else 'MISS'} {typed!r:22} -> {len(got)} suggestions")
                if not ok: bad.append(("packs", typed))
            await pg.fill("#qa-q", "")
            await pg.click("#t-wish"); await pg.wait_for_timeout(300)
            for typed, want in CASES[:5]:
                await pg.fill("#wl-q", typed); await pg.wait_for_timeout(200)
                got = await names("#wl-sug .name, #wl-sug li"); ok = any(want in g for g in got)
                print(f"Wish List    {'OK  ' if ok else 'MISS'} {typed!r:22} -> {len(got)} suggestions")
                if not ok: bad.append(("wish", typed))
            # My Decks: make a deck, then add a card by a half-typed name
            await pg.evaluate("""() => { localStorage.setItem('rb-decks', JSON.stringify([{id: 'dtest', name: 'Search Test', sub: 'Your deck', text: '1 Jinx - Loose Cannon'}])); localStorage.setItem('rb-deck', JSON.stringify('dtest')); }""")
            await pg.reload(); await pg.wait_for_timeout(800)
            await pg.click("#t-decks"); await pg.wait_for_timeout(400)
            if await pg.locator("#dk-addn").count():
                await pg.fill("#dk-addn", "azir sov"); await pg.click("#dk-addgo"); await pg.wait_for_timeout(400)
                body = await pg.inner_text("#deck-body"); ok = "Azir - Sovereign" in body
                print(f"My Decks     {'OK  ' if ok else 'MISS'} 'azir sov' -> {(await pg.text_content('#dk-addmsg') or '').strip()}")
                if not ok: bad.append(("decks", "azir sov"))
                label = await pg.evaluate("document.querySelector('#dk-names option[value=\"Azir - Sovereign\"]')?.label")
                print("My Decks     suggestion label:", label)
            else:
                print("My Decks     (no Add a Card box found)"); bad.append(("decks", "box"))
            print("errors:", errs or "none"); await b.close()
    finally:
        srv.terminate()
    print("FAILED:", bad) if bad else print("OK: every search found its card")
    return 1 if bad or errs else 0
sys.exit(asyncio.run(main()))
