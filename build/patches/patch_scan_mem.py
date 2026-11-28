#!/usr/bin/env python3
"""Scanner memory fix (website only, last; after patch_scan + patch_scan_ai).
Tesseract.js keeps about 1.7 MB more after every read and never gives it back, so a long scan grew the page by
hundreds of MB until phone browsers closed it ("the scanner crashes"). Measured in Chromium: +68 MB every 40 reads,
without end; the picture model (scan-ai.js) stays flat.
- The text reader is swapped for a fresh one after SC_RECYCLE reads (`scRecycle`), which frees all of its memory;
  never while a read is under way (`sc.reading`). The next read starts the new one (~1 s, nothing downloaded again).
- The camera picture's canvas is reused (only resized when its size changes) and kept in ordinary memory.
- With the picture model working, the text reader only runs for battlefields (▭ Battlefield on, or a battlefield is the
  best match): both at once crashed iPhones after the first card.
- Closing the scanner (Done) shuts the text reader down too, so the page doesn't keep it between scans.
Usage: patch_scan_mem.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

rep('''async function scLook(w){
  let all = {text: "", words: []}, m = null;''', '''// Tesseract leaks a little memory on every read: after SC_RECYCLE reads it's swapped for a fresh one (frees it all)
const SC_RECYCLE = 24;
function scRecycle(force){
  if (!sc.worker || sc.reading || (!force && (sc.reads || 0) < SC_RECYCLE)) return;
  const w = sc.worker; sc.worker = null; sc.ready = null; sc.tm = undefined; sc.reads = 0;
  try { w.terminate(); } catch(e){}
}
async function scLook(w){
  sc.reading = (sc.reading || 0) + 1;
  try { return await scLook1(w); }
  finally { sc.reading--; scRecycle(!$("sc-dlg").open); }
}
async function scLook1(w){
  let all = {text: "", words: []}, m = null;''')
rep('''    const d = (await w.recognize(flip ? scFlipped() : scCan)).data;''',
    '''    const d = (await w.recognize(flip ? scFlipped() : scCan)).data; sc.reads = (sc.reads || 0) + 1;''')
rep('''  sc.stream = null; $("sc-video").srcObject = null;
}''', '''  sc.stream = null; $("sc-video").srcObject = null;
  setTimeout(() => { if (!$("sc-dlg").open) scRecycle(true); }, 0);
}''')

# the camera picture: the canvas is only resized when its size changes (resizing every look made a new picture buffer
# each time), and it's kept in ordinary memory (willReadFrequently), since every look reads its pixels back
rep('''const scCan = document.createElement("canvas");''', '''const scCan = document.createElement("canvas"), scCx = scCan.getContext("2d", {willReadFrequently: true});''')
rep('''  scCan.width = W; scCan.height = Math.round(hh * W / w);
  scCan.getContext("2d").drawImage(v, x, y, w, hh, 0, 0, scCan.width, scCan.height);''', '''  const H = Math.round(hh * W / w);
  if (scCan.width !== W) scCan.width = W;
  if (scCan.height !== H) scCan.height = H;
  scCx.drawImage(v, x, y, w, hh, 0, 0, W, H);''')

# only battlefields need their text read as well (they look alike); for every other card the picture is enough. Running
# the text reader beside the picture model was too much for iPhones: the scanner found one card, then the page crashed
rep('''      if (sc.ai.sim >= SC_SURE || sc.ai.sim < 0.4) return c;''', '''      if (sc.ai.sim >= SC_SURE || sc.ai.sim < 0.4) return c;
      if (!sc.wide && !(c && c.type === "Battlefield")) return c;''')

open(out, "w", encoding="utf-8").write(h)
