"""Quick reset on phones (website only, last).

On phones Collection's filters fold away behind the Filters button, so resetting took two taps (Filters, then Reset
filters). A small "✕ Reset" button (`#fquick`) now sits beside Filters in the search row: phones only, shown only when
a filter is on (`syncReset`), hidden while the panel is open (the full Reset filters button is showing then). It does
the same as Reset filters (it clicks #freset).
Usage: patch_quick_reset.py in.html out.html"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    h = h.replace(old, new)

rep('<span class="fcount" id="fcount"></span></button>',
    '<span class="fcount" id="fcount"></span></button>\n'
    '      <button class="btn fquick" id="fquick" type="button" hidden aria-label="Reset filters">✕ Reset</button>')
rep('.ftoggle{display:none}', '.ftoggle{display:none}\n.fquick{display:none}')
rep('  .ftoggle{display:inline-flex;align-items:center}',
    '  .ftoggle{display:inline-flex;align-items:center}\n'
    '  .fquick{display:inline-flex;align-items:center;flex:none;white-space:nowrap}\n'
    '  .fquick[hidden], .filters.open .fquick{display:none}')
rep('b.disabled = !n; b.textContent = n ? `Reset filters (${n})` : "Reset filters"; }',
    'b.disabled = !n; b.textContent = n ? `Reset filters (${n})` : "Reset filters"; const q = $("fquick"); if (q) q.hidden = !n; }')
rep('$("freset").addEventListener("click", () => {',
    '$("fquick").addEventListener("click", () => $("freset").click());\n$("freset").addEventListener("click", () => {')

open(out, "w", encoding="utf-8").write(h)
