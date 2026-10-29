"""Card scanner in Open Packs (website only, last).

A "📷 Scan Cards" button in Open Packs opens the scanner (`#sc-dlg`, full screen on phones): the back camera's picture
with a card-shaped frame. Every frame inside it is read on the device with Tesseract.js (text recognition, loaded from
jsdelivr the first time the scanner opens, about 7 MB, then cached; no picture leaves the phone). The card is found by:
- its name: each name's words are matched against the words read (one letter off allowed, two for long words); a name
  needs 80% of its letters found, and the tallest text wins, since the name is the biggest text on a card (`scRead`);
- its collector line ("VEN • 039/166 • EN"): set code + number (+ a/* for alt art/signature) + set size (`scCol`).
The name picks the card; the collector line picks the printing when it was read, otherwise the printing comes from the
"Which set are you opening?" menu, then the regular printing of the newest set (`scPrint`). The match shows with its
picture, price and "you have N"; other printings of it are chips to switch to. Scanning never stops: each card that comes into view replaces
the shown one; the same card staying in view changes nothing, and counts as new once it has left the frame (2 empty
looks). "＋ Add to Collection" adds it to the collection and This Pack (the same as typing it in), and every further tap
adds another copy; "Undo" takes back the last one. "Not This Card" hides it and ignores that name until something
else shows. Auto-add (`#sc-auto`, remembered in rb-scan-auto) adds each new card as soon as it's found. "▭ Battlefield"
switches to a sideways frame for battlefields (and hints at it after a few empty looks). "Take a Photo Instead" reads a photo (for browsers without live camera access). Closing the scanner turns the camera off.
Usage: patch_scan.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

CSS = r"""
.scan-row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.scan-row .btn{font-size:16px;padding:10px 16px}
#sc-dlg{border:1px solid var(--line);border-radius:12px;background:var(--panel);color:var(--fg);padding:14px;width:min(520px,calc(100vw - 32px));max-width:none;max-height:calc(100dvh - 32px);overflow:auto}
#sc-dlg::backdrop{background:rgb(5 6 10 / .85)}
.scd{display:grid;gap:10px}
.sc-top{display:flex;justify-content:space-between;align-items:center;gap:10px}
.sc-top h2{font-family:var(--display);font-size:18px;margin:0}
.sc-tb{display:flex;gap:8px}
#sc-wide[aria-pressed="true"]{border-color:var(--accent);color:var(--accent)}
.sc-cam{position:relative;background:#000;border-radius:10px;overflow:hidden;height:min(56vh,520px)}
.sc-cam video{width:100%;height:100%;object-fit:cover;display:block}
.sc-frame{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);border:2px solid var(--accent);border-radius:12px;box-shadow:0 0 0 2000px rgb(0 0 0 / .42);transition:border-color .2s}
.sc-frame.hit{border-color:var(--ok);border-width:3px}
.sc-msg{position:absolute;left:8px;right:8px;bottom:8px;margin:0;padding:6px 10px;border-radius:8px;background:rgb(10 12 18 / .78);color:var(--fg);font-size:13.5px;text-align:center}
.sc-msg:empty{display:none}
.sc-res{display:grid;grid-template-columns:76px minmax(0,1fr);gap:8px 12px;align-items:center;background:var(--row);border:1px solid var(--ok);border-radius:10px;padding:10px}
.sc-res[hidden]{display:none}
.sc-res img{width:76px;border-radius:5px;display:block}
.sc-info{display:grid;gap:3px;min-width:0}
.sc-info b{font-size:16px}
.sc-pick,.sc-btns{grid-column:1/-1;display:grid;gap:6px}
.sc-pick[hidden]{display:none}
.sc-pr{display:flex;gap:6px;flex-wrap:wrap}
.sc-p{background:var(--panel);border:1px solid var(--line);border-radius:999px;padding:4px 10px;font-size:13px;color:var(--muted)}
.sc-p small{font-size:11.5px}
.sc-p[aria-pressed="true"]{border-color:var(--accent);color:var(--fg)}
.sc-btns{grid-template-columns:1fr auto}
.sc-btns .btn{padding:11px 14px;font-size:15px}
.sc-done{margin:0;font-size:14px;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.sc-done:empty{display:none}
.sc-auto{color:var(--fg)}
.sc-auto input{width:18px;height:18px}
.sc-foot{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.sc-file{position:absolute;width:1px;height:1px;opacity:0;pointer-events:none}
@media (max-width:640px){
  #sc-dlg{width:100vw;height:100dvh;max-height:100dvh;margin:0;border:0;border-radius:0;padding:12px}
  .sc-cam{height:50dvh}
}
"""
rep('.qa-head{display:grid;gap:4px}', '.qa-head{display:grid;gap:4px}' + CSS)

rep('''          <ul class="sug" id="qa-sug" role="listbox" aria-label="Matching cards"></ul>
        </div>
      </div>
''', '''          <ul class="sug" id="qa-sug" role="listbox" aria-label="Matching cards"></ul>
        </div>
      </div>
      <div class="scan-row"><button class="btn primary" id="sc-open" type="button">📷 Scan Cards</button><span class="meta">Or point your phone's camera at each card and tap to add it.</span></div>
      <dialog id="sc-dlg" aria-labelledby="sc-title"><div class="scd">
        <div class="sc-top"><h2 id="sc-title">Scan Cards</h2><span class="sc-tb"><button class="btn" id="sc-wide" type="button" aria-pressed="false">▭ Battlefield</button><button class="btn" id="sc-close" type="button">Done</button></span></div>
        <div class="sc-cam" id="sc-cam"><video id="sc-video" playsinline muted autoplay></video><div class="sc-frame" id="sc-frame" aria-hidden="true"></div><p class="sc-msg" id="sc-msg" aria-live="polite"></p></div>
        <div class="sc-res" id="sc-res" hidden>
          <img id="sc-img" alt="" referrerpolicy="no-referrer">
          <div class="sc-info"><b id="sc-name"></b><span class="meta" id="sc-sub"></span></div>
          <div class="sc-pick" id="sc-pick"><span class="meta">Different printing? Pick it:</span><div class="sc-pr" id="sc-pr" role="group" aria-label="Printings"></div></div>
          <div class="sc-btns"><button class="btn primary" id="sc-add" type="button">＋ Add to Collection</button><button class="btn" id="sc-skip" type="button">Not This Card</button></div>
        </div>
        <p class="sc-done" id="sc-done" aria-live="polite"></p>
        <label class="chk sc-auto"><input type="checkbox" id="sc-auto"> Auto-add: add each new card as soon as it's found</label>
        <div class="sc-foot"><label class="btn" for="sc-file">Take a Photo Instead</label><input class="sc-file" type="file" id="sc-file" accept="image/*" capture="environment" tabindex="-1"><span class="meta">Hold one card flat inside the frame, in good light, then swap in the next; scanning never stops. Cards you add also show under This Pack.</span></div>
      </div></dialog>
''')

JS = r"""// ---- card scanner: the camera reads a card's name and collector line on the device (Tesseract.js), one tap adds it
const SC_LIB = "https://cdn.jsdelivr.net/npm/tesseract.js@5.1.1/dist/tesseract.min.js";
const SC_SETS = new Set(CARDS.map(c => c.set));
const sc = {stream:null, worker:null, ready:null, busy:false, paused:true, card:null, skip:"", miss:0, n:0, t:0, last:null};
const scCan = document.createElement("canvas");
window.rbScan = sc;                // for tests: sc.data = what was read last, sc.fn = the matching steps
const scMsg = t => { $("sc-msg").textContent = t; };
const scLabel = c => `${c.set} ${String(c.num ?? "").padStart(3, "0")}`;
function scLoad(){
  if (sc.ready) return sc.ready;
  sc.ready = new Promise((ok, no) => { if (window.Tesseract) return ok(); const s = document.createElement("script"); s.src = SC_LIB; s.onload = ok; s.onerror = () => no(new Error("load")); document.head.appendChild(s); })
    .then(() => Tesseract.createWorker("eng", 1))
    .then(async w => { await w.setParameters({tessedit_pageseg_mode: "11"}); sc.worker = w; return w; })
    .catch(e => { sc.ready = null; throw e; });
  return sc.ready;
}
// edit distance, giving up once it's over max
function scLev(a, b, max){
  if (Math.abs(a.length - b.length) > max) return max + 1;
  let p = Array.from({length: b.length + 1}, (_, i) => i);
  for (let i = 1; i <= a.length; i++){
    const q = [i]; let lo = i;
    for (let j = 1; j <= b.length; j++){ q[j] = Math.min(p[j] + 1, q[j-1] + 1, p[j-1] + (a[i-1] === b[j-1] ? 0 : 1)); if (q[j] < lo) lo = q[j]; }
    if (lo > max) return max + 1; p = q;
  }
  return p[b.length];
}
const scKey = w => w.replace(/'/g, "");
let scNames = null;
// names whose words were read (80% of their letters); the tallest text wins, as the name is the biggest text on a card
function scRead(words){
  if (!scNames) scNames = Object.keys(groups).map(k => ({k, ws: k.split(" ").map(scKey).filter(Boolean)}));
  const memo = new Map();
  const hit = nw => {             // [height of the tallest matching word, was it spelled exactly]
    if (memo.has(nw)) return memo.get(nw);
    const tol = nw.length >= 8 ? 2 : nw.length >= 4 ? 1 : 0; let best = [0, false];
    for (const o of words){ const ex = o.w === nw; if ((o.h > best[0] || (ex && !best[1] && o.h >= best[0] * 0.7)) && (ex || (tol && scLev(nw, o.w, tol) <= tol))) best = [o.h, ex]; }
    memo.set(nw, best); return best;
  };
  // exact = share of letters spelled exactly; a name that only matched with typos ("deal of units" ≈ "Seal of Unity") is weak
  const score = n => { let got = 0, all = 0, wt = 0, ex = 0; for (const nw of n.ws){ all += nw.length; const [h, e] = hit(nw); if (h){ got += nw.length; wt += nw.length * h; if (e) ex += nw.length; } } return {k: n.k, score: all ? got / all : 0, wt, h: got ? wt / got : 0, solid: all >= 6 && ex / all >= 0.9}; };
  const list = scNames.map(score).filter(x => x.score >= 0.8).sort((a, b) => b.wt - a.wt);
  return {list, of: k => score({k, ws: k.split(" ").map(scKey).filter(Boolean)}).score};
}
// collector lines like "VEN • 039/166 • EN" or "OGN 030a/298" (the slash is often missed): the printings they point
// to; strong = the set code or the set size was read too. The signature "*" is often read as "%", the slash as f/l/I.
function scCol(txt){
  const out = [];
  for (const m of txt.matchAll(/(?:\b([A-Za-z]{2,4})\b[^A-Za-z0-9\n]{0,4})?\b(\d{1,3}) ?([ab*%#]?) ?([\/|fIlj]| ) ?(\d{2,3})\b/g)){
    const set = (m[1] || "").toUpperCase(), sure = SC_SETS.has(set), num = +m[2], suf = (m[3] || "").replace(/[%#]/, "*"), tot = m[5];
    if (m[4] === " " && !sure) continue;         // "115 221" counts only right after a set code
    if (num === 0 || m[2].length < 3) continue;  // numbers are printed with 3 digits ("039"); fewer = one was lost
    const cards = CARDS.filter(c => {
      if (c.num !== num || (sure && c.set !== set)) return false;
      const p = c.id.replace(/~.*$/, "").match(/^[a-z]+-(\d+[a-z*]*)-(\d+)$/);
      if (!p) return sure;                       // TCGplayer-only printings carry no set size; trust them only with the set code
      return +p[2] === +tot && (!suf || p[1].endsWith(suf));
    }).sort((a, b) => (!suf && a.variant ? 1 : 0) - (!suf && b.variant ? 1 : 0));
    if (cards.length) out.push({cards, strong: sure || cards.some(c => /^[a-z]+-\d/.test(c.id))});
  }
  return out.sort((a, b) => b.strong - a.strong);
}
// the likeliest printing of a name: the set being opened, then regular printings of the newest set
function scRank(c){ const set = $("qa-set").value, i = META.sets.findIndex(x => x.code === c.set); return (set && c.set !== set ? 20 : 0) + (c.variant ? 3 : 0) + (["OPP","PR","JDG"].includes(c.set) ? 2 : 0) + (c.token ? 6 : 0) + (i < 0 ? 9 : i) * 0.1; }
const scPrint = list => [...list].sort((a, b) => scRank(a) - scRank(b))[0];
function scMatch(d){
  sc.data = {text: d.text, words: (d.words || []).map(x => ({text: x.text, h: x.bbox.y1 - x.bbox.y0, c: Math.round(x.confidence)}))};
  const words = [];
  for (const x of d.words || []){
    if (x.confidence < 25) continue;
    for (const w of norm(x.text).replace(/[^a-z0-9' ]/g, " ").split(" ")){ const k = scKey(w); if (k.length >= 2) words.push({w: k, h: x.bbox.y1 - x.bbox.y0}); }
  }
  const R = scRead(words), col = scCol(d.text || ""), best = R.list[0], strong = col.find(cl => cl.strong);
  const hs = words.map(x => x.h).sort((a, b) => a - b), big = best && best.h >= 1.5 * (hs[hs.length >> 1] || 1);
  // {c: the printing, sure: name and collector line agree, or one of them is clear}
  if (best) for (const cl of col){ const c = cl.cards.find(c => norm(c.name) === best.k); if (c) return {c, sure: true}; }
  // they disagree: a name read exactly and big (or long) beats a misread number; otherwise the number wins
  if (best && best.solid && (big || best.k.replace(/ /g, "").length >= 10)) return {c: scPrint(groups[best.k]), sure: true};
  if (strong) return {c: strong.cards[0], sure: true};
  if (best && (best.solid || big)) return {c: scPrint(groups[best.k]), sure: best.solid && big};
  for (const cl of col){ const c = cl.cards.find(c => R.of(norm(c.name)) >= 0.34); if (c) return {c, sure: false}; }
  return scRune(d);
}
// runes: only six names, often read with a letter off ("ury Rune"), and a collector line with no set size
// ("VEN • R02", where 0/5/1 are often read as O/S/L). A domain word right before "rune" names it, in any confidence.
const SC_DOMS = ["fury", "calm", "mind", "body", "chaos", "order"];
function scRune(d){
  const t = (d.words || []).map(x => scKey(norm(x.text).replace(/[^a-z0-9' ]/g, "")));
  let dom = "";
  for (let i = 1; i < t.length && !dom; i++) if (t[i] === "rune" || t[i] === "rue") dom = SC_DOMS.find(x => t[i-1] === x) || SC_DOMS.find(x => scLev(x, t[i-1], 1) <= 1) || "";
  const key = c => c.type === "Rune" && (!dom || norm(c.name) === dom + " rune");
  for (const m of (d.text || "").matchAll(/\b([A-Za-z]{3})\b[^A-Za-z0-9\n]{0,4}R ?([0-9OoSsLlIiZz]{2})\b/g)){
    const set = m[1].toUpperCase(), n = +m[2].replace(/[Oo]/g, "0").replace(/[Ss]/g, "5").replace(/[LlIi]/g, "1").replace(/[Zz]/g, "2");
    if (!SC_SETS.has(set) || !n) continue;
    const c = scPrint(CARDS.filter(c => key(c) && c.set === set && c.num === n));
    if (c) return {c, sure: true};
  }
  return dom && groups[dom + " rune"] ? {c: scPrint(groups[dom + " rune"]), sure: true} : null;
}
sc.fn = {scRead, scCol, scMatch};
// white names on coloured banners read badly: a copy where white turns black and colours turn light
// (255 minus the darkest channel)
const scFlip = document.createElement("canvas");
function scFlipped(){
  scFlip.width = scCan.width; scFlip.height = scCan.height;
  const x = scFlip.getContext("2d", {willReadFrequently: true}); x.drawImage(scCan, 0, 0);
  const im = x.getImageData(0, 0, scFlip.width, scFlip.height), p = im.data;
  for (let i = 0; i < p.length; i += 4){ const v = 255 - Math.min(p[i], p[i+1], p[i+2]); p[i] = p[i+1] = p[i+2] = v; }
  x.putImageData(im, 0, 0); return scFlip;
}
// up to three looks, until one is sure: as is; with light/dark judged area by area instead of over the whole picture
// (catches names on grey banners and small collector lines, e.g. battlefields); the colour-flipped copy.
// Each look adds its words to the earlier ones.
const SC_LOOKS = [["0", false], ["1", false], ["0", true]];
async function scLook(w){
  let all = {text: "", words: []}, m = null;
  for (const [i, [tm, flip]] of SC_LOOKS.entries()){
    if (i && sc.paused && !sc.photo) return null;
    if (sc.tm !== tm){ await w.setParameters({thresholding_method: tm}); sc.tm = tm; }
    const d = (await w.recognize(flip ? scFlipped() : scCan)).data;
    all = {text: all.text + "\n" + d.text, words: [...all.words, ...(d.words || [])]}; m = scMatch(all);
    sc.how = m ? `look ${i + 1}${m.sure ? "" : ", not sure"}` : "";
    if (m && m.sure) return m.c;
  }
  return m ? m.c : null;
}
// the camera picture inside the frame (plus a little around it), the size the reader likes
function scGrab(v){
  const box = $("sc-cam").getBoundingClientRect(), f = $("sc-frame").getBoundingClientRect();
  const vw = v.videoWidth, vh = v.videoHeight, s = Math.max(box.width / vw, box.height / vh);
  const ox = (box.width - vw * s) / 2, oy = (box.height - vh * s) / 2;
  let w = f.width / s * 1.12, hh = f.height / s * 1.12;
  let x = (f.left - box.left - ox) / s - f.width / s * 0.06, y = (f.top - box.top - oy) / s - f.height / s * 0.06;
  x = Math.max(0, x); y = Math.max(0, y); w = Math.min(vw - x, w); hh = Math.min(vh - y, hh);
  const W = sc.wide ? 1250 : 900;
  scCan.width = W; scCan.height = Math.round(hh * W / w);
  scCan.getContext("2d").drawImage(v, x, y, w, hh, 0, 0, scCan.width, scCan.height);
}
// a card-shaped frame, or a sideways one for battlefields (▭ Battlefield)
function scSize(){
  const b = $("sc-cam"), f = $("sc-frame"), r = sc.wide ? 1039 / 744 : 744 / 1039;
  let hh = b.clientHeight * 0.88, w = hh * r;
  if (w > b.clientWidth * (sc.wide ? 0.94 : 0.8)){ w = b.clientWidth * (sc.wide ? 0.94 : 0.8); hh = w / r; }
  f.style.width = w + "px"; f.style.height = hh + "px";
}
const scLooking = () => sc.wide ? "Looking for a battlefield… hold it sideways, filling the frame."
  : sc.empty >= 4 ? "Scanning a battlefield? Tap ▭ Battlefield at the top."
  : sc.n ? "Show the next card…" : "Looking for a card… hold it flat inside the frame, in good light.";
async function scTick(){
  clearTimeout(sc.t);
  const v = $("sc-video");
  if (!$("sc-dlg").open || sc.paused || sc.busy || !sc.stream || document.hidden) return;
  if (!v.videoWidth){ sc.t = setTimeout(scTick, 300); return; }
  sc.busy = true;
  try {
    const w = await scLoad();
    if (sc.paused || !sc.stream) return;
    scGrab(v);
    const c = await scLook(w);
    if (sc.paused || !$("sc-dlg").open) return;
    scSaw(c);
  } catch(e){ scMsg("The card reader couldn't load. Check your internet connection, then close the scanner and try again."); return; }
  finally { sc.busy = false; }
  sc.t = setTimeout(scTick, 150);
}
async function scCamera(){
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia){ scMsg("This browser can't use the camera here. Use Take a Photo Instead below."); return; }
  try { sc.stream = await navigator.mediaDevices.getUserMedia({audio: false, video: {facingMode: {ideal: "environment"}, width: {ideal: 1920}, height: {ideal: 1080}}}); }
  catch(e){ scMsg(e.name === "NotAllowedError" ? "Camera access is blocked. Allow the camera for this site in your browser's settings, or use Take a Photo Instead below." : "Couldn't start the camera. Use Take a Photo Instead below."); return; }
  if (!$("sc-dlg").open){ scStop(); return; }
  const v = $("sc-video"); v.srcObject = sc.stream; try { await v.play(); } catch(e){}
  try { const t = sc.stream.getVideoTracks()[0], cap = t.getCapabilities ? t.getCapabilities() : {}; if ((cap.focusMode || []).includes("continuous")) await t.applyConstraints({advanced: [{focusMode: "continuous"}]}); } catch(e){}
  scTick();
}
function scStop(){
  clearTimeout(sc.t); sc.paused = true;
  if (sc.stream) sc.stream.getTracks().forEach(t => t.stop());
  sc.stream = null; $("sc-video").srcObject = null;
}
function scOpen(){
  const d = $("sc-dlg"); if (!d.open){ try { d.showModal(); } catch(e){ d.setAttribute("open", ""); } }
  sc.paused = false; sc.skip = ""; sc.inView = ""; sc.card = null; sc.empty = 0; sc.addN = 0; $("sc-res").hidden = true; $("sc-add").textContent = "＋ Add to Collection"; $("sc-frame").classList.remove("hit"); scSize();
  scMsg("Getting the card reader ready… (the first time downloads about 7 MB)");
  scLoad().then(() => { if (!sc.paused && !sc.card && sc.stream) scMsg(scLooking()); }).catch(() => scMsg("The card reader couldn't load. Check your internet connection, then close the scanner and try again."));
  scCamera();
}
// scanning never stops: a card that comes into view is shown (and added, with Auto-add on); the same card staying in
// view changes nothing; it counts as new again once it has left the frame (2 empty looks). "Not This Card" ignores
// that name until something else shows.
function scSaw(c){
  const k = c ? norm(c.name) : "";
  if (!c){
    if (++sc.empty >= 2){ sc.inView = ""; sc.skip = ""; }
    if (!sc.card) scMsg(scLooking());
    return;
  }
  sc.empty = 0;
  if (k === sc.skip || k === sc.inView) return;
  sc.skip = ""; sc.inView = k; scShow(c);
  if (sc.auto){ scPut(sc.card); scDone(true); }
}
function scShow(c){
  sc.card = c; sc.addN = 0;
  const f = $("sc-frame"); f.classList.add("hit"); clearTimeout(sc.hitT); sc.hitT = setTimeout(() => f.classList.remove("hit"), 900);
  try { navigator.vibrate && navigator.vibrate(30); } catch(e){}
  scMsg(sc.auto ? `Added ${c.name}. Show the next card…` : `Found ${c.name}. Tap Add (again for more copies), or show the next card.`);
  scDraw(); $("sc-res").hidden = false;
}
function scDraw(){
  const c = sc.card, list = c.token ? [c] : [...(groups[norm(c.name)] || [c])].sort((a, b) => scRank(a) - scRank(b)), u = imgURL(c, 200);
  $("sc-img").hidden = !u; if (u) $("sc-img").src = u;
  $("sc-name").textContent = c.name;
  $("sc-sub").innerHTML = `${esc(scLabel(c))} · <span class="r-${c.rarity}">${esc(c.rarity)}</span>${c.variant ? ` · ${esc(c.variant)}` : ""} · ${c.price != null ? esc(money(c.price)) : "No price"}${counts[c.id] ? ` · you have ${counts[c.id]}` : ""}`;
  $("sc-pick").hidden = list.length < 2;
  $("sc-pr").innerHTML = list.map(p => `<button type="button" class="sc-p" data-id="${esc(p.id)}" aria-pressed="${p.id === c.id}">${esc(scLabel(p))}${p.variant ? ` <small>${esc(p.variant)}</small>` : ""}</button>`).join("");
}
function scPut(c){ adjust(c.id, 1); pack.push(c.id); LS.set("rb-pack", pack); renderPack(); sc.n++; sc.addN++; sc.last = c; }
function scDone(auto){
  const c = sc.last; if (!c){ $("sc-done").innerHTML = ""; return; }
  $("sc-done").innerHTML = `<span>✓ ${auto ? "Auto-added" : "Added"} <b>${esc(c.name)}</b> (${esc(scLabel(c))}${c.variant ? `, ${esc(c.variant)}` : ""})${sc.addN > 1 ? ` ×${sc.addN}` : ""} · you have ${counts[c.id] || 0} · ${sc.n} added</span><button class="btn" id="sc-undo" type="button">Undo</button>`;
  $("sc-add").textContent = sc.addN ? "＋ Add Another Copy" : "＋ Add to Collection";
}
// takes back the last card the scanner added (from the collection and This Pack)
function scUndo(){
  const c = sc.last, i = c ? pack.lastIndexOf(c.id) : -1; if (i < 0) return;
  pack.splice(i, 1); LS.set("rb-pack", pack); adjust(c.id, -1); renderPack(); sc.n--; sc.addN = Math.max(0, sc.addN - 1);
  if (!sc.addN || sc.card !== c){ sc.last = null; $("sc-done").innerHTML = `<span>Took back <b>${esc(c.name)}</b> · you have ${counts[c.id] || 0}</span>`; $("sc-add").textContent = "＋ Add to Collection"; }
  else scDone();
  if (sc.card) scDraw();
}
$("sc-open").addEventListener("click", scOpen);
$("sc-wide").addEventListener("click", () => {
  sc.wide = !sc.wide; sc.empty = 0; $("sc-wide").setAttribute("aria-pressed", sc.wide); scSize();
  if (!sc.card) scMsg(scLooking());
});
$("sc-close").addEventListener("click", () => $("sc-dlg").close());
$("sc-dlg").addEventListener("close", scStop);
$("sc-pr").addEventListener("click", e => { const b = e.target.closest(".sc-p"); if (b && byId[b.dataset.id]){ sc.card = byId[b.dataset.id]; scDraw(); } });
// every tap adds one more copy; scanning carries on meanwhile
$("sc-add").addEventListener("click", () => { const c = sc.card; if (!c) return; if (sc.last !== c) sc.addN = 0; scPut(c); scDone(); scDraw(); });
$("sc-skip").addEventListener("click", () => {
  if (sc.card) sc.skip = norm(sc.card.name);
  sc.card = null; sc.inView = ""; $("sc-res").hidden = true; $("sc-add").textContent = "＋ Add to Collection";
  scMsg("Move the card a little, or type its name in the box under the scanner.");
});
$("sc-done").addEventListener("click", e => { if (e.target.id === "sc-undo") scUndo(); });
$("sc-auto").checked = sc.auto = !!LS.get("rb-scan-auto");
$("sc-auto").addEventListener("change", e => { sc.auto = e.target.checked; LS.set("rb-scan-auto", sc.auto); if (!sc.card) scMsg(scLooking()); });
addEventListener("resize", () => { if ($("sc-dlg").open) scSize(); });
document.addEventListener("visibilitychange", () => {
  if (document.hidden || !$("sc-dlg").open) return;
  const t = sc.stream && sc.stream.getVideoTracks()[0];
  if (sc.stream && (!t || t.readyState === "ended")){ scStop(); sc.paused = false; scCamera(); } else scTick();
});
$("sc-file").addEventListener("change", async e => {
  const f = e.target.files[0]; e.target.value = ""; if (!f) return;
  sc.paused = true; sc.photo = true; clearTimeout(sc.t); scMsg("Reading the photo…");
  try {
    const url = URL.createObjectURL(f), img = new Image();
    await new Promise((ok, no) => { img.onload = ok; img.onerror = no; img.src = url; });
    const s = Math.min(1, 1400 / Math.max(img.naturalWidth, img.naturalHeight));
    scCan.width = Math.round(img.naturalWidth * s); scCan.height = Math.round(img.naturalHeight * s);
    scCan.getContext("2d").drawImage(img, 0, 0, scCan.width, scCan.height); URL.revokeObjectURL(url);
    const c = await scLook(await scLoad()); sc.photo = false; sc.paused = false;
    if (c){ sc.skip = ""; sc.inView = ""; scSaw(c); }
    else scMsg("Couldn't read that card. Take the photo closer, with the card filling the picture, in good light.");
    sc.t = setTimeout(scTick, 2500);
  } catch(err){ sc.photo = false; sc.paused = false; scMsg("Couldn't read that photo. Try again, or type the card's name in the box under the scanner."); sc.t = setTimeout(scTick, 2500); }
});

// ---- deck checker"""
rep('// ---- deck checker', JS)

open(out, "w", encoding="utf-8").write(h)
