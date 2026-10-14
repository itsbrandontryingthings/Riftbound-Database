#!/usr/bin/env python3
"""Smoke test for the built website (../../index.html): loads it with stand-in images and a fake Supabase,
checks there are no JavaScript errors, filters work, and a card's info sheet opens.
Run: python3 build/tests/smoke.py   (needs: pip install playwright; a Chromium Playwright can launch)"""
import asyncio, os, subprocess, sys, time
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PH = os.path.join(HERE, "ph.png")
if not os.path.exists(PH):
    from PIL import Image; Image.new("RGB", (744, 1039), (60, 70, 110)).save(PH)
async def main():
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8765"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(); pg = await b.new_page(viewport={"width": 1400, "height": 900}); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            async def h(r):
                u = r.request.url
                if "supabase-js" in u: return await r.fulfill(path=os.path.join(HERE, "fake_supabase.js"), content_type="application/javascript")
                if "rgpub" in u or "tcgplayer-cdn" in u: return await r.fulfill(path=PH)
                if "fonts.g" in u: return await r.abort()
                await r.continue_()
            await pg.route("**/*", h)
            await pg.goto("http://127.0.0.1:8765/index.html"); await pg.wait_for_timeout(800)
            print("cards:", await pg.text_content("#count"))
            await pg.select_option("#kw", "Action"); await pg.wait_for_timeout(300); print("Action keyword:", await pg.text_content("#count"))
            await pg.click("#freset"); await pg.wait_for_timeout(300)
            await pg.fill("#q", "portal rescue"); await pg.wait_for_timeout(400)
            await (await pg.query_selector("#list button.thumb")).click(); await pg.wait_for_timeout(400)
            print("info sheet:", (await pg.inner_text("#lb-info"))[:120].replace("\n", " | "))
            print("errors:", errs or "none"); await b.close()
            return 1 if errs else 0
    finally:
        srv.terminate()
sys.exit(asyncio.run(main()))
