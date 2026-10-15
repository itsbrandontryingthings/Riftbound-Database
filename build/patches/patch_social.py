#!/usr/bin/env python3
"""Link previews and the site icon (website; runs last, after patch_marketplace.py).
- Open Graph / Twitter tags in <head>, so a link to the site posted in Discord, iMessage, etc. shows a card with the
  title, a short description and og-image.jpg (1200 x 630).
- The RBDB logo (logo-512.png) as the browser tab icon and the phone home-screen icon; theme colour = site green.
og-image.jpg and logo-512.png sit at the repo root and are made from build/og/og.html and logo.html by
build/og/render.py. Discord remembers a link's preview for a while: to see a new picture straight away, post the link
with something on the end, like https://rbdatabase.pages.dev/?v=2.
Usage: patch_social.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

SITE = "https://rbdatabase.pages.dev/"
TITLE = "Riftbound Database (RBDB)"
DESC = "Every Riftbound card, printing and price in CAD + USD. Track your collection, check your decks and trade with friends."
rep('</style></head><body>', f'''</style>
<meta name="description" content="{DESC}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Riftbound Database">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{DESC}">
<meta property="og:url" content="{SITE}">
<meta property="og:image" content="{SITE}og-image.jpg">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Riftbound Database: the RBDB logo and a fan of Riftbound cards, with Shen in the middle">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{TITLE}">
<meta name="twitter:description" content="{DESC}">
<meta name="twitter:image" content="{SITE}og-image.jpg">
<meta name="theme-color" content="#8fc25a">
<link rel="icon" type="image/png" sizes="512x512" href="/logo-512.png">
<link rel="apple-touch-icon" href="/logo-512.png">
</head><body>''')

open(out, "w", encoding="utf-8").write(h)
print("patch_social: ok ->", out)
