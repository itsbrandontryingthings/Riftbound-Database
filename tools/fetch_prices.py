#!/usr/bin/env python3
"""Daily prices for the website (run by .github/workflows/prices.yml every day after tcgcsv.com updates, ~20:00 UTC).

Fetches every Riftbound product's TCGplayer prices from tcgcsv.com (category 89), keeps the main price of each card
for the last ~40 days in build/prices/history.json, and writes prices.js:
  window.RB_PRICES = {updated, p: {productId: [market, lowest, foilMarket, foilLowest, change7, change30]}}
Prices are USD; a missing value is null (trailing nulls are left off). The main price is the regular printing's market
price, or the foil one when only foil exists (the same as `price` in cards.js). change7 / change30 = % change of the
main price since about 7 / 30 days ago (null until there's a price that old in the history).
Only products in cards.js are written. tcgcsv's own daily archive isn't downloadable, so the history was seeded from
earlier cards.js versions (Oct 13 and Oct 23, 2026) and grows by one day per run.
Usage: python3 tools/fetch_prices.py [repo root]"""
import datetime, json, os, re, sys, urllib.request

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), ".."))
HIST = os.path.join(ROOT, "build", "prices", "history.json")
API = "https://tcgcsv.com/tcgplayer/89"
UA = {"User-Agent": "RiftboundDatabase/1.0 (+https://rbdatabase.pages.dev)"}
KEEP_DAYS = 40

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read().decode("utf-8")

def card_ids():
    s = open(os.path.join(ROOT, "cards.js"), encoding="utf-8").read()
    cards = json.loads(re.search(r"RB_CARDS\s*=\s*(\[.*\])", s, re.S).group(1).rstrip(";"))
    return {str(c["tcg"]) for c in cards if c.get("tcg")}

def main_price(row):
    """[market, lowest, foil market, foil lowest] -> the main price (regular, else foil)"""
    m, l, fm, fl = row
    return m if m is not None else l if l is not None else fm if fm is not None else fl

def snapshot(hist, today, days, slack):
    """the history day closest to `days` ago (within `slack` days): {productId: main price}, or None"""
    best = None
    for d, prices in hist.items():
        age = (today - datetime.date.fromisoformat(d)).days
        if abs(age - days) <= slack and (best is None or abs(age - days) < abs(best[0] - days)): best = (age, prices)
    return best[1] if best else None

def main():
    ids = card_ids()
    updated = get("https://tcgcsv.com/last-updated.txt").strip()[:10]
    today = datetime.date.fromisoformat(updated)
    rows = {}
    for g in json.loads(get(f"{API}/groups"))["results"]:
        for p in json.loads(get(f"{API}/{g['groupId']}/prices"))["results"]:
            pid = str(p["productId"])
            if pid not in ids: continue
            r = rows.setdefault(pid, [None, None, None, None])
            foil = (p.get("subTypeName") or "").lower().startswith("foil")
            r[2 if foil else 0] = p.get("marketPrice"); r[3 if foil else 1] = p.get("lowPrice")
    hist = json.load(open(HIST, encoding="utf-8")) if os.path.exists(HIST) else {}
    hist[updated] = {pid: main_price(r) for pid, r in rows.items() if main_price(r) is not None}
    hist = {d: v for d, v in sorted(hist.items()) if (today - datetime.date.fromisoformat(d)).days <= KEEP_DAYS}
    out = {}
    for pid, r in rows.items():
        now = main_price(r); vals = [None if v is None else round(v, 2) for v in r]
        for days, slack in ((7, 2), (30, 4)):
            old = snapshot({d: v for d, v in hist.items() if d != updated}, today, days, slack)
            o = old.get(pid) if old else None
            vals.append(round((now - o) / o * 100) if now is not None and o else None)
        while vals and vals[-1] is None: vals.pop()
        out[pid] = vals
    os.makedirs(os.path.dirname(HIST), exist_ok=True)
    with open(HIST, "w", encoding="utf-8") as f: json.dump(hist, f, separators=(",", ":"), sort_keys=True)
    with open(os.path.join(ROOT, "prices.js"), "w", encoding="utf-8") as f:
        f.write("window.RB_PRICES = " + json.dumps({"updated": updated, "p": out}, separators=(",", ":")) + ";\n")
    print(f"prices {updated}: {len(out)} products, history {len(hist)} days ({min(hist)} to {max(hist)})")

if __name__ == "__main__":
    main()
