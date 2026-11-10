"""Faster scanner: recognition by picture, Scan Now, flash (website only, after patch_scan).

- Cards are recognised by their picture; an unsure match (SC_MIN..SC_SURE) also reads the card's text (Tesseract), which wins when sure (scan-ai.js: DINOv2-small running on the device, ~22 MB once, then cached),
  compared with every card picture's fingerprint in cardvecs.bin (tools/embed_cards.py). A look takes about 0.3 s on a
  PC (more on a phone) instead of 1-5 s of text reading, and it works on full-art cards, runes and alt arts, whose art
  tells them apart. Pictures that match the best one almost as well (the same art reprinted) are pooled, and the
  printing comes from scPrint (set being opened, then the regular printing). A best match under SC_MIN is "no card".
  Tesseract text reading stays as the fallback when the model can't load (`sc.noAI`).
- "📸 Scan Now" (#sc-snap) reads the picture in the frame at once, without the second look the live scan needs.
- "🔦 Flash" (#sc-torch) turns the phone's light on and off; it only shows when the camera supports it (mostly Android).
`sc.ai` = {key, sim, gap} of the last look, for tests.
Usage: patch_scan_ai.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

rep('''<span class="sc-tb"><button class="btn" id="sc-wide"''',
    '''<span class="sc-tb"><button class="btn" id="sc-torch" type="button" aria-pressed="false" hidden>🔦 Flash</button><button class="btn" id="sc-wide"''')
rep('''<p class="sc-msg" id="sc-msg" aria-live="polite"></p></div>''',
    '''<p class="sc-msg" id="sc-msg" aria-live="polite"></p></div>
        <button class="btn primary sc-snap" id="sc-snap" type="button">📸 Scan Now</button>''')
rep('''#sc-wide[aria-pressed="true"]{border-color:var(--accent);color:var(--accent)}''',
    '''#sc-wide[aria-pressed="true"]{border-color:var(--accent);color:var(--accent)}
#sc-torch[aria-pressed="true"]{border-color:var(--warn);color:var(--warn)}
.sc-snap{width:100%;font-size:17px;padding:12px}''')
rep('''Hold one card flat inside the frame, in good light, then swap in the next; scanning never stops.''',
    '''Hold one card flat inside the frame, then swap in the next; scanning never stops. Tap 📸 Scan Now to read it straight away.''')

rep('''const scLabel = c => `${c.set} ${String(c.num ?? "").padStart(3, "0")}`;''', '''const scLabel = c => `${c.set} ${String(c.num ?? "").padStart(3, "0")}`;
// ---- recognition by picture (scan-ai.js + cardvecs.bin): the on-device model's numbers for the photo are compared
// with every card picture's; the Tesseract text reading below is only the fallback when the model can't load
// a best match under SC_MIN is no card (an empty table scores ~0.38); SC_SURE and up is taken at once; in between, the
// card's text is read as well and wins when it's sure (battlefields look alike: grey banners, landscape art).
// Pictures within SC_SAME of the best are the same art (reprints).
const SC_MIN = 0.42, SC_SURE = 0.6, SC_SAME = 0.02;
const scKeyOf = c => c.img ? c.img.replace(/\\.png$/, "") : c.imgTcg && c.tcg ? "tcg-" + c.tcg : "";
const scAI = {ready: null};
function scAILoad(){
  if (scAI.ready) return scAI.ready;
  scAI.ready = Promise.all([import("./scan-ai.js").then(m => m.load().then(() => m)), fetch("cardvecs.json").then(r => r.json()), fetch("cardvecs.bin").then(r => r.arrayBuffer())])
    .then(([m, meta, buf]) => {
      const by = {}; for (const c of CARDS){ const k = scKeyOf(c); if (k) (by[k] ||= []).push(c); }
      return Object.assign(scAI, {m, by, keys: meta.keys, dim: meta.dim, mean: Float32Array.from(meta.mean), vecs: new Int8Array(buf)});
    })
    .catch(e => { scAI.ready = null; throw e; });
  return scAI.ready;
}
async function scAIMatch(src){
  const a = await scAILoad(), v = await a.m.vector(src), d = a.dim;
  let n = 0; for (let j = 0; j < d; j++){ v[j] -= a.mean[j]; n += v[j] * v[j]; } n = (Math.sqrt(n) || 1) * 127;
  const sims = new Float32Array(a.keys.length); let best = -2, bi = -1, second = -2;
  for (let i = 0, o = 0; i < a.keys.length; i++, o += d){
    let s = 0; for (let j = 0; j < d; j++) s += a.vecs[o + j] * v[j];
    sims[i] = s /= n;
    if (s > best){ second = best; best = s; bi = i; } else if (s > second) second = s;
  }
  sc.ai = {key: a.keys[bi], sim: best, gap: best - second};
  if (best < SC_MIN) return null;
  const pool = [];
  sims.forEach((s, i) => { if (s >= best - SC_SAME) pool.push(...(a.by[a.keys[i]] || [])); });
  const same = pool.filter(c => norm(c.name) === norm((a.by[a.keys[bi]] || pool)[0].name));
  return same.length ? scPrint(same) : null;
}
async function scFind(){
  if (!sc.noAI){
    let c;
    try { c = await scAIMatch(scCan); }
    catch(e){ sc.noAI = true; console.warn("Picture recognition isn't available here; reading the card's text instead.", e); }
    if (!sc.noAI){
      if (sc.ai.sim >= SC_SURE || sc.ai.sim < 0.4) return c;
      try { const t = await scLook(await scLoad()); if (t && /^look \\d+$/.test(sc.how || "")) return t; } catch(e){}
      return c;
    }
  }
  return scLook(await scLoad());
}''')

rep('''    const w = await scLoad();
    if (sc.paused || !sc.stream) return;
    scGrab(v);
    const c = await scLook(w);''', '''    scGrab(v);
    const c = await scFind();''')
rep('''  scMsg("Getting the card reader ready… (the first time downloads about 7 MB)");
  scLoad().then(''', '''  scMsg("Getting the card reader ready… (the first time downloads about 30 MB, then it's saved on your phone)");
  scAILoad().catch(() => { sc.noAI = true; return scLoad(); }).then(''')
rep('''    const c = await scLook(await scLoad()); sc.photo = false; sc.paused = false;''', '''    const c = await scFind(); sc.photo = false; sc.paused = false;''')
rep('''if ((cap.focusMode || []).includes("continuous")) await t.applyConstraints({advanced: [{focusMode: "continuous"}]}); } catch(e){}''',
    '''if ((cap.focusMode || []).includes("continuous")) await t.applyConstraints({advanced: [{focusMode: "continuous"}]}); } catch(e){}
  try { const cap = sc.stream.getVideoTracks()[0].getCapabilities(); sc.torch = false; $("sc-torch").setAttribute("aria-pressed", "false"); $("sc-torch").hidden = !cap.torch; } catch(e){ $("sc-torch").hidden = true; }''')

rep('''$("sc-file").addEventListener("change", async e => {''', '''// 🔦 Flash: the phone's light, where the camera allows it
$("sc-torch").addEventListener("click", async () => {
  const t = sc.stream && sc.stream.getVideoTracks()[0]; if (!t) return;
  sc.torch = !sc.torch;
  try { await t.applyConstraints({advanced: [{torch: sc.torch}]}); } catch(e){ sc.torch = false; scMsg("This phone's browser won't turn on the light."); }
  $("sc-torch").setAttribute("aria-pressed", String(sc.torch));
});
// 📸 Scan Now: one picture of what's in the frame, read at once (no second look needed)
$("sc-snap").addEventListener("click", async () => {
  const v = $("sc-video"); if (!sc.stream || !v.videoWidth) return;
  for (let i = 0; sc.busy && i < 80; i++) await new Promise(r => setTimeout(r, 50));
  clearTimeout(sc.t); sc.busy = true; scMsg("Scanning…");
  try {
    scGrab(v); const c = await scFind();
    if (c){ sc.skip = ""; sc.inView = ""; sc.run = {k: norm(c.name)}; scSaw(c); }
    else scMsg("Couldn't recognise that. Hold the card inside the frame and try again.");
  } catch(e){ scMsg("The card reader couldn't load. Check your internet connection, then close the scanner and try again."); }
  finally { sc.busy = false; }
  sc.t = setTimeout(scTick, 1200);
});
$("sc-file").addEventListener("change", async e => {''')

open(out, "w", encoding="utf-8").write(h)
