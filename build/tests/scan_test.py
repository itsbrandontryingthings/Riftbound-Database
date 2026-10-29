#!/usr/bin/env python3
"""Card scanner test: real card pictures (from Riot's image server) are turned into phone-like photos (card on a busy
table, tilted, blurred, JPEG), fed to Open Packs → Scan Cards → Take a Photo Instead, and the card it finds is checked
(right name; right printing). Then one is added and must show in This Pack. Needs internet (card images + Tesseract.js).
Run: python3 build/tests/scan_test.py [how many cards, default 16]"""
import asyncio, io, os, random, re, json, subprocess, sys, tempfile, time, urllib.request
from PIL import Image, ImageFilter, ImageDraw
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
N = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 16
NB = 8                                            # battlefields, read with the sideways frame
RC = "https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/"

def cards():
    s = open(os.path.join(ROOT, "cards.js"), encoding="utf-8").read()
    return json.loads(re.search(r"RB_CARDS\s*=\s*(\[.*\])", s, re.S).group(1).rstrip(";"))

def photo(card_img, rnd):
    """the card on a cluttered background, a bit rotated, smaller, blurred and compressed like a phone photo"""
    bg = Image.new("RGB", (1200, 1600), (rnd.randint(30, 200),) * 3); d = ImageDraw.Draw(bg)
    for _ in range(40):
        x, y = rnd.randint(0, 1200), rnd.randint(0, 1600)
        d.rectangle([x, y, x + rnd.randint(20, 300), y + rnd.randint(20, 300)], fill=tuple(rnd.randint(0, 255) for _ in range(3)))
    wide = card_img.width > card_img.height       # battlefields are sideways: across the width of a phone held upright
    w = rnd.randint(980, 1150) if wide else rnd.randint(780, 1000); c = card_img.convert("RGB").resize((w, int(w * card_img.height / card_img.width)))
    c = c.rotate(rnd.uniform(-6, 6), expand=True, fillcolor=(0, 0, 0))
    bg.paste(c, ((1200 - c.width) // 2 + rnd.randint(-40, 40), (1600 - c.height) // 2 + rnd.randint(-40, 40)))
    bg = bg.filter(ImageFilter.GaussianBlur(rnd.uniform(0.6, 1.4)))
    b = io.BytesIO(); bg.save(b, "JPEG", quality=rnd.randint(55, 80)); return b.getvalue()

async def main():
    rnd = random.Random(7); C = [c for c in cards() if c.get("img") and not c.get("token")]
    pick = rnd.sample([c for c in C if c["type"] != "Battlefield"], N) + rnd.sample([c for c in C if c["type"] == "Battlefield"], NB)
    tmp = tempfile.mkdtemp(); files = []
    for c in pick:
        raw = urllib.request.urlopen(f"{RC}{c['img']}?accountingTag=RB&fm=png&w=744", timeout=30).read()
        p = os.path.join(tmp, c["id"].replace("*", "s") + ".jpg"); open(p, "wb").write(photo(Image.open(io.BytesIO(raw)), rnd)); files.append((c, p))
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8766"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
    name_ok = print_ok = bf_ok = 0
    try:
        async with async_playwright() as pw:
            b = await pw.chromium.launch(); pg = await b.new_page(viewport={"width": 390, "height": 844}); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            async def h(r):
                u = r.request.url
                if "supabase-js" in u: return await r.fulfill(path=os.path.join(HERE, "fake_supabase.js"), content_type="application/javascript")
                if "fonts.g" in u: return await r.abort()
                await r.continue_()
            await pg.route("**/*", h)
            await pg.goto("http://127.0.0.1:8766/index.html"); await pg.wait_for_timeout(800)
            await pg.click("#t-packs"); await pg.click("#sc-open"); await pg.wait_for_timeout(500)
            for c, p in files:
                await pg.evaluate("() => { document.getElementById('sc-res').hidden = true; window.__t0 = performance.now(); }")
                await pg.set_input_files("#sc-file", p)
                try: await pg.wait_for_function("() => !document.getElementById('sc-res').hidden || /Couldn't/.test(document.getElementById('sc-msg').textContent)", timeout=90000)
                except Exception: pass
                ms = await pg.evaluate("() => Math.round(performance.now() - window.__t0)")
                got = await pg.evaluate("() => document.getElementById('sc-res').hidden ? '' : document.querySelector('.sc-p[aria-pressed=true]')?.dataset.id || document.getElementById('sc-name').textContent")
                gc = next((x for x in C if x["id"] == got), None); nm = gc and gc["name"] == c["name"]; pr = got == c["id"]
                if c["type"] == "Battlefield": bf_ok += bool(nm)
                else: name_ok += bool(nm); print_ok += bool(pr)
                print(f"{'OK ' if pr else 'name' if nm else 'MISS'}  {c['id']:<16} {c['name'][:34]:<34} -> {got or '(nothing)'}  {ms} ms")
                if gc and await pg.is_visible("#sc-skip"): await pg.click("#sc-skip")
            # add the last match and check it's in This Pack
            await pg.set_input_files("#sc-file", files[0][1])
            await pg.wait_for_function("() => !document.getElementById('sc-res').hidden", timeout=60000)
            await pg.click("#sc-add"); await pg.wait_for_timeout(300)
            print("added note:", await pg.inner_text("#sc-done"))
            await pg.screenshot(path=os.path.join(tmp, "scanner_phone.png"))
            await pg.click("#sc-close"); print("This Pack:", await pg.inner_text("#qa-count"))
            await b.close()
            # live camera: Chromium's fake camera plays a phone-like photo; a card, then a battlefield with ▭ Battlefield on
            async def live(c, path, wide):
                mj = os.path.join(tmp, "camera.mjpeg"); im = Image.open(path).resize((720, 960))
                with open(mj, "wb") as f:
                    for _ in range(10): b2 = io.BytesIO(); im.save(b2, "JPEG", quality=85); f.write(b2.getvalue())
                b = await pw.chromium.launch(args=["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", f"--use-file-for-fake-video-capture={mj}"])
                ctx = await b.new_context(viewport={"width": 390, "height": 844}, permissions=["camera"]); pg = await ctx.new_page()
                pg.on("pageerror", lambda e: errs.append(str(e))); await pg.route("**/*", h)
                await pg.goto("http://127.0.0.1:8766/index.html"); await pg.wait_for_timeout(800)
                await pg.click("#t-packs"); await pg.click("#sc-open")
                if wide: await pg.click("#sc-wide")
                try:
                    await pg.wait_for_function("() => !document.getElementById('sc-res').hidden", timeout=60000)
                    cam = await pg.text_content("#sc-name")
                except Exception: cam = "(nothing found)"
                await pg.screenshot(path=os.path.join(tmp, f"scanner_camera{'_wide' if wide else ''}.png"))
                ok = cam == c["name"]; print(f"live camera{' (battlefield)' if wide else ''}: expected {c['name']}, found {cam} -> {'OK' if ok else 'WRONG'}")
                await pg.click("#sc-close"); await pg.wait_for_timeout(300)
                off = await pg.evaluate("() => !document.getElementById('sc-video').srcObject"); print("camera off after Done:", off)
                await b.close(); return ok and off
            cam_ok = await live(*files[1], False)
            bfs = [f for f in files if f[0]["type"] == "Battlefield"]; cam_ok = await live(*bfs[0], True) and cam_ok
            print(f"\nright card {name_ok}/{N}, right printing {print_ok}/{N}, battlefields {bf_ok}/{NB}; errors: {errs or 'none'}; photos + screenshots in {tmp}")
            return 1 if errs or name_ok < N * 0.75 or bf_ok < NB * 0.75 or not cam_ok else 0
    finally:
        srv.terminate()
if __name__ == "__main__": sys.exit(asyncio.run(main()))
