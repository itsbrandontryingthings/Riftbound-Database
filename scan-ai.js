// Card recognition by picture, on the device: DINOv2-small (Transformers.js, about 22 MB, downloaded once and cached by
// the browser) turns a card picture into 384 numbers. The site compares them with every card's numbers in cardvecs.bin,
// which tools/embed_cards.py makes with this same file, so both sides prepare pictures exactly the same way.
// The model runs in a background worker (scan-ai-worker.js) so the page never freezes while it works; where a browser
// can't start one, it runs here on the page instead (the same numbers either way).
export const MODEL = "Xenova/dinov2-small", DTYPE = "uint8", SIZE = 256;

let wk = null, seq = 0, here = null;
const wait = new Map();
function ask(px){
  return new Promise((ok, no) => {
    const id = ++seq; wait.set(id, {ok, no});
    wk.postMessage({id, model: MODEL, dtype: DTYPE, size: SIZE, px}, px ? [px.buffer] : []);
  });
}
async function onPage(){      // the fallback: the model on the page itself
  if (!here) here = import("https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.7.1").then(async t => {
    t.env.allowLocalModels = false;
    return {t, ext: await t.pipeline("image-feature-extraction", MODEL, {dtype: DTYPE, device: "wasm"})};
  }).catch(e => { here = null; throw e; });
  return here;
}
let ready = null;
export function load(){
  return ready ||= (async () => {
    try {
      wk = new Worker(new URL("./scan-ai-worker.js", import.meta.url), {type: "module"});
      wk.onmessage = ({data}) => { const w = wait.get(data.id); if (!w) return; wait.delete(data.id); data.err ? w.no(new Error(data.err)) : w.ok(data.v); };
      wk.onerror = e => { e.preventDefault && e.preventDefault(); for (const w of wait.values()) w.no(new Error("worker")); wait.clear(); };
      await ask(null);
    } catch(e){
      console.warn("Running the picture model on the page (no background worker here).", e);
      if (wk) wk.terminate(); wk = null; await onPage();
    }
    return true;
  })().catch(e => { ready = null; throw e; });
}

const cv = document.createElement("canvas"); cv.width = cv.height = SIZE;
const cx = cv.getContext("2d", {willReadFrequently: true});

// the whole picture (or the box [x, y, w, h] of it), letterboxed onto grey so the card keeps its shape -> 384 numbers
export async function vector(img, box){
  await load();
  const [x, y, w, h] = box || [0, 0, img.naturalWidth || img.videoWidth || img.width, img.naturalHeight || img.videoHeight || img.height];
  cx.fillStyle = "#808080"; cx.fillRect(0, 0, SIZE, SIZE);
  const s = Math.min(SIZE / w, SIZE / h), dw = w * s, dh = h * s;
  cx.drawImage(img, x, y, w, h, (SIZE - dw) / 2, (SIZE - dh) / 2, dw, dh);
  const px = cx.getImageData(0, 0, SIZE, SIZE).data;
  if (wk) return ask(new Uint8ClampedArray(px));
  const {t, ext} = await onPage();
  const out = await ext(new t.RawImage(px, SIZE, SIZE, 4).rgb());
  return Float32Array.from(out.data.slice(0, out.dims[out.dims.length - 1]));   // the [CLS] token: the whole picture
}
