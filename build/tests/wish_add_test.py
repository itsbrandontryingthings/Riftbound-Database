#!/usr/bin/env python3
"""Wish List "+ Add to...": a wanted card goes into the collection and a deck in one go, comes off the wish list,
Undo puts everything back, and adding to a deck only leaves the wish list alone. Desktop and phone.
Run: python3 build/tests/wish_add_test.py   (needs playwright + Chromium; no internet)"""
import asyncio, json, os, subprocess, sys, time
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PH = os.path.join(HERE, "ph.png")
if not os.path.exists(PH):
    from PIL import Image; Image.new("RGB", (744, 1039), (60, 70, 110)).save(PH)
CARD = "ogn-047-298"
STATE = f"(() => {{ const g = k => JSON.parse(localStorage.getItem(k) || 'null'); return {{have: (g('rb-counts') || {{}})['{CARD}'] || 0, want: (g('rb-wish') || {{}})['{CARD}'] || 0, deck: g('rb-decks')[0].text}}; }})()"
DECK = {"id": "dtest", "name": "Test Deck", "sub": "Your deck", "text": "Legend:\n1 Jinx, Loose Cannon\n\nMain deck:\n2 Get Excited!"}

async def main():
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8778"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
    bad = []
    def check(ok, what):
        print(("ok   " if ok else "FAIL ") + what)
        if not ok: bad.append(what)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch()
            for width, height, size in [(1400, 900, "desktop"), (390, 844, "phone")]:
                pg = await b.new_page(viewport={"width": width, "height": height}); errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)))
                async def h(r):
                    u = r.request.url
                    if "supabase-js" in u: return await r.fulfill(path=os.path.join(HERE, "fake_supabase.js"), content_type="application/javascript")
                    if "rgpub" in u or "tcgplayer-cdn" in u: return await r.fulfill(path=PH)
                    if "fonts.g" in u: return await r.abort()
                    await r.continue_()
                await pg.route("**/*", h)
                await pg.add_init_script(f"if (!sessionStorage.getItem('t')){{ sessionStorage.setItem('t', 1); localStorage.setItem('rb-wish', JSON.stringify({{'{CARD}': 3}})); localStorage.setItem('rb-decks', JSON.stringify([{json.dumps(DECK)}])); localStorage.setItem('rb-counts', JSON.stringify({{}})); }}")
                await pg.goto("http://127.0.0.1:8778/index.html"); await pg.wait_for_timeout(900)
                await pg.click("#t-wish"); await pg.wait_for_timeout(300)
                name = await pg.evaluate(f"RB_CARDS.find(c => c.id === '{CARD}').name")
                await pg.click(f"#wish-list [data-waadd='{CARD}']"); await pg.wait_for_timeout(200)
                check(await pg.is_visible("#wa-dlg"), f"{size}: picker opens")
                check((await pg.text_content("#wa-n")) == "3", f"{size}: copies start at the 3 wanted")
                await pg.click("#wa-minus")
                await pg.click("#wa-rows [data-wato='dtest']")
                check(await pg.is_checked("#wa-off"), f"{size}: 'take off wish list' ticked with Collection")
                if os.environ.get("SHOTS"): await pg.screenshot(path=os.path.join(os.environ["SHOTS"], f"wa-{size}.png"))
                await pg.click("#wa-go"); await pg.wait_for_timeout(300)
                st = await pg.evaluate(STATE)
                check(st["have"] == 2, f"{size}: collection has 2 (got {st['have']})")
                check(st["want"] == 1, f"{size}: wish list down to 1 (got {st['want']})")
                check(f"2 {name}" in st["deck"], f"{size}: deck has 2 {name}: {st['deck']!r}")
                check("still want 1" in (await pg.text_content("#shop-toast")), f"{size}: note says still want 1")
                await pg.click("#wa-undo"); await pg.wait_for_timeout(300)
                st = await pg.evaluate(STATE)
                check(st["have"] == 0 and st["want"] == 3 and st["deck"] == DECK["text"], f"{size}: Undo puts everything back {st}")
                # deck only: wish list stays
                await pg.click(f"#wish-list [data-waadd='{CARD}']"); await pg.wait_for_timeout(200)
                await pg.click("#wa-rows [data-wato='__col']"); await pg.click("#wa-rows [data-wato='dtest']")
                check(not await pg.is_checked("#wa-off"), f"{size}: deck only leaves 'take off' unticked")
                await pg.click("#wa-go"); await pg.wait_for_timeout(300)
                st = await pg.evaluate(STATE)
                check(st["have"] == 0 and st["want"] == 3 and f"3 {name}" in st["deck"], f"{size}: deck-only add {st}")
                await pg.reload(); await pg.wait_for_timeout(900)
                saved = (await pg.evaluate(STATE))["deck"]
                check(f"3 {name}" in saved, f"{size}: deck change kept after a reload")
                check(not errs, f"{size}: no JS errors {errs}")
                await pg.close()
            await b.close()
    finally:
        srv.terminate()
    print("errors: " + ("; ".join(bad) if bad else "none")); sys.exit(1 if bad else 0)

asyncio.run(main())
