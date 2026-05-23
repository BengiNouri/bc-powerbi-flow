"""transform_demo.py — example thin per-client transform built on transform_lib.

Use this as the template for new client transforms (transform_<client>.py).
The lib does the heavy lifting; the per-client file just orchestrates which
tables get which treatment.

For the existing AkseDemoDW data, transform_full.py is the legacy version with
inline helpers. Future clients should follow the pattern below.

Usage:
    python transform_demo.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from transform_lib import (
    active_status,
    assert_unique_key,
    build_dim_date,
    coerce_date,
    coerce_int,
    coerce_numeric,
    compute_tenure_years,
    conformed_customer_key,
    derive_country_group,
    derive_date_key,
    derive_revenue_segment,
    derive_status_from_stage,
    from_records,
    layer_dir,
    save_parquet,
)

ROOT = Path(__file__).parent
OUTPUT = ROOT / "output"
BRONZE = OUTPUT / "bronze"
SILVER = layer_dir(OUTPUT, "silver")
GOLD = layer_dir(OUTPUT, "gold")


# ─── SILVER ────────────────────────────────────────────────────────────────

def silver_crm_companies(raw: list[dict]) -> pd.DataFrame:
    df = from_records(raw)
    df = coerce_numeric(df, ["annual_revenue_dkk"])
    df = coerce_int(df, ["employees"])
    df = coerce_date(df, ["created_date"])
    save_parquet(df, SILVER, "crm_companies")
    return df


def silver_crm_deals(raw: list[dict]) -> pd.DataFrame:
    df = from_records(raw)
    df = coerce_numeric(df, ["amount_dkk", "weighted_amount_dkk", "probability"])
    df = coerce_date(df, ["created_date", "close_date"])
    df["deal_status"] = derive_status_from_stage(df["stage"])
    save_parquet(df, SILVER, "crm_deals")
    return df


# ─── GOLD — DIMENSIONS ─────────────────────────────────────────────────────

def gold_dim_customer(silver_companies: pd.DataFrame) -> pd.DataFrame:
    df = silver_companies.copy()
    df["customer_key"] = conformed_customer_key(df)
    df["country_group"] = derive_country_group(df["country"])
    df["revenue_segment"] = derive_revenue_segment(df["annual_revenue_dkk"])
    df["customer_status"] = df["lifecycle_stage"].apply(
        lambda s: "Customer" if s == "customer" else "Prospect"
    )
    keep = [
        "customer_key", "crm_company_id", "bc_customer_number", "company_name",
        "city", "country", "country_group", "industry", "segment", "revenue_segment",
        "customer_status", "annual_revenue_dkk", "employees", "lead_source", "owner",
    ]
    dim = df[[c for c in keep if c in df.columns]].rename(columns={"company_name": "customer_name"})
    assert_unique_key(dim, "customer_key", "gold_dim_customer")
    save_parquet(dim, GOLD, "dim_customer")
    return dim


def gold_dim_date(start_date: str, end_date: str) -> pd.DataFrame:
    dim = build_dim_date(start_date, end_date)
    assert_unique_key(dim, "date_key", "gold_dim_date")
    save_parquet(dim, GOLD, "dim_date")
    return dim


def gold_dim_employee(silver_employees: pd.DataFrame) -> pd.DataFrame:
    df = silver_employees.copy()
    df["tenure_years"] = compute_tenure_years(df["hire_date"])
    df["status"] = active_status(df["is_active"])
    keep = [
        "employee_id", "first_name", "last_name", "department", "role",
        "hire_date", "termination_date", "status", "tenure_years",
        "annual_salary_dkk", "monthly_cost_dkk", "city", "employment_type",
    ]
    dim = df[[c for c in keep if c in df.columns]]
    assert_unique_key(dim, "employee_id", "gold_dim_employee")
    save_parquet(dim, GOLD, "dim_employee")
    return dim


# ─── GOLD — FACTS ──────────────────────────────────────────────────────────

def gold_fact_pipeline(silver_deals: pd.DataFrame, customer_lookup: pd.DataFrame) -> pd.DataFrame:
    df = silver_deals.copy()
    # Conformed customer_key from dim
    df = df.merge(
        customer_lookup[["crm_company_id", "customer_key"]],
        on="crm_company_id", how="left",
    )
    df["created_date_key"] = derive_date_key(df["created_date"])
    df["close_date_key"] = derive_date_key(df["close_date"])
    df["is_won"] = df["deal_status"] == "Won"
    df["is_lost"] = df["deal_status"] == "Lost"
    df["days_in_pipeline"] = (df["close_date"] - df["created_date"]).dt.days.fillna(0).astype(int)
    save_parquet(df, GOLD, "fact_pipeline")
    return df


# ─── ORCHESTRATION ─────────────────────────────────────────────────────────

def main() -> None:
    """Demo orchestrator. Real clients call only the silver/gold builders that
    map to their source data."""
    print("transform_demo: example pipeline using transform_lib")
    print(f"  bronze: {BRONZE}")
    print(f"  silver: {SILVER}")
    print(f"  gold:   {GOLD}")

    # Load bronze JSON (matches synthetic_full.py output)
    crm_companies_path = BRONZE / "crm_companies.json"
    if not crm_companies_path.exists():
        print(f"  [skip] {crm_companies_path.name} not found — run synthetic_full.py / pipeline_full.py first")
        return

    companies = json.loads(crm_companies_path.read_text(encoding="utf-8"))
    deals = json.loads((BRONZE / "crm_deals.json").read_text(encoding="utf-8"))

    silver_co = silver_crm_companies(companies)
    silver_de = silver_crm_deals(deals)

    dim_customer = gold_dim_customer(silver_co)
    gold_dim_date("2024-07-01", "2026-12-31")
    gold_fact_pipeline(silver_de, dim_customer)

    print("\nDone — demo gold tables in output/gold/")


if __name__ == "__main__":
    main()
