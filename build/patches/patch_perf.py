#!/usr/bin/env python3
"""Lighter on the computer, so videos in other tabs/windows don't stutter (website; runs last, after patch_winter.py).
- Foil shine: still moves on every foil card (it was briefly hover-only; Brandon asked for it back). It's the heaviest
  animation on the page (color-dodge, repainted every frame), so it's covered by the pause below.
- Sound: the Web Audio context (only a fallback for the offer chime) used to be woken on every tap and left running,
  which keeps an audio stream open in Chrome all the time. Now it's only woken until the <audio> chime is unlocked, and
  it's suspended once the chime works (and after a fallback chime finishes).
- Animations pause while the window is not focused (html.rb-idle), so a page on another monitor draws nothing.
Usage: patch_perf.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

# (the foil shine keeps moving on every foil card, Brandon asked for it back; it pauses with the rest below)

# sound: let the Web Audio context rest unless it's needed
rep('''function audioCtx(){''',
    '''function audioRest(){ try { if (actx && actx.state === "running"){ const r = actx.suspend(); if (r && r.catch) r.catch(() => {}); } } catch(e){} }
function audioCtx(){''')
rep('''function soundWake(){
  audioCtx();''',
    '''function soundWake(){
  if (!chimeOK) audioCtx(); else if (Date.now() - chimeAt > CHIME_LEN * 1000) audioRest();''')
rep('''if (ok){ el.pause(); el.currentTime = 0; chimeOK = true; }''',
    '''if (ok){ el.pause(); el.currentTime = 0; chimeOK = true; audioRest(); }''')
rep('''s.connect(a.destination); s.start(); }''',
    '''s.connect(a.destination); s.start(); setTimeout(audioRest, CHIME_LEN * 1000 + 300); }''')

# while you're in another window (e.g. a video on the other monitor), every animation on the page pauses where it is
# (the Halloween / Winter decorations would otherwise make Chrome draw new frames nonstop); clicking back resumes them
rep('''.thumb.foil:hover .sheen{opacity:.8}''',
    '''.thumb.foil:hover .sheen{opacity:.8}
html.rb-idle *,html.rb-idle *::before,html.rb-idle *::after{animation-play-state:paused!important}''')
rep('''function audioCtx(){''',
    '''const rbIdle = () => document.documentElement.classList.toggle("rb-idle", !document.hasFocus());
addEventListener("blur", rbIdle); addEventListener("focus", rbIdle); document.addEventListener("visibilitychange", rbIdle); rbIdle();
function audioCtx(){''')

open(out, "w", encoding="utf-8").write(h)
print("ok")
