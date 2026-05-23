#!/usr/bin/env bash
# swap_client.sh — Activate a demo client's branding on AkseDemoDW_v2.pbip.
#
# Usage:
#   ./swap_client.sh <slug>
#   e.g.  ./swap_client.sh vestas
#         ./swap_client.sh coloplast
#         ./swap_client.sh lakrids-by-bulow
#
# Thin wrapper around swap_client.py — keeps the same CLI ergonomics
# regardless of whether you prefer bash or python.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python "$SCRIPT_DIR/swap_client.py" "$@"
