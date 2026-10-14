#!/usr/bin/env bash
# Rebuild the website (../index.html) and, optionally, the private Desktop copy.
#   ./build/make.sh                         -> rebuilds index.html at the repo root
#   ./build/make.sh --local                 -> also builds the accounts-free local copy into build/out/
# Python 3, no extra packages. Every patch is a plain string-replace script that fails loudly if its anchor text is missing.
set -euo pipefail
cd "$(dirname "$0")"
P=patches; T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
run(){ local i=0 cur="$1"; shift; for p in "$@"; do i=$((i+1)); python3 -I "$P/$p.py" "$cur" "$T/s$i.html" >/dev/null; cur="$T/s$i.html"; done; echo "$cur"; }

WEB=(patch_local patch_bans patch_web patch_accounts patch_sharing patch_mobile patch_wish patch_polish patch_foil patch_info patch_links patch_share_tidy patch_decks_ui patch_friends_ui patch_shop patch_offers patch_shop_add patch_uisize patch_friends_size patch_fixes patch_chime patch_offer_threads)
out=$(run base/shared.html "${WEB[@]}"); cp "$out" ../index.html; echo "website -> index.html"

if [[ "${1:-}" == "--local" ]]; then
  LOCAL=(patch_local patch_bans patch_mobile patch_wish patch_polish patch_foil patch_info)
  T2=$(mktemp -d); mkdir -p out
  i=0; cur=base/shared.html; for p in "${LOCAL[@]}"; do i=$((i+1)); python3 -I "$P/$p.py" "$cur" "$T2/s$i.html" >/dev/null; cur="$T2/s$i.html"; done
  cp "$cur" out/local.html; cp ../cards.js ../text.js out/; rm -rf "$T2"
  echo "local copy -> build/out/local.html (+ cards.js, text.js); copy all three into the Desktop folder"
fi
