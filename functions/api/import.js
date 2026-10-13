// Cloudflare Pages Function: GET /api/import?url=<deck page link>
// Opens a public deck page and returns its card list as plain text, ready for the deck checker:
//   { name, text, source }   or   { error }
// Other sites: a text box on the page, a decklist embedded as JSON in the page (e.g. Piltover Archive),
// or any "3 Card Name" / "3x Card Name" lines found in the page.
// RiftDecks blocks requests from servers (HTTP 403), so its links get a message pointing to Export TXT instead.

const MAX_BYTES = 2_000_000;
const SECTION = /^(legend|champions?|main ?deck|deck|units?|spells?|gear|battlefields?|runes?|rune pool|sideboard|side ?deck|tokens?)\s*(\(\d+\))?\s*:?$/i;

export async function onRequestGet({ request }) {
  const raw = (new URL(request.url).searchParams.get("url") || "").trim();
  let target;
  try { target = new URL(raw); } catch { return reply({ error: "That doesn't look like a link. Copy the full address of the deck page, starting with https://" }, 400); }
  if (!/^https?:$/.test(target.protocol)) return reply({ error: "Only web links (https://…) can be imported." }, 400);
  const host = target.hostname.toLowerCase();
  if (host === "localhost" || host.endsWith(".local") || host.endsWith(".internal") || /^[\d.]+$/.test(host) || host.includes(":"))
    return reply({ error: "That link can't be imported." }, 400);

  try {
    const page = await get(target);
    const name = titleOf(page);
    let text = listFromTextarea(page);
    if (!text && /(^|\.)riftdecks\.com$/.test(host)) {
      const m = page.match(/\/decks\/export\/([0-9a-f-]{36})/i);
      if (m) text = listFromTextarea(await get(new URL(`/decks/export/${m[1]}/txt`, target)));
    }
    if (!text) text = listFromJson(page);
    if (!text) text = listFromLines(page);
    if (!text) return reply({ error: "Couldn't find a decklist on that page. Copy the list from the page and paste it into the Decklist box instead." }, 422);
    return reply({ name, text, source: host });
  } catch (e) {
    const why = String(e && e.message || e).slice(0, 120);
    if (/(^|\.)riftdecks\.com$/.test(host) && /HTTP 40[13]/.test(why))
      return reply({ error: "RiftDecks doesn't let other websites read its decks, so the list can't be imported from a link. Use the steps below instead: Export this Deck → Export TXT, then copy and paste the text.", detail: why }, 502);
    return reply({ error: "Couldn't open that page. Check the link works in your browser, or copy the list and paste it instead.", detail: why }, 502);
  }
}

async function get(url) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 9000);
  try {
    const r = await fetch(url, {
      signal: ctrl.signal, redirect: "follow",
      headers: {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.9",
      },
    });
    if (!r.ok) throw new Error("HTTP " + r.status);
    const t = await r.text();
    return t.length > MAX_BYTES ? t.slice(0, MAX_BYTES) : t;
  } finally { clearTimeout(timer); }
}

function decode(s) {
  return s.replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(+n))
          .replace(/&#x([0-9a-f]+);/gi, (_, n) => String.fromCodePoint(parseInt(n, 16)))
          .replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&nbsp;/g, " ").replace(/&amp;/g, "&");
}

function titleOf(html) {
  const m = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
  return m ? decode(m[1]).split(/\s+[|–—]\s+/)[0].trim().slice(0, 80) : "";
}

const isCardLine = l => /^\d{1,2}\s*x?\s+\S/i.test(l);

// a <textarea> or <pre> holding a decklist (RiftDecks' Export TXT page, many other sites)
function listFromTextarea(html) {
  const boxes = [...html.matchAll(/<(textarea|pre)[^>]*>([\s\S]*?)<\/\1>/gi)].map(m => decode(m[2]).replace(/\r/g, "").trim());
  let best = "", bestN = 0;
  for (const b of boxes) {
    const n = b.split("\n").filter(l => isCardLine(l.trim())).length;
    if (n > bestN) { best = b; bestN = n; }
  }
  return bestN >= 3 ? best.slice(0, 8000) : "";
}

// any "3 Card Name" lines in the page text, keeping section headings
function listFromLines(html) {
  const text = decode(html
    .replace(/<(script|style|noscript|svg)[\s\S]*?<\/\1>/gi, " ")
    .replace(/<br\s*\/?>|<\/(tr|li|p|div|h\d|td|th)>/gi, "\n")
    .replace(/<[^>]+>/g, " "));
  const out = [];
  for (let line of text.split("\n")) {
    line = line.replace(/\s+/g, " ").trim();
    if (!line) continue;
    if (SECTION.test(line)) { out.push(line.replace(/\s*\(\d+\)\s*/, "").replace(/:?$/, ":")); continue; }
    const m = line.match(/^(\d{1,2})\s*x?\s+(.{2,60}?)(\s+\$[\d.,]+)?$/i);
    if (m && /[a-z]/i.test(m[2])) out.push(`${m[1]} ${m[2].trim()}`);
  }
  while (out.length && SECTION.test(out[out.length - 1])) out.pop();
  return out.filter(isCardLine).length >= 3 ? out.slice(0, 200).join("\n") : "";
}

// decklists embedded as JSON in the page (Next.js and similar sites): {"quantity":3,"card":{..."name":"Gust"...}}
function listFromJson(html) {
  const t = html.replace(/\\\\"/g, '"').replace(/\\"/g, '"');
  const SECT = /"(legends?|champions?|mainDeck|main_deck|maindeck|mainboard|deck|units|spells|gear|battlefields?|runes?|runeDeck|sideboard|sideDeck|side_deck)"\s*:\s*\[/gi;
  const marks = [];
  for (const m of t.matchAll(SECT)) marks.push([m.index, m[1]]);
  const label = k => {
    k = k.toLowerCase();
    if (k.startsWith("legend")) return "Legend";
    if (k.startsWith("champion")) return "Champion";
    if (k.startsWith("battlefield")) return "Battlefields";
    if (k.startsWith("rune")) return "Runes";
    if (k.startsWith("side")) return "Sideboard";
    return "Main Deck";
  };
  const seen = new Set(), bySection = new Map();
  for (const m of t.matchAll(/"(?:quantity|count|qty|copies)"\s*:\s*(\d{1,2})\b/g)) {
    const q = +m[1]; if (q < 1 || q > 12) continue;
    const after = t.slice(m.index, m.index + 600);
    const nm = after.match(/"name"\s*:\s*"([^"]{2,60})"/); if (!nm) continue;
    let sec = "Main Deck";
    for (const [pos, key] of marks) { if (pos < m.index) sec = label(key); else break; }
    const k = sec + "|" + nm[1];
    if (seen.has(k)) continue; seen.add(k);
    if (!bySection.has(sec)) bySection.set(sec, []);
    bySection.get(sec).push(`${q} ${nm[1]}`);
  }
  const order = ["Legend", "Champion", "Main Deck", "Battlefields", "Runes", "Sideboard"];
  const lines = [];
  for (const s of order) if (bySection.has(s)) { lines.push(s + ":", ...bySection.get(s), ""); }
  const count = [...bySection.values()].reduce((a, v) => a + v.length, 0);
  return count >= 3 ? lines.join("\n").trim().slice(0, 8000) : "";
}

function reply(body, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });
}
