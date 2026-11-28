// Runs the scanner's picture model (see scan-ai.js) in the background, so the page, the camera picture and the buttons
// keep working while a look is being worked out. Phones can take a second or more per look; on the page itself that
// froze the scanner (iPhones). Gets the letterboxed picture's pixels from scan-ai.js and sends back the 384 numbers.
import { pipeline, RawImage, env } from "https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.7.1";
env.allowLocalModels = false;
let ext = null;
onmessage = async ({data: {id, model, dtype, size, px}}) => {
  try {
    ext ||= pipeline("image-feature-extraction", model, {dtype, device: "wasm"});
    const e = await ext;
    if (!px) return postMessage({id});
    const out = await e(new RawImage(px, size, size, 4).rgb());
    const v = Float32Array.from(out.data.slice(0, out.dims[out.dims.length - 1]));   // the [CLS] token: the whole picture
    postMessage({id, v}, [v.buffer]);
  } catch(err){ ext = null; postMessage({id, err: String(err && err.message || err)}); }
};
