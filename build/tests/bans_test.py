#!/usr/bin/env python3
"""Announced bans (bans.txt date in the future): before the date they show "To Be Banned", appear under the Banned chip
and don't make decks illegal; from that date on (faked clock) they show as plain "Banned". Needs playwright + Chromium."""
import asyncio, os, subprocess, sys, time, datetime
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))

def soon_date():
    for line in open(os.path.join(ROOT, "build/tcg/bans.txt"), encoding="utf-8"):
        if line.startswith("#") or "|" not in line: continue
        d = line.split("|")[2].strip()
        if d > datetime.date.today().isoformat(): return d
    return None

async def check(p, when, name):
    b = await p.chromium.launch(); pg = await b.new_page(viewport={"width": 1400, "height": 900}); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.clock.set_fixed_time(when)
    async def h(r):
        u = r.request.url
        if "supabase-js" in u: return await r.fulfill(path=os.path.join(HERE, "fake_supabase.js"), content_type="application/javascript")
        if "rgpub" in u or "tcgplayer-cdn" in u or "fonts.g" in u or "jsdelivr" in u: return await r.abort()
        await r.continue_()
    await pg.route("**/*", h)
    await pg.goto("http://127.0.0.1:8766/index.html"); await pg.wait_for_timeout(800)
    await pg.click('#doms button[data-ban]'); await pg.wait_for_timeout(300)
    count = await pg.text_content("#count")
    await pg.fill("#q", name); await pg.wait_for_timeout(400)
    row = await pg.inner_text("#list")
    await (await pg.query_selector("#list button.thumb")).click(); await pg.wait_for_timeout(400)
    info = (await pg.inner_text("#lb-info"))[:80].replace("\n", " | ")
    await b.close()
    return count, row, info, errs

async def main():
    d = soon_date()
    if not d: print("no announced-but-not-active bans in bans.txt; nothing to test"); return
    name = next(l.split("|")[0] for l in open(os.path.join(ROOT, "build/tcg/bans.txt"), encoding="utf-8") if "|" in l and not l.startswith("#") and l.split("|")[2].strip() == d)
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8766"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
    ok = True
    try:
        async with async_playwright() as p:
            before = datetime.datetime.fromisoformat(d) - datetime.timedelta(days=1, hours=-12)
            after = datetime.datetime.fromisoformat(d) + datetime.timedelta(hours=9)
            c1, r1, i1, e1 = await check(p, before, name)
            c2, r2, i2, e2 = await check(p, after, name)
            print(f"{name} — day before {d}: Banned chip {c1} | row has 'To Be Banned': {'To Be Banned' in r1} | info: {i1}")
            print(f"{name} — on {d}: Banned chip {c2} | row has 'To Be Banned': {'To Be Banned' in r2} | info: {i2}")
            ok = ("To Be Banned" in r1 and "Legal until" in i1 and "To Be Banned" not in r2 and "Banned" in r2
                  and "Standard: Banned" in i2 and c1 == c2 and not e1 and not e2)
            print("errors:", e1 + e2 or "none")
    finally:
        srv.terminate()
    print("PASS" if ok else "FAIL"); sys.exit(0 if ok else 1)
asyncio.run(main())
