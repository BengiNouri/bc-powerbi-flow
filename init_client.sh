#!/usr/bin/env bash
# init_client.sh — Scaffold a fresh Akse Demo DW project for a new client.
#
# Usage:
#   ./init_client.sh <client-slug> <client-url> [<parent-dir>]
#
# Example:
#   ./init_client.sh nordicsteel https://nordicsteel.dk ~/Projects
#   → creates ~/Projects/akse-dw-nordicsteel/ ready for the playbook
set -euo pipefail

# ─── Parse args ─────────────────────────────────────────────
if [ $# -lt 2 ]; then
  cat <<USAGE
Usage: $(basename "$0") <client-slug> <client-url> [parent-dir]

  client-slug   Short kebab-case name, e.g. 'nordicsteel'
  client-url    Full URL incl. https://, e.g. 'https://nordicsteel.dk'
  parent-dir    Where to create the project folder (default: current dir)

Example:
  $(basename "$0") nordicsteel https://nordicsteel.dk ~/Projects
USAGE
  exit 1
fi

CLIENT_SLUG="$1"
CLIENT_URL="$2"
PARENT_DIR="${3:-$(pwd)}"
PROJECT_DIR="$PARENT_DIR/akse-dw-$CLIENT_SLUG"
TEMPLATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -d "$PROJECT_DIR" ]; then
  echo "ERROR: $PROJECT_DIR already exists. Pick a different slug or remove it first."
  exit 1
fi

echo "Scaffolding $PROJECT_DIR from template $TEMPLATE_DIR..."
mkdir -p "$PROJECT_DIR"

# ─── Copy template files ────────────────────────────────────
TEMPLATE_FILES=(
  ".mcp.json"
  ".env.example"
  ".gitignore"
  "PLAYBOOK.md"
  "scan_source.py"
  "extract_brand.py"
  "gen_pbi_theme.py"
  "gen_design_brief.py"
  "gen_pbi_schemas.py"
  "gen_pbi_report.py"
  "export_gold_csv.py"
  "synthetic_full.py"
  "transform_full.py"
  "pipeline_full.py"
  "upload_supabase.py"
  "fabric_load_supabase.py"
  "dax_measures_full.dax"
  "semantic_model.md"
)

for f in "${TEMPLATE_FILES[@]}"; do
  if [ -f "$TEMPLATE_DIR/$f" ]; then
    cp "$TEMPLATE_DIR/$f" "$PROJECT_DIR/"
  else
    echo "  ⚠️  Skipping missing template: $f"
  fi
done

# Copy template directories
for d in templates docs; do
  if [ -d "$TEMPLATE_DIR/$d" ]; then
    cp -r "$TEMPLATE_DIR/$d" "$PROJECT_DIR/"
  fi
done

# ─── Generate .env from .env.example ────────────────────────
ENV_FILE="$PROJECT_DIR/.env"
cp "$TEMPLATE_DIR/.env.example" "$ENV_FILE"
# Insert CLIENT_URL at the top
{
  echo "# Auto-generated $(date +%Y-%m-%d)"
  echo "CLIENT_URL=$CLIENT_URL"
  echo "CLIENT_NAME=$CLIENT_SLUG"
  echo ""
  cat "$ENV_FILE"
} > "$ENV_FILE.tmp" && mv "$ENV_FILE.tmp" "$ENV_FILE"

# ─── Init git ───────────────────────────────────────────────
cd "$PROJECT_DIR"
git init -q
git add -A
git commit -q -m "init: scaffold $CLIENT_SLUG from akse-dw template ($CLIENT_URL)"

# ─── Done ───────────────────────────────────────────────────
cat <<DONE

✓ Project scaffolded at $PROJECT_DIR

Next steps:
  1. cd $PROJECT_DIR
  2. Edit .env to fill in source credentials + FABRIC_WORKSPACE_ID + FABRIC_LAKEHOUSE_ID
  3. Open this folder in Claude Code (claude)
  4. Paste the orchestration prompt from PLAYBOOK.md and let Claude run Phase 0a onwards

The playbook will:
  - Phase 0a: scan the client database (set SOURCE_TYPE in .env first)
  - Phase 0b: design semantic model (you + client decide KPIs)
  - Phase 0c: auto-extract brand from $CLIENT_URL → theme.json + design_brief.md
  - Phase 1-7: bronze → silver → gold → Supabase → Fabric → PBI model → report → publish
DONE
