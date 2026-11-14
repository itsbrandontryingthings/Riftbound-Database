#!/usr/bin/env python3
"""Pick-several filter menus: picking two options in one menu shows the cards of both (the count is the sum of each alone,
as the options don't overlap), the button says "First +1", the set buttons show both sets, Reset clears it, and the
Wish List's menus work the same. Run: python3 build/tests/multi_test.py   (needs playwright + Chromium; no internet)"""
import asyncio, os, re, subprocess, sys, time
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PH = os.path.join(HERE, "ph.png")
if not os.path.exists(PH):
    from PIL import Image; Image.new("RGB", (744, 1039), (60, 70, 110)).save(PH)

async def main():
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8777"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
    bad = []
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
                await pg.add_init_script("localStorage.setItem('rb-wish', JSON.stringify({'ogn-047-298': 1, 'ogn-001-298': 1, 'ven-001-166': 1, 'sfd-001-221': 1}))")
                await pg.goto("http://127.0.0.1:8777/index.html"); await pg.wait_for_timeout(900)
                if size == "phone": await pg.click("#ftoggle")
                count = lambda: pg.text_content("#count")
                num = lambda t: int(re.sub(r"\D", "", t.split(" card")[0]) or 0)
                async def pick(sel, labels):
                    w = pg.locator(f".msel:has({sel})"); await w.locator(".msel-b").click()
                    for l in labels: await w.locator(".msel-o", has_text=re.compile("^" + re.escape(l) + r"( \(\d+\))?$")).locator("input").check()
                    await w.locator("[data-done]").click(); await pg.wait_for_timeout(300)
                    return (await w.locator(".msel-b").text_content()).strip()
                async def clear(sel):
                    w = pg.locator(f".msel:has({sel})"); await w.locator(".msel-b").click(); await w.locator("[data-clear]").click(); await w.locator("[data-done]").click(); await pg.wait_for_timeout(200)
                for sel, a, bb in [("#type", "Champion Unit", "Regular Unit"), ("#cset", "Radiance", "Vendetta"), ("#rarity", "Epic", "Showcase")]:
                    await pick(sel, [a]); na = num(await count()); await clear(sel)
                    await pick(sel, [bb]); nb = num(await count()); await clear(sel)
                    label = await pick(sel, [a, bb]); nab = num(await count())
                    ok = nab == na + nb and na > 0 and nb > 0 and label in (f"{a} +1", f"{bb} +1")
                    print(f"{size:7} {'OK  ' if ok else 'WRONG'} {sel:8} {a} {na} + {bb} {nb} = {nab}  (button: {label!r})")
                    if not ok: bad.append((size, sel))
                    if sel == "#cset":
                        pressed = await pg.evaluate("[...document.querySelectorAll('.setbtn[aria-pressed=true]')].map(b => b.dataset.set)")
                        txt = await count(); ok = sorted(pressed) == ["RAD", "VEN"] and "Radiance + Vendetta" in txt
                        print(f"{size:7} {'OK  ' if ok else 'WRONG'} set buttons pressed {pressed}, count says {txt!r}")
                        if not ok: bad.append((size, "setbtns"))
                    await clear(sel)
                await pick("#type", ["Champion Unit", "Regular Unit"]); await pick("#cset", ["Radiance", "Vendetta"])
                await pg.click("#freset"); await pg.wait_for_timeout(300)
                labels = [(await pg.locator(f".msel:has({s}) .msel-b").text_content()).strip() for s in ("#type", "#cset")]
                ok = num(await count()) == 1739 and labels == ["All types", "All sets"]
                print(f"{size:7} {'OK  ' if ok else 'WRONG'} Reset filters -> {await count()} {labels}")
                if not ok: bad.append((size, "reset"))
                # Wish List
                await pg.click("#t-wish"); await pg.wait_for_timeout(400)
                rows = lambda: pg.locator("#wish-list .card, #wish-list .wrow").count()
                n0 = await rows(); await pick("#wlf-set", ["Origins", "Vendetta"]); n1 = await rows()
                ok = (n0, n1) == (4, 3)
                print(f"{size:7} {'OK  ' if ok else 'WRONG'} Wish List: {n0} cards, Origins + Vendetta -> {n1}")
                if not ok: bad.append((size, "wish"))
                if size == "phone":
                    w = pg.locator(".msel:has(#wlf-type)"); await w.locator(".msel-b").click(); await pg.wait_for_timeout(200)
                    await pg.screenshot(path=os.path.join(os.environ.get("TEMP", "."), "multi_phone_sheet.png")); await w.locator("[data-done]").click()
                print(f"{size:7} errors: {errs or 'none'}")
                if errs: bad.append((size, "errors"))
            await b.close()
    finally:
        srv.terminate()
    print("FAILED: " + str(bad) if bad else "OK: picking several works")
    return 1 if bad else 0
sys.exit(asyncio.run(main()))
