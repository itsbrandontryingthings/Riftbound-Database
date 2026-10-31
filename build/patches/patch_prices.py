"""Daily prices (website only, last).

prices.js (made every day by tools/fetch_prices.py in .github/workflows/prices.yml) loads after cards.js and replaces
each card's weekly `price` with today's TCGplayer market price (regular, or foil when the printing only comes in foil),
so every total, list and sort uses it. Each card also gets `px` = [market, lowest, foil market, foil lowest, 7-day %,
30-day %]. The card info sheet's price box (now full width) shows the market price, the 7 / 30-day changes (green up,
red down; hidden until there's a price that old), a Regular / Foil table of market and lowest listing, the price date,
and "Listings & Recent Sales on TCGplayer ↗" (TCGplayer doesn't let other sites show its recent sales). The header
says prices update every day and the card list every Monday. Without prices.js the site works as before.
Usage: patch_prices.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

rep('<script src="cards.js"></script>', '''<script src="cards.js"></script>
<script src="prices.js"></script>
<script>(() => {  // daily prices (tools/fetch_prices.py) replace the weekly ones in cards.js
  const P = window.RB_PRICES; if (!P || !P.p) return;
  for (const c of window.RB_CARDS || []){
    const p = c.tcg && P.p[c.tcg]; if (!p) continue;
    c.px = p;
    const v = c.foil ? (p[2] ?? p[3] ?? p[0] ?? p[1]) : (p[0] ?? p[1] ?? p[2] ?? p[3]);
    if (v != null) c.price = v;
  }
  if (window.RB_META) window.RB_META.pricesUpdated = P.updated;
})();</script>''')

rep('#lb .ip{font-family:var(--display);font-size:22px;font-weight:700}', '''#lb .ibox.iprice{grid-column:1/-1}
#lb .chgs{display:flex;gap:8px;flex-wrap:wrap}
#lb .chg{font-size:13px;font-weight:600;border:1px solid var(--line);border-radius:999px;padding:2px 9px;color:var(--muted);font-variant-numeric:tabular-nums}
#lb .chg.up{color:var(--ok);border-color:color-mix(in srgb,var(--ok) 45%,var(--line))}
#lb .chg.dn{color:#ef6b6b;border-color:color-mix(in srgb,#ef6b6b 45%,var(--line))}
#lb .iprs{display:grid;gap:2px;font-size:13.5px;font-variant-numeric:tabular-nums}
#lb .ipr{display:grid;grid-template-columns:64px minmax(0,1fr) minmax(0,1fr);gap:8px;padding:4px 0;border-top:1px solid var(--line)}
#lb .ipr.h{border-top:0;padding:0;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
#lb .ipr span:first-child{color:var(--muted)}
#lb .ip{font-family:var(--display);font-size:22px;font-weight:700}''')

rep('''  const priceBox = `<div class="ibox"><div class="ih"><span>Market</span><span>TCGplayer</span></div>
      ${c.price != null ? `<div class="ip">${moneyHTML(c.price)}</div>${c.foil ? '<div class="meta">This printing only comes in foil</div>' : ""}` : '<div class="meta">No recent sales yet</div>'}
      <a class="ibuy" href="${tcgURL(c)}" target="_blank" rel="noopener">View on TCGplayer ↗</a></div>`;''',
'''  // daily prices: market price, its 7 / 30-day change, market + lowest listing for regular and foil
  const px = c.px, P = window.RB_PRICES;
  const prow = (m, l, label) => m == null && l == null ? "" : `<div class="ipr"><span>${label}</span><span>${m != null ? esc(money(m)) : "—"}</span><span>${l != null ? esc(money(l)) : "—"}</span></div>`;
  const chg = (v, label) => v == null ? "" : `<span class="chg${v > 0 ? " up" : v < 0 ? " dn" : ""}" title="Change in the market price over the last ${label}">${label} ${v > 0 ? "↑" : v < 0 ? "↓" : "→"} ${Math.abs(v)}%</span>`;
  const rows = px ? prow(px[0], px[1], "Regular") + prow(px[2], px[3], "Foil") : "";
  const priceBox = `<div class="ibox iprice"><div class="ih"><span>Market</span><span>TCGplayer</span></div>
      ${c.price != null ? `<div class="ip">${moneyHTML(c.price)}</div>${c.foil ? '<div class="meta">This printing only comes in foil</div>' : ""}` : '<div class="meta">No recent sales yet</div>'}
      ${px && (px[4] != null || px[5] != null) ? `<div class="chgs">${chg(px[4], "7 days")}${chg(px[5], "30 days")}</div>` : ""}
      ${rows ? `<div class="iprs"><div class="ipr h"><span></span><span>Market</span><span>Lowest listing</span></div>${rows}</div>` : ""}
      ${P && px ? `<div class="meta">Prices from ${esc(longDate(P.updated))} · updated daily</div>` : ""}
      <a class="ibuy" href="${tcgURL(c)}" target="_blank" rel="noopener">Listings &amp; Recent Sales on TCGplayer ↗</a></div>`;''')

rep('''The card list and prices are updated <b>every Monday</b>. Last updated <b>${esc(longDate(META.updated))}</b> · next update <b>''',
    '''Prices are updated <b>every day</b>${window.RB_PRICES ? ` (last <b>${esc(longDate(window.RB_PRICES.updated))}</b>)` : ""}, the card list <b>every Monday</b>. Card list last updated <b>${esc(longDate(META.updated))}</b> · next <b>''')

rep('Prices are TCGplayer market prices in US dollars, refreshed weekly;', 'Prices are TCGplayer market prices in US dollars, refreshed daily;')

open(out, "w", encoding="utf-8").write(h)
