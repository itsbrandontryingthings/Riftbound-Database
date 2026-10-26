"""Quiet sound wake-up (website only, last).

To let phones play the offer chime later without a tap, the first tap on the page played the chime itself with
el.muted = true and paused it at once. Phones (iPhones above all) don't reliably honour muted on an <audio> element,
so the full poro sound played on the first tap of every visit / refresh, even with no offer. Now the wake-up plays a
short silent WAV (`chimeSil`) in the same element, then switches it back to the chime (`chimeSrc`); the element stays
unlocked (the same trick howler.js uses), and nothing can be heard even if muted is ignored.
Usage: patch_quiet_wake.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

rep('let chimeEl = null, chimeBuf = null,', 'let chimeSrc = "", chimeSil = "", chimeEl = null, chimeBuf = null,')
rep('    const el = new Audio(URL.createObjectURL(wavBlob(buf)));',
    '    chimeSrc = URL.createObjectURL(wavBlob(buf));\n'
    '    chimeSil = URL.createObjectURL(wavBlob({ sampleRate: sr, getChannelData: () => new Float32Array(Math.round(sr * 0.05)) }));\n'
    '    const el = new Audio(chimeSrc);')
# the wake-up plays silence, never the chime
rep('chimeWaking = true; el.muted = true; const p = el.play();',
    'chimeWaking = true; el.muted = true; el.src = chimeSil; const p = el.play();')
rep('const done = ok => { if (!chimeWaking) return; chimeWaking = false; if (ok){ el.pause(); el.currentTime = 0; chimeOK = true; audioRest(); } el.muted = false; };',
    'const done = ok => { if (!chimeWaking) return; chimeWaking = false; if (ok){ el.pause(); chimeOK = true; audioRest(); } el.src = chimeSrc; el.muted = false; };')
# a real chime started during the wake-up switches back to the chime first
rep('if (el){ chimeWaking = false; try { el.pause(); el.muted = false;',
    'if (el){ chimeWaking = false; try { el.pause(); if (el.src !== chimeSrc) el.src = chimeSrc; el.muted = false;')

open(out, "w", encoding="utf-8").write(h)
