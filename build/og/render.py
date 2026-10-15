#!/usr/bin/env python3
"""Make the site's pictures from the HTML in build/og/:
- og-image.jpg  (og.html, 1200 x 630): the link preview Discord, iMessage, etc. show for the site.
- logo-512.png  (logo.html, 512 x 512, transparent corners): the RBDB logo, used as the site icon.
Both go to the repo root. Run: python3 build/og/render.py
(needs: pip install playwright; python -m playwright install chromium). It loads card art from Riot's image server
and Google Fonts, so it needs the internet."""
import asyncio, os
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

async def shot(b, page, size, out, **kw):
    pg = await b.new_page(viewport={"width": size[0], "height": size[1]}, device_scale_factor=1)
    await pg.goto("file:///" + os.path.join(HERE, page).replace("\\", "/"), wait_until="networkidle")
    await pg.evaluate("document.fonts.ready")
    broken = await pg.evaluate("[...document.images].filter(i => !i.complete || !i.naturalWidth).length")
    assert broken == 0, f"{page}: {broken} pictures didn't load"
    path = os.path.join(ROOT, out)
    await pg.screenshot(path=path, **kw)
    await pg.close()
    print(out, "->", os.path.getsize(path), "bytes")

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        await shot(b, "og.html", (1200, 630), "og-image.jpg", type="jpeg", quality=88)
        await shot(b, "logo.html", (512, 512), "logo-512.png", type="png", omit_background=True)
        await b.close()

asyncio.run(main())
