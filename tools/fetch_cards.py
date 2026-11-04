#!/usr/bin/env python3
"""Monday card list refresh (run by .github/workflows/cards.yml, or by hand): rebuilds cards.js.

Reads every card from Riftcodex, adds pictures of new cards to build/tcg/images.txt, a new set to build/tcg/sets.txt,
and TCGplayer prices (via tcgcsv.com) to build/tcg/prices.txt, then runs build/patches/build.py with build/tcg/*.
Card ids stay as they are: collections are saved by id, so a printing that moves from a temporary "tcg-<product>" id
to a Riftcodex one (Radiance, once Riftcodex lists it) keeps its old id.
cards.js is only replaced if the new one is safe (`check`): Riftcodex gave every card, and printings, prices and pictures
didn't drop by more than MAX_DROP, and no more than MAX_LOST ids vanished. Otherwise it stops with an error and
changes nothing, and GitHub marks the run as failed.
Usage: python3 tools/fetch_cards.py [--dry-run]     (--dry-run prints what would change and writes nothing)"""
import json, os, re, shutil, subprocess, sys, time, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_prices import fetch_rows

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
TCG = os.path.join(ROOT, "build", "tcg")
RAW = os.path.join(ROOT, "build", "raw")
API = "https://api.riftcodex.com"
UA = {"User-Agent": "RiftboundDatabase/1.0 (+https://rbdatabase.pages.dev)"}
MAX_DROP, MAX_LOST = 20, 0
FILE = re.compile(r"game_data_live/([0-9a-f]{40}-\d+x\d+\.[a-z]+)\?")

def get(url):
    for i in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.load(r)
        except Exception as e:
            print("retry", url, e, file=sys.stderr); time.sleep(3 * (i + 1))
    raise SystemExit("could not fetch " + url)

def all_cards():
    first = get(f"{API}/cards?size=100&page=1")
    items = list(first["items"])
    for p in range(2, first["pages"] + 1): items += get(f"{API}/cards?size=100&page={p}")["items"]
    if len({c["id"] for c in items}) != first["total"]: raise SystemExit(f"Riftcodex gave {len(items)} of {first['total']} cards")
    return items

def clean(v):
    return str(v if v is not None else "").replace("|", " ").replace("\n", " ").strip()

def write_raw(items):
    shutil.rmtree(RAW, ignore_errors=True); os.makedirs(RAW)
    by = {}
    # a fixed order: Riftcodex's varies, and on repeated rows the build keeps what comes first
    for c in sorted(items, key=lambda c: (c.get("collector_number") or 0, c.get("riftbound_id") or "", c["name"])):
        k, rid = c.get("classification") or {}, c.get("riftbound_id")
        if not rid: continue
        by.setdefault(rid.split("-")[0], []).append("|".join(clean(v) for v in (rid, c["name"], c["collector_number"], k.get("type"), k.get("supertype"), k.get("rarity"), ",".join(k.get("domain") or []), c.get("tcgplayer_id"))))
    for s, rows in by.items():
        with open(os.path.join(RAW, s + ".txt"), "w", encoding="utf-8") as f: f.write("\n".join(rows) + "\n")

def new_images(items):
    """lines for images.txt: cards it doesn't have yet (existing lines are never changed)"""
    f = os.path.join(TCG, "images.txt")
    have = {l.split("|")[0] for l in open(f, encoding="utf-8") if "|" in l and not l.startswith("#")}
    out = []
    for c in items:
        rid = c.get("riftbound_id"); m = FILE.search((c.get("media") or {}).get("image_url") or "")
        if rid and rid not in have and m:
            have.add(rid); out.append("|".join((rid, clean(c.get("tcgplayer_id")), m.group(1), clean(c["name"]))))
    return out

def new_sets():
    """sets Riftcodex has that the build doesn't know yet, as sets.txt lines (newest added last, shown first)"""
    src = open(os.path.join(ROOT, "build", "patches", "build.py"), encoding="utf-8").read()
    f = os.path.join(TCG, "sets.txt")
    known = set(re.findall(r'\("([A-Z0-9]+)", "', src)) | ({l.split("|")[0] for l in open(f, encoding="utf-8")} if os.path.exists(f) else set())
    out = []
    for s in get(f"{API}/sets")["items"]:
        if s["set_id"] not in known: out.append("|".join((s["set_id"], clean(s["name"]), clean(s.get("publish_date") or s.get("release_date"))[:10])))
    return out

def merged_prices():
    """prices.txt with today's prices: the regular market price, else the foil one (marked f when no regular printing exists)"""
    old = {}
    for t in open(os.path.join(TCG, "prices.txt"), encoding="utf-8").read().replace("\n", ",").split(","):
        if ":" in t: k, v = t.strip().split(":"); old[k] = v
    rows, normal = fetch_rows()
    for pid, (m, _, fm, _) in rows.items():
        if m is not None: old[pid] = str(m)
        elif fm is not None and pid not in normal: old[pid] = f"{fm}f"
    return ",".join(f"{k}:{v}" for k, v in old.items()) + "\n"

def load(path):
    s = open(path, encoding="utf-8").read()
    return json.loads(re.search(r"window\.RB_META=(.*?);\n", s).group(1)), json.loads(re.search(r"window\.RB_CARDS=(.*);\s*$", s, re.S).group(1))

def keep_ids(cards, old):
    """a printing keeps the id it has on the site (found by its TCGplayer product id)"""
    ids = {c["id"] for c in cards}
    by_tcg = {c["tcg"]: c["id"] for c in old if c.get("tcg") and c["id"] not in ids}
    moved = 0
    for c in cards:
        was = by_tcg.get(c.get("tcg"))
        if was and c["id"] not in {o["id"] for o in old}: c["id"] = was; moved += 1
    return moved

def check(meta, cards, old_meta, old):
    """reasons not to publish"""
    bad = []
    ids, old_ids = {c["id"] for c in cards}, {c["id"] for c in old}
    if len(ids) != len(cards): bad.append("duplicate card ids")
    lost = sorted(old_ids - ids)
    if len(lost) > MAX_LOST: bad.append(f"{len(lost)} card ids would vanish, and collections are saved by id: {lost[:12]}")
    if len(cards) < len(old) - MAX_DROP: bad.append(f"printings would drop from {len(old)} to {len(cards)}")
    if meta["priced"] < old_meta.get("priced", 0) - MAX_DROP: bad.append(f"priced cards would drop from {old_meta['priced']} to {meta['priced']}")
    pics = lambda m: sum(v for k, v in (m.get("images") or {}).items() if k != "none")
    if pics(meta) < pics(old_meta) - MAX_DROP: bad.append(f"cards with a picture would drop from {pics(old_meta)} to {pics(meta)}")
    return bad, lost

def main():
    dry = "--dry-run" in sys.argv
    items = all_cards()
    write_raw(items)
    imgs, sets, prices = new_images(items), new_sets(), merged_prices()
    keep = {n: open(os.path.join(TCG, n), "rb").read() if os.path.exists(os.path.join(TCG, n)) else None for n in ("images.txt", "prices.txt", "sets.txt")}
    out = os.path.join(ROOT, "build", "cards.new.js")
    try:
        if imgs:
            with open(os.path.join(TCG, "images.txt"), "a", encoding="utf-8") as f: f.write("\n".join(imgs) + "\n")
        if sets:
            with open(os.path.join(TCG, "sets.txt"), "a", encoding="utf-8") as f: f.write("\n".join(sets) + "\n")
        with open(os.path.join(TCG, "prices.txt"), "w", encoding="utf-8") as f: f.write(prices)
        subprocess.run([sys.executable, "-I", os.path.join(ROOT, "build", "patches", "build.py"), RAW, out], check=True, stdout=subprocess.DEVNULL)
        meta, cards = load(out)
        old_meta, old = load(os.path.join(ROOT, "cards.js"))
        moved = keep_ids(cards, old)
        bad, lost = check(meta, cards, old_meta, old)
        new = sorted({c["id"] for c in cards} - {c["id"] for c in old})
        print(f"{len(old)} -> {len(cards)} printings, priced {old_meta.get('priced')} -> {meta['priced']}, images {meta['images']}, {len(new)} new, {len(lost)} gone, {moved} kept their old id, {len(imgs)} new pictures, new sets {sets}")
        print("new:", new[:20]); print("gone:", lost[:20])
        if bad: raise SystemExit("NOT PUBLISHED: " + "; ".join(bad))
        if not dry:
            with open(os.path.join(ROOT, "cards.js"), "w", encoding="utf-8") as fh:
                fh.write("window.RB_META=" + json.dumps(meta, separators=(",", ":")) + ";\n")
                fh.write("window.RB_CARDS=" + json.dumps(cards, separators=(",", ":"), ensure_ascii=False) + ";\n")
            print("cards.js updated")
    except BaseException:
        dry = True; raise
    finally:
        if dry:                                   # leave the inputs as they were
            for n, b in keep.items():
                p = os.path.join(TCG, n)
                if b is None:
                    if os.path.exists(p): os.remove(p)
                else: open(p, "wb").write(b)
        shutil.rmtree(RAW, ignore_errors=True)
        if os.path.exists(out): os.remove(out)

if __name__ == "__main__":
    main()
