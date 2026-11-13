#!/usr/bin/env python3
"""Announced bans that aren't in effect yet (banSince in the future, from build/tcg/bans.txt).
Until that day the card shows "To Be Banned Nov 23" (amber) instead of "Banned", the grid tag reads "BAN NOV 23",
and decks aren't flagged as illegal yet. On the day itself (the visitor's own date) it turns into a normal ban by itself,
with no rebuild. The Banned filter chip shows both. Runs last in both pipelines (the tiles and deck checks come from later patches).
Usage: patch_ban_soon.py in.html out.html"""
import re, sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:70]!r}, found {n}"
    h = h.replace(old, new)

# mark not-yet-active bans once, when the page starts (local date, so it flips at midnight where the visitor is)
rep('function banPill(c){', r'''const BAN_TODAY = (() => { const d = new Date(); return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); })();
for (const c of (window.RB_CARDS || [])) if (c.ban && c.banSince && c.banSince > BAN_TODAY) c.banSoon = 1;
const banShort = d => { try { return new Date(d + "T12:00:00").toLocaleDateString("en-US", {month:"short", day:"numeric"}); } catch(e){ return d; } };
function banPill(c){
  if (c && c.banSoon) return `<span class="pill ban soon" title="${esc(`Announced: ${c.ban === "2v2" ? "banned in 2v2" : "banned in competitive play (Standard and 2v2)"} from ${fmtDate(c.banSince)}. Still legal until then.`)}">To Be Banned ${banShort(c.banSince)}</span>`;''')

rep('.tag.ban{color:var(--fury)}',
    '.tag.ban{color:var(--fury)}\n'
    '.pill.ban.soon{color:var(--warn);border-color:color-mix(in srgb,var(--warn) 55%,var(--line));background:color-mix(in srgb,var(--warn) 12%,transparent)}\n'
    '.tban.soon{background:var(--warn);color:#1a1a1a}\n'
    '.tag.bansoon{color:var(--warn)}')

# grid picture tag
T = '<span class="tban">${c.ban === "2v2" ? "2v2 BAN" : "BANNED"}</span>'
n = h.count(T); assert n >= 1, n
h = h.replace(T, '${c.banSoon ? `<span class="tban soon">BAN ${banShort(c.banSince).toUpperCase()}</span>` : `' + T + '`}')

# deck legality: only bans already in effect make a deck illegal
h, k = re.subn(r'\b(\w+)\.ban === "std"', r'(\1.ban === "std" && !\1.banSoon)', h)
assert k >= 1, k

# info sheet legality: "Standard: Legal until Nov 23" in amber while a ban is only announced
if 'const legal = (fmt, banned) =>' in h:  # website + local both have the info sheet, but stay safe
    rep('const legal = (fmt, banned) => `<span class="lgl${banned ? " no" : ""}">${fmt}: ${banned ? "Banned" : "Legal"}</span>`;',
        'const legal = (fmt, banned) => banned && c.banSoon ? `<span class="lgl soon" title="Banned from ${esc(fmtDate(c.banSince))}">${fmt}: Legal until ${banShort(c.banSince)}</span>` : `<span class="lgl${banned ? " no" : ""}">${fmt}: ${banned ? "Banned" : "Legal"}</span>`;')
    rep('legal("Standard", (c.ban === "std" && !c.banSoon))', 'legal("Standard", c.ban === "std")')
    rep('.lgl.no{', '.lgl.soon{color:var(--warn);border-color:color-mix(in srgb,var(--warn) 55%,var(--line));background:color-mix(in srgb,var(--warn) 12%,transparent)}\n.lgl.no{')

rep("Riot's ban list as of September 18, 2026", "Riot's ban list as of November 13, 2026")
rep("<b>Banned in 2v2</b> cards are still legal in 1v1.",
    "<b>Banned in 2v2</b> cards are still legal in 1v1. <b>To Be Banned</b> cards are announced but still legal until the date shown.")
rep('title="Show only cards banned from competitive play"', 'title="Show only cards banned from competitive play (and ones announced to be banned soon)"')

open(out, "w", encoding="utf-8").write(h)
print("ok", n, "tiles,", k, "deck checks")
