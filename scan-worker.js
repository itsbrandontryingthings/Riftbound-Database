// Runs the scanner's picture model (scan-ai.js) off the page. The page sends {id} to load it, or {id, data} (prepared
// pixels from prep) to get 384 numbers back; it ends this worker when the scanner closes, which frees all its memory.
import { load, embed } from "./scan-ai.js";
self.onmessage = async e => {
  const {id, data} = e.data;
  try {
    if (data){ const v = await embed(data); self.postMessage({id, v}, [v.buffer]); }
    else { await load(); self.postMessage({id, v: true}); }
  } catch(err){ self.postMessage({id, err: String(err && err.message || err)}); }
};
