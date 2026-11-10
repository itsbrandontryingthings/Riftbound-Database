// Card recognition by picture, on the device: DINOv2-small (Transformers.js, about 22 MB, downloaded once and cached by
// the browser) turns a card picture into 384 numbers. The site compares them with every card's numbers in cardvecs.bin,
// which tools/embed_cards.py makes with this same file, so both sides prepare pictures exactly the same way.
import { pipeline, RawImage, env } from "https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.7.1";

export const MODEL = "Xenova/dinov2-small", DTYPE = "uint8", SIZE = 256;
env.allowLocalModels = false;

let ext = null;
export async function load(){
  ext ||= await pipeline("image-feature-extraction", MODEL, {dtype: DTYPE, device: "wasm"});
  return ext;
}

const cv = document.createElement("canvas"); cv.width = cv.height = SIZE;
const cx = cv.getContext("2d", {willReadFrequently: true});

// the whole picture (or the box [x, y, w, h] of it), letterboxed onto grey so the card keeps its shape -> 384 numbers
export async function vector(img, box){
  const [x, y, w, h] = box || [0, 0, img.naturalWidth || img.videoWidth || img.width, img.naturalHeight || img.videoHeight || img.height];
  cx.fillStyle = "#808080"; cx.fillRect(0, 0, SIZE, SIZE);
  const s = Math.min(SIZE / w, SIZE / h), dw = w * s, dh = h * s;
  cx.drawImage(img, x, y, w, h, (SIZE - dw) / 2, (SIZE - dh) / 2, dw, dh);
  const d = cx.getImageData(0, 0, SIZE, SIZE);
  const out = await (await load())(new RawImage(d.data, SIZE, SIZE, 4).rgb());
  return Float32Array.from(out.data.slice(0, out.dims[out.dims.length - 1]));   // the [CLS] token: the whole picture
}
