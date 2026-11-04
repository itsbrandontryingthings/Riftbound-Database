#!/usr/bin/env python3
"""Price change test: for every day from the seed prices on, using the history as it stood that day, there must be a
short price change to show, even across the gap in the history (Oct 24-29, 2026), which once blanked every chip.
Needs no internet. Run: python3 build/tests/prices_test.py"""
import datetime, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from fetch_prices import PERIODS, snapshot

hist = json.load(open(os.path.join(ROOT, "build", "prices", "history.json"), encoding="utf-8"))
days = sorted(datetime.date.fromisoformat(d) for d in hist)
bad = []
for today in days:
    if today < datetime.date(2026, 11, 2): continue
    seen = {d: v for d, v in hist.items() if datetime.date.fromisoformat(d) <= today}
    age = snapshot(seen, today, *PERIODS[0])[0]
    print(today, "short change covers", age, "days; long", snapshot(seen, today, *PERIODS[1])[0])
    if age is None: bad.append(today)
print("FAILED on", bad if bad else "no days")
sys.exit(1 if bad else 0)
