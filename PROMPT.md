# Master orchestration prompt — Lodværket BI Accelerator

> **Paste this verbatim into any new Claude Code session in this repo.**
> It tells Claude exactly which docs to read, which skills to invoke, and
> which mistakes to avoid. Everything Claude needs is already in the repo.

---

## Copy-paste prompt

```
You are orchestrating a Lodværket BI Accelerator engagement — turning a
client's data (BC ERP + CRM + other systems) into a branded Power BI
report on Microsoft Fabric in 1-2 weeks.

═════════════════════════════════════════════════════════════════════════
READ FIRST (in this order, before doing ANYTHING else):
═════════════════════════════════════════════════════════════════════════

  1. WORKFLOW.md          — master flow (phases A through H)
  2. PLAYBOOK.md          — technical build steps (phases 0a-7)
  3. CREDENTIALS.md       — what to ask client for in phase D
  4. docs/PBI_PATTERNS.md — TESTED DO/DON'T patterns. READ BEFORE
                            generating ANY DAX measure or visual.json.
                            Each entry was verified — using untested
                            patterns broke the demo three times in
                            session 2026-05-23.
  5. PLAYBOOK_DRYRUN.md   — known gaps log
  6. sales/PITCH.md       — what the client is buying
  7. sales/PRICING.md     — three packages (45K / 85K / 150K)

After reading, do not proceed until you have used AskUserQuestion to ask
me ALL four of these in ONE message:

  1. Client name (display name on report Page 1)
  2. Client website URL (for Phase 0c brand auto-extract)
  3. Source data type — pick one:
       postgres | mssql | bc_odata | hubspot | csv_folder | multi
  4. Fabric workspace ID + Lakehouse ID

═════════════════════════════════════════════════════════════════════════
RULES OF ENGAGEMENT (Karpathy CLAUDE.md, non-negotiable):
═════════════════════════════════════════════════════════════════════════

  1. Think before coding. State assumptions. If two reasonable paths
     exist, ASK via AskUserQuestion — don't pick silently.
  2. Simplicity first. No speculative abstractions, no configuration
     knobs for scenarios we haven't hit.
  3. Surgical changes. Every diff line traces to the current phase goal.
  4. Goal-driven execution. Each phase has a verify gate. STOP if it
     fails — do not silently proceed.

═════════════════════════════════════════════════════════════════════════
SKILLS TO INVOKE AT EACH PHASE:
═════════════════════════════════════════════════════════════════════════

  Phase B Discovery     — superpowers:brainstorming (live with client)
  Phase 0a Source scan  — scan_source.py / scan_all.py
                          + data:explore-data, database-reviewer agent
  Phase 0b Model design — superpowers:brainstorming + engineering:architecture
  Phase 0c Brand        — extract_brand.py + gen_pbi_theme.py + gen_design_brief.py
  Phase 0d Design       — superpowers:brainstorming with client (40 questions
                          in templates/design_questionnaire.md)
                          → captures decisions to output/branding/design_decisions.yaml
  Phase 1-2 Bronze/Silver/Gold — pipeline_full.py (transform_lib.py helpers)
                          + superpowers:test-driven-development
                          + python-reviewer agent
  Phase 3 Supabase      — gen_supabase_ddl.py + upload_supabase.py
                          + database-reviewer agent
  Phase 4 Fabric        — paste fabric_load_supabase.py into Fabric notebook
  Phase 5 Semantic model — powerbi-modeling-mcp ONLY
                          (table_operations, relationship_operations,
                          measure_operations, dax_query_operations)
  Phase 6 Visuals       — gen_pbi_report.py
                          MUST consult docs/PBI_PATTERNS.md first
  Phase 7 Publish       — File → Publish from PBI Desktop to Fabric workspace
                          + design:accessibility-review

═════════════════════════════════════════════════════════════════════════
HARD RULES THAT BROKE BEFORE (DO NOT VIOLATE):
═════════════════════════════════════════════════════════════════════════

  • Never write TMDL / model.bim by hand — use powerbi-modeling MCP only
  • Every table_operations.Create MUST be followed by RefreshWithXMLA
    BEFORE any DAX runs against it
  • Every visual.json projection MUST have queryRef + nativeQueryRef
  • Save .pbip (not .pbix) — only .pbip exposes visual JSON for scripting
  • Slicer visuals use role 'Field' (not 'Values' like cards)
  • Card visuals do NOT support color tokens in formatStrings — colors
    only render in Table/Matrix visuals
  • Disable chart auto-titles via theme.visualStyles.*.title.show=false
    (NOT per-visual objects.title.show=false — PBI ignores that)
  • After MCP measure changes, EXPORT TMDL back to disk
    (output/AkseDemoDW/<name>.SemanticModel/definition/tables/*.tmdl)
    or the measures vanish next time PBI Desktop opens cold
  • WCAG AA contrast required on all brand colors
  • Test ONE example of any new pattern in PBI Desktop before generating
    it across 100 visuals

═════════════════════════════════════════════════════════════════════════
WHEN PHASE 0d STARTS (live brainstorm session with client):
═════════════════════════════════════════════════════════════════════════

  1. Invoke superpowers:brainstorming skill
  2. Open templates/design_questionnaire.md — 10 sections, ~40 questions
  3. Use AskUserQuestion ONE QUESTION AT A TIME (never batch all 40)
  4. After each section: summarize back and confirm
  5. Capture all answers to output/branding/design_decisions.yaml
     (schema: templates/design_decisions.yaml.example)
  6. Re-render design_brief.md and send to client for written sign-off
  7. Do not proceed to Phase 1 without sign-off

═════════════════════════════════════════════════════════════════════════
START NOW:
═════════════════════════════════════════════════════════════════════════

After reading the docs, propose the 9-phase plan with verify commands
for each phase, then wait for my approval before Phase 0a.
```

---

## Quick reference — what's already in this repo

| You need | It lives in |
|---|---|
| Full lifecycle docs | `WORKFLOW.md` |
| Technical build steps | `PLAYBOOK.md` |
| Credential checklist | `CREDENTIALS.md` |
| Tested PBI patterns | `docs/PBI_PATTERNS.md` (READ BEFORE generating measures/visuals) |
| Design brainstorm Q&A | `templates/design_questionnaire.md` |
| Design decisions schema | `templates/design_decisions.yaml.example` |
| Scaffold new client | `./init_client.sh <slug> <url>` |
| Demo clients (5) | `demo-clients/{coloplast,vestas,toms,lego,lakrids-by-bulow}/` |
| Brand auto-extract | `extract_brand.py` + `gen_pbi_theme.py` + `gen_design_brief.py` |
| Theme template | `templates/theme_skeleton.json` |
| Multi-source scan | `scan_all.py` + `sources.yaml.example` |
| Single-source scan | `scan_source.py` (Postgres/MSSQL/BC OAuth/HubSpot/CSV) |
| Pipeline (legacy demo) | `synthetic_full.py` + `transform_full.py` + `pipeline_full.py` |
| Pipeline (client template) | `transform_lib.py` + `transform_demo.py` |
| Supabase DDL gen | `gen_supabase_ddl.py` |
| Fabric notebook | `fabric_load_supabase.py` (paste into Fabric) |
| PBI model schemas | `gen_pbi_schemas.py` |
| PBI report visuals | `gen_pbi_report.py` |
| 65+ DAX measures | `dax_measures_full.dax` |
| Logo placeholder | `gen_logo_placeholder.py` |
| Swap demo client | `./swap_client.sh <slug>` |
| Sales materials | `sales/{PITCH,PRICING,SCREENCAST,CASE_STUDY_TEMPLATE}.md` |
| QA before publish | `docs/VISUAL_QA_CHECKLIST.md` |
| Test the generator | `python -m pytest tests/` (9 tests) |

## Where the 3-tier naming sits

| Audience | Use this name |
|---|---|
| Git, Claude sessions, technical | `bc-powerbi-flow` |
| Internal Lodværket | "BI Flow" |
| Client / sales / website | **Lodværket BI Accelerator** |

## How to start a fresh client engagement

```bash
# 1. Clone the template
git clone https://github.com/BengiNouri/bc-powerbi-flow akse-engagement-<client-slug>
cd akse-engagement-<client-slug>

# 2. Or scaffold via the helper
./init_client.sh <client-slug> https://<client-url>.dk ~/Projects

# 3. Open in Claude Code
cd ~/Projects/bc-powerbi-flow-<client-slug>
claude

# 4. Paste the orchestration prompt from this file (PROMPT.md ↑)
```
