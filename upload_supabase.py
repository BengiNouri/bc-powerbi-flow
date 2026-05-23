"""
Upload Gold Layer to Supabase
=============================
1. Creates tables via Supabase SQL endpoint
2. Inserts data via REST API with service_role key
3. Verifies row counts

Usage:
    python upload_supabase.py

Requires .env with SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY
"""
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

from config import OUTPUT_DIR

load_dotenv(Path(__file__).parent / ".env")

GOLD = Path(OUTPUT_DIR) / "gold"

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


def get_client():
    if not SUPABASE_URL or not SUPABASE_KEY or "your-service" in SUPABASE_KEY:
        print("ERROR: Udfyld .env filen med SUPABASE_URL og SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def pandas_dtype_to_pg(dtype: str, col_name: str) -> str:
    """Map pandas dtype to PostgreSQL type."""
    d = str(dtype)
    if "int" in d:
        return "BIGINT"
    if "float" in d:
        return "DOUBLE PRECISION"
    if "bool" in d:
        return "BOOLEAN"
    if "datetime" in d:
        return "TIMESTAMPTZ"
    if "date" in col_name and "key" in col_name:
        return "INTEGER"
    return "TEXT"


def build_create_sql(table_name: str, df: pd.DataFrame) -> str:
    """Build CREATE TABLE statement from DataFrame."""
    cols = []
    for col in df.columns:
        pg_type = pandas_dtype_to_pg(str(df[col].dtype), col)
        cols.append(f'    "{col}" {pg_type}')
    cols_sql = ",\n".join(cols)
    return f'DROP TABLE IF EXISTS "{table_name}" CASCADE;\nCREATE TABLE "{table_name}" (\n{cols_sql}\n);'


def clean_df(df: pd.DataFrame) -> list[dict]:
    """Convert DataFrame to list of dicts safe for JSON/REST API."""
    import math
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].astype(str).replace("NaT", None)
        # Handle date objects
        if df[col].apply(lambda x: isinstance(x, __import__('datetime').date) and not isinstance(x, __import__('datetime').datetime)).any():
            df[col] = df[col].apply(lambda x: str(x) if x is not None else None)
        # Replace NaN/None with None for JSON
        df[col] = df[col].where(df[col].notna(), None)

    rows = df.to_dict(orient="records")
    # Clean any remaining float NaN
    for row in rows:
        for k, v in row.items():
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                row[k] = None
    return rows


def main() -> None:
    if not GOLD.exists():
        print(f"Gold layer not found at {GOLD}. Run pipeline_full.py first.")
        sys.exit(1)

    parquet_files = sorted(GOLD.glob("*.parquet"))
    if not parquet_files:
        print("No parquet files in gold layer.")
        sys.exit(1)

    # Load all gold tables
    tables: dict[str, pd.DataFrame] = {}
    print("Loading gold parquet files...\n")
    for f in parquet_files:
        name = f"gold_{f.stem}"
        df = pd.read_parquet(f)
        tables[name] = df
        print(f"  {name:.<40} {len(df):>6,} rows")

    # Connect
    print(f"\nConnecting to Supabase...")
    client = get_client()
    print("Connected.\n")

    # Step 1: Create tables via SQL
    print("=== CREATING TABLES ===\n")
    all_sql = []
    for name, df in tables.items():
        sql = build_create_sql(name, df)
        all_sql.append(sql)

    combined_sql = "\n\n".join(all_sql)
    try:
        client.postgrest.schema("public")
        # Use rpc to execute raw SQL
        result = client.rpc("exec_sql", {"query": combined_sql}).execute()
        print("  Tables created via RPC")
    except Exception:
        # RPC might not exist, fall back to writing SQL file
        sql_path = Path(OUTPUT_DIR) / "create_tables.sql"
        sql_path.write_text(combined_sql, encoding="utf-8")
        print(f"  RPC not available. SQL saved to: {sql_path}")
        print("  => Kopiér indholdet til Supabase SQL Editor og kør det.")
        print("  => Kør derefter dette script igen for at indsette data.\n")

        # Check if tables already exist by trying to select
        first_table = list(tables.keys())[0]
        try:
            client.table(first_table).select("*", count="exact").limit(0).execute()
            print(f"  (Tabeller eksisterer allerede - fortsætter med insert)")
        except Exception:
            print(f"  (Tabeller eksisterer IKKE endnu - kør SQL først)")
            return

    # Step 2: Insert data
    print("\n=== INSERTING DATA ===\n")
    for name, df in tables.items():
        rows = clean_df(df)
        if not rows:
            print(f"  {name:.<40} SKIP (empty)")
            continue

        try:
            # Insert in chunks
            chunk_size = 500
            inserted = 0
            for i in range(0, len(rows), chunk_size):
                chunk = rows[i:i + chunk_size]
                client.table(name).insert(chunk).execute()
                inserted += len(chunk)

            print(f"  {name:.<40} {inserted:>6,} rows  OK")
        except Exception as e:
            err_msg = str(e)[:120]
            print(f"  {name:.<40} FAILED: {err_msg}")

    # Step 3: Verify
    print("\n=== VERIFICATION ===\n")
    total = 0
    for name in tables:
        try:
            result = client.table(name).select("*", count="exact").limit(0).execute()
            count = result.count or 0
            total += count
            print(f"  {name:.<40} {count:>6,} rows")
        except Exception as e:
            print(f"  {name:.<40} ERROR")

    print(f"\n  Total: {total:,} rows across {len(tables)} tables")
    print(f"\n{'=' * 50}")
    print("Upload complete!")
    print("Power BI: Get Data -> PostgreSQL")
    print(f"  Server: db.mudmhjwtezizwkjasoqu.supabase.co:5432")
    print(f"  Database: postgres")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
