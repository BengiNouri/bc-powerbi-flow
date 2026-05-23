"""Source database / API scanner — Phase 0a of the client onboarding playbook.

Usage:
    python scan_source.py                 # full scan
    python scan_source.py --validate      # quick sanity counts only
    python scan_source.py --source pg     # force a specific source type

Reads SOURCE_TYPE from .env. Supported values:
    postgres | mssql | bc_odata | mysql | csv_folder

Outputs:
    source_schema.json   machine-readable (used by next phases)
    source_schema.md     human-readable (review with client)
"""
from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# ─── CONFIG ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
OUT_JSON = ROOT / "source_schema.json"
OUT_MD = ROOT / "source_schema.md"

# Skip patterns — system / staging tables that clients never report on.
SKIP_PATTERNS = (
    re.compile(r"^pg_", re.I),
    re.compile(r"^sys", re.I),
    re.compile(r"^_", re.I),
    re.compile(r"audit", re.I),
    re.compile(r"log$", re.I),
    re.compile(r"^staging_", re.I),
    re.compile(r"_temp$", re.I),
    re.compile(r"_bkp$", re.I),
)

SAMPLE_ROWS = 5
PK_HINTS = ("id", "key", "_id", "_key", "_no", "number")


@dataclass
class Column:
    name: str
    type: str
    nullable: bool = True
    pk_hint: bool = False
    fk_hint: str | None = None  # "other_table.column" if guessed


@dataclass
class Table:
    name: str
    row_count: int = 0
    columns: list[Column] = field(default_factory=list)
    sample: list[dict[str, Any]] = field(default_factory=list)
    classification: str = "unknown"  # dim | fact | bridge | skip
    skip_reason: str | None = None


def should_skip(name: str) -> str | None:
    for pat in SKIP_PATTERNS:
        if pat.search(name):
            return f"matches skip pattern '{pat.pattern}'"
    return None


def looks_like_pk(col_name: str) -> bool:
    n = col_name.lower()
    return any(n == h or n.endswith(h) for h in PK_HINTS)


def detect_fk(col_name: str, tables: list[Table]) -> str | None:
    """Heuristic: col 'customer_id' → look for table 'customer'/'customers' with PK 'id' or 'customer_id'."""
    n = col_name.lower()
    if not (n.endswith("_id") or n.endswith("_key") or n.endswith("_no")):
        return None
    base = re.sub(r"_(id|key|no)$", "", n)
    candidates = [base, base + "s", base + "es"]
    for t in tables:
        tn = t.name.lower()
        if tn in candidates or tn.endswith("." + candidates[0]):
            for c in t.columns:
                if c.pk_hint or c.name.lower() in (n, "id", base + "_id"):
                    return f"{t.name}.{c.name}"
    return None


def classify(t: Table) -> str:
    """Naïve dim/fact split — review and override in source_schema.md."""
    if t.skip_reason:
        return "skip"
    n = t.name.lower()
    if any(k in n for k in ("dim_", "_dim")):
        return "dim"
    if any(k in n for k in ("fact_", "_fact", "line", "transaction", "event", "log")):
        return "fact"
    # Heuristic: many FKs + numeric columns → fact; few FKs + descriptive cols → dim
    fk_count = sum(1 for c in t.columns if c.fk_hint)
    numeric_count = sum(1 for c in t.columns if c.type in ("int", "bigint", "decimal", "numeric", "float", "double"))
    if t.row_count > 1000 and fk_count >= 2:
        return "fact"
    if t.row_count < 1000 and numeric_count <= 3:
        return "dim"
    return "unknown"


# ─── SOURCE DRIVERS ────────────────────────────────────────────────────────

def scan_postgres() -> list[Table]:
    import psycopg2
    conn = psycopg2.connect(
        host=os.environ["PG_HOST"],
        port=os.environ.get("PG_PORT", 5432),
        dbname=os.environ["PG_DATABASE"],
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
        sslmode=os.environ.get("PG_SSLMODE", "require"),
    )
    schema = os.environ.get("PG_SCHEMA", "public")
    cur = conn.cursor()
    cur.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = %s AND table_type='BASE TABLE'",
        (schema,),
    )
    table_names = [r[0] for r in cur.fetchall()]
    tables: list[Table] = []
    for tn in sorted(table_names):
        t = Table(name=tn)
        skip = should_skip(tn)
        if skip:
            t.skip_reason = skip
            tables.append(t)
            continue
        cur.execute(
            "SELECT column_name, data_type, is_nullable FROM information_schema.columns "
            "WHERE table_schema=%s AND table_name=%s ORDER BY ordinal_position",
            (schema, tn),
        )
        for cname, ctype, nul in cur.fetchall():
            t.columns.append(Column(name=cname, type=ctype, nullable=(nul == "YES"), pk_hint=looks_like_pk(cname)))
        cur.execute(f'SELECT COUNT(*) FROM "{schema}"."{tn}"')
        t.row_count = cur.fetchone()[0]
        cur.execute(f'SELECT * FROM "{schema}"."{tn}" LIMIT %s', (SAMPLE_ROWS,))
        col_names = [d[0] for d in cur.description]
        t.sample = [dict(zip(col_names, row)) for row in cur.fetchall()]
        tables.append(t)
    cur.close()
    conn.close()
    return tables


def scan_mssql() -> list[Table]:
    import pyodbc
    cs = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={os.environ['MSSQL_SERVER']};DATABASE={os.environ['MSSQL_DATABASE']};"
        f"UID={os.environ['MSSQL_USER']};PWD={os.environ['MSSQL_PASSWORD']};"
        f"Encrypt=yes;TrustServerCertificate={os.environ.get('MSSQL_TRUST', 'no')}"
    )
    conn = pyodbc.connect(cs)
    cur = conn.cursor()
    cur.execute(
        "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
        "WHERE TABLE_TYPE='BASE TABLE' AND TABLE_SCHEMA NOT IN ('sys','INFORMATION_SCHEMA')"
    )
    rows = cur.fetchall()
    tables: list[Table] = []
    for sch, tn in sorted(rows):
        full = f"{sch}.{tn}"
        t = Table(name=full)
        skip = should_skip(tn)
        if skip:
            t.skip_reason = skip
            tables.append(t)
            continue
        cur.execute(
            "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA=? AND TABLE_NAME=? ORDER BY ORDINAL_POSITION",
            sch, tn,
        )
        for cname, ctype, nul in cur.fetchall():
            t.columns.append(Column(name=cname, type=ctype, nullable=(nul == "YES"), pk_hint=looks_like_pk(cname)))
        cur.execute(f"SELECT COUNT(*) FROM [{sch}].[{tn}]")
        t.row_count = cur.fetchone()[0]
        cur.execute(f"SELECT TOP {SAMPLE_ROWS} * FROM [{sch}].[{tn}]")
        col_names = [d[0] for d in cur.description]
        t.sample = [dict(zip(col_names, row)) for row in cur.fetchall()]
        tables.append(t)
    conn.close()
    return tables


def _bc_session(base_url: str) -> tuple["requests.Session", dict]:
    """Return a session + headers, using OAuth if BC_TENANT_ID is set, else Basic."""
    import requests
    sess = requests.Session()
    if os.environ.get("BC_TENANT_ID"):
        # OAuth2 client credentials (BC SaaS)
        token_url = f"https://login.microsoftonline.com/{os.environ['BC_TENANT_ID']}/oauth2/v2.0/token"
        resp = requests.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": os.environ["BC_CLIENT_ID"],
                "client_secret": os.environ["BC_CLIENT_SECRET"],
                "scope": "https://api.businesscentral.dynamics.com/.default",
            },
            timeout=15,
        )
        resp.raise_for_status()
        token = resp.json()["access_token"]
        return sess, {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    # Fallback: Basic auth (on-prem BC)
    sess.auth = (os.environ["BC_USER"], os.environ["BC_PASSWORD"])
    return sess, {"Accept": "application/json"}


def scan_bc_odata() -> list[Table]:
    """Business Central OData v4 — auto-picks OAuth or Basic from env."""
    base = os.environ["BC_BASE_URL"].rstrip("/")
    sess, headers = _bc_session(base)
    r = sess.get(base, headers=headers, timeout=20)
    r.raise_for_status()
    entities = [e["url"] for e in r.json().get("value", [])]
    tables: list[Table] = []
    for ent in sorted(entities):
        t = Table(name=ent)
        skip = should_skip(ent)
        if skip:
            t.skip_reason = skip
            tables.append(t)
            continue
        rr = sess.get(f"{base}/{ent}?$top={SAMPLE_ROWS}", headers=headers, timeout=20)
        if rr.status_code != 200:
            t.skip_reason = f"HTTP {rr.status_code}"
            tables.append(t)
            continue
        rows = rr.json().get("value", [])
        t.sample = rows
        if rows:
            for k, v in rows[0].items():
                t.columns.append(Column(name=k, type=type(v).__name__, pk_hint=looks_like_pk(k)))
        # Approximate count via $count (skip if --no-counts)
        if not os.environ.get("SCAN_NO_COUNTS"):
            rc = sess.get(f"{base}/{ent}/$count", headers=headers, timeout=30)
            if rc.status_code == 200 and rc.text.isdigit():
                t.row_count = int(rc.text)
        tables.append(t)
    return tables


def scan_hubspot() -> list[Table]:
    """HubSpot CRM via private app token (https://app.hubspot.com → Settings → Integrations → Private Apps)."""
    import requests
    token = os.environ["HUBSPOT_TOKEN"]
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    # Standard CRM objects worth scanning (extend if client uses custom objects)
    objects = [
        ("companies", "/crm/v3/objects/companies"),
        ("contacts",  "/crm/v3/objects/contacts"),
        ("deals",     "/crm/v3/objects/deals"),
        ("tickets",   "/crm/v3/objects/tickets"),
        ("pipelines", "/crm/v3/pipelines/deals"),
        ("owners",    "/crm/v3/owners"),
    ]
    base = "https://api.hubapi.com"
    tables: list[Table] = []
    for name, path in objects:
        t = Table(name=f"hubspot_{name}")
        params = {"limit": SAMPLE_ROWS} if "/objects/" in path else {}
        r = requests.get(f"{base}{path}", headers=headers, params=params, timeout=15)
        if r.status_code != 200:
            t.skip_reason = f"HTTP {r.status_code} — {r.text[:120]}"
            tables.append(t)
            continue
        data = r.json()
        # HubSpot returns {"results": [...]} for objects, [...] for pipelines/owners
        rows = data.get("results", data if isinstance(data, list) else [])
        t.sample = rows[:SAMPLE_ROWS]
        # HubSpot rows nest most data under "properties"; flatten one level for column inference
        if rows:
            sample_row = {**rows[0].get("properties", {}), **{k: v for k, v in rows[0].items() if k != "properties"}}
            for k, v in sample_row.items():
                t.columns.append(Column(name=k, type=type(v).__name__, pk_hint=looks_like_pk(k)))
        # Row count via /crm/v3/objects/<obj>/search with total — skip if SCAN_NO_COUNTS
        if not os.environ.get("SCAN_NO_COUNTS") and "/objects/" in path:
            rc = requests.post(
                f"{base}{path}/search",
                headers=headers,
                json={"limit": 1},
                timeout=20,
            )
            if rc.status_code == 200:
                t.row_count = rc.json().get("total", 0)
        tables.append(t)
    return tables


def scan_csv_folder() -> list[Table]:
    import pandas as pd
    folder = Path(os.environ.get("CSV_FOLDER", "./input"))
    tables: list[Table] = []
    for f in sorted(folder.glob("*.csv")):
        df = pd.read_csv(f, nrows=SAMPLE_ROWS + 1000)
        t = Table(name=f.stem)
        t.row_count = sum(1 for _ in open(f, encoding="utf-8")) - 1  # quick line count
        for c in df.columns:
            t.columns.append(Column(name=c, type=str(df[c].dtype), pk_hint=looks_like_pk(c)))
        t.sample = df.head(SAMPLE_ROWS).to_dict("records")
        tables.append(t)
    return tables


DRIVERS = {
    "postgres":    scan_postgres,
    "pg":          scan_postgres,
    "mssql":       scan_mssql,
    "bc_odata":    scan_bc_odata,
    "bc":          scan_bc_odata,
    "hubspot":     scan_hubspot,
    "csv_folder":  scan_csv_folder,
}


# ─── MAIN ──────────────────────────────────────────────────────────────────

def enrich(tables: list[Table]) -> None:
    for t in tables:
        for c in t.columns:
            c.fk_hint = detect_fk(c.name, tables)
        t.classification = classify(t)


def write_md(tables: list[Table]) -> None:
    lines: list[str] = ["# Source schema scan\n"]
    in_scope = [t for t in tables if not t.skip_reason]
    skipped = [t for t in tables if t.skip_reason]
    lines.append(f"**Tables in scope:** {len(in_scope)}  ·  **Skipped:** {len(skipped)}\n")
    for group in ("dim", "fact", "bridge", "unknown"):
        gt = [t for t in in_scope if t.classification == group]
        if not gt:
            continue
        lines.append(f"\n## {group.upper()} candidates ({len(gt)})\n")
        for t in gt:
            lines.append(f"\n### `{t.name}` — {t.row_count:,} rows")
            for c in t.columns:
                pk = " 🔑" if c.pk_hint else ""
                fk = f" → `{c.fk_hint}`" if c.fk_hint else ""
                lines.append(f"- `{c.name}` ({c.type}){pk}{fk}")
    if skipped:
        lines.append("\n## Skipped\n")
        for t in skipped:
            lines.append(f"- `{t.name}` — {t.skip_reason}")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=os.environ.get("SOURCE_TYPE"))
    ap.add_argument("--validate", action="store_true")
    args = ap.parse_args()

    # Load .env if present
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))

    src = args.source
    if not src or src not in DRIVERS:
        raise SystemExit(f"Set SOURCE_TYPE to one of {sorted(DRIVERS)} via .env or --source")

    tables = DRIVERS[src]()
    enrich(tables)

    if args.validate:
        in_scope = [t for t in tables if not t.skip_reason]
        fks = sum(1 for t in in_scope for c in t.columns if c.fk_hint)
        print(f"{len(in_scope)} tables scanned, {fks} FK candidates, {len(tables) - len(in_scope)} skipped")
        return

    OUT_JSON.write_text(json.dumps([asdict(t) for t in tables], default=str, indent=2))
    write_md(tables)
    print(f"Wrote {OUT_JSON.name} and {OUT_MD.name} — {len(tables)} tables")


if __name__ == "__main__":
    main()
