# Lodværket BI Accelerator

> Lodværket's reusable template for delivering data warehouse + Power BI projects to clients.
> Goes from "BC + CRM + other systems" to "branded Power BI report on Fabric" in 1-2 weeks.

## How to refer to this project

| Context | Name | Example |
|---|---|---|
| Git / Claude sessions / technical | `bc-powerbi-flow` | *"Open the bc-powerbi-flow repo"* |
| Internal Lodværket (standups, Slack, Notion) | **BI Flow** | *"BI Flow tager Nordic Steel den her uge"* |
| Client-facing / sales / website | **Lodværket BI Accelerator** | *"We deliver the Lodværket BI Accelerator — branded Power BI in 1-2 weeks"* |

Same project, three labels. Use the one that fits the audience.

## Start here

1. **`WORKFLOW.md`** — Master document. Full client lifecycle from first contact to upsell. **Read this first in every new session.**
2. **`CREDENTIALS.md`** — Checklist for what to ask each client (BC keys, Supabase, etc.).
3. **`PLAYBOOK.md`** — Technical build playbook (Phase E of the workflow).

## Spin up a new client project

```bash
./init_client.sh nordicsteel https://nordicsteel.dk ~/Projects
cd ~/Projects/akse-dw-nordicsteel
claude
```

Then in Claude: paste the orchestration prompt from `PLAYBOOK.md`.

## Demo artefacts for sales

See `demo-clients/`:

- `vestas/` — navy + sky-blue, B2B manufacturing
- `toms/` — chocolate red, FMCG
- `lego/` — Lego red + yellow, retail
- `lakrids-by-bulow/` — black + gold, premium FMCG

Drop any of these `theme.json` files into PBI Desktop (View → Themes → Browse) on
top of `AkseDemoDW_v2.pbip` to instantly re-skin the report as if it were that brand.

## What's where

- `scan_source.py` — auto-discover client database schema (Postgres / MS SQL / BC / HubSpot / CSV)
- `extract_brand.py` + `gen_pbi_theme.py` + `gen_design_brief.py` — auto-extract client brand from their URL
- `transform_full.py` — silver + gold star schema (template — clients get a thinned version)
- `fabric_load_supabase.py` — paste into Fabric notebook to land Delta tables
- `gen_pbi_report.py` — generate all 6 pages of PBIP visuals
- `dax_measures_full.dax` — 65-measure cookbook

## Note on naming

Company rename in progress: **Akse → Lodværket**. Docs and code now use Lodværket.
Some deployed Fabric artefacts (Lakehouse name `Akse_Demo_DW`, notebook
`Akse_Load_Supabase`, `.pbip` filename `AkseDemoDW_v2.pbip`) still carry the old
name — they'll be renamed in the next re-deploy session.

## License

Lodværket-internal. Not for redistribution.
