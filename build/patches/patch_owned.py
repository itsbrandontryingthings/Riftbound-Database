"""Owned cards look like the others (last in both pipelines).

The base page faded cards you own (opacity .62, darker background) so missing ones stood out; Brandon wants them all
the same. Owned cards now only differ by the green copy count and price.
Usage: patch_owned.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

rep('.card.got{background:var(--panel);opacity:.62}\n.card.got:hover,.card.got:focus-within{opacity:.9}\n', '')

open(out, "w", encoding="utf-8").write(h)
