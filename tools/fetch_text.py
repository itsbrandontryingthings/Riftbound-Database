#!/usr/bin/env python3
"""Fetch every card's rules text, stats, flavour and artist from Riftcodex and write text.js for the site.

text.js sets window.RB_TEXT = {
  updated: "YYYY-MM-DD",
  n: { "<normalized base name>": [energy, might, power, text, flavour, tags, supertype] },
  a: { "<riftbound_id or tcg:<tcgplayer id>>": artist }
}
Rules text keeps Riftcodex's markers: [Keyword], [>] (separates a cost from its effect),
:rb_might:, :rb_energy_N:, :rb_exhaust:, :rb_rune_<domain>: and :rb_rune_rainbow:.
Usage: python3 tools/fetch_text.py text.js
"""
import json, re, sys, time, html, datetime, urllib.request

API = "https://api.riftcodex.com/cards?size=100&page={}"
TAGS = ["Alternate Art", "Overnumbered", "Signature", "Metal", "Starter", "GG EZ", "Launch Exclusive", "Ultimate", "Special"]
TAG_RE = re.compile(r"\s*\((%s)\)\s*$" % "|".join(re.escape(t) for t in TAGS))

def norm(n):
    n = TAG_RE.sub("", n)
    return re.sub(r"[^a-z0-9]+", " ", n.lower().replace(", ", " - ", 1)).strip()

def get(url):
    for i in range(5):
        try:
            req = urllib.request.Request(url, headers={"user-agent": "rbdatabase-text/1.0 (+https://rbdatabase.pages.dev)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:
            print("retry", url, e, file=sys.stderr); time.sleep(3 * (i + 1))
    raise SystemExit("could not fetch " + url)

def clean_flavour(f):
    """Riftcodex flavour text drops the opening quote mark, keeps the closing one, and sometimes has stray
    formatting (<em?, </e>, \r, blank lines of spaces). Returns the quote, plus "\n— Speaker" when it names one."""
    t = (f or "").replace("\r", "")
    t = re.sub(r"</?[a-z]+(?:\s[^<>]*)?>", "", t)                # <em>, </em>, <br />
    t = re.sub(r"</?em?\??", "", t)                              # broken "<em?", "</e", "</em"
    t = html.unescape(t).replace(" ", " ")
    t = "\n".join(l.strip() for l in t.split("\n"))
    t = re.sub(r"\n{2,}", "\n", t).strip()
    t = re.sub(r"[ \t]{2,}", " ", t)
    who = ""
    m = re.search(r'(?:^|\n|["”]\s*)[-–—]\s*([^\n"“”-][^\n"“”]*?)\s*$', t)
    if m and len(m.group(1)) <= 40:
        who, t = m.group(1).strip(), t[:m.start()].rstrip()
    t = t.strip().strip('"“”').strip()
    return t + ("\n— " + who if who else "")

def plain(rich):
    t = (rich or "").replace("\r", "")
    t = re.sub(r"<br\s*/?>", "\n", t)
    t = re.sub(r"</p>\s*<p>", "\n", t)
    t = re.sub(r"<li>", "\n• ", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(t)
    t = re.sub(r"\n{2,}", "\n", t).strip()
    t = re.sub(r"[ \t]{2,}", " ", t)
    return "" if t == "[NO TEXT]" else t

TCG = "https://tcgcsv.com/tcgplayer/89/"
SUP = {"Champion Unit": "Champion", "Legend": "Champion", "Signature Unit": "Signature", "Signature Spell": "Signature",
       "Signature Gear": "Signature", "Rune": "Basic"}

def tcg_fallback(names):
    """A set Riftcodex hasn't added yet (Radiance, at release): take text and stats from TCGplayer (via tcgcsv.com)
    for card names Riftcodex doesn't have. Plain words, no :rb_…: icons. Riftcodex wins as soon as it has the card."""
    have = {s["set_id"] for s in get("https://api.riftcodex.com/sets").get("items", [])}
    num = lambda v: int(v) if str(v or "").isdigit() else None
    added = 0
    for g in get(TCG + "groups").get("results", []):
        if g.get("abbreviation") in have: continue
        for p in get(TCG + f"{g['groupId']}/products").get("results", []):
            ed = {e["name"]: e["value"] for e in p.get("extendedData") or []}
            if not ed.get("Number") or not ed.get("Card Type"): continue
            key = norm(re.sub(r"\s*\([^()]+\)\s*$", "", p["name"]))
            if key in names: continue
            names[key] = [num(ed.get("Energy Cost")), num(ed.get("Might")), num(ed.get("Power Cost")),
                          plain(ed.get("Description")), clean_flavour(ed.get("Flavor Text")),
                          ",".join(t for t in (ed.get("Tag") or "").split(";") if t), SUP.get(ed["Card Type"], "")]
            added += 1
        time.sleep(0.3)
    print(f"{added} card names from TCGplayer (sets Riftcodex doesn't have yet)")

def main(out):
    items, page, pages = {}, 1, 1
    while page <= pages:
        j = get(API.format(page)); pages = j.get("pages", 1)
        for c in j.get("items", []): items[c["id"]] = c
        page += 1; time.sleep(0.3)
    if len(items) < 500: raise SystemExit(f"only {len(items)} cards came back; not writing")
    names, artists = {}, {}
    # regular printings first, so their text wins over promos with the same name
    for c in sorted(items.values(), key=lambda c: (bool(TAG_RE.search(c["name"])), c.get("riftbound_id", ""))):
        a, cl, tx = c.get("attributes") or {}, c.get("classification") or {}, c.get("text") or {}
        key = norm(c["name"])
        row = [a.get("energy"), a.get("might"), a.get("power"), plain(tx.get("rich") or tx.get("plain")),
               clean_flavour(tx.get("flavour")), ",".join(c.get("tags") or []), cl.get("supertype") or ""]
        if key not in names or (not names[key][3] and row[3]): names[key] = row
        art = ((c.get("media") or {}).get("artist") or "").strip()
        if art:
            if c.get("riftbound_id"): artists[c["riftbound_id"]] = art
            if c.get("tcgplayer_id"): artists["tcg:" + str(c["tcgplayer_id"])] = art
    tcg_fallback(names)
    data = {"updated": datetime.date.today().isoformat(), "n": names, "a": artists}
    with open(out, "w", encoding="utf-8") as f:
        f.write("window.RB_TEXT=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print(f"{len(items)} printings, {len(names)} card names, {len(artists)} artists -> {out}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "text.js")
