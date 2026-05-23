# Akse Demo DW — Technical build playbook (Phase E)

> **This is the technical playbook for the build phase only.**
> For the full client lifecycle (lead → proposal → kickoff → build → handover → upsell), read [`WORKFLOW.md`](./WORKFLOW.md) first.
> For credential collection (Phase D), see [`CREDENTIALS.md`](./CREDENTIALS.md).
>
> **Goal of this file:** Take a new client from raw source data (Business Central, Supabase, CSV, etc.)
> to a working Power BI report in a single guided session.

---

## What we built last time (proof point)

| Stage | Tool / Output |
|---|---|
| Source data | BC ERP API + synthetic CRM/Marketing/Finance/HR/CSAT |
| Bronze → Silver → Gold | Pandas/PySpark, star schema (5 dims + 9 facts) |
| Cloud staging | Supabase PostgreSQL (14 gold tables) |
| Fabric Lakehouse | Delta tables loaded via PySpark notebook |
| Semantic Model | Direct Lake on SQL, all relationships + 65 DAX measures |
| Report | 6-page PBIP (Executive / Pipeline / Marketing / Finance / HR / CSAT) |

**Total time end-to-end: ~3 hours. Replicable by Claude Code + MCP in under 1 hour for next client.**

---

## Prerequisites (one-time setup per client engagement)

1. **Power BI Desktop** installed locally (Windows). Open a blank `.pbip` before starting.
2. **Node.js 24+** (`node --version` should report v20+).
3. **Microsoft Fabric workspace** access with Lakehouse + workspace IDs in hand.
4. **Source credentials** (Supabase URL + service_role key, BC OAuth, or whatever applies).
5. **Claude Code** running from project root.

## MCP servers to register

Drop this in the project's `.mcp.json` **before** starting Claude:

```json
{
  "mcpServers": {
    "powerbi-modeling": {
      "command": "npx",
      "args": ["-y", "@microsoft/powerbi-modeling-mcp@latest", "--start", "--skipconfirmation"]
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    }
  }
}
```

The `--skipconfirmation` flag is critical — without it every write fails with "user declined".

Also recommended: `Claude in Chrome` extension for any Fabric web UI step we can't avoid.

---

## The orchestration prompt (paste this to Claude on day one)

```
You are building a Power BI data warehouse demo for a new Akse client.

Follow PLAYBOOK.md exactly. Each phase has a verify gate — STOP at it if it
fails. Do not silently proceed.

Before phase 0a, ASK ME these 4 things in one message (use AskUserQuestion):

  1. Client name (display name on report Page 1)
  2. Client website URL (used by Phase 0c to extract brand)
  3. Source data type — pick one:
       postgres | mssql | bc_odata | hubspot | csv_folder
  4. Fabric workspace ID + Lakehouse ID (paste both)

After I answer, write them into .env, then propose the 9-phase plan
(0a / 0b / 0c / 0d / 1-7) with verify commands and wait for my approval
before Phase 0a.

Phase 0d is a live design brainstorming session with the client —
invoke superpowers:brainstorming, walk through templates/design_questionnaire.md
one question at a time, and capture answers into design_decisions.yaml.

Rules of engagement (in addition to the playbook):
1. Think before coding. Surface assumptions. If a step has two reasonable paths,
   present both and ask — don't pick silently.
2. Simplicity first. No abstractions, configuration knobs, or error handling for
   scenarios we haven't seen.
3. Surgical changes. Each diff line must trace to the current phase's goal.
4. Goal-driven. Each phase has a "verify" command that must pass before moving on.
5. Never write TMDL or model.bim by hand. Use powerbi-modeling MCP only.
6. Each PBI table Create MUST be followed by RefreshWithXMLA before any DAX runs.
7. Each visual.json projection MUST have queryRef + nativeQueryRef populated.
8. Save report as .pbip (not .pbix) — only .pbip exposes visual JSON for scripting.
9. WCAG AA contrast required on all brand colours. If contrast fails, auto-fall
   back and warn — do not ship a low-contrast report.
```

---

## Phases

Each phase has: **goal → steps → verify gate**. Don't skip the gate.

### Phase 0a — Source database scan (20 min)

**Goal:** Auto-discover the client's actual schema before we make any modeling choices.

Steps:
1. Identify source type with the client (check all that apply):
   - PostgreSQL / Supabase
   - MS SQL Server (BC SaaS / on-prem)
   - Business Central OData/REST API
   - MySQL / MariaDB
   - Snowflake / BigQuery / Redshift
   - CSV / Excel folder
2. Drop credentials into `.env` (never commit). Required keys depend on source — see `.env.example`.
3. Run `python scan_source.py` — emits `source_schema.json` + `source_schema.md`.
4. Read `source_schema.md` together with the client. Mark which tables are in scope (entities they care about) and which to skip (audit logs, queues, staging junk).
5. Heuristic FK detection runs automatically — review flagged relationships, correct misses, drop false positives.

**Verify:**
```bash
python scan_source.py --validate
# prints: N tables scanned, M FK candidates, K skipped (no rows)
```
Plus client signs off on the scope list in `source_schema.md`.

### Phase 0b — Semantic model design (15 min)

**Goal:** Translate the scanned schema into a star schema and pick KPIs.

Steps:
1. From scan output, classify each in-scope table:
   - Dimension (entity master data: customer, employee, item, date, …)
   - Fact (transactions/events: sales lines, deals, tickets, sessions, …)
   - Bridge (many-to-many — only if unavoidable)
2. Generate `semantic_model.md` (one section per dim/fact with key, columns, grain).
3. Ask the client: "Top 5 questions you'd ask this report on Monday morning?"
4. Map each question to 1–3 DAX measures. Write them in `dax_measures.dax`.

**Verify:** Client reviews `semantic_model.md` + KPI list and signs off in writing/Slack.

### Phase 0c — Branding & design (15-20 min)

**Goal:** Auto-extract client brand → PBI `theme.json` + design brief for client sign-off.

Pre-flight: `CLIENT_URL=https://<client-website>` in `.env`.

Steps:
1. `python extract_brand.py` → `output/branding/brand_assets.json` + `logo.png`
2. `python gen_pbi_theme.py`  → `output/branding/theme.json` (drag-drop into PBI Desktop View → Themes)
3. `python gen_design_brief.py` → `output/branding/design_brief.md`
4. Send `design_brief.md` to client. Wait for sign-off OR hex-code corrections.
5. If corrected: edit `brand_assets.json` manually, re-run steps 2-3.

**Verify:**
- `python -m json.tool output/branding/theme.json > /dev/null` (valid JSON)
- All "medium"/"low" confidence flags in `design_brief.md` either resolved to "high" or explicitly approved by client in writing
- No WCAG contrast warnings in `brand_assets.json.warnings[]`

⚠️ **Do not proceed to Phase 1 without client design sign-off** — rebranding after the report is built means re-running Phases 5 & 6.

**Iteration (if client returns layout feedback, not just hex codes):** invoke `superpowers:brainstorming` skill with the feedback as input to revise `design_decisions.yaml`; then re-run `gen_pbi_report.py` in Phase 6.

### Phase 0d — Design brainstorming with client (45-60 min live)

**Goal:** Pin down every visual decision (beyond just colours) so Phase 6 has a
complete spec to build from. **This is a real conversation with the client**, driven
by Claude using `superpowers:brainstorming`.

**Pre-flight:**
- Phase 0c artefacts in place (`brand_assets.json`, `theme.json`, `design_brief.md`)
- Client has reviewed `design_brief.md` and confirmed/corrected the brand basics
- 45-60 min booked with client's design/marketing/operations contact

**Steps:**

1. Open `templates/design_questionnaire.md` together with the client
2. Claude invokes `superpowers:brainstorming`:
   - One question at a time (40 questions, ~1 min each)
   - For each multi-choice question, list 2-3 options + recommendation
   - For open questions, ask follow-ups when the answer is vague
3. After each major section (colours / typography / logos / slicers / pages / charts /
   KPI cards / language / interactivity), summarise back what was decided and confirm
4. Capture all answers into `output/branding/design_decisions.yaml` (see
   `templates/design_decisions.yaml.example` for schema)
5. Re-render `design_brief.md` with the new decisions and send to client for written sign-off

**Verify:**
- `output/branding/design_decisions.yaml` exists and validates against the schema
- Every page in the `pages` array has an `enabled` field and `top_kpis` (for the exec page)
- Client signs off in writing — "yes, build this design"

⚠️ **Phase 6 (report) is driven by `design_decisions.yaml`.** Don't proceed past 0d without it. Building first and re-skinning later means rewriting all 62 visuals.

### Phase 1 — Synthetic / Bronze (30 min, skip if real data ready)

**Goal:** Generate or extract raw data into `output/bronze/*.parquet`.

Steps:
1. If real source: write `extract.py` using vendor SDK (BC OData, Supabase REST, etc).
2. If demo: write `synthetic_full.py` mirroring the agreed schema with realistic volumes.
3. Save each table as parquet under `output/bronze/`.

**Verify:** `python pipeline_full.py` runs without errors and parquet row counts match expectations.

### Phase 2 — Silver + Gold (45 min)

**Goal:** Clean, conform, and aggregate into star schema gold tables.

Steps:
1. `transform_full.py` — silver layer: type coercion, dedup, derived columns.
2. Same file — gold layer: dimensions with surrogate keys (`*_key`), facts with FKs to dim keys.
3. Use Pandas as intermediary if PySpark inferring of mixed int/float fails.

**Verify:**
```bash
python pipeline_full.py
ls output/gold/*.parquet  # should list 5 dims + N facts
```

### Phase 3 — Cloud staging (15 min)

**Goal:** Push gold to Supabase Postgres so Fabric (and any other consumer) can read it.

Steps:
1. Generate `output/create_tables.sql` from gold parquet schemas.
2. Run the SQL once in Supabase SQL editor.
3. `upload_supabase.py` — uses `supabase-py` to insert all gold rows.

**Verify:** Spot-check 2 random tables via Supabase REST:
```bash
curl "$SUPABASE_URL/rest/v1/gold_dim_customer?select=*&limit=3" -H "apikey: $KEY"
```

### Phase 4 — Fabric Lakehouse load (15 min)

**Goal:** Land gold tables as Delta tables in the client's Fabric Lakehouse.

Steps:
1. Generate `fabric_load_supabase.py` parameterized with Workspace ID + Lakehouse ID.
2. In Fabric: create notebook → paste code → attach Lakehouse → run.
3. **Critical pattern:** Use `pd.DataFrame(data)` as intermediary before `spark.createDataFrame()`
   to avoid `CANNOT_MERGE_TYPE` errors on mixed int/float JSON values.

**Verify:** Lakehouse explorer shows all 14 gold tables with row counts in the SQL analytics endpoint.

### Phase 5 — Semantic Model + DAX (30 min, MCP-driven)

**Goal:** Build the model directly in Power BI Desktop via `powerbi-modeling-mcp`.

Pre-flight:
1. Open blank `.pbip` in PBI Desktop.
2. `connection_operations` → `ListLocalInstances` → `Connect` to the PBI port.

Steps (in this order — don't reorder):
1. `table_operations.Create` (batch) — all dimensions first (with explicit `columns` array, **no `isKey`** for Import mode).
2. `table_operations.RefreshWithXMLA` after every Create.
3. Repeat for facts.
4. `relationship_operations.Create` (batch) — Many→One, OneDirection, isActive=true (except the second date FK on the same fact).
5. `table_operations.MarkAsDateTable` on the date dim with the date column.
6. `table_operations.Create` `_Measures` with `daxExpression: "ROW(\"placeholder\", BLANK())"` (no `columns`).
7. `measure_operations.Create` (batch, grouped by `displayFolder`) — all 60+ measures from `dax_measures_full.dax`.

**Verify:** Run a smoke DAX query through `dax_query_operations.Execute`:
```dax
EVALUATE ROW(
  "Revenue", [Revenue], "Pipeline", [Pipeline Value],
  "Headcount", [Total Headcount], "NPS", [NPS Score]
)
```
All values must be non-blank.

### Phase 6 — Report (PBIP visuals) (45 min)

**Goal:** Generate the 6-page report as `visual.json` files inside the `.pbip` Report folder.

Pre-flight:
1. In PBI Desktop: File → Options → Preview features → enable **"Power BI Project (.pbip) save option"**.
2. File → Save As → `.pbip` format. Reconnect MCP afterwards (port changes).

Steps:
1. Run `gen_pbi_report.py` — generates `definition/pages/<hex>/visuals/<hex>/visual.json` for every visual.
2. **Critical:** every projection needs `queryRef` and `nativeQueryRef` (see template below).
3. Write `pages.json` before PBI ever reopens the file — otherwise PBI regenerates page structure.
4. Close PBI Desktop, reopen the `.pbip`. Accept PBIR upgrade. Decline TMDL upgrade.

**Verify:** All 6 pages render without "Required property 'queryRef'…" errors and KPI cards show non-blank numbers.

### Phase 7 — Publish (5 min)

**Goal:** Get the report into the client's Fabric workspace.

Steps:
1. In PBI Desktop: **Udgiv / Publish** → choose client workspace.

**Verify:** Open the report in `app.fabric.microsoft.com` → click through all 6 pages → at least one slicer filters at least one visual.

---

## Critical patterns (failure modes we already hit)

| Symptom | Fix |
|---|---|
| `Cannot set IsKey … only supported for DirectQuery` | Remove `isKey` from columns in Import-mode tables. Engine manages this. |
| `CANNOT_MERGE_TYPE` (LongType vs DoubleType) | Add `pd.DataFrame(data)` before `spark.createDataFrame(pdf)` in the Fabric notebook. |
| `Columns are required. The schema cannot be automatically inferred` | Always pass explicit `columns` array to `table_operations.Create`. |
| `Columns cannot be specified for calculated tables` | The `_Measures` table uses `daxExpression`, so omit `columns`. |
| `Refresh required: …` warning after table Create | Always immediately call `table_operations.RefreshWithXMLA`. |
| `Required property 'queryRef' was not included` | Every projection in `visual.json` needs both `queryRef` and `nativeQueryRef`. |
| PBI regenerates page folders and wipes visuals | `pages.json` was missing on first open. Write it before any PBI open. |
| Fabric web upload says "kun .pbix understøttes" | Fabric upload doesn't accept `.pbip`. Use **Publish from PBI Desktop** instead. |

## Visual JSON projection template (the only correct shape)

```json
{
  "field": {
    "Measure": {
      "Expression": {"SourceRef": {"Entity": "_Measures"}},
      "Property": "Revenue"
    },
    "Name": "_Measures.Revenue",
    "NativeReferenceName": "Revenue"
  },
  "queryRef": "_Measures.Revenue",
  "nativeQueryRef": "Revenue"
}
```

Replace `Measure` with `Column` for column projections. Both forms need `queryRef` + `nativeQueryRef`.

## Files this repo provides as templates

```
synthetic_full.py        # bronze layer demo data generator
transform_full.py        # silver + gold transformations (star schema)
pipeline_full.py         # orchestrates extract → bronze → silver → gold
upload_supabase.py       # gold → Supabase staging
fabric_load_supabase.py  # Supabase → Fabric Lakehouse (paste into notebook)
gen_pbi_schemas.py       # parquet → PBI column schemas (JSON)
gen_pbi_report.py        # PBIP report generator (6 pages, 62 visuals)
dax_measures_full.dax    # 65 DAX measures in 7 display folders
.mcp.json                # powerbi-modeling-mcp server config
```

Copy these into a new `cronus-dw-<client>` folder and edit the synthetic/extract step.
Everything downstream is automatic.

## Sanity checks before declaring done

- [ ] All gold parquet files exist with non-zero row counts
- [ ] Supabase REST returns rows for every gold table
- [ ] Fabric Lakehouse Tables folder shows all 14 tables
- [ ] PBI Desktop `_Measures` table contains 65 measures
- [ ] `EVALUATE ROW([Revenue], [Pipeline Value], …)` returns real numbers
- [ ] All 6 report pages open in PBI Desktop without errors
- [ ] Report opens in Fabric web after Publish
- [ ] At least one slicer cross-filters at least one chart
