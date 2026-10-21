#!/usr/bin/env python3
"""Lighter on the computer, so videos in other tabs/windows don't stutter (website; runs last, after patch_winter.py).
- Foil shine: the rainbow (mix-blend-mode color-dodge) no longer moves forever on every foil card in the grid. It sits
  still, and only moves while the pointer is over a card or the card is open in the preview. Before, every foil card on
  screen was repainted every frame, which competed with video playback for the graphics card.
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

# foil shine: still by default, moving on hover and in the preview (.lbwrap.foil.live still turns it off for the tilt)
rep('''background-size:300% 300%;animation:foilmove 7s ease-in-out infinite}
.thumb.foil:hover .sheen{opacity:.8}''',
    '''background-size:300% 300%;background-position:50% 50%}
.thumb.foil:hover .sheen{opacity:.8;animation:foilmove 7s ease-in-out infinite}
.lbwrap.foil .sheen{animation:foilmove 7s ease-in-out infinite}''')

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
rep('''.lbwrap.foil .sheen{animation:foilmove 7s ease-in-out infinite}''',
    '''.lbwrap.foil .sheen{animation:foilmove 7s ease-in-out infinite}
html.rb-idle *,html.rb-idle *::before,html.rb-idle *::after{animation-play-state:paused!important}''')
rep('''function audioCtx(){''',
    '''const rbIdle = () => document.documentElement.classList.toggle("rb-idle", !document.hasFocus());
addEventListener("blur", rbIdle); addEventListener("focus", rbIdle); document.addEventListener("visibilitychange", rbIdle); rbIdle();
function audioCtx(){''')

open(out, "w", encoding="utf-8").write(h)
print("ok")
