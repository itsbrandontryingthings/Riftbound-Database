#!/usr/bin/env python3
"""Normalize raw Riftcodex pipe rows into cards.js for the collection tracker.

Raw row format (one per line, files in raw/):
  riftbound_id|name|collector_number|type|supertype|rarity|domains|tcgplayer_id
Usage: python3 build.py raw_dir out_cards.js
       python3 build.py --images-only tcg_dir in_cards.js out_cards.js   (re-attach images to an existing cards.js)

Images (tcg/images.txt, from api.riftcodex.com /cards media.image_url):
  img     = Riftcodex image file; page URL = RC_IMG + img  (Riot CDN, resizable with &w=)
  imgTcg  = 1 -> no Riftcodex image; use TCGplayer's product photo for this tcg id
  imgBase = 1 -> no image of this exact printing; img is the regular printing's art
Bans (tcg/bans.txt): ban = "std" (banned in Standard and 2v2) or "2v2" (2v2 only), banSince = date
"""
import json, re, sys, glob, os, datetime

SETS = [  # code, name, release
    ("RAD", "Radiance", "2026-10-23"),
    ("VEN", "Vendetta", "2026-07-31"),
    ("UNL", "Unleashed", "2026-05-08"),
    ("SFD", "Spiritforged", "2026-02-13"),
    ("OGN", "Origins", "2025-10-31"),
    ("OGS", "Origins: Proving Grounds", "2025-10-31"),
    ("OPP", "Organized Play Promos", "2025-10-31"),
    ("PR", "Promotional Cards", "2025-10-31"),
    ("JDG", "Judge Promos", "2025-12-01"),
]
SET_ORDER = {c: i for i, (c, _, _) in enumerate(SETS)}
TAGS = ["Alternate Art", "Overnumbered", "Signature", "Metal", "Starter",
        "GG EZ", "Launch Exclusive", "Ultimate", "Special"]
TAG_RE = re.compile(r"\s*\((%s)\)\s*$" % "|".join(re.escape(t) for t in TAGS))

def parse(line):
    p = line.rstrip("\n").split("|")
    if len(p) < 7 or p[0] == "riftbound_id":
        return None
    p += [""] * (8 - len(p))
    rid, name, num, typ, sup, rar, dom, tcg = [x.strip() for x in p[:8]]
    if sup == "null": sup = ""
    return dict(rid=rid, name=name, num=int(num) if num.isdigit() else 0,
                type=typ, sup=sup, rarity=rar,
                domains=[d for d in dom.split(",") if d and d != "Colorless"],
                tcg=tcg if tcg.isdigit() else "")

def split_tag(name):
    m = TAG_RE.search(name)
    return (name[:m.start()], m.group(1)) if m else (name, "")

def _norm(n):
    return re.sub(r"[^a-z0-9]+", " ", n.lower().replace(", ", " - ", 1)).strip()

def attach_images(cards, tcg_dir):
    """Add img / imgTcg / imgBase to each card dict (list). Returns coverage counts."""
    for c in cards:
        for k in ("img", "imgTcg", "imgBase"): c.pop(k, None)
    by_rid, by_tcg = {}, {}
    f = os.path.join(tcg_dir, "images.txt")
    if os.path.exists(f):
        for line in open(f, encoding="utf-8"):
            if line.startswith("#") or "|" not in line: continue
            rid, tcg, fn = line.rstrip("\n").split("|")[:3]
            if rid not in by_rid or tcg: by_rid[rid] = fn
            if tcg: by_tcg[tcg] = fn
    photos = set()
    pf = os.path.join(tcg_dir, "tcg_photos.txt")
    if os.path.exists(pf):
        photos = {l.strip() for l in open(pf, encoding="utf-8") if l.strip() and not l.startswith("#")}
    n = dict(riftcodex=0, tcgplayer=0, base=0, none=0)
    # pass 1: exact printing
    for c in cards:
        fn = by_rid.get(c["id"].split("~")[0]) or by_tcg.get(c.get("tcg", ""))
        if fn: c["img"] = fn; n["riftcodex"] += 1
        elif c.get("tcg") in photos: c["imgTcg"] = 1; n["tcgplayer"] += 1
    # pass 2: borrow the regular printing's art (prefer no-variant, lowest set order)
    base = {}
    for c in sorted(cards, key=lambda c: (bool(c.get("variant")), SET_ORDER.get(c["set"], 99))):
        if c.get("img") and not c.get("imgBase"): base.setdefault(_norm(c["name"]), c["img"])
    # double-sided tokens: also index by front side, ignoring collector numbers ("Recruit (271) // Buff" -> "recruit")
    tok = {}
    for line in (open(os.path.join(tcg_dir, "images.txt"), encoding="utf-8") if os.path.exists(os.path.join(tcg_dir, "images.txt")) else []):
        if line.startswith("#") or " // " not in line: continue
        p = line.rstrip("\n").split("|")
        tok.setdefault(_norm(re.sub(r"\(\d+\)", "", p[3].split(" // ")[0])), p[2])
    for c in cards:
        if c.get("img") or c.get("imgTcg"): continue
        nm = _norm(c["name"])
        fn = base.get(nm) or base.get(_norm(c["name"].split(" // ")[0])) or tok.get(_norm(c["name"].split(" // ")[0]))
        if fn: c["img"] = fn; c["imgBase"] = 1; n["base"] += 1
        else: n["none"] += 1
    return n

def attach_bans(cards, tcg_dir):
    """Mark banned cards (every printing of a banned name). ban = "std" (Standard + 2v2) or "2v2"; banSince = date."""
    for c in cards:
        c.pop("ban", None); c.pop("banSince", None)
    f = os.path.join(tcg_dir, "bans.txt")
    if not os.path.exists(f): return 0
    bans = {}
    for line in open(f, encoding="utf-8"):
        if line.startswith("#") or "|" not in line: continue
        name, fmt, since = [x.strip() for x in line.split("|")[:3]]
        bans[_norm(name)] = (fmt, since)
    n = 0
    for c in cards:
        b = bans.get(_norm(c["name"]))
        if b: c["ban"], c["banSince"] = b; n += 1
    return n

def main(raw_dir, out):
    rows = []
    for f in sorted(glob.glob(os.path.join(raw_dir, "*.txt"))):
        for line in open(f, encoding="utf-8"):
            r = parse(line)
            if r: rows.append(r)

    cards = {}
    for r in rows:
        setc = r["rid"].split("-")[0].upper()
        base, tag = split_tag(r["name"])
        # Vendetta uses "Champion, Title"; match the other sets' "Champion - Title"
        if setc == "VEN" and r["sup"] == "Champion" and ", " in base and " - " not in base:
            base = base.replace(", ", " - ", 1)
        if base.startswith("Yordle, "):
            base = base[len("Yordle, "):]
        idpart = r["rid"].split("-")[1] if "-" in r["rid"] else ""
        if not tag:
            if re.fullmatch(r"\d+a", idpart): tag = "Alternate Art"
            elif idpart.endswith("*"): tag = "Signature"
            elif idpart.startswith("sp"): tag = "Special"
            elif setc == "VEN" and r["num"] > 166: tag = "Overnumbered"
        key = r["rid"] + ("~metal" if tag == "Metal" else "")
        c = dict(id=key, set=setc, num=r["num"], name=base, variant=tag,
                 type=r["type"], champ=r["sup"] == "Champion", sig=r["sup"] == "Signature",
                 token=r["sup"] == "Token", rarity=r["rarity"], domains=r["domains"], tcg=r["tcg"])
        old = cards.get(key)
        if old is None:
            cards[key] = c
        else:  # merge duplicate rows: keep a tcg id and the most descriptive name
            if not old["tcg"] and c["tcg"]: old["tcg"] = c["tcg"]
            if " - " in c["name"] and " - " not in old["name"]: old["name"] = c["name"]
            if c["variant"] and not old["variant"]: old["variant"] = c["variant"]

    # Vendetta legend rows sometimes lack the champion name: borrow it by domain pair
    legend_names = {}
    for c in cards.values():
        if c["type"] == "Legend" and " - " in c["name"]:
            legend_names[(c["set"], c["name"].split(" - ", 1)[1])] = c["name"]
    for c in cards.values():
        if c["type"] == "Legend" and " - " not in c["name"]:
            c["name"] = legend_names.get((c["set"], c["name"]), c["name"])

    tcg_dir = os.path.join(os.path.dirname(os.path.abspath(raw_dir)), "tcg")

    # Attach TCGplayer ids the card database lacks (by collector number, e.g. "084a", "sp1")
    vmap = os.path.join(tcg_dir, "ven_map.txt")
    if os.path.exists(vmap):
        by_num = {c["id"].split("-")[1]: c for c in cards.values() if c["set"] == "VEN" and not c["tcg"]}
        for line in open(vmap, encoding="utf-8"):
            pid, num = line.strip().split("|")
            if num.lower() in by_num: by_num[num.lower()]["tcg"] = pid

    add_extras(cards, tcg_dir)
    finish(cards, tcg_dir, out)

def add_extras(cards, tcg_dir):
    """TCGplayer-only printings (tcg/extras.txt): borrow type/champion flags from the regular printing.
    A 7th field, TCGplayer's card type ("Champion Unit", "Signature Spell", "Legend"…), is used for cards with no
    regular printing yet (a new set Riftcodex hasn't added). Rows whose product id is already known are skipped."""
    by_name = {}
    for c in cards.values(): by_name.setdefault(c["name"].lower(), c)
    known_tcg = {c["tcg"] for c in cards.values() if c["tcg"]}
    ext = os.path.join(tcg_dir, "extras.txt")
    if not os.path.exists(ext): return
    for line in open(ext, encoding="utf-8"):
        if not line.strip() or line.startswith("#"): continue
        p = line.rstrip("\n").split("|") + [""]
        setc, pid, name, num, rar, doms, ttype = p[:7]
        if pid in known_tcg: continue
        m = re.search(r"\s*\(([^()]+)\)\s*$", name)
        tag = m.group(1) if m else ("Promo" if setc in ("OPP", "PR", "JDG") else "")
        base = name[:m.start()] if m else name
        ref = by_name.get(base.lower()) or by_name.get(base.replace(", ", " - ", 1).lower())
        if ref: base = ref["name"]
        if ref: typ = ref["type"]
        elif ttype: typ = ttype.replace("Champion ", "").replace("Signature ", "")
        else: typ = "Rune" if base.endswith(" Rune") else "Battlefield" if tag == "Oversized" else "Unit"
        c = dict(id="tcg-" + pid, set=setc, num=int(re.sub(r"\D", "", num) or 0), name=base, variant=tag,
                 type=typ, champ=bool(ref["champ"]) if ref else ttype == "Champion Unit",
                 sig=bool(ref["sig"]) if ref else ttype.startswith("Signature "),
                 token=" // " in base, rarity=rar if rar in ("Common","Uncommon","Rare","Epic","Showcase","Promo") else "Promo",
                 domains=[d for d in doms.split(";") if d and d != "None"], tcg=pid)
        cards[c["id"]] = c

def finish(cards, tcg_dir, out):
    # Prices: "productId:price" (suffix f = only a foil printing exists, price is the foil price)
    prices = {}
    pf = os.path.join(tcg_dir, "prices.txt")
    if os.path.exists(pf):
        for tok in open(pf, encoding="utf-8").read().replace("\n", ",").split(","):
            if ":" not in tok: continue
            pid, p = tok.strip().split(":")
            prices[pid] = (float(p.rstrip("f")), p.endswith("f"))
    priced = 0
    for c in cards.values():
        c.pop("price", None); c.pop("foil", None)
        if c["tcg"] in prices:
            c["price"], foil = prices[c["tcg"]]; priced += 1
            if foil: c["foil"] = True

    out_list = sorted(cards.values(), key=lambda c: (SET_ORDER.get(c["set"], 99), c["num"], c["variant"] != "", c["id"]))
    for c in out_list:
        for k in ("champ", "sig", "token", "foil"):
            c.setdefault(k, False)
            if not c[k]: del c[k]
        if not c.get("variant"): c.pop("variant", None)
        if not c["tcg"]: del c["tcg"]
    images = attach_images(out_list, tcg_dir)
    banned = attach_bans(out_list, tcg_dir)
    counts = {}
    for c in out_list: counts[c["set"]] = counts.get(c["set"], 0) + 1
    pdate = datetime.date.fromtimestamp(os.path.getmtime(pf)).isoformat() if os.path.exists(pf) else ""
    fx = {}
    fxf = os.path.join(tcg_dir, "fx.txt")  # "rate|date" — Bank of Canada USD->CAD
    if os.path.exists(fxf):
        rate, fdate = open(fxf, encoding="utf-8").read().strip().split("|")
        fx = dict(usdcad=float(rate), date=fdate)
    meta = dict(updated=datetime.date.today().isoformat(), pricesUpdated=pdate, priced=priced, fx=fx, images=images, banned=banned,
                source="Riftcodex API (api.riftcodex.com) + TCGplayer via tcgcsv.com",
                sets=[dict(code=c, name=n, released=d, count=counts.get(c, 0)) for c, n, d in SETS if counts.get(c)])
    write_out(out, meta, out_list)

def write_out(out, meta, out_list):
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("window.RB_META=" + json.dumps(meta, separators=(",", ":")) + ";\n")
        fh.write("window.RB_CARDS=" + json.dumps(out_list, separators=(",", ":"), ensure_ascii=False) + ";\n")
    print(json.dumps(meta, indent=1))
    print("total", len(out_list))

def images_only(tcg_dir, src, out):
    s = open(src, encoding="utf-8").read()
    meta = json.loads(re.search(r"window\.RB_META=(.*?);\n", s).group(1))
    cards = json.loads(re.search(r"window\.RB_CARDS=(.*);\s*$", s, re.S).group(1))
    meta["images"] = attach_images(cards, tcg_dir)
    meta["banned"] = attach_bans(cards, tcg_dir)
    write_out(out, meta, cards)

def extras_only(tcg_dir, src, out):
    """Add new extras.txt rows to an existing cards.js and redo prices, images, bans and meta (no raw rows needed)."""
    s = open(src, encoding="utf-8").read()
    cards = {c["id"]: c for c in json.loads(re.search(r"window\.RB_CARDS=(.*);\s*$", s, re.S).group(1))}
    for c in cards.values():
        for k in ("champ", "sig", "token"): c.setdefault(k, False)
        c.setdefault("variant", ""); c.setdefault("tcg", "")
    add_extras(cards, tcg_dir)
    finish(cards, tcg_dir, out)

if __name__ == "__main__":
    if sys.argv[1] == "--images-only":
        images_only(sys.argv[2], sys.argv[3], sys.argv[4])
    elif sys.argv[1] == "--extras-only":
        extras_only(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        main(sys.argv[1], sys.argv[2])
