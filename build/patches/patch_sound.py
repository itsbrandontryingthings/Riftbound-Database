#!/usr/bin/env python3
"""New-offer sound that actually plays (website; runs last, after patch_offer_live.py).
Before, the poro coin was drawn live with Web Audio and gave up silently when the browser had it paused: on iPhones
(muted by the ring/silent switch, paused after switching apps), and on any page nobody had tapped since it loaded.
- The poro coin is rendered once (OfflineAudioContext) into a short WAV and played with an <audio> element, which
  iPhones play even on silent and desktop browsers allow once the site has had a click. Web Audio is the fallback.
- Every play is the same recording at one fixed level (Web Audio fallback plays that same recording too), and
  a chime never starts on top of one that's still playing; the silent unlock never cuts off a real chime.
- The clip is set to one fixed level, peak 0.1225 (Brandon asked for half of the first 0.7, then 65% quieter than that; the live chime peaked at about 0.15).
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
// Every play is the same recording at the same level (chimeBuf, normalized once), and a chime never stacks on another.
let chimeEl = null, chimeBuf = null, chimeBusy = null, chimeOK = false, chimeWarned = false, chimeAt = 0, chimeWaking = false;
const CHIME_LEN = 1.8;
function wavBlob(buf){
  const d = buf.getChannelData(0), n = d.length, v = new DataView(new ArrayBuffer(44 + n * 2)), sr = buf.sampleRate;
  const w = (o, s) => { for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); };
  w(0, "RIFF"); v.setUint32(4, 36 + n * 2, true); w(8, "WAVE"); w(12, "fmt "); v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
  v.setUint32(24, sr, true); v.setUint32(28, sr * 2, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true); w(36, "data"); v.setUint32(40, n * 2, true);
  for (let i = 0; i < n; i++){ const s = Math.max(-1, Math.min(1, d[i])); v.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true); }
  return new Blob([v], { type: "audio/wav" });
}
function chimeReady(){
  if (chimeEl) return Promise.resolve(chimeEl);
  return chimeBusy ||= (async () => {
    const OAC = window.OfflineAudioContext || window.webkitOfflineAudioContext; if (!OAC) return null;
    const sr = 44100, oc = new OAC(1, Math.round(sr * CHIME_LEN), sr); poroGraph(oc);
    const buf = await new Promise((ok, no) => { const p = oc.startRendering(); if (p && p.then) p.then(ok, no); else oc.oncomplete = e => ok(e.renderedBuffer); });
    // the live chime was very quiet (peak about 15%): bring the recording up to one clear, fixed level
    const d = buf.getChannelData(0); let peak = 0; for (let i = 0; i < d.length; i++) peak = Math.max(peak, Math.abs(d[i]));
    const gain = peak > 0 ? Math.min(5, 0.1225 / peak) : 1; for (let i = 0; i < d.length; i++) d[i] *= gain;
    chimeBuf = buf;
    const el = new Audio(URL.createObjectURL(wavBlob(buf))); el.preload = "auto"; el.setAttribute("playsinline", ""); el.volume = 1;
    return chimeEl = el;
  })().catch(() => null);
}
setTimeout(chimeReady, 800);
function soundWake(){
  audioCtx();
  const el = chimeEl; if (!el || chimeOK || chimeWaking || Date.now() - chimeAt < CHIME_LEN * 1000) return;
  // play it silently once inside the tap, so later plays (with no tap) are allowed; a real chime started meanwhile wins
  chimeWaking = true; el.muted = true; const p = el.play();
  const done = ok => { if (!chimeWaking) return; chimeWaking = false; if (ok){ el.pause(); el.currentTime = 0; chimeOK = true; } el.muted = false; };
  if (p && p.then) p.then(() => done(true), () => done(false)); else done(true);
}
["pointerdown", "touchend", "click", "keydown"].forEach(ev => addEventListener(ev, soundWake, { capture: true, passive: true }));
async function coinChime(){
  if (Date.now() - chimeAt < CHIME_LEN * 1000) return true;   // one is already playing: don't stack a second on top
  chimeAt = Date.now();
  const el = chimeEl || await chimeReady();
  if (el){ chimeWaking = false; try { el.pause(); el.muted = false; el.volume = 1; el.currentTime = 0; await el.play(); chimeOK = true; return true; } catch(e){} }
  // fallback: the same recording through Web Audio, at the same level
  const a = audioCtx();
  if (a && a.state !== "running"){ try { await a.resume(); } catch(e){} }
  if (a && a.state === "running"){
    if (chimeBuf){ const s = a.createBufferSource(); s.buffer = chimeBuf; s.connect(a.destination); s.start(); } else poroGraph(a);
    return true;
  }
  chimeAt = 0; return false;
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
