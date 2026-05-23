# Client credentials checklist (Phase D)

> Open this with the client's IT contact during the kickoff call.
> Each section corresponds to a possible source. Skip sections that don't apply.
> Every value lands in the project's `.env` file. **Never commit `.env` to git.**

---

## Always required (regardless of source)

| Key | Where to find | Notes |
|---|---|---|
| `CLIENT_URL` | Their public website | Used by Phase 0c brand extractor |
| `CLIENT_NAME` | Display name for report Page 1 | e.g. "Nordic Steel A/S" |
| `FABRIC_WORKSPACE_ID` | Fabric portal → Workspace settings → Workspace ID (GUID) | Where the lakehouse + report land |
| `FABRIC_LAKEHOUSE_ID` | Fabric workspace → Lakehouse → ⋯ → Lakehouse settings → ID (GUID) | Where Delta tables land |

**AskUserQuestion template (use at kickoff):**

```
1. What is your company's public URL?
2. What name should appear on the report cover page?
3. Have you created a Fabric workspace + Lakehouse for this project yet?
   If yes — share the IDs. If no — we create them now together.
4. Which data sources are in scope (pick all that apply):
   BC SaaS | BC on-prem | Supabase Postgres | other Postgres | MS SQL Server
   | HubSpot | Salesforce | Mailchimp | CSV exports | other
```

---

## Source-specific credentials

### Business Central SaaS (cloud) — OAuth2

**Recommended path. Basic auth is deprecated in BC Online.**

You need someone with Azure AD admin rights to register an app.

| Key | What it is | How to get it |
|---|---|---|
| `BC_TENANT_ID` | Azure AD tenant GUID | Azure Portal → Microsoft Entra ID → Overview → Tenant ID |
| `BC_CLIENT_ID` | App registration client ID | Azure Portal → Microsoft Entra ID → App registrations → New registration → Single tenant; then copy "Application (client) ID" |
| `BC_CLIENT_SECRET` | App registration secret | Same app registration → Certificates & secrets → New client secret → copy the **Value** (not the ID) immediately |
| `BC_BASE_URL` | OData v4 endpoint | `https://api.businesscentral.dynamics.com/v2.0/<tenant>/<env>/ODataV4/Company('<company>')` — get `<env>` and `<company>` from BC URL when logged in |

**App registration also needs these API permissions** (BC admin grants consent):
- `Microsoft Dynamics 365 Business Central → Application permissions → API.ReadWrite.All`
- `Microsoft Dynamics 365 Business Central → Application permissions → app_access`
- Admin consent: yes

**In BC itself:** Microsoft Entra Applications page → Add the App ID → Status: Enabled → User Permission Sets: `D365 READ` (or your read-only equivalent).

**Verify:**
```bash
SOURCE_TYPE=bc_odata python scan_source.py --validate
# expect: N tables scanned, M FK candidates, K skipped
```

### Business Central on-prem — Basic auth fallback

Older NAV/BC on-prem setups still allow Web Services with Basic auth.

| Key | What it is |
|---|---|
| `BC_BASE_URL` | OData endpoint, often `https://<server>:7048/<instance>/ODataV4/Company('<company>')` |
| `BC_USER` | Service account username |
| `BC_PASSWORD` | The user's **Web Service Access Key** (NOT the AD password) — generate in User Card → Web Service Access Key |

Leave `BC_TENANT_ID` empty so the scanner uses Basic auth.

### Supabase Postgres

| Key | Where to find |
|---|---|
| `SUPABASE_URL` | `https://<project-ref>.supabase.co` — Supabase dashboard → Project Settings → API → Project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase dashboard → Project Settings → API → `service_role` secret (NOT `anon`) |
| `PG_HOST` | `db.<project-ref>.supabase.co` — Project Settings → Database → Connection string |
| `PG_PORT` | `5432` (or `6543` for connection pooling) |
| `PG_DATABASE` | `postgres` (default) |
| `PG_USER` | `postgres` (default) |
| `PG_PASSWORD` | Project Settings → Database → reset password if forgotten |
| `PG_SCHEMA` | `public` unless they keep app tables in a custom schema |
| `PG_SSLMODE` | `require` |

⚠️ **`service_role` bypasses Row-Level Security.** Use it only for the upload script in Phase 3, never in a client-facing app.

### Generic PostgreSQL (not Supabase)

Same `PG_*` keys as above. `SSLMODE=require` for cloud, `disable` for local Docker.

### MS SQL Server (BC backend, Dynamics, on-prem)

| Key | What |
|---|---|
| `MSSQL_SERVER` | `tcp:server.database.windows.net,1433` (Azure SQL) or `server\\instance` (on-prem) |
| `MSSQL_DATABASE` | DB name |
| `MSSQL_USER` | SQL user (not Windows auth — that needs a different driver flow) |
| `MSSQL_PASSWORD` | Password |
| `MSSQL_TRUST` | `no` for Azure SQL, `yes` for on-prem with self-signed cert |

Driver requirement on Akse machine: `ODBC Driver 18 for SQL Server` installed.

### HubSpot

| Key | Where |
|---|---|
| `HUBSPOT_TOKEN` | HubSpot → Settings → Integrations → **Private Apps** → Create → enable scopes: `crm.objects.companies.read`, `crm.objects.contacts.read`, `crm.objects.deals.read`, `crm.objects.tickets.read`, `crm.schemas.deals.read`, `crm.schemas.contacts.read`, `crm.schemas.companies.read` |

Tokens look like `pat-eu1-...` or `pat-na1-...`.

### CSV / Excel folder fallback

| Key | What |
|---|---|
| `CSV_FOLDER` | Absolute path to the folder, e.g. `C:/Users/Sajad/Clients/Nordic/csv-export` |

Drop all CSVs flat in that folder — scanner picks them up by filename.

### Multi-source clients (most real engagements)

Run the scanner once per source with different `SOURCE_TYPE` values, then manually merge the schema files:

```bash
SOURCE_TYPE=bc_odata python scan_source.py
mv source_schema.json source_schema_bc.json

SOURCE_TYPE=hubspot python scan_source.py
mv source_schema.json source_schema_hubspot.json

# Merge by hand into source_schema.md (one section per source)
```

(P0 gap: a `--source-config sources.yaml` flag that loops + merges automatically. Not built yet.)

---

## Brand assets (Phase 0c)

Usually just `CLIENT_URL` is enough — `extract_brand.py` does the rest.

If auto-extract is wrong, the client can correct it by editing
`output/branding/brand_assets.json` directly and re-running `gen_pbi_theme.py` +
`gen_design_brief.py`.

If the client has a real brand guide (PDF, Figma), grab it for reference. Manual
hex codes from a guide always beat auto-extracted ones — but we don't parse
PDFs yet, so it's still a manual paste.

---

## Sign-off before Phase E

Before moving from Phase D to E, get these confirmations from the client:

- [ ] We have **read access** to every source listed in scope
- [ ] We have **write access** to the Fabric workspace + lakehouse
- [ ] The sponsor has approved `proposal.md` in writing
- [ ] The sponsor has approved `design_brief.md` in writing (after Phase 0c runs)
- [ ] No secrets are written into any document we'll commit (`.env` is gitignored — but double-check)
- [ ] We agreed on a single point of contact for the next 1-2 weeks

**Run `python scan_source.py --validate` as the final go/no-go.** If it returns table counts > 0, we're good. If it errors, fix credentials before scheduling Phase E.
