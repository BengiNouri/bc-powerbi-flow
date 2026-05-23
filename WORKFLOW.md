# Akse — Master client workflow

> **This is the canonical, end-to-end flow from first contact to delivered Power BI report.**
> Every new Claude Code session should start by reading this file. It links out to
> `PLAYBOOK.md` for the technical build details and `CREDENTIALS.md` for what to ask the client.

---

## The pitch (10 sec elevator)

> "We turn your BC + CRM + other systems into one Power BI dashboard branded as yours —
> medallion architecture, Direct Lake on Fabric, 60+ DAX measures, live in 1-2 weeks.
> Plus we show your team how to use Claude to keep improving the report after delivery."

Two revenue streams from each engagement:

1. **Build:** the data warehouse + dashboard (fixed-price project)
2. **Enablement:** training their team on Claude + showing them how to integrate Claude into their own product (retainer / consultancy)

---

## Phase map

| Phase | Owner | Duration | Skills / tools invoked |
|---|---|---|---|
| **A — Lead generation** | Sales | 1-2 weeks | (Manual outreach, no Claude) |
| **B — Discovery meeting** | Sales + tech | 1 hour live | `superpowers:brainstorming` (with prospect) |
| **C — Proposal** | Tech + sales | 2-3 days | `engineering:documentation`, demo-clients/ artefacts |
| **D — Kickoff & access** | Tech (you) | 1 day | `CREDENTIALS.md` checklist + AskUserQuestion |
| **E — Build (Playbook 0a–7)** | Claude + you | 4-8 hours | `PLAYBOOK.md` (full stack) |
| **F — Handoff & training** | You | 1 hour live | `engineering:documentation`, screencasts |
| **G — Post-launch** | You (retainer) | Ongoing | `engineering:incident-response`, iteration |
| **H — Upsell: Claude in their product** | You | Separate engagement | New SOW |

---

## Phase A — Lead generation (sales)

Not Claude's job. Sales reaches out, books a 30-min discovery call.

Output going into Phase B: company name + URL + initial pain point.

---

## Phase B — Discovery meeting (1 hour with prospect)

**Goal:** Understand current data landscape, pain, decision-makers, success criteria.

**Skill to invoke:** `superpowers:brainstorming` — but **with the prospect on the call**, not solo.
Use it to surface assumptions and present 2-3 approaches live.

**Capture these in `clients/<slug>/discovery.md` during the call:**

```markdown
# {Client} — Discovery notes

## Stakeholders
- Sponsor: <name, title>
- Daily user: <name, title>
- IT/data owner: <name, title>

## Current state
- ERP: <BC SaaS | BC on-prem | NAV | Dynamics 365 | other>
- CRM: <HubSpot | Salesforce | Pipedrive | none>
- Marketing: <HubSpot | Mailchimp | Adform | other>
- Existing BI: <Power BI | none | Excel | other>

## Pain
- <verbatim quote 1>
- <verbatim quote 2>

## Top 5 Monday-morning questions
1. <question>
2. <question>
...

## Success criteria (signed off by sponsor)
- <criterion 1>
- <criterion 2>

## Constraints
- Budget range: <kr>
- Deadline: <date>
- Compliance: <GDPR | ISO | sector-specific>
```

**Verify before leaving the meeting:** sponsor has agreed to the top-5 questions and success criteria.

---

## Phase C — Proposal (2-3 days)

**Goal:** Send a written proposal the client signs.

**Skill chain:**
1. `engineering:documentation` — structure the proposal
2. Run `extract_brand.py` on their URL → get `brand_assets.json`
3. Hand-craft a preview design brief based on their data sources from Phase B
4. Pick a comparable `demo-clients/<example>/` to show "this is roughly what your dashboard will look like"

**Proposal template (`clients/<slug>/proposal.md`):**

```markdown
# {Client} — Data warehouse + Power BI proposal

## Scope
- Sources: <BC, HubSpot, ...>
- Star schema: ~N dimensions + M facts
- DAX measures: 50-70 covering <KPI areas>
- Power BI report: 6 pages (Exec, Pipeline, Marketing, Finance, HR, CSAT)
- Direct Lake on Fabric for sub-second refresh

## Approach
1. Phase 0a — Scan source databases (this validates exact table list before quote is final)
2. Phase 0b — Star schema design (1 review meeting)
3. Phase 0c — Brand auto-extracted from {client_url}, you sign off in 1 round
4. Phase 1-7 — Build, validate, publish to your Fabric workspace

## Deliverables
- `.pbip` source files in your private GitHub
- Documentation in Markdown
- 1-hour handover session + 1 month of small-change support
- A short Claude playbook for your team to keep iterating

## Investment
- Build: <kr>
- Optional enablement retainer: <kr/month for 3 months>

## Timeline
- Kickoff: <date>
- Demo: <date>
- Launch: <date>

## What we need from you to start (Phase D credentials checklist)
See attached CREDENTIALS.md
```

**Verify:** proposal signed by sponsor before any infrastructure work starts.

---

## Phase D — Kickoff & access (1 day)

**Goal:** Collect every credential and ID Claude needs to run Phases 0a-7 without further client interruption.

**Skill to invoke:** This is mostly checklist work. Use `AskUserQuestion` in the **kickoff session with the client's IT contact**.

The checklist lives in `CREDENTIALS.md`. Open that file with the IT contact and walk through it line by line.

**Scaffold a fresh project for them:**

```bash
./init_client.sh <client-slug> <client-url> ~/Projects
cd ~/Projects/akse-dw-<client-slug>
claude
```

In Claude, paste the orchestration prompt from `PLAYBOOK.md` (which now asks for the 4 inputs upfront via AskUserQuestion). Then collect the rest using the CREDENTIALS.md checklist.

**Verify gate before Phase E:**
- [ ] `.env` has every credential needed for their source type
- [ ] `python scan_source.py --validate` returns table count > 0
- [ ] `python extract_brand.py` produced a sensible `brand_assets.json`
- [ ] Fabric workspace + lakehouse IDs work (test with a 1-cell notebook)

If any of these fails, fix it now — don't proceed to building.

---

## Phase E — Build (Playbook 0a–7)

This is the big one. **The full technical playbook is in `PLAYBOOK.md`.**

In this WORKFLOW we just note which skills + agents Claude should invoke at each sub-phase:

| Playbook step | Claude skill / agent / MCP | Purpose |
|---|---|---|
| 0a — Source scan | `data:explore-data`, `data:data-context-extractor` | Inventory tables, infer FKs |
| 0a — Postgres scan | `database-reviewer` agent | Validate query safety on prod |
| 0b — Model design | `superpowers:brainstorming` + `engineering:architecture` | Star schema choices |
| 0b — DAX cookbook | `data:sql-queries` (DAX is SQL-adjacent) | Measure templates |
| 0c — Brand | `extract_brand.py`, `gen_pbi_theme.py`, `gen_design_brief.py` | Auto-brand |
| **0d — Design brainstorm** | **`superpowers:brainstorming` with client (live)** | **Refine every visual decision: colours / fonts / sizes / logos / slicers / pages / charts / KPIs → `design_decisions.yaml`** |
| 1 — Bronze ingestion | `superpowers:test-driven-development` + `tdd-guide` agent | Tests on extract code |
| 1 — Code review | `python-reviewer` agent | Each Python file before commit |
| 2 — Silver/Gold | `tdd-guide` agent, `data:validate-data` | Transformations + data quality |
| 3 — Supabase | `database-reviewer` agent | Schema + RLS + indexing |
| 4 — Fabric notebook | (no specific skill — paste-into-notebook + verify in Lakehouse) | Loading Delta tables |
| 5 — Semantic model | **`powerbi-modeling-mcp`** (table_operations, relationship_operations, measure_operations, dax_query_operations) | Direct authoring in PBI Desktop |
| 5 — DAX validation | `dax_query_operations.Execute` | Smoke-test every measure |
| 6 — Report visuals | `gen_pbi_report.py` (reads `design_decisions.yaml`, writes `visual.json`) | Generate PBIP visuals |
| 6 — Visual schema | Reference `powerbi-claude` repo patterns | Correct queryRef format |
| 6 — Accessibility | `design:accessibility-review` | WCAG final check before publish |
| 7 — Publish | (manual via PBI Desktop → Publish) | Land in client's Fabric workspace |
| All phases | `superpowers:verification-before-completion` | Don't mark done without verify |
| When broken | `superpowers:systematic-debugging` | Reproduce → isolate → fix |
| Always | **Karpathy CLAUDE.md guidelines** | Think before coding, simplicity, surgical, goal-driven |

**Orchestration prompt for Phase E** (use this verbatim — already in PLAYBOOK.md):

```
You are building a Power BI data warehouse for an Akse client.

Read WORKFLOW.md, CREDENTIALS.md, and PLAYBOOK.md in full before doing anything else.

Then use AskUserQuestion to collect these 4 things in one message:
  1. Client name (display name on report Page 1)
  2. Client website URL (for Phase 0c brand extraction)
  3. Source data type — pick one:
       postgres | mssql | bc_odata | hubspot | csv_folder
  4. Fabric workspace ID + Lakehouse ID

After I answer, write them into .env, then run through PLAYBOOK.md Phase 0a → 7
in order. After every phase, verify the gate. STOP at any verify failure.

Rules of engagement:
1. Think before coding. Surface assumptions. If two reasonable paths exist,
   ask via AskUserQuestion — don't pick silently. (Karpathy rule)
2. Simplicity first. No speculative abstractions. (Karpathy rule)
3. Surgical changes. Every line traces to the current phase's goal. (Karpathy rule)
4. Goal-driven. Each phase's verify gate must pass before next. (Karpathy rule)
5. Never write TMDL or model.bim by hand. Use powerbi-modeling MCP only.
6. Each PBI table Create MUST be followed by RefreshWithXMLA before any DAX.
7. Each visual.json projection MUST have queryRef + nativeQueryRef.
8. Save report as .pbip (not .pbix) — only .pbip exposes visual JSON.
9. WCAG AA contrast required on all brand colours.
10. For Phase 5 DAX measures, invoke superpowers:test-driven-development:
    write a smoke DAX query asserting non-blank result, then create the measure.
11. After Phase 0c, send design_brief.md to the client. Wait for sign-off via
    a real reply — do not assume.
```

---

## Phase F — Handoff & training (1 hour live)

**Goal:** Client team can open, refresh, and make small edits to the report without us.

**Skill to invoke:** `engineering:documentation` — produce a `HANDOVER.md`.

**Walk-through agenda (60 min):**
1. (10 min) Tour the 6 pages — what each KPI means, where data comes from
2. (10 min) Show how to add a new slicer / change a chart visual in PBI Desktop
3. (10 min) Show the refresh schedule + how to re-run Fabric notebook if data is stale
4. (10 min) Show the GitHub repo structure: where `.pbip`, where DAX, where pipeline code
5. (10 min) Brief intro to Claude Code — how to ask it to add a new measure or page
6. (10 min) Q&A + sign-off

**Deliverable file `HANDOVER.md`:**

```markdown
# {Client} — Handover document

## Access
- Fabric workspace: {url}
- GitHub repo: {url}
- Supabase project: {url}

## How to refresh data
1. Open Akse_Load_Supabase notebook in Fabric → Run all cells (~50 sec)
2. In Power BI workspace → Semantic model → Refresh now

## How to add a new measure
1. Open AkseDemoDW_v2.pbip in PBI Desktop
2. _Measures table → New measure → write DAX → Enter
3. Commit and push to GitHub

## How to ask Claude for changes
Open this folder in Claude Code and say:
  "Add a measure called 'YTD Revenue' as TOTALYTD([Revenue], gold_dim_date[date])"

## Support
- 1 month included for small changes
- After that: retainer agreement (see proposal)
```

---

## Phase G — Post-launch (retainer / ad-hoc)

**Skills:**
- `engineering:incident-response` — when refresh fails or visuals break
- `superpowers:systematic-debugging` — reproduce → isolate → fix
- `code-reviewer` agent — every change before push

**Common change requests:**
- Add a new KPI → `measure_operations.Create` + add to a page's visual.json
- Add a new source table → re-run Phase 0a scan, extend silver/gold, re-publish
- Theme refresh → swap `theme.json`, no other change needed

---

## Phase H — Upsell: "Claude in your product"

Different SOW. Different skills. The conversation starter:

> "You've now seen us deliver this whole project in 2 weeks where 12 months ago it would
> have been 3-6 months of consultancy. The same multiplier works inside your own product.
> Want us to scope a 4-week pilot where we embed Claude into your <support / sales / onboarding>
> workflow?"

**Skills used for this kind of engagement:**
- `claude-api` — building with Anthropic SDK
- `engineering:system-design` — integration architecture
- `engineering:tech-debt` — assessing their current codebase first
- `superpowers:writing-plans` — proper plan before implementing

(This is its own playbook, not in this repo — yet.)

---

## Skill / plugin reference

The full list of skills, MCP servers, and reference repos we lean on:

### MCP servers (configured in `.mcp.json`)

| Server | What it does | Used in |
|---|---|---|
| `@microsoft/powerbi-modeling-mcp` | Direct authoring of PBI semantic models (tables, relationships, measures, DAX) | Phase 5 |
| `@upstash/context7-mcp` | Up-to-date library docs (BC API, Supabase, Fabric Spark) | Any phase when API knowledge needed |

### Superpowers skills (from claude-plugins-official)

| Skill | When to invoke |
|---|---|
| `superpowers:brainstorming` | Open-ended design questions (Phase B with prospect; Phase 0b for KPIs; Phase 0c for design tweaks) |
| `superpowers:writing-plans` | After every spec is approved — produces step-by-step implementation plan |
| `superpowers:executing-plans` | Follow an approved plan; mark each step verified |
| `superpowers:test-driven-development` | Phase 1+ — write tests first, then implementation |
| `superpowers:verification-before-completion` | Always at end of a task — concrete checks, not "looks good" |
| `superpowers:systematic-debugging` | When verify fails — reproduce → isolate → fix |
| `superpowers:using-superpowers` | Auto-loaded at session start — meta orchestration |

### Engineering / data / design skills

| Skill | When |
|---|---|
| `engineering:architecture` | Phase 0b model design decisions |
| `engineering:documentation` | Phase C proposal, Phase F handover |
| `engineering:debug` | Same as `systematic-debugging` but lighter |
| `engineering:incident-response` | Phase G when refreshes break |
| `data:explore-data` | Phase 0a — understand what's in the source |
| `data:data-context-extractor` | Phase 0a — capture semantic context |
| `data:validate-data` | Phase 2 — gold layer quality |
| `data:sql-queries` | Phase 0b, Phase 5 DAX |
| `design:accessibility-review` | Phase 6 — WCAG check before publish |
| `design:design-system` | Phase 0c — theme decisions for non-standard brands |

### Subagents (`Agent` tool)

| Agent | Use case |
|---|---|
| `python-reviewer` | Review each Python file before commit |
| `tdd-guide` | Enforce write-tests-first in Phase 1+ |
| `database-reviewer` | Phase 3 Supabase schema + RLS + indexes |
| `code-reviewer` | All code changes |
| `security-reviewer` | After Phase 3, before publish |
| `e2e-runner` | Phase 7 — verify report works in Fabric |
| `architect` | When the model design is non-obvious |
| `planner` | After spec, before implementation |

### Reference repos (not code-deps; pattern references)

| Repo | What we borrow |
|---|---|
| `allanbrunorj/powerbi-claude` | PBIP `visual.json` schema + the `queryRef + nativeQueryRef` projection format |
| `multica-ai/andrej-karpathy-skills` | CLAUDE.md behavioural guidelines (think before coding, simplicity, surgical, goal-driven) |

### Always-on rules (Karpathy CLAUDE.md)

1. **Think before coding.** State assumptions explicitly. If multiple interpretations exist, present them — don't pick silently.
2. **Simplicity first.** Minimum code that solves the problem. No speculative abstractions.
3. **Surgical changes.** Every changed line traces to the user's request.
4. **Goal-driven execution.** Each task has a verify check. Loop until it passes.

These override default model behaviour. They are non-negotiable.

---

## Files in this repo (canonical layout)

```
cronus-dw/
├── WORKFLOW.md                  ← you are here (master)
├── PLAYBOOK.md                  ← Phase E technical playbook
├── CREDENTIALS.md               ← Phase D access checklist
├── PLAYBOOK_DRYRUN.md           ← Known gaps (audit log)
├── init_client.sh               ← Scaffold a new client project
├── .mcp.json                    ← MCP server config
├── .env.example                 ← Credential keys per source
│
├── scan_source.py               ← Phase 0a (Postgres/MSSQL/BC/HubSpot/CSV)
├── extract_brand.py             ← Phase 0c (URL → brand_assets.json)
├── gen_pbi_theme.py             ← Phase 0c (→ theme.json)
├── gen_design_brief.py          ← Phase 0c (→ design_brief.md)
│
├── synthetic_full.py            ← Phase 1 demo data generator (real engagements skip)
├── transform_full.py            ← Phase 2 silver + gold (will be split into lib + thin)
├── pipeline_full.py             ← Phase 1-2 orchestrator
├── upload_supabase.py           ← Phase 3
├── fabric_load_supabase.py      ← Phase 4 (paste into Fabric notebook)
├── gen_pbi_schemas.py           ← Phase 5 prep (parquet → PBI column metadata)
├── gen_pbi_report.py            ← Phase 6 (writes 6 pages of visual.json)
├── dax_measures_full.dax        ← Phase 5 reference measure cookbook
│
├── templates/
│   ├── theme_skeleton.json
│   └── (more as we add them)
│
├── demo-clients/                ← Sales artefacts
│   ├── README.md
│   ├── vestas/
│   ├── toms/
│   ├── lego/
│   └── lakrids-by-bulow/
│
├── docs/
│   └── superpowers/specs/       ← Design specs from brainstorming sessions
│
└── output/                      ← gitignored — generated per-client artefacts
    ├── bronze/
    ├── silver/
    ├── gold/
    └── branding/
```

---

## When to update this document

- After every client engagement: add lessons learned to `PLAYBOOK_DRYRUN.md`
- When a new source type comes up: add a driver to `scan_source.py` + key to `CREDENTIALS.md` + doc here
- When a new skill proves useful: add it to the Skill reference table above
- When PBI Desktop / Fabric / MCP server breaks something: add the failure mode to `PLAYBOOK.md`

Treat this file as living. The version in git is the source of truth.
