"""
Full Stack Silver + Gold Layers
================================
Transforms synthetic_full output into a star schema:

Dimensions: dim_date, dim_customer, dim_employee, dim_campaign, dim_department
Facts:      fact_sales, fact_pipeline, fact_marketing, fact_budget,
            fact_hr, fact_nps, fact_tickets
"""
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from config import OUTPUT_DIR

BRONZE = Path(OUTPUT_DIR) / "bronze"
SILVER = Path(OUTPUT_DIR) / "silver"
GOLD = Path(OUTPUT_DIR) / "gold"


def save_layer(df: pd.DataFrame, layer: Path, name: str) -> None:
    layer.mkdir(parents=True, exist_ok=True)
    path = layer / f"{name}.parquet"
    df.to_parquet(path, index=False)
    print(f"  {layer.name}/{name}.parquet -- {len(df)} rows")


def from_records(records: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(records)


# ========================================================================
# SILVER LAYER — clean, type, deduplicate
# ========================================================================

def silver_crm_companies(raw: list[dict]) -> pd.DataFrame:
    df = from_records(raw)
    df["annual_revenue_dkk"] = pd.to_numeric(df["annual_revenue_dkk"], errors="coerce").fillna(0)
    df["employees"] = pd.to_numeric(df["employees"], errors="coerce").fillna(0).astype(int)
    df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")
    save_layer(df, SILVER, "crm_companies")
    return df


def silver_crm_contacts(raw: list[dict]) -> pd.DataFrame:
    df = from_records(raw)
    df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")
    save_layer(df, SILVER, "crm_contacts")
    return df


def silver_crm_deals(raw: list[dict]) -> pd.DataFrame:
    df = from_records(raw)
    df["amount_dkk"] = pd.to_numeric(df["amount_dkk"], errors="coerce").fillna(0)
    df["weighted_amount_dkk"] = pd.to_numeric(df["weighted_amount_dkk"], errors="coerce").fillna(0)
    df["probability"] = pd.to_numeric(df["probability"], errors="coerce").fillna(0)
    df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")
    df["close_date"] = pd.to_datetime(df["close_date"], errors="coerce")
    # Derive deal_status
    df["deal_status"] = df["stage"].apply(
        lambda s: "Won" if s == "closed_won"
        else "Lost" if s == "closed_lost"
        else "Open"
    )
    save_layer(df, SILVER, "crm_deals")
    return df


def silver_crm_activities(raw: list[dict]) -> pd.DataFrame:
    df = from_records(raw)
    df["activity_date"] = pd.to_datetime(df["activity_date"], errors="coerce")
    df["duration_minutes"] = pd.to_numeric(df["duration_minutes"], errors="coerce").fillna(0).astype(int)
    save_layer(df, SILVER, "crm_activities")
    return df


def silver_campaigns(raw: list[dict]) -> pd.DataFrame:
    df = from_records(raw)
    df["budget_dkk"] = pd.to_numeric(df["budget_dkk"], errors="coerce").fillna(0)
    df["spent_dkk"] = pd.to_numeric(df["spent_dkk"], errors="coerce").fillna(0)
    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
    df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")
    save_layer(df, SILVER, "campaigns")
    return df


def silver_leads(raw: list[dict]) -> pd.DataFrame:
    df = from_records(raw)
    df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0).astype(int)
    df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")
    df["converted_date"] = pd.to_datetime(df["converted_date"], errors="coerce")
    save_layer(df, SILVER, "leads")
    return df


def silver_web_sessions(raw: list[dict]) -> pd.DataFrame:
    df = from_records(raw)
    df["session_month"] = pd.to_datetime(df["session_month"], errors="coerce")
    for col in ["sessions", "new_users", "conversions"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    for col in ["bounce_rate", "conversion_rate", "pages_per_session"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    save_layer(df, SILVER, "web_sessions")
    return df


def silver_budget(raw: list[dict]) -> pd.DataFrame:
    df = from_records(raw)
    for col in ["budget_dkk", "actual_dkk", "variance_dkk"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype(int)
    df["month"] = pd.to_numeric(df["month"], errors="coerce").astype(int)
    save_layer(df, SILVER, "budget")
    return df


def silver_employees(raw: list[dict]) -> pd.DataFrame:
    df = from_records(raw)
    df["hire_date"] = pd.to_datetime(df["hire_date"], errors="coerce")
    df["termination_date"] = pd.to_datetime(df["termination_date"], errors="coerce")
    df["annual_salary_dkk"] = pd.to_numeric(df["annual_salary_dkk"], errors="coerce").fillna(0)
    df["monthly_cost_dkk"] = pd.to_numeric(df["monthly_cost_dkk"], errors="coerce").fillna(0)
    save_layer(df, SILVER, "employees")
    return df


def silver_timesheets(raw: list[dict]) -> pd.DataFrame:
    df = from_records(raw)
    for col in ["billable_hours", "internal_hours", "total_hours"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["utilization_pct"] = pd.to_numeric(df["utilization_pct"], errors="coerce").fillna(0)
    save_layer(df, SILVER, "timesheets")
    return df


def silver_nps(raw: list[dict]) -> pd.DataFrame:
    df = from_records(raw)
    df["survey_date"] = pd.to_datetime(df["survey_date"], errors="coerce")
    df["nps_score"] = pd.to_numeric(df["nps_score"], errors="coerce").fillna(0).astype(int)
    save_layer(df, SILVER, "nps_surveys")
    return df


def silver_tickets(raw: list[dict]) -> pd.DataFrame:
    df = from_records(raw)
    df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")
    df["resolved_date"] = pd.to_datetime(df["resolved_date"], errors="coerce")
    df["response_time_hours"] = pd.to_numeric(df["response_time_hours"], errors="coerce").fillna(0)
    df["sla_target_hours"] = pd.to_numeric(df["sla_target_hours"], errors="coerce").fillna(0)
    df["satisfaction_rating"] = pd.to_numeric(df["satisfaction_rating"], errors="coerce")
    save_layer(df, SILVER, "support_tickets")
    return df


def run_silver(data: dict[str, list[dict]]) -> dict[str, pd.DataFrame]:
    print("\n=== SILVER LAYER ===\n")
    return {
        "crm_companies": silver_crm_companies(data["crm_companies"]),
        "crm_contacts": silver_crm_contacts(data["crm_contacts"]),
        "crm_deals": silver_crm_deals(data["crm_deals"]),
        "crm_activities": silver_crm_activities(data["crm_activities"]),
        "campaigns": silver_campaigns(data["campaigns"]),
        "leads": silver_leads(data["leads"]),
        "web_sessions": silver_web_sessions(data["web_sessions"]),
        "budget": silver_budget(data["budget"]),
        "employees": silver_employees(data["employees"]),
        "timesheets": silver_timesheets(data["timesheets"]),
        "nps_surveys": silver_nps(data["nps_surveys"]),
        "support_tickets": silver_tickets(data["support_tickets"]),
    }


# ========================================================================
# GOLD LAYER — star schema dimensions + facts
# ========================================================================

def gold_dim_date() -> pd.DataFrame:
    start = date(2023, 1, 1)
    end = date(2027, 12, 31)
    dates = [start + timedelta(days=i) for i in range((end - start).days + 1)]

    df = pd.DataFrame({"date": dates})
    df["date_key"] = df["date"].apply(lambda d: int(d.strftime("%Y%m%d")))
    df["year"] = df["date"].apply(lambda d: d.year)
    df["quarter"] = df["date"].apply(lambda d: (d.month - 1) // 3 + 1)
    df["month"] = df["date"].apply(lambda d: d.month)
    df["day"] = df["date"].apply(lambda d: d.day)
    df["day_name"] = df["date"].apply(lambda d: d.strftime("%A"))
    df["month_name"] = df["date"].apply(lambda d: d.strftime("%B"))
    df["day_of_week"] = df["date"].apply(lambda d: d.isoweekday())
    df["week_of_year"] = df["date"].apply(lambda d: d.isocalendar()[1])
    df["year_quarter"] = df.apply(lambda r: f"{r['year']}-Q{r['quarter']}", axis=1)
    df["year_month"] = df["date"].apply(lambda d: d.strftime("%Y-%m"))
    df["is_weekend"] = df["day_of_week"].isin([6, 7])

    save_layer(df, GOLD, "dim_date")
    return df


def gold_dim_customer(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    comp = silver["crm_companies"].copy()

    comp["customer_key"] = comp["bc_customer_number"].fillna(comp["crm_company_id"])
    comp["customer_status"] = comp["lifecycle_stage"].apply(
        lambda s: "Customer" if s == "customer" else "Prospect"
    )
    comp["country_group"] = comp["country"].apply(
        lambda c: "Denmark" if c == "DK"
        else "UK" if c == "GB"
        else "USA" if c == "US"
        else "Other"
    )
    # Revenue segment
    comp["revenue_segment"] = comp["annual_revenue_dkk"].apply(
        lambda r: "Enterprise" if r >= 5_000_000
        else "Mid-Market" if r >= 1_000_000
        else "SMB"
    )

    dim = comp[[
        "customer_key", "crm_company_id", "bc_customer_number",
        "company_name", "city", "country", "country_group",
        "industry", "segment", "revenue_segment", "customer_status",
        "annual_revenue_dkk", "employees", "lead_source", "owner",
    ]].rename(columns={"company_name": "customer_name"})

    save_layer(dim, GOLD, "dim_customer")
    return dim


def gold_dim_employee(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    emp = silver["employees"].copy()
    emp["tenure_years"] = emp["hire_date"].apply(
        lambda d: round((pd.Timestamp.now() - d).days / 365.25, 1) if pd.notna(d) else 0
    )
    emp["status"] = emp["is_active"].apply(lambda a: "Active" if a else "Terminated")

    dim = emp[[
        "employee_id", "first_name", "last_name", "department", "role",
        "hire_date", "termination_date", "status", "tenure_years",
        "annual_salary_dkk", "monthly_cost_dkk", "city", "employment_type",
    ]]

    save_layer(dim, GOLD, "dim_employee")
    return dim


def gold_dim_campaign(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    camp = silver["campaigns"].copy()
    camp["roi_pct"] = camp.apply(
        lambda r: round((r["spent_dkk"] - r["budget_dkk"]) / r["budget_dkk"] * 100, 1)
        if r["budget_dkk"] > 0 else 0,
        axis=1,
    )

    dim = camp[[
        "campaign_id", "campaign_name", "campaign_type", "status",
        "start_date", "end_date", "budget_dkk", "spent_dkk",
        "target_audience", "owner", "roi_pct",
    ]]

    save_layer(dim, GOLD, "dim_campaign")
    return dim


def gold_dim_department(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    emp = silver["employees"]
    dept_stats = (
        emp[emp["is_active"]]
        .groupby("department")
        .agg(
            headcount=("employee_id", "count"),
            avg_salary=("annual_salary_dkk", "mean"),
            total_cost=("monthly_cost_dkk", "sum"),
        )
        .reset_index()
    )
    dept_stats["avg_salary"] = dept_stats["avg_salary"].round(0).astype(int)
    dept_stats["total_cost"] = dept_stats["total_cost"].round(0).astype(int)
    dept_stats["department_id"] = [f"dept_{i+1:02d}" for i in range(len(dept_stats))]

    save_layer(dept_stats, GOLD, "dim_department")
    return dept_stats


def gold_fact_pipeline(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    deals = silver["crm_deals"].copy()
    deals["created_date_key"] = deals["created_date"].apply(
        lambda d: int(d.strftime("%Y%m%d")) if pd.notna(d) else 19000101
    )
    deals["close_date_key"] = deals["close_date"].apply(
        lambda d: int(d.strftime("%Y%m%d")) if pd.notna(d) else 19000101
    )
    # Map customer key
    deals["customer_key"] = deals["bc_customer_number"].fillna(deals["crm_company_id"])
    deals["days_in_pipeline"] = (deals["close_date"] - deals["created_date"]).dt.days.fillna(0).astype(int)

    fact = deals[[
        "deal_id", "customer_key", "crm_company_id",
        "deal_name", "amount_dkk", "weighted_amount_dkk",
        "stage", "probability", "deal_status",
        "is_won", "is_lost",
        "created_date_key", "close_date_key", "days_in_pipeline",
        "deal_owner", "deal_source",
    ]]

    save_layer(fact, GOLD, "fact_pipeline")
    return fact


def gold_fact_marketing(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    leads = silver["leads"].copy()

    # Aggregate leads per campaign
    lead_stats = (
        leads.groupby("campaign_id")
        .agg(
            total_leads=("lead_id", "count"),
            qualified_leads=("status", lambda s: (s == "qualified").sum()),
            converted_leads=("status", lambda s: (s == "converted").sum()),
            avg_score=("score", "mean"),
        )
        .reset_index()
    )
    lead_stats["avg_score"] = lead_stats["avg_score"].round(1)
    lead_stats["conversion_rate"] = (
        lead_stats["converted_leads"] / lead_stats["total_leads"].replace(0, 1)
    ).round(4)

    # Join with campaign spend
    camp = silver["campaigns"][["campaign_id", "campaign_type", "budget_dkk", "spent_dkk"]].copy()
    fact = lead_stats.merge(camp, on="campaign_id", how="left")
    fact["cost_per_lead"] = (fact["spent_dkk"] / fact["total_leads"].replace(0, 1)).round(0).astype(int)
    fact["cost_per_conversion"] = (
        fact["spent_dkk"] / fact["converted_leads"].replace(0, 1)
    ).round(0).astype(int)

    save_layer(fact, GOLD, "fact_marketing")
    return fact


def gold_fact_web(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    web = silver["web_sessions"].copy()
    web["date_key"] = web["session_month"].apply(
        lambda d: int(d.strftime("%Y%m%d")) if pd.notna(d) else 19000101
    )

    save_layer(web, GOLD, "fact_web_sessions")
    return web


def gold_fact_budget(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    budget = silver["budget"].copy()
    budget["date_key"] = budget.apply(
        lambda r: int(f"{r['year']}{r['month']:02d}01"), axis=1
    )
    budget["variance_pct"] = budget.apply(
        lambda r: round((r["actual_dkk"] - r["budget_dkk"]) / abs(r["budget_dkk"]) * 100, 1)
        if pd.notna(r.get("actual_dkk")) and r.get("budget_dkk", 0) != 0 else None,
        axis=1,
    )

    save_layer(budget, GOLD, "fact_budget")
    return budget


def gold_fact_hr(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    ts = silver["timesheets"].copy()
    emp = silver["employees"][["employee_id", "department", "monthly_cost_dkk"]].copy()

    fact = ts.merge(emp, on="employee_id", how="left", suffixes=("", "_emp"))
    # Keep the original department from timesheet if present
    if "department_emp" in fact.columns:
        fact["department"] = fact["department"].fillna(fact["department_emp"])
        fact = fact.drop(columns=["department_emp"])

    fact["cost_per_billable_hour"] = (
        fact["monthly_cost_dkk"] / fact["billable_hours"].replace(0, 1)
    ).round(0).astype(int)

    save_layer(fact, GOLD, "fact_hr")
    return fact


def gold_fact_nps(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    nps = silver["nps_surveys"].copy()
    nps["date_key"] = nps["survey_date"].apply(
        lambda d: int(d.strftime("%Y%m%d")) if pd.notna(d) else 19000101
    )
    # customer_key = bc_customer_number
    nps["customer_key"] = nps["bc_customer_number"]
    # Numeric encoding for aggregation
    nps["is_promoter"] = (nps["nps_category"] == "Promoter").astype(int)
    nps["is_detractor"] = (nps["nps_category"] == "Detractor").astype(int)

    save_layer(nps, GOLD, "fact_nps")
    return nps


def gold_fact_tickets(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    tkt = silver["support_tickets"].copy()
    tkt["created_date_key"] = tkt["created_date"].apply(
        lambda d: int(d.strftime("%Y%m%d")) if pd.notna(d) else 19000101
    )
    tkt["customer_key"] = tkt["bc_customer_number"]
    tkt["resolution_days"] = (tkt["resolved_date"] - tkt["created_date"]).dt.days

    save_layer(tkt, GOLD, "fact_tickets")
    return tkt


def run_gold(silver: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    print("\n=== GOLD LAYER (Star Schema) ===\n")
    return {
        # Dimensions
        "dim_date": gold_dim_date(),
        "dim_customer": gold_dim_customer(silver),
        "dim_employee": gold_dim_employee(silver),
        "dim_campaign": gold_dim_campaign(silver),
        "dim_department": gold_dim_department(silver),
        # Facts
        "fact_pipeline": gold_fact_pipeline(silver),
        "fact_marketing": gold_fact_marketing(silver),
        "fact_web_sessions": gold_fact_web(silver),
        "fact_budget": gold_fact_budget(silver),
        "fact_hr": gold_fact_hr(silver),
        "fact_nps": gold_fact_nps(silver),
        "fact_tickets": gold_fact_tickets(silver),
    }


# ========================================================================
# Verification
# ========================================================================

def verify(gold: dict[str, pd.DataFrame]) -> None:
    print("\n=== VERIFICATION ===\n")

    print("Gold tables:")
    for name, df in gold.items():
        print(f"  {name:.<30} {len(df):>6,} rows")

    # Pipeline summary
    pipe = gold["fact_pipeline"]
    print(f"\n--- Pipeline Summary ---")
    print(f"  Total deals:     {len(pipe)}")
    print(f"  Pipeline value:  {pipe['amount_dkk'].sum():,.0f} kr")
    print(f"  Weighted:        {pipe['weighted_amount_dkk'].sum():,.0f} kr")
    won = pipe[pipe["deal_status"] == "Won"]
    lost = pipe[pipe["deal_status"] == "Lost"]
    if len(won) + len(lost) > 0:
        print(f"  Win rate:        {len(won) / (len(won) + len(lost)) * 100:.1f}%")

    # Marketing summary
    mkt = gold["fact_marketing"]
    print(f"\n--- Marketing Summary ---")
    print(f"  Campaigns:       {len(mkt)}")
    print(f"  Total leads:     {mkt['total_leads'].sum():,}")
    print(f"  Converted:       {mkt['converted_leads'].sum():,}")
    print(f"  Avg CPL:         {mkt['cost_per_lead'].mean():,.0f} kr")

    # HR summary
    hr = gold["fact_hr"]
    print(f"\n--- HR Summary ---")
    print(f"  Timesheet rows:  {len(hr)}")
    print(f"  Avg utilization: {hr['utilization_pct'].mean():.1f}%")

    # NPS
    nps = gold["fact_nps"]
    if len(nps) > 0:
        prom = nps["is_promoter"].sum()
        det = nps["is_detractor"].sum()
        total = len(nps)
        nps_score = round((prom - det) / total * 100)
        print(f"\n--- NPS Summary ---")
        print(f"  Responses:       {total}")
        print(f"  NPS Score:       {nps_score}")

    # Budget
    bgt = gold["fact_budget"]
    actual = bgt["actual_dkk"].dropna()
    if len(actual) > 0:
        print(f"\n--- Budget Summary ---")
        rev_rows = bgt[bgt["category"] == "Revenue"]
        print(f"  Revenue budget:  {rev_rows['budget_dkk'].sum():,.0f} kr")
        print(f"  Revenue actual:  {rev_rows['actual_dkk'].sum():,.0f} kr")

    print("\nDW verification complete -- Power BI ready")
