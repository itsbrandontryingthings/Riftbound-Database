// Cloudflare Pages Function: GET /api/import?url=<deck page link>
// Opens a public deck page and returns its card list as plain text, ready for the deck checker:
//   { name, text, source }   or   { error }
// RiftDecks: uses the deck's own "Export TXT" list. Other sites: a text box on the page, or any
// "3 Card Name" / "3x Card Name" lines found in the page.

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
    if (!text) text = listFromLines(page);
    if (!text) return reply({ error: "Couldn't find a decklist on that page. Copy the list from the page and paste it into the Decklist box instead." }, 422);
    return reply({ name, text, source: host });
  } catch (e) {
    return reply({ error: "Couldn't open that page. Check the link works in your browser, or copy the list and paste it instead." }, 502);
  }
}

async function get(url) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 9000);
  try {
    const r = await fetch(url, {
      signal: ctrl.signal, redirect: "follow",
      headers: { "user-agent": "Mozilla/5.0 (compatible; RiftboundDatabase/1.0; +https://rbdatabase.pages.dev)", "accept": "text/html,text/plain;q=0.9,*/*;q=0.5" },
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

function reply(body, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });
}
