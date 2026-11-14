// Card recognition by picture, on the device: DINOv2-small (Transformers.js, about 22 MB, downloaded once and cached by
// the browser) turns a card picture into 384 numbers. The site compares them with every card's numbers in cardvecs.bin,
// which tools/embed_cards.py makes with this same file, so both sides prepare pictures exactly the same way.
// The website runs the model in scan-worker.js (prep here on the page, embed there), so closing the scanner can end the
// worker and give all of the model's memory back to the phone; tools/embed.html calls vector() directly.
const LIB = "https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.7.1";
export const MODEL = "Xenova/dinov2-small", DTYPE = "uint8", SIZE = 256;

let T = null, ext = null;
export async function load(){
  if (!T){ T = await import(LIB); T.env.allowLocalModels = false; }
  ext ||= await T.pipeline("image-feature-extraction", MODEL, {dtype: DTYPE, device: "wasm"});
  return ext;
}
// frees the model where it can't be run in a worker (the memory of a worker is freed by ending it)
export async function unload(){ const e = ext; ext = null; if (e && e.dispose) await e.dispose(); }

let cv = null, cx = null;
// the whole picture (or the box [x, y, w, h] of it), letterboxed onto grey so the card keeps its shape -> SIZE x SIZE pixels
export function prep(img, box){
  if (!cv){ cv = document.createElement("canvas"); cv.width = cv.height = SIZE; cx = cv.getContext("2d", {willReadFrequently: true}); }
  const [x, y, w, h] = box || [0, 0, img.naturalWidth || img.videoWidth || img.width, img.naturalHeight || img.videoHeight || img.height];
  cx.fillStyle = "#808080"; cx.fillRect(0, 0, SIZE, SIZE);
  const s = Math.min(SIZE / w, SIZE / h), dw = w * s, dh = h * s;
  cx.drawImage(img, x, y, w, h, (SIZE - dw) / 2, (SIZE - dh) / 2, dw, dh);
  return cx.getImageData(0, 0, SIZE, SIZE);
}
// prepared pixels -> 384 numbers
export async function embed(d){
  const f = await load(), out = await f(new T.RawImage(d.data, SIZE, SIZE, 4).rgb());
  return Float32Array.from(out.data.slice(0, out.dims[out.dims.length - 1]));   // the [CLS] token: the whole picture
}
export async function vector(img, box){ return embed(prep(img, box)); }
