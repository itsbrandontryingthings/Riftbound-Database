#!/usr/bin/env python3
"""Chime for new shopping-list offers (website; runs last, after patch_fixes.py).
- While the page is open, you're signed in and your shopping list is shared, offers are checked every minute (and
  when you come back to the tab). An offer you haven't seen before plays a cute poro "brrr-eep!" and a mystical "ca-ching" made with the
  Web Audio API (no sound file), and shows a "New" tag. Seen offer ids are kept in localStorage "rb-offers-seen".
- Offers panel has a "Sound on / Sound off" button (localStorage "rb-offer-sound"); turning it on plays the chime.
- Browsers only allow sound after you've clicked or typed on the page once, so the sound is unlocked on the
  first click or key press.
Usage: patch_chime.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

# spot new offers as they load
rep('''  else { offersOff = false; offers = data || []; }''',
    '''  else {
    offersOff = false; offers = data || [];
    const had = LS.get("rb-offers-seen"), seen = new Set(had || []), fresh = offers.filter(o => !seen.has(o.id));
    fresh.forEach(o => offersNew.add(o.id));
    if (fresh.length && had && offerSound()) coinChime();
    LS.set("rb-offers-seen", offers.map(o => o.id));
  }''')
rep('''<b class="of-from">${esc(o.from_name)}</b>''', '''${offersNew.has(o.id) ? '<span class="of-new">New</span>' : ""}<b class="of-from">${esc(o.from_name)}</b>''')
rep('''<h3 class="of-h">Offers <small>${offers.length}</small></h3><button class="btn" id="of-refresh">Check for new offers</button></div>''',
    '''<h3 class="of-h">Offers <small>${offers.length}</small></h3><span class="frow"><button class="btn" id="of-sound" aria-pressed="${offerSound()}" title="Play a coin sound when a new offer comes in">${offerSound() ? "🔔 Sound on" : "🔕 Sound off"}</button><button class="btn" id="of-refresh">Check for new offers</button></span></div>''')
rep('''  if (e.target.id === "of-refresh"){''', '''  if (e.target.id === "of-sound"){ LS.set("rb-offer-sound", !offerSound()); if (offerSound()) coinChime(); renderOffers(); return; }
  if (e.target.id === "of-refresh"){''')

rep('''function saveDeckView(){''', r'''// ---- new-offer chime: a short coin "cha-ching" made with Web Audio (no sound file)
const offersNew = new Set();
const offerSound = () => LS.get("rb-offer-sound") !== false;
let actx = null;
function audioCtx(){
  try { actx ||= new (window.AudioContext || window.webkitAudioContext)(); if (actx.state === "suspended") actx.resume(); return actx; }
  catch(e){ return null; }
}
// browsers only allow sound after the first click or key press on the page
["pointerdown", "keydown"].forEach(ev => addEventListener(ev, () => audioCtx(), { once: true, capture: true }));
function coinChime(){
  const a = audioCtx(); if (!a || a.state !== "running") return;
  const t = a.currentTime + 0.02;
  // a cute poro "brrr-eep!", then a mystical "ca-ching" (a bell with a shimmering echo and sparkles)
  const out = a.createDynamicsCompressor(); out.connect(a.destination);
  // the poro: a soft voice shaped into "oo" then "ee" by two filters, fluttering ("brrr") then squeaking up ("eep!")
  const voice = (at, dur, f0a, f0b, f1, f2, vol, flutter) => {
    const o = a.createOscillator(), g = a.createGain(), trem = a.createGain(), lfo = a.createOscillator(), lg = a.createGain();
    o.type = "sawtooth";
    o.frequency.setValueAtTime(f0a, t + at); o.frequency.exponentialRampToValueAtTime(f0b, t + at + dur);
    for (const [f, q, lv] of [[f1, 6, 1], [f2, 8, 0.5]]){
      const bp = a.createBiquadFilter(), fg = a.createGain();
      bp.type = "bandpass"; bp.frequency.value = f; bp.Q.value = q; fg.gain.value = lv;
      o.connect(bp); bp.connect(fg); fg.connect(trem);
    }
    trem.gain.value = 1 - flutter; lfo.frequency.value = 32; lg.gain.value = flutter; lfo.connect(lg); lg.connect(trem.gain);
    trem.connect(g);
    g.gain.setValueAtTime(0.0001, t + at); g.gain.exponentialRampToValueAtTime(vol, t + at + 0.02);
    g.gain.setValueAtTime(vol, t + at + dur * 0.65); g.gain.exponentialRampToValueAtTime(0.0001, t + at + dur);
    g.connect(out);
    o.start(t + at); lfo.start(t + at); o.stop(t + at + dur + 0.05); lfo.stop(t + at + dur + 0.05);
  };
  voice(0,    0.16, 560, 640, 380, 900, 0.75, 0.45);    // "brrr" (soft "oo", fluttering)
  voice(0.15, 0.15, 900, 1500, 330, 2500, 0.62, 0.1);  // "eep!" (squeaks up)
  // the mystical ca-ching rings through a shimmering echo
  const echo = a.createDelay(1), fb = a.createGain(), tone = a.createBiquadFilter(), wet = a.createGain(), bell = a.createGain();
  echo.delayTime.value = 0.12; fb.gain.value = 0.38; tone.type = "lowpass"; tone.frequency.value = 5000; wet.gain.value = 0.45;
  bell.connect(out); bell.connect(echo); echo.connect(tone); tone.connect(fb); fb.connect(echo); tone.connect(wet); wet.connect(out);
  const ring = (f, at, dur, vol, type) => {
    const o = a.createOscillator(), g = a.createGain();
    o.type = type; o.frequency.value = f;
    g.gain.setValueAtTime(0.0001, t + at); g.gain.exponentialRampToValueAtTime(vol, t + at + 0.006); g.gain.exponentialRampToValueAtTime(0.0001, t + at + dur);
    o.connect(g); g.connect(bell); o.start(t + at); o.stop(t + at + dur + 0.05);
  };
  ring(1568, 0.36, 0.09, 0.07, "triangle");   // "ca" (G6)
  ring(2093, 0.44, 0.75, 0.085, "sine");       // "ching" (C7)...
  ring(5776, 0.44, 0.35, 0.018, "sine");      // ...with a bell-like overtone
  ring(2637, 0.52, 0.35, 0.022, "sine");       // sparkles drifting up
  ring(3136, 0.58, 0.32, 0.018, "sine");
  ring(4186, 0.64, 0.30, 0.015, "sine");
}
// check for offers every minute while the page is open (and when you come back to it)
const offerPoll = () => { if (cloudUser && sb && shopP().shared && document.visibilityState === "visible") loadOffers(true); };
setInterval(offerPoll, 60000);
document.addEventListener("visibilitychange", offerPoll);
function saveDeckView(){''')

_i = h.rfind("</style>"); h = h[:_i] + """.of-new{display:inline-block;background:var(--accent);color:var(--bg);font-size:11px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;border-radius:4px;padding:0 6px;line-height:18px;margin-right:6px;vertical-align:2px}
#of-sound{padding:6px 10px;font-size:13px}
""" + h[_i:]

open(out, "w", encoding="utf-8").write(h)
print("patch_chime: ok ->", out)
