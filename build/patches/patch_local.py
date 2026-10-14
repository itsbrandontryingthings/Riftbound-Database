#!/usr/bin/env python3
"""Make the local (on-your-computer) copy of the Riftbound tracker: card thumbnails on every row,
loaded straight from Riot's image server (Riftcodex links) or TCGplayer, plus a tap-to-enlarge view.
Works only when opened as a file in a normal browser (Claude pages block outside images).
Usage: patch_local.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:70]!r}, found {n}"
    h = h.replace(old, new)

import re
h = re.sub(r"<title>[^<]*</title>", "<title>Riftbound - Complete Database (Local)</title>", h, count=1)

# ---------- CSS: a thumbnail column on every list
rep(".sug li{display:grid;grid-template-columns:64px minmax(0,1fr) auto;",
    ".sug li{display:grid;grid-template-columns:36px 64px minmax(0,1fr) auto;")
rep(".log li{display:grid;grid-template-columns:72px minmax(0,1fr) auto auto;",
    ".log li{display:grid;grid-template-columns:40px 72px minmax(0,1fr) auto auto;")
rep(".drow{display:grid;grid-template-columns:44px minmax(0,1fr) 84px minmax(96px,auto);",
    ".drow{display:grid;grid-template-columns:40px 44px minmax(0,1fr) 84px minmax(96px,auto);")
rep("@media (max-width:520px){.drow{grid-template-columns:36px minmax(0,1fr) auto;}.drow .p{grid-column:2/4;justify-self:start}.log li{grid-template-columns:54px minmax(0,1fr) auto}.log li .pp{grid-column:2}}",
    "@media (max-width:520px){.drow{grid-template-columns:36px 36px minmax(0,1fr) auto;}.drow .p{grid-column:3/5;justify-self:start}.log li{grid-template-columns:36px 54px minmax(0,1fr) auto}.log li .pp{grid-column:3}}")
rep(".card{display:grid;grid-template-columns:72px minmax(0,1fr) auto;",
    ".card{display:grid;grid-template-columns:60px 72px minmax(0,1fr) auto;")
rep("  .card{grid-template-columns:54px minmax(0,1fr) auto;gap:8px;padding:8px}",
    "  .card{grid-template-columns:48px 50px minmax(0,1fr) auto;gap:8px;padding:8px}")
rep(".more{justify-self:center}", """.more{justify-self:center}
.thumb{position:relative;display:block;width:100%;max-width:100%;aspect-ratio:744/1039;padding:0;border:1px solid var(--line);border-radius:4px;background:var(--bg);overflow:hidden}
button.thumb{cursor:zoom-in}
button.thumb:hover{border-color:var(--muted)}
.thumb img{display:block;width:100%;height:100%;object-fit:contain}
.thumb.none{display:grid;place-items:center;text-align:center;color:var(--muted);font-size:10px;line-height:1.2;font-family:var(--display)}
.thumb .bm{position:absolute;left:0;right:0;bottom:0;background:rgb(0 0 0 / .72);color:var(--warn);font-size:9px;line-height:13px;text-align:center;letter-spacing:.04em;white-space:nowrap}
@media (max-width:520px){.thumb .bm{font-size:7px;letter-spacing:0;line-height:11px}}
#lb{border:1px solid var(--line);border-radius:12px;background:var(--panel);color:var(--fg);padding:14px;max-width:min(640px,calc(100vw - 32px));width:auto;max-height:calc(100dvh - 24px);overflow:auto}
#lb::backdrop{background:rgb(5 6 10 / .78)}
#lb .lbimg{display:block;width:min(612px,calc(100vw - 60px),(100dvh - 150px) * 0.716);max-width:100%;height:auto;margin:0 auto;border-radius:10px;background:var(--bg);aspect-ratio:744/1039;object-fit:contain}
#lb .lbimg.land{aspect-ratio:1039/744;width:min(612px,calc(100vw - 60px),(100dvh - 150px) * 1.396)}
#lb .lbh{display:flex;justify-content:space-between;align-items:flex-start;gap:10px;margin-bottom:10px}
#lb h2{font-family:var(--display);font-size:17px;margin:0}
#lb .lbx{background:none;border:1px solid var(--line);border-radius:6px;width:32px;height:32px;font-size:18px;line-height:1;color:var(--muted);flex:none}
#lb .lbf{display:flex;gap:8px 12px;flex-wrap:wrap;align-items:center;margin-top:10px}
.localnote{background:var(--row);border:1px solid var(--line);border-radius:8px;padding:10px 12px;font-size:13.5px;color:var(--muted)}
.localnote b{color:var(--fg)}""")

# ---------- local-copy note under the header + lightbox
rep('    <div class="meta" id="c-updated"></div>\n  </div>',
    '    <div class="meta" id="c-updated"></div>\n  </div>\n  <p class="localnote"><b>Local copy on this computer.</b> Your cards and decks here save in this browser only. To bring over what you entered on your online page, open it, go to <b>Back up or move your collection</b>, tap <b>Copy backup code</b>, then paste the code under Restore at the bottom of this page.</p>')
rep('<button class="btn more" id="more" hidden>Show more</button>',
    '<button class="btn more" id="more" hidden>Show more</button>\n  <dialog id="lb" aria-labelledby="lb-name"><div class="lbh"><div><h2 id="lb-name"></h2><div class="sub" id="lb-sub"></div></div><button class="lbx" id="lb-x" aria-label="Close">×</button></div><img class="lbimg" id="lb-img" alt="" referrerpolicy="no-referrer"><div class="lbf"><span class="meta" id="lb-note"></span><span style="flex:1"></span><span id="lb-link"></span></div></dialog>')

# ---------- helpers
rep('function cardHTML(c){', r'''// card images, loaded from Riot's image server (via Riftcodex links) or TCGplayer's product photo
const RC_IMG = "https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/";
function imgURL(c, w){
  if (!c) return "";
  // WebP keeps card text crisp at a fraction of the PNG size; 744 = the card's full resolution
  if (c.img) return w >= 744 ? `${RC_IMG}${c.img}?accountingTag=RB&fm=webp&q=92` : `${RC_IMG}${c.img}?accountingTag=RB&w=${w}&fm=webp&q=90`;
  if (c.imgTcg && c.tcg) return w > 200 ? `https://tcgplayer-cdn.tcgplayer.com/product/${c.tcg}_in_1000x1000.jpg` : `https://tcgplayer-cdn.tcgplayer.com/product/${c.tcg}_200w.jpg`;
  return "";
}
function thumbHTML(c, w){
  const u = imgURL(c, w || 160);
  if (!u) return `<span class="thumb none" title="No picture of this printing exists yet" aria-hidden="true">No<br>image</span>`;
  return `<button class="thumb" data-img="${esc(c.id)}" aria-label="Enlarge ${esc(c.name)}"${c.imgBase ? ' title="Regular printing\'s art; no image of this exact printing yet"' : ""}><img src="${u}" alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer">${c.imgBase ? '<span class="bm">BASE ART</span>' : ""}</button>`;
}
let lbToken = 0;
function openCard(c){
  if (!c) return;
  $("lb-name").textContent = c.name;
  const code = c.set + " " + c.id.split("-").slice(1).join("-").replace(/-\d+$/,"").replace("~metal","").toUpperCase();
  $("lb-sub").innerHTML = `<span>${esc(code)}</span><span class="r-${c.rarity}">${c.rarity}</span>${c.variant?`<span class="pill var">${esc(c.variant)}</span>`:""}`;
  // show the small picture (usually already loaded) at once, then swap in the full-size one;
  // a newer click wins, so an earlier card's picture can never flash up
  const im = $("lb-img"), token = ++lbToken, full = imgURL(c, 744), quick = imgURL(c, typeof st !== "undefined" && st.view === "grid" ? 240 : 160);
  im.removeAttribute("src"); im.alt = c.name; im.classList.toggle("land", c.type === "Battlefield");
  if (quick) im.src = quick;
  if (full && full !== quick){ const pre = new Image(); pre.referrerPolicy = "no-referrer"; pre.onload = () => { if (token === lbToken) im.src = full; }; pre.src = full; }
  $("lb-note").textContent = c.imgBase ? "Regular printing's art. There's no image of this exact printing yet." : c.imgTcg ? "Image: TCGplayer" : "Image: Riot Games, via Riftcodex";
  $("lb-link").innerHTML = viewLink(c);
  try { $("lb").showModal(); } catch(e){ $("lb").setAttribute("open", ""); }
}
document.addEventListener("click", e => { const t = e.target.closest("button.thumb[data-img]"); if (t){ e.preventDefault(); e.stopPropagation(); openCard(CARDS.find(x => x.id === t.dataset.img)); } }, true);
$("lb-x").addEventListener("click", () => $("lb").close());
$("lb").addEventListener("click", e => { if (e.target === $("lb")) $("lb").close(); });
// a picture that fails to load is retried twice (after a pause, then at full size) before showing "No image"
document.addEventListener("error", e => {
  const im = e.target; if (im.tagName !== "IMG" || !im.parentElement || !im.parentElement.classList.contains("thumb")) return;
  const tries = +(im.dataset.tries || 0);
  if (tries < 2){ im.dataset.tries = tries + 1; const src = im.src; setTimeout(() => { im.src = tries === 0 ? src + (src.includes("?") ? "&" : "?") + "r=1" : src.replace(/&w=\d+/, "").replace(/_200w\.jpg/, "_in_1000x1000.jpg"); }, 1200 * (tries + 1)); return; }
  im.parentElement.outerHTML = `<span class="thumb none" title="This picture didn't load. Reload the page to try again." aria-hidden="true">No<br>image</span>`;
}, true);
function cardHTML(c){''')

# rows
rep('''  return `<div class="card${n?" got":""}" data-id="${esc(c.id)}">
    <div class="code">''', '''  return `<div class="card${n?" got":""}" data-id="${esc(c.id)}">
    ${thumbHTML(c)}
    <div class="code">''')
rep('''aria-selected="${i===sel}">
    <span class="code">''', '''aria-selected="${i===sel}">
    ${thumbHTML(c, 100).replace("<button", "<span").replace("</button>", "</span>").replace(/ data-img="[^"]*"/, "")}
    <span class="code">''')
rep('''return `<li><span class="code">''', '''return `<li>${thumbHTML(c, 100)}<span class="code">''')
rep('''    <span class="q">${r.q}×</span>''', '''    ${r.known ? thumbHTML(r.cheap || (groups[r.key]||[])[0], 100) : '<span class="thumb none" aria-hidden="true">No<br>image</span>'}
    <span class="q">${r.q}×</span>''')

# footnote: storage is local here
rep("your counts are saved to your Claude account, so they follow you to your phone. Each card name opens its TCGplayer page.</p>",
    "on this local copy your counts save in this browser, so use the backup code to move them between this page and your online one. Each card name opens its TCGplayer page. Card images load from Riot's image server (found through the Riftcodex card database); tap a picture to enlarge it. A few promo printings Riftcodex doesn't list use TCGplayer's photo, or the regular printing's art marked <b>BASE ART</b>.</p>")
rep("<p class=\"note\">🔒 Your card counts and decks are private. Anyone else who opens this link gets their own empty database, and nobody, including the person who shared it, can see what you've entered.</p>",
    "<p class=\"note\">🔒 This file lives only on your computer. Nobody else can see what you enter here.</p>")

open(out, "w", encoding="utf-8").write(h)
print("ok", len(h))
