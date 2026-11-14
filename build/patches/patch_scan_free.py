"""Scanner memory (website only, after patch_scan_ai): phones closed the page after scanning, because the picture
model (DINOv2 in onnxruntime's WebAssembly memory, which never shrinks) and the Tesseract text reader stayed loaded
after Done, on top of the card pictures and animations of the rest of the site.
- The picture model runs in a Web Worker (scan-worker.js); the page only prepares the 256x256 picture (scan-ai.js prep,
  the same steps as the fingerprints). Browsers that can't run a module worker fall back to the page (unload on Done).
- Closing the scanner (`scFree`, on the dialog's close) ends that worker and the Tesseract worker: every byte goes back.
  Opening it again loads both from the browser's cache (a few seconds, no new download). The card fingerprints
  (cardvecs.*) are kept, they're small.
- A look still running when the scanner closes is dropped quietly (`sc.gen`), so it can't show an error, switch to
  text-only reading (`sc.noAI`) or stall the next scan.
- The grab canvas keeps its size between looks instead of being remade three times a second.
Usage: patch_scan_free.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

rep('''const scAI = {ready: null};
function scAILoad(){
  if (scAI.ready) return scAI.ready;
  scAI.ready = Promise.all([import("./scan-ai.js").then(m => m.load().then(() => m)), fetch("cardvecs.json").then(r => r.json()), fetch("cardvecs.bin").then(r => r.arrayBuffer())])
    .then(([m, meta, buf]) => {
      const by = {}; for (const c of CARDS){ const k = scKeyOf(c); if (k) (by[k] ||= []).push(c); }
      return Object.assign(scAI, {m, by, keys: meta.keys, dim: meta.dim, mean: Float32Array.from(meta.mean), vecs: new Int8Array(buf)});
    })
    .catch(e => { scAI.ready = null; throw e; });
  return scAI.ready;
}''', '''const scAI = {ready: null, wk: null};
const scClosed = () => Object.assign(new Error("scanner closed"), {closed: true});
// the picture model in its own worker (scan-worker.js), so Done can end it and free all of its memory
function scWorker(){
  const w = new Worker("./scan-worker.js", {type: "module"}), q = new Map(); let n = 0;
  const fail = e => { for (const p of q.values()) p.no(e); q.clear(); };
  w.onmessage = e => { const p = q.get(e.data.id); if (!p) return; q.delete(e.data.id); e.data.err ? p.no(new Error(e.data.err)) : p.ok(e.data.v); };
  w.onerror = e => { e.preventDefault && e.preventDefault(); fail(new Error("worker: " + (e.message || "failed to start"))); };
  const call = d => new Promise((ok, no) => { const id = ++n; q.set(id, {ok, no}); d ? w.postMessage({id, data: d}, [d.data.buffer]) : w.postMessage({id}); });
  return {call, end(){ w.terminate(); fail(scClosed()); }};
}
async function scModel(m){
  if (typeof Worker === "function"){
    const wk = scAI.wk = scWorker();
    try { await wk.call(); return {vec: src => wk.call(m.prep(src)), end: () => wk.end()}; }
    catch(e){ wk.end(); if (scAI.wk === wk) scAI.wk = null; if (e.closed) throw e; console.warn("The scanner's worker didn't start; running the model on the page.", e); }
  }
  await m.load(); return {vec: src => m.vector(src), end: () => m.unload().catch(() => {})};
}
function scAILoad(){
  if (scAI.ready) return scAI.ready;
  const p = scAI.ready = Promise.all([import("./scan-ai.js").then(m => scModel(m).then(x => ({m, ...x}))), scAI.meta || fetch("cardvecs.json").then(r => r.json()), scAI.buf || fetch("cardvecs.bin").then(r => r.arrayBuffer())])
    .then(([{m, vec, end}, meta, buf]) => {
      if (scAI.ready !== p){ end(); throw scClosed(); }      // closed while it was loading
      const by = {}; for (const c of CARDS){ const k = scKeyOf(c); if (k) (by[k] ||= []).push(c); }
      return Object.assign(scAI, {m, vec, meta, buf, by, keys: meta.keys, dim: meta.dim, mean: Float32Array.from(meta.mean), vecs: new Int8Array(buf)});
    })
    .catch(e => { if (scAI.ready === p) scAI.ready = null; throw e; });
  return p;
}
// Done: end the model's worker and the text reader, so the phone gets their memory back
function scFree(){
  sc.gen = (sc.gen || 0) + 1; sc.busy = false;
  const wk = scAI.wk; scAI.wk = null; scAI.ready = null;
  if (wk) wk.end(); else if (scAI.m) scAI.m.unload().catch(() => {});
  scAI.vec = null;
  const t = sc.worker; sc.worker = null; sc.ready = null; sc.tm = undefined;
  if (t) try { t.terminate(); } catch(e){}
}''')
rep('''  const a = await scAILoad(), v = await a.m.vector(src), d = a.dim;''', '''  const a = await scAILoad(), v = await a.vec(src), d = a.dim;''')
rep('''    catch(e){ sc.noAI = true; console.warn(''', '''    catch(e){ if (e.closed || !$("sc-dlg").open) return null; sc.noAI = true; console.warn(''')
rep('''  scCan.width = W; scCan.height = Math.round(hh * W / w);
  scCan.getContext("2d").drawImage(v, x, y, w, hh, 0, 0, scCan.width, scCan.height);''', '''  const H = Math.round(hh * W / w);
  if (scCan.width !== W || scCan.height !== H){ scCan.width = W; scCan.height = H; }     // same size: no new memory each look
  scCan.getContext("2d").drawImage(v, x, y, w, hh, 0, 0, scCan.width, scCan.height);''')
rep('''  sc.busy = true;
  try {
    scGrab(v);
    const c = await scFind();
    if (sc.paused || !$("sc-dlg").open) return;
    scSaw(c);
  } catch(e){ scMsg("The card reader couldn't load. Check your internet connection, then close the scanner and try again."); return; }
  finally { sc.busy = false; }''', '''  sc.busy = true; const gen = sc.gen;
  try {
    scGrab(v);
    const c = await scFind();
    if (gen !== sc.gen || sc.paused || !$("sc-dlg").open) return;
    scSaw(c);
  } catch(e){ if (gen === sc.gen && $("sc-dlg").open) scMsg("The card reader couldn't load. Check your internet connection, then close the scanner and try again."); return; }
  finally { if (gen === sc.gen) sc.busy = false; }''')
rep('''  scAILoad().catch(() => { sc.noAI = true; return scLoad(); }).then(''', '''  scAILoad().catch(e => { if (e.closed || !$("sc-dlg").open) throw e; sc.noAI = true; return scLoad(); }).then(''')
rep('''.then(async w => { await w.setParameters({tessedit_pageseg_mode: "11"}); sc.worker = w; return w; })''',
    '''.then(async w => { await w.setParameters({tessedit_pageseg_mode: "11"}); if (!$("sc-dlg").open){ w.terminate(); sc.ready = null; throw scClosed(); } sc.worker = w; return w; })''')
rep('''$("sc-dlg").addEventListener("close", scStop);''', '''$("sc-dlg").addEventListener("close", scStop);
$("sc-dlg").addEventListener("close", scFree);''')

open(out, "w", encoding="utf-8").write(h)
