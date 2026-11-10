#!/usr/bin/env python3
"""Card picture fingerprints for the scanner (run after the card list changes; .github/workflows/cards.yml does it).

For every card picture the site uses (Riot's image, or TCGplayer's photo when there's none) it stores the 384 numbers
scan-ai.js makes from it, in cardvecs.bin (int8, one row per picture) + cardvecs.json:
  {model, dtype, dim, mean: [...], keys: [picture key, ...]}   key = the img file without ".png", or "tcg-<product id>"
Rows are centred on `mean` and scaled to length 127 (the site does the same to a photo, then the closest row wins).
Only pictures without a row yet are done (a few seconds each in a headless browser); the mean stays fixed once set.
Usage: python3 tools/embed_cards.py [--all]      (needs: pip install playwright; python -m playwright install chromium)"""
import asyncio, json, math, os, re, shutil, subprocess, sys, time, urllib.request
from playwright.async_api import async_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
TMP = os.path.join(ROOT, "build", "refs")
JSON, BIN = os.path.join(ROOT, "cardvecs.json"), os.path.join(ROOT, "cardvecs.bin")
RC = "https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/"
UA = {"User-Agent": "RiftboundDatabase/1.0 (+https://rbdatabase.pages.dev)"}

def picture_keys():
    """{key: download url} for every picture a card shows (same rule as scan's scKeyOf in the site)"""
    s = open(os.path.join(ROOT, "cards.js"), encoding="utf-8").read()
    out = {}
    for c in json.loads(re.search(r"RB_CARDS\s*=\s*(\[.*\])", s, re.S).group(1).rstrip(";")):
        if c.get("img"): out.setdefault(re.sub(r"\.png$", "", c["img"]), f"{RC}{c['img']}?accountingTag=RB&fm=jpg&q=85&w=320")
        elif c.get("imgTcg") and c.get("tcg"): out.setdefault("tcg-" + c["tcg"], f"https://tcgplayer-cdn.tcgplayer.com/product/{c['tcg']}_in_400x400.jpg")
    return out

def download(key, url):
    p = os.path.join(TMP, key + ".jpg")
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r: open(p, "wb").write(r.read())
            return True
        except Exception as e:
            print("retry", key, e, file=sys.stderr); time.sleep(2 * (i + 1))
    return False

async def fingerprint(keys):
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8791"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(); pg = await b.new_page()
            await pg.goto("http://127.0.0.1:8791/tools/embed.html"); await pg.wait_for_function("window.ready", timeout=60000)
            await pg.evaluate("window.ready")
            out = []
            for i in range(0, len(keys), 50):
                out += await pg.evaluate("s => vectors(s)", ["/build/refs/" + k + ".jpg" for k in keys[i:i + 50]])
                print(f"  {min(i + 50, len(keys))}/{len(keys)}", flush=True)
            await b.close(); return out
    finally:
        srv.terminate()

def main():
    want = picture_keys()
    old = json.load(open(JSON, encoding="utf-8")) if os.path.exists(JSON) and "--all" not in sys.argv else None
    rows = {}
    if old:
        raw = open(BIN, "rb").read(); d = old["dim"]
        for i, k in enumerate(old["keys"]): rows[k] = raw[i * d:(i + 1) * d]
    todo = [k for k in want if k not in rows]
    print(f"{len(want)} pictures, {len(todo)} to fingerprint")
    vecs = []
    if todo:
        shutil.rmtree(TMP, ignore_errors=True); os.makedirs(TMP)
        todo = [k for k in todo if download(k, want[k])]
        vecs = asyncio.run(fingerprint(todo))
        shutil.rmtree(TMP, ignore_errors=True)
    dim = len(vecs[0]) if vecs else old["dim"]
    mean = old["mean"] if old else [round(sum(v[j] for v in vecs) / len(vecs), 5) for j in range(dim)]
    for k, v in zip(todo, vecs):
        c = [x - m for x, m in zip(v, mean)]; n = math.sqrt(sum(x * x for x in c)) or 1
        rows[k] = bytes((round(x / n * 127)) & 0xFF for x in c)
    keys = [k for k in want if k in rows]        # pictures no card uses any more are dropped
    with open(BIN, "wb") as f:
        for k in keys: f.write(rows[k])
    with open(JSON, "w", encoding="utf-8") as f:
        json.dump({"model": "Xenova/dinov2-small", "dtype": "uint8", "dim": dim, "mean": mean, "keys": keys}, f, separators=(",", ":"))
    print(f"cardvecs: {len(keys)} pictures x {dim}")

if __name__ == "__main__":
    main()
