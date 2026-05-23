# Playbook dry-run — Hypothetical client: Nordic Steel A/S

> **Scenario:** Danish manufacturing SMB. 80 employees. Business Central SaaS for ERP,
> HubSpot for CRM, three CSV files from Mailchimp for marketing. Wants one Power BI
> report covering sales, pipeline and operations.

This walks every phase as if Claude Code were running the playbook live. **Gaps and
fixes are flagged with ⚠️.**

---

## Phase 0a — Source database scan

**What works:**
- `scan_source.py` connects to Postgres / MS SQL / BC OData / CSV
- Outputs `source_schema.json` + readable `source_schema.md`
- Auto-classifies dim vs fact, detects FK candidates by naming

**⚠️ Gaps surfaced by this scenario:**

1. **Multi-source scanning** — Nordic Steel has 3 sources (BC + HubSpot + CSV).
   Scanner currently scans one source per run (SOURCE_TYPE env var).
   *Fix:* run scanner 3 times with different `.env` files and merge outputs, OR add a
   `sources:` array to a `scan_config.yaml`. Document the 3-run workaround for now.

2. **BC SaaS auth** — Basic auth was retired in BC Online. Real flow is OAuth2 client
   credentials against `https://login.microsoftonline.com/<tenant>/oauth2/v2.0/token`
   with scope `https://api.businesscentral.dynamics.com/.default`.
   *Fix:* add `bc_odata_oauth` driver variant with token fetch + caching.

3. **HubSpot driver missing entirely** — common CRM source we'd hit on 60% of clients.
   *Fix:* add `scan_hubspot()` using `hubspot-api-client` SDK against Contacts, Companies,
   Deals, Pipelines, Owners.

4. **Schema-only scan vs row counts** — counting rows on BC sales-line endpoints with
   millions of records via `$count` is slow (minutes). Should be optional / sampled.
   *Fix:* add `--no-counts` flag for fast initial scan.

**Verify gate result:** ✅ would pass for Postgres-only client. ⚠️ blocks for BC/HubSpot
clients until drivers ship.

---

## Phase 0b — Semantic model design

**What works:**
- Classification heuristic is simple enough that a human review catches mistakes
- The "5 Monday-morning questions" framing produces useful KPIs

**⚠️ Gaps:**

5. **No conformed dimension template** — clients with both BC customers AND HubSpot
   companies need a unified `dim_customer` mapping `bc_customer_no` + `hubspot_company_id`
   to one `customer_key`. The demo `cronus-dw` does this in `transform_full.py` line
   206 (`customer_key = bc_customer_number.fillna(crm_company_id)`) but it's not
   documented as a pattern.
   *Fix:* add `conformed_dimensions.md` template with worked example.

6. **No DAX template library** — `dax_measures_full.dax` is specific to our demo schema.
   New client gets a blank file and has to write 60 measures from scratch.
   *Fix:* extract a `dax_patterns.md` cookbook (Pipeline / Sales / HR / Marketing /
   Finance / Support templates) that maps abstract patterns to concrete DAX.

---

## Phase 1 — Synthetic / Bronze

**What works:**
- `synthetic_full.py` is great for demos when client data isn't ready

**⚠️ Gaps:**

7. **No real extract templates** — playbook says "write `extract.py` using vendor SDK"
   but provides nothing concrete. For BC OAuth, HubSpot pagination, MS SQL queries,
   each has its own gotchas (rate limits, pagination, incremental sync).
   *Fix:* ship 4 starter files in `templates/`:
   - `extract_bc_oauth.py`
   - `extract_hubspot.py`
   - `extract_mssql.py`
   - `extract_postgres.py`

---

## Phase 2 — Silver + Gold

**What works:**
- The Pandas-intermediary trick (`pd.DataFrame(data)` before `spark.createDataFrame`)
  is in the failure mode table

**⚠️ Gaps:**

8. **`transform_full.py` is hard-coded to demo schema** — references `crm_companies`,
   `crm_deals`, `employees`, etc. Won't run for any other client without rewrite.
   *Fix:* split into `transform_lib.py` (reusable helpers: `make_dim`, `make_fact`,
   `add_date_keys`, `compute_variance`) + `transform_<client>.py` (thin orchestration).

9. **Date dimension not parameterized** — `gold_dim_date` in the demo is hard-coded
   to 2024-07-01 onwards. Client needs to set start/end based on their data range.
   *Fix:* make `gold_dim_date(start_date, end_date)` a helper in `transform_lib.py`.

---

## Phase 3 — Cloud staging (Supabase)

**What works:**
- Supabase REST + service_role key flow is fast and well-documented

**⚠️ Gaps:**

10. **`create_tables.sql` is hand-written for demo** — needs to be generated from gold
    parquet schemas per client.
    *Fix:* add `gen_supabase_ddl.py` (analogous to `gen_pbi_schemas.py`).

11. **`upload_supabase.py` hard-codes the 14-table list** — clients have different counts.
    *Fix:* discover tables dynamically from `output/gold/*.parquet`.

---

## Phase 4 — Fabric Lakehouse load

**What works:**
- The `fabric_load_supabase.py` paste-into-notebook flow is reliable

**⚠️ Gaps:**

12. **Workspace/Lakehouse IDs hard-coded** in the script we paste into Fabric.
    *Fix:* templatize via `${FABRIC_WORKSPACE_ID}` / `${FABRIC_LAKEHOUSE_ID}` placeholders
    that `init_client.py` replaces.

13. **Direct Lake on OneLake vs SQL choice** — we hit refresh failures on OneLake mode
    (cf. session notes from 18:24 compaction). The playbook should say upfront:
    **"Always create the semantic model on the SQL analytics endpoint, never on the
    Lakehouse directly."**
    *Fix:* added to failure mode table.

---

## Phase 5 — Semantic Model + DAX

**What works:**
- powerbi-modeling-mcp is rock-solid once `--skipconfirmation` is set
- Pattern for batched table create + RefreshWithXMLA + relationship create is repeatable

**⚠️ Gaps:**

14. **`gen_pbi_schemas.py` heuristic mis-types some columns** — e.g. `roi_pct` got
    typed as "double / format 0.00%" but the underlying value is already a percentage
    number (15.5 not 0.155). Resulted in `0.00%` showing 0.00% instead of 15.50%.
    *Fix:* heuristic should only apply pct format if max(value) < 1; otherwise use
    plain number format. Update `gen_pbi_schemas.py`.

15. **MarkAsDateTable runs after relationships** — works, but if any relationship
    targets the date column before marking, PBI gives a warning. Move marking before
    relationships in the playbook.
    *Fix:* reorder Phase 5 steps.

---

## Phase 6 — Report (PBIP visuals)

**What works:**
- The PBIP folder format is well-defined; once `queryRef` + `nativeQueryRef` are
  populated, all visuals render

**⚠️ Gaps:**

16. **`gen_pbi_report.py` has hardcoded page builders** (`page_exec`, `page_pipeline`,
    etc.) referencing our specific measures and columns. Won't generalize.
    *Fix:* drive page generation from a `report_spec.yaml` that lists pages → KPIs →
    chart specs. Then `gen_pbi_report.py` becomes a generic renderer.

17. **Slicer cross-filter not verified** in our last session — we never confirmed a
    slicer actually filters charts in the rendered report. Need an explicit verify step.
    *Fix:* add to sanity checklist: "click country slicer on Pipeline page → confirm
    revenue chart updates."

---

## Phase 7 — Publish

**What works:**
- File → Publish from PBI Desktop is the only reliable path. Fabric web upload of
  `.pbip` is **not supported** (only `.pbix`, `.rdl`, `.xlsx`). This is in the
  failure mode table now.

**⚠️ Gaps:**

18. **Permission to publish** — first publish to a workspace requires PBI workspace
    Member role. Worth a pre-check.
    *Fix:* add to prerequisites checklist.

---

## Summary of gaps to close before next client

**P0 — Blocks most engagements (do first):**
- [x] `extract_bc_oauth.py` template — done via `scan_source.py` OAuth driver (commit c1f1246)
- [x] `extract_hubspot.py` template — done via `scan_source.scan_hubspot()` (commit c1f1246)
- [x] Multi-source scan merge — `scan_all.py` + `sources.yaml.example`
- [x] Split `transform_full.py` into `transform_lib.py` + `transform_demo.py` exemplar
- [x] `gen_supabase_ddl.py` to generate DDL from gold parquets
- [x] `init_client.sh` to scaffold new client folder + replace placeholders (commit c1f1246)

**P1 — Quality improvements:**
- [ ] `dax_patterns.md` measure cookbook
- [ ] `conformed_dimensions.md` pattern guide
- [ ] Fix `roi_pct` style format heuristic in `gen_pbi_schemas.py`
- [ ] `report_spec.yaml` schema for `gen_pbi_report.py`
- [ ] Slicer cross-filter verification step in sanity checklist
- [ ] Reorder MarkAsDateTable before relationships in Phase 5

**P2 — Nice to have:**
- [ ] `--no-counts` flag on scanner for fast scans
- [ ] MS SQL Server scanner used by an actual client (we only tested code path)

---

## Time estimate revisited

With the P0 gaps closed and a well-known source (Postgres or BC OData with proven extract template), end-to-end onboarding drops to **~1 hour** plus client review time. Without P0 closed, expect 3-4 hours per client because every extract is bespoke.

**Recommendation:** invest 1-2 days closing P0 before pitching this as a productized offering.
