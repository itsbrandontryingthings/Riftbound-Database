#!/usr/bin/env python3
"""New-offer sound that actually plays (website; runs last, after patch_offer_live.py).
Before, the poro coin was drawn live with Web Audio and gave up silently when the browser had it paused: on iPhones
(muted by the ring/silent switch, paused after switching apps), and on any page nobody had tapped since it loaded.
- The poro coin is rendered once (OfflineAudioContext) into a short WAV and played with an <audio> element, which
  iPhones play even on silent and desktop browsers allow once the site has had a click. Web Audio is the fallback.
- The clip is brought up to a clear level (the live chime peaked at about 15% volume, easy to miss on a phone).
- Every tap / click / key press (not just the first) wakes the sound up and unlocks the <audio> element.
- If the browser still blocks it, a note pops up: "New offer! Tap anywhere on the page to turn on sounds." (once a visit).
Usage: patch_sound.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

# waking the sound before anyone has tapped is refused by some browsers: ignore that quietly
rep('''if (actx.state === "suspended") actx.resume(); return actx; }''', '''if (actx.state !== "running" && actx.state !== "closed"){ const r = actx.resume(); if (r && r.catch) r.catch(() => {}); } return actx; }''')
# the sound itself, drawn into any audio context (live or offline)
rep('''function poroCoin(){
  const a = audioCtx(); if (!a || a.state !== "running") return;''', '''function poroGraph(a){''')

rep('''// browsers only allow sound after the first click or key press on the page
["pointerdown", "keydown"].forEach(ev => addEventListener(ev, () => audioCtx(), { once: true, capture: true }));
function coinChime(){ poroCoin(); }''', r'''// browsers only allow sound after a click or key press on the page, and phones pause it again (silent switch,
// switching apps), so every tap wakes it up. The chime plays as a little WAV in an <audio> element (iPhones play those
// even on silent); Web Audio is the fallback.
let chimeEl = null, chimeBusy = null, chimeOK = false, chimeWarned = false;
function wavBlob(buf){
  const d = buf.getChannelData(0), n = d.length, v = new DataView(new ArrayBuffer(44 + n * 2)), sr = buf.sampleRate;
  const w = (o, s) => { for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); };
  w(0, "RIFF"); v.setUint32(4, 36 + n * 2, true); w(8, "WAVE"); w(12, "fmt "); v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
  v.setUint32(24, sr, true); v.setUint32(28, sr * 2, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true); w(36, "data"); v.setUint32(40, n * 2, true);
  let peak = 0; for (let i = 0; i < n; i++) peak = Math.max(peak, Math.abs(d[i]));
  const gain = peak > 0 ? Math.min(5, 0.7 / peak) : 1;   // the live chime was very quiet: bring it up to a clear level
  for (let i = 0; i < n; i++){ const s = Math.max(-1, Math.min(1, d[i] * gain)); v.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true); }
  return new Blob([v], { type: "audio/wav" });
}
function chimeReady(){
  if (chimeEl) return Promise.resolve(chimeEl);
  return chimeBusy ||= (async () => {
    const OAC = window.OfflineAudioContext || window.webkitOfflineAudioContext; if (!OAC) return null;
    const sr = 44100, oc = new OAC(1, Math.round(sr * 1.8), sr); poroGraph(oc);
    const buf = await new Promise((ok, no) => { const p = oc.startRendering(); if (p && p.then) p.then(ok, no); else oc.oncomplete = e => ok(e.renderedBuffer); });
    const el = new Audio(URL.createObjectURL(wavBlob(buf))); el.preload = "auto"; el.setAttribute("playsinline", "");
    return chimeEl = el;
  })().catch(() => null);
}
setTimeout(chimeReady, 800);
function soundWake(){
  audioCtx();
  const el = chimeEl; if (!el || chimeOK) return;
  // play it silently once inside the tap, so later plays (with no tap) are allowed
  el.muted = true; const p = el.play();
  if (p && p.then) p.then(() => { el.pause(); el.currentTime = 0; el.muted = false; chimeOK = true; }, () => { el.muted = false; });
}
["pointerdown", "touchend", "click", "keydown"].forEach(ev => addEventListener(ev, soundWake, { capture: true, passive: true }));
async function coinChime(){
  const el = chimeEl || await chimeReady();
  if (el){ try { el.pause(); el.muted = false; el.currentTime = 0; await el.play(); chimeOK = true; return true; } catch(e){} }
  const a = audioCtx();
  if (a && a.state !== "running"){ try { await a.resume(); } catch(e){} }
  if (a && a.state === "running"){ poroGraph(a); return true; }
  return false;
}
function poroCoin(){ return coinChime(); }
// the new-offer sound: if the browser blocks it, say how to turn sounds on
async function offerChime(){
  if (await coinChime() || chimeWarned) return;
  chimeWarned = true;
  if (typeof toast === "function") toast("🔔 New offer! Tap anywhere on the page to turn on sounds.", 6000);
}''')

rep('''    if (fresh.length && !first && offerSound()) coinChime();''', '''    if (fresh.length && !first && offerSound()) offerChime();''')
rep('''  if (fresh.length && old && offerSound()) coinChime();''', '''  if (fresh.length && old && offerSound()) offerChime();''')

open(out, "w", encoding="utf-8").write(h)
print("ok")
