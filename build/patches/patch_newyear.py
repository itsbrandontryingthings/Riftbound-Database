#!/usr/bin/env python3
"""New Year and Chinese New Year looks (website; runs last). Both switch themselves on by date, after winter (Dec 31):
- New Year (Jan 1 - Jan 14, html.newyear): gold accent, fireworks bursting over the top art strip, a party garland on
  the header, 🎆 after the title, Captain Teemo in a party hat, a party row along the bottom strip and a little confetti
  falling behind the page.
- Chinese New Year (Jan 15 to the Lantern Festival, 14 days after Chinese New Year; html.cny): red accent, red and gold
  fireworks, red lanterns hanging from the header, that year's zodiac animal after the title, Teemo in a red cap, a
  lucky row (🧧🏮🍊🥟🐉) along the bottom strip and plum blossoms falling behind the page.
Teemo says something new every two days in each (NY_SAYS / CN_SAYS), with special lines on Jan 1, Chinese New Year's
Eve and Day, and the Lantern Festival. Chinese New Year dates are in CNY_DATES (2027-2036); later years end Feb 20.
Like the other seasons: decoration only, transform/opacity animations, falling bits drawn behind the page (z-index
-1) so they never cover cards, nothing moves for reduced motion. Preview with ?season=newyear or ?season=cny
(plus &tip=N for Teemo's line N).
Usage: patch_newyear.py in.html out.html"""
import json, sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

CNY_DATES = {2027: "0206", 2028: "0126", 2029: "0213", 2030: "0203", 2031: "0123", 2032: "0211", 2033: "0131",
             2034: "0219", 2035: "0208", 2036: "0128"}
ANIMALS = [["Rat", "🐀"], ["Ox", "🐂"], ["Tiger", "🐅"], ["Rabbit", "🐇"], ["Dragon", "🐉"], ["Snake", "🐍"],
           ["Horse", "🐎"], ["Goat", "🐐"], ["Monkey", "🐒"], ["Rooster", "🐓"], ["Dog", "🐕"], ["Pig", "🐖"]]  # 2020 = Rat

NY_SAYS = [  # Jan 1 - 14, one every two days
    ("Happy New Year from Captain Teemo!", "New year, new decks, same old mushrooms.", "🎆"),
    ("Captain Teemo's resolution:", "finally finish that one set. This is the year!", "📋"),
    ("Fresh calendar, fresh binder!", "A great time to check how close your collection is to complete.", "📊"),
    ("Still finding confetti everywhere…", "Captain Teemo may have overdone the party poppers.", "🎊"),
    ("New year tip:", "the Marketplace tab shows every card your decks still need.", "🛒"),
    ("A whole year of Riftbound ahead!", "Captain Teemo is already scouting out the next set.", "🔭"),
    ("Cheers to you, Summoner!", "Thanks for building your collection with RBDB.", "🥂"),
]
NY_SPECIAL = {"101": ("Happy New Year from Captain Teemo!", "Here's to a year of great pulls and even better games.", "🥳")}
CN_SAYS = [  # Jan 15 to the Lantern Festival (up to 49 days), one every two days; {animal} = that year's animal
    ("The Year of the {animal} is coming!", "Captain Teemo is hanging lanterns all over Bandle City.", "🏮"),
    ("Red envelope season!", "Captain Teemo hopes yours is full of booster packs.", "🧧"),
    ("Spring cleaning time!", "Sweep out the old year and tidy up your decks in My Decks.", "🧹"),
    ("Dumplings, noodles and Riftbound…", "Captain Teemo's perfect holiday menu.", "🥟"),
    ("Lucky tip:", "share your wish list link so friends know what to get you.", "🍀"),
    ("Oranges for luck!", "Captain Teemo is saving the shiniest one for pack-opening day.", "🍊"),
    ("Firecrackers scare away bad luck!", "And bad pulls, Captain Teemo hopes.", "🧨"),
    ("The {animal} brings good fortune!", "May your next pack hold a foil.", "✨"),
    ("Captain Teemo learned the lion dance!", "Well, half of it. He still needs a partner.", "🦁"),
    ("New year, lucky pulls!", "Add every one to your collection in the Open Packs tab.", "📦"),
    ("Gold is a lucky colour!", "Speaking of gold, how's your collection's value looking?", "💰"),
    ("Wishing you prosperity!", "And a binder with no empty pockets.", "📚"),
    ("Paper cutting time!", "Captain Teemo is making window decorations. Carefully.", "✂️"),
    ("Family, friends and a few friendly games!", "That's what the new year is all about.", "🎴"),
    ("Captain Teemo tried the dragon dance!", "He was the tail. The very, very short tail.", "🐉"),
    ("Trade tip:", "make offers on your friends' shopping lists in Marketplace.", "🤝"),
    ("Sticky rice cake for a sticky-good year!", "Captain Teemo had three. Maybe four.", "🍡"),
    ("Out with the old, in with the new!", "Check your Wish List for cards to chase this year.", "💝"),
    ("Lanterns lit, decks shuffled!", "Captain Teemo is ready for a lucky game.", "🏮"),
    ("Good fortune is coming your way!", "Captain Teemo can feel it in his mushrooms.", "🍄"),
    ("Watching the market?", "Every card shows how much its price changed lately.", "📈"),
    ("Happy Spring Festival!", "Captain Teemo's favourite festival has \"spring\" right in the name.", "🌸"),
    ("Riddle time!", "What's small, fast and always hidden? Captain Teemo, of course.", "🫣"),
    ("May the {animal} bring you rare pulls!", "Captain Teemo is keeping his paws crossed.", "🤞"),
    ("Thanks for celebrating with Captain Teemo!", "May the Year of the {animal} be your luckiest yet.", "💛"),
]
CN_SPECIAL = {"eve": ("Happy Lunar New Year's Eve!", "Captain Teemo is staying up late for the fireworks.", "🎆"),
              "day": ("Happy Lunar New Year!", "新年快乐! Captain Teemo wishes you a lucky Year of the {animal}.", "🧧"),
              "lantern": ("Happy Lantern Festival!", "The last night of the new year: Captain Teemo saved his brightest lantern.", "🏮")}

# fireworks over the top strip: 12 dots per burst flying out from a point, then a pause before the next burst
def burst(x, y, c, c2, d):  # c = New Year colour, c2 = Chinese New Year colour (red / gold)
    return f'<span class="ny-fw" style="left:{x}%;top:{y}%;--c:{c};--c2:{c2};--d:{d}s">' + "".join(f'<i style="--a:{a * 30}deg"></i>' for a in range(12)) + '</span>'
FIREWORKS = burst(14, 34, "#ffd34d", "#ffcf5a", 0) + burst(38, 22, "#ff5fa2", "#ff4b3e", 1.1) + burst(63, 40, "#5ad1ff", "#ffcf5a", 2.0) + burst(86, 26, "#9dff7a", "#ff4b3e", .6)
CONFETTI = "".join(f'<i style="left:{x}%;background:{c};--d:-{d}s;--w:{w}s;--dx:{dx}px"></i>' for x, c, d, w, dx in [
    (4, "#ffd34d", 0, 24, 30), (15, "#ff5fa2", 9, 29, -25), (27, "#5ad1ff", 17, 26, 25), (39, "#9dff7a", 4, 31, -30), (51, "#ffd34d", 21, 27, 20),
    (62, "#c48dff", 12, 30, -25), (73, "#ff5fa2", 6, 25, 30), (84, "#5ad1ff", 15, 32, -20), (95, "#ffd34d", 2, 28, 20)])
BLOSSOMS = "".join(f'<i style="left:{x}%;font-size:{s}px;--d:-{d}s;--w:{w}s;--dx:{dx}px">🌸</i>' for x, s, d, w, dx in [
    (4, 13, 0, 27, 40), (15, 11, 9, 32, -30), (27, 14, 17, 29, 35), (39, 11, 4, 34, -40), (51, 13, 21, 30, 30),
    (62, 11, 12, 33, -35), (73, 14, 6, 28, 40), (84, 11, 15, 35, -30), (95, 12, 2, 31, 30)])
GARLAND = "".join(f"<span>{e}</span>" for e in "🎊⭐🎉✨🎊⭐🎉✨🎊⭐🎉✨🎊⭐🎉")
LANTERNS = "".join(f'<span style="--d:{i * .4:.1f}s">🏮</span>' for i in range(9))
NY_ROW = "".join(f"<span>{e}</span>" for e in ["🎉", "🥂", "🎆", "🎊", "✨", "🍾", "⭐", "🎉", "🥂", "🎆", "🎊", "✨", "🍾", "⭐", "🎉"])
CN_ROW = "".join(f"<span>{e}</span>" for e in ["🧧", "🏮", "🍊", "🥟", "🐉", "🧧", "🎆", "🍊", "🏮", "🥟", "🧧", "🐉", "🍊", "🏮", "🧧"])
FACE = "https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/4fd9e82cbd96010e2556430970d433022b541a51-1488x2078.png?accountingTag=RB&w=300&fm=webp&q=85"
PARTY_HAT = ('<svg class="ny-hat" viewBox="0 0 40 40"><path d="M8 37 20 5l12 32z" fill="#7b5cff"/>'
             '<path d="M12.3 25.5h15.4l1.6 4.3H10.7zM15.7 16.3h8.6l1.4 3.7H14.3z" fill="#f2c14e"/><circle cx="20" cy="5" r="4.2" fill="#ff5fa2"/></svg>')
RED_CAP = ('<svg class="cn-hat" viewBox="0 0 40 34"><path d="M4 29C4 13 36 13 36 29z" fill="#c8202a"/>'
           '<rect x="3" y="26" width="34" height="6" rx="3" fill="#f5c542"/><circle cx="20" cy="13" r="3.6" fill="#f5c542"/></svg>')

# season switch (after winter's): New Year Jan 1-14, Chinese New Year Jan 15 to the Lantern Festival
rep('<div class="wrap" id="app">', '''<script>window.NY_SAYS = ''' + json.dumps(NY_SAYS, ensure_ascii=False) + ''';
window.NY_SPECIAL = ''' + json.dumps(NY_SPECIAL, ensure_ascii=False) + ''';
window.CN_SAYS = ''' + json.dumps(CN_SAYS, ensure_ascii=False) + ''';
window.CN_SPECIAL = ''' + json.dumps(CN_SPECIAL, ensure_ascii=False) + ''';
window.NY_SEASON = (() => {
  const q = new URLSearchParams(location.search).get("season"), now = new Date(), y = now.getFullYear();
  const today = new Date(y, now.getMonth(), now.getDate()), md = (now.getMonth() + 1) * 100 + now.getDate();
  const cy = q === "cny" && now.getMonth() >= 2 ? y + 1 : y, dates = ''' + json.dumps(CNY_DATES) + ''';
  const cd = dates[cy], cny = cd ? new Date(cy, +cd.slice(0, 2) - 1, +cd.slice(2)) : null;
  const lantern = cny ? new Date(cy, cny.getMonth(), cny.getDate() + 14) : new Date(cy, 1, 20);
  const newyear = q ? q === "newyear" : md >= 101 && md <= 114, chinese = q ? q === "cny" : md >= 115 && today <= lantern;
  document.documentElement.classList.toggle("newyear", newyear); document.documentElement.classList.toggle("cny", chinese);
  return {today, newyear, chinese, cny, lantern, animal: ''' + json.dumps(ANIMALS, ensure_ascii=False) + '''[((cy - 2020) % 12 + 12) % 12]};
})();</script>
<div class="ny-fall" aria-hidden="true">''' + CONFETTI + '''</div><div class="cn-fall" aria-hidden="true">''' + BLOSSOMS + '''</div>
<div class="wrap" id="app">''')
rep('<div class="art-band art-top" aria-hidden="true">', '<div class="art-band art-top" aria-hidden="true">' + FIREWORKS)
rep('<div class="art-band art-bottom" aria-hidden="true">', '<div class="art-band art-bottom" aria-hidden="true"><span class="ny-row">' + NY_ROW + '</span><span class="ny-row cn-row">' + CN_ROW + '</span>')
rep('  <div class="top">\n', '  <div class="top">\n    <div class="ny-garland" aria-hidden="true">' + GARLAND + '</div><div class="cn-lanterns" aria-hidden="true">' + LANTERNS + '</div>\n')
rep('<span class="xm-tree" aria-hidden="true">🎄</span></h1>', '<span class="xm-tree" aria-hidden="true">🎄</span><span class="ny-t" aria-hidden="true">🎆</span><span class="cn-t" aria-hidden="true" id="cn-animal"></span></h1>')
rep('<div class="xm-hi" aria-hidden="true">', '<div class="ny-hi" aria-hidden="true"><span class="hw-face"><span class="hw-ring"><img src="' + FACE + '" alt="" referrerpolicy="no-referrer" decoding="async" loading="lazy"></span>'
    + PARTY_HAT + RED_CAP + '</span><span class="hw-bubble" id="ny-say"></span></div>\n    <div class="xm-hi" aria-hidden="true">')

# Teemo's line: a special day's line, else a new one every two days from the start of the season; ?tip=N previews line N
_j = h.rfind("</body>")
h = h[:_j] + '''<script>(() => {
  const S = window.NY_SEASON, el = document.getElementById("ny-say"); if (!S || !el || !(S.newyear || S.chinese)) return;
  const esc = s => s.replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"})[c]);
  const t = S.today, md = String((t.getMonth() + 1) * 100 + t.getDate()), tip = new URLSearchParams(location.search).get("tip");
  const days = (a, b) => Math.round((a - b) / 864e5), list = S.newyear ? NY_SAYS : CN_SAYS;
  const start = S.newyear ? new Date(t.getFullYear(), 0, 1) : new Date(t.getFullYear(), 0, 15);
  let say = list[Math.max(0, Math.floor(days(t, start) / 2)) % list.length];
  if (S.newyear && NY_SPECIAL[md]) say = NY_SPECIAL[md];
  if (S.chinese && S.cny) { const k = days(t, S.cny); if (k === -1) say = CN_SPECIAL.eve; else if (k === 0) say = CN_SPECIAL.day; else if (days(t, S.lantern) === 0) say = CN_SPECIAL.lantern; }
  if (tip !== null) say = list[Math.abs(+tip || 0) % list.length];
  const a = S.animal, fill = s => s.replace(/\\{animal\\}/g, a[0]);
  el.innerHTML = `<b>${esc(fill(say[0]))}</b> ${esc(fill(say[1]))} <span class="hw-shroom">${say[2]}</span>`;
  const ce = document.getElementById("cn-animal"); if (ce) { ce.textContent = a[1]; ce.title = "Year of the " + a[0]; }
})();</script>
''' + h[_j:]

_i = h.rfind("</style>"); h = h[:_i] + """/* New Year / Chinese New Year (patch_newyear) */
.ny-fall,.cn-fall,.ny-fw,.ny-row,.ny-garland,.cn-lanterns,.ny-t,.cn-t,.ny-hi,.ny-hat,.cn-hat{display:none}
html.newyear{--accent:#f2c14e;--tc:#f2c14e}
html.cny{--accent:#ff6a5c;--tc:#ff6a5c}
html.newyear .art-top::after{background:linear-gradient(180deg,rgb(60 30 120 / .22) 0%,rgb(20 15 45 / .35) 55%,var(--bg) 100%)}
html.cny .art-top::after{background:linear-gradient(180deg,rgb(150 20 20 / .22) 0%,rgb(45 12 12 / .35) 55%,var(--bg) 100%)}
html.newyear .top,html.cny .top{position:relative;border-color:color-mix(in srgb,var(--tc) 35%,var(--line));box-shadow:0 0 0 1px color-mix(in srgb,var(--tc) 8%,transparent),0 10px 30px -12px color-mix(in srgb,var(--tc) 40%,transparent)}
/* fireworks */
html.newyear .ny-fw,html.cny .ny-fw{display:block;position:absolute;z-index:2;width:0;height:0;--r:54px}
.ny-fw i{position:absolute;left:-3px;top:-3px;width:6px;height:6px;border-radius:50%;background:var(--c);box-shadow:0 0 8px 1px var(--c);opacity:0;animation:ny-burst 3.4s ease-out var(--d) infinite}
html.cny .ny-fw i{--c:var(--c2)}
@keyframes ny-burst{0%{transform:rotate(var(--a)) translateX(0) scale(.6);opacity:0}4%{opacity:1}34%{transform:rotate(var(--a)) translateX(var(--r)) scale(1);opacity:.9}48%{transform:rotate(var(--a)) translateX(calc(var(--r) * 1.15)) scale(.4);opacity:0}100%{transform:rotate(var(--a)) translateX(calc(var(--r) * 1.15)) scale(.4);opacity:0}}
/* falling confetti / plum blossoms, behind the page */
html.newyear .ny-fall,html.cny .cn-fall{display:block;position:fixed;inset:0;z-index:-1;pointer-events:none;overflow:hidden}
.ny-fall i,.cn-fall i{position:absolute;top:0;font-style:normal;line-height:1;opacity:0;animation:ny-drop var(--w) linear var(--d) infinite;will-change:transform}
.ny-fall i{width:6px;height:10px;border-radius:1px}
@keyframes ny-drop{0%{transform:translate3d(0,-30px,0) rotate(0);opacity:0}10%{opacity:.5}50%{transform:translate3d(var(--dx),50vh,0) rotate(200deg)}90%{opacity:.45}100%{transform:translate3d(0,105vh,0) rotate(400deg);opacity:0}}
/* header: party garland / red lanterns */
html.newyear .ny-garland{display:flex;justify-content:space-between;position:absolute;left:14px;right:14px;top:-15px;z-index:2;pointer-events:none;font-size:22px;line-height:1}
html.newyear .ny-garland::before{content:"";position:absolute;left:0;right:0;top:4px;height:10px;border-bottom:1.5px solid rgb(242 193 78 / .5);border-radius:0 0 50% 50%;z-index:-1}
.ny-garland span{display:block}
.ny-garland span:nth-child(odd){transform:translateY(3px) rotate(-8deg)}
.ny-garland span:nth-child(even){transform:rotate(7deg)}
html.cny .top{padding-top:42px}
html.cny .cn-lanterns{display:flex;justify-content:space-around;position:absolute;left:10px;right:10px;top:0;z-index:2;pointer-events:none;font-size:22px;line-height:1}
.cn-lanterns span{display:block;position:relative;padding-top:8px;transform-origin:50% 0;animation:cn-sway 3s ease-in-out var(--d) infinite}
.cn-lanterns span::before{content:"";position:absolute;left:50%;top:0;width:1.5px;height:9px;margin-left:-.75px;background:#f5c542}
@keyframes cn-sway{0%,100%{transform:rotate(-5deg)}50%{transform:rotate(5deg)}}
html.newyear .ny-t,html.cny .cn-t{display:inline-block;font-size:.9em;margin-left:-2px}
/* Teemo */
html.newyear .ny-hi,html.cny .ny-hi{display:flex;align-items:center;gap:12px;pointer-events:none;margin:14px 0 8px}
.ny-hi .hw-ring{border-color:var(--tc);box-shadow:0 0 14px color-mix(in srgb,var(--tc) 45%,transparent)}
.ny-hi .hw-bubble{background:color-mix(in srgb,var(--tc) 12%,var(--row));border-color:color-mix(in srgb,var(--tc) 40%,var(--line))}
.ny-hi .hw-bubble b{color:var(--tc)}
html.newyear .ny-hat{display:block;position:absolute;overflow:visible;left:12px;top:-30px;width:38px;height:auto;transform:rotate(-12deg)}
html.cny .cn-hat{display:block;position:absolute;overflow:visible;left:4px;top:-17px;width:50px;height:auto;transform:rotate(-8deg)}
/* bottom strip row */
html.newyear .ny-row:not(.cn-row),html.cny .cn-row{display:flex;justify-content:space-around;align-items:flex-end;position:absolute;left:0;right:0;bottom:6px;z-index:2;font-size:30px;line-height:1;pointer-events:none}
@media (max-width:640px){
  html.newyear .ny-fw,html.cny .ny-fw{--r:34px}
  .ny-fw i{width:4px;height:4px;left:-2px;top:-2px}
  .ny-fall i:nth-child(even),.cn-fall i:nth-child(even){display:none}
  html.newyear .ny-garland{font-size:16px;top:-11px;left:8px;right:8px}
  .ny-garland span:nth-child(n+10){display:none}
  html.cny .cn-lanterns{font-size:18px}
  .cn-lanterns span:nth-child(n+6){display:none}
  html.newyear .ny-hat{width:32px;top:-26px;left:10px}
  html.cny .cn-hat{width:42px;top:-14px;left:3px}
  html.newyear .ny-row:not(.cn-row),html.cny .cn-row{font-size:20px;bottom:4px}
  .ny-row span:nth-child(n+10){display:none}
}
@media (prefers-reduced-motion:reduce){
  .ny-fw i,.cn-lanterns span{animation:none!important}
  .ny-fw{display:none!important}
  html.newyear .ny-fall,html.cny .cn-fall{display:none}
}
""" + h[_i:]

open(out, "w", encoding="utf-8").write(h)
print("patch_newyear: ok ->", out)
