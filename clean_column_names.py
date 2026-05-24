"""Generate column rename + hide map for Power BI semantic model.

Reads the live PBI Desktop model via MCP listing (hardcoded sample below),
emits two JSON payloads:
  1. column_operations.Rename   (snake_case  →  Title Case)
  2. column_operations.Update   (technical FK/flag columns  →  isHidden=true)

Usage:
    python clean_column_names.py            # dry-run, prints what would change
    python clean_column_names.py --apply    # writes apply.json + hide.json

Then call MCP column_operations.Rename + Update with those payloads.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).parent

# Acronyms that should stay uppercase
ACRONYMS = {"id", "ids", "dkk", "kr", "nps", "bc", "crm", "sla", "cogs", "opex", "csat", "vat",
            "roi", "kpi", "url", "uk", "us", "ai", "p&l", "fk", "pk", "sql"}

# Compound terms that get special formatting
SPECIAL = {
    "year_month":   "Year-Month",
    "year_quarter": "Year-Quarter",
    "day_of_week":  "Day of Week",
    "week_of_year": "Week of Year",
    "annual_revenue_dkk":     "Annual Revenue (DKK)",
    "annual_salary_dkk":      "Annual Salary (DKK)",
    "monthly_cost_dkk":       "Monthly Cost (DKK)",
    "amount_dkk":             "Amount (DKK)",
    "weighted_amount_dkk":    "Weighted Amount (DKK)",
    "budget_dkk":             "Budget (DKK)",
    "spent_dkk":              "Spent (DKK)",
    "actual_dkk":             "Actual (DKK)",
    "variance_dkk":           "Variance (DKK)",
    "revenue_dkk":            "Revenue (DKK)",
    "discount_dkk":           "Discount (DKK)",
    "vat_dkk":                "VAT (DKK)",
    "cogs_dkk":               "COGS (DKK)",
    "gross_profit_dkk":       "Gross Profit (DKK)",
    "cost_per_billable_hour": "Cost per Billable Hour (DKK)",
    "cost_per_lead":          "Cost per Lead (DKK)",
    "cost_per_conversion":    "Cost per Conversion (DKK)",
    "roi_pct":                "ROI %",
    "variance_pct":           "Variance %",
    "utilization_pct":        "Utilization %",
    "gross_margin_pct":       "Gross Margin %",
    "conversion_rate":        "Conversion Rate %",
    "bounce_rate":            "Bounce Rate %",
    "margin_pct":             "Margin %",
    "response_time_hours":    "Response Time (hrs)",
    "sla_target_hours":       "SLA Target (hrs)",
    "resolution_days":        "Resolution (days)",
    "tenure_years":           "Tenure (years)",
    "billable_hours":         "Billable Hours",
    "internal_hours":         "Internal Hours",
    "total_hours":            "Total Hours",
    "days_in_pipeline":       "Days in Pipeline",
    "pages_per_session":      "Pages per Session",
    "avg_duration_sec":       "Avg Duration (sec)",
    "nps_score":              "NPS Score",
    "nps_category":           "NPS Category",
    "deal_owner":             "Deal Owner",
    "deal_source":            "Deal Source",
    "deal_status":            "Deal Status",
    "deal_name":              "Deal Name",
    "campaign_type":          "Campaign Type",
    "campaign_name":          "Campaign Name",
    "lead_source":            "Lead Source",
    "customer_name":          "Customer Name",
    "customer_status":        "Customer Status",
    "country_group":          "Country Group",
    "revenue_segment":        "Revenue Segment",
    "first_name":             "First Name",
    "last_name":              "Last Name",
    "hire_date":              "Hire Date",
    "termination_date":       "Termination Date",
    "employment_type":        "Employment Type",
    "company_name":           "Company Name",
    "survey_date":            "Survey Date",
    "created_date":           "Created Date",
    "resolved_date":          "Resolved Date",
    "session_month":          "Session Month",
    "total_leads":            "Total Leads",
    "qualified_leads":        "Qualified Leads",
    "converted_leads":        "Converted Leads",
    "new_users":              "New Users",
    "avg_score":              "Avg Score",
    "avg_salary":             "Avg Salary (DKK)",
    "total_cost":             "Total Cost (DKK)",
    "target_audience":        "Target Audience",
    "start_date":             "Start Date",
    "end_date":               "End Date",
    "item_name":              "Item Name",
    "item_type":              "Item Type",
    "unit_price":             "Unit Price (DKK)",
    "unit_cost":              "Unit Cost (DKK)",
    "inventory_qty":          "Inventory Qty",
    "revenue_category":       "Revenue Category",
    "assigned_to":            "Assigned to",
    "satisfaction_rating":    "Satisfaction Rating",
    "month_name":             "Month Name",
    "day_name":               "Day Name",
}

# Suffixes that mean "hide this column" (FKs, technical IDs, boolean flags)
HIDE_SUFFIX = ("_key", "_id")
HIDE_PREFIX = ("is_",)
HIDE_EXACT = {
    "sla_met", "invoice_number", "category_code", "department_id",
    "bc_customer_number", "crm_company_id", "budget_id", "line_id",
    "timesheet_id", "ticket_id", "deal_id", "survey_id", "campaign_id",
    "employee_id", "item_key", "customer_key", "date_key",
    "created_date_key", "close_date_key",
}


def is_hidden(col: str) -> bool:
    if col in HIDE_EXACT:
        return True
    if any(col.startswith(p) for p in HIDE_PREFIX):
        return True
    if any(col.endswith(s) for s in HIDE_SUFFIX):
        return True
    return False


def title_case(snake: str) -> str:
    """snake_case → Title Case with acronym handling."""
    if snake in SPECIAL:
        return SPECIAL[snake]
    parts = snake.split("_")
    out = []
    for p in parts:
        if not p:
            continue
        if p.lower() in ACRONYMS:
            out.append(p.upper())
        else:
            out.append(p[:1].upper() + p[1:])
    return " ".join(out)


# ─── COLUMN INVENTORY (pasted from column_operations.List output) ──────────
TABLES = {
    "gold_dim_date": ["date", "date_key", "year", "quarter", "month", "day",
                       "day_name", "month_name", "day_of_week", "week_of_year",
                       "year_quarter", "year_month", "is_weekend"],
    "gold_dim_campaign": ["campaign_id", "campaign_name", "campaign_type", "status",
                           "start_date", "end_date", "budget_dkk", "spent_dkk",
                           "target_audience", "owner", "roi_pct"],
    "gold_dim_customer": ["customer_key", "crm_company_id", "bc_customer_number",
                           "customer_name", "city", "country", "country_group",
                           "industry", "segment", "revenue_segment", "customer_status",
                           "annual_revenue_dkk", "employees", "lead_source", "owner"],
    "gold_dim_department": ["department", "headcount", "avg_salary", "total_cost",
                             "department_id"],
    "gold_dim_employee": ["employee_id", "first_name", "last_name", "department",
                           "role", "hire_date", "termination_date", "status",
                           "tenure_years", "annual_salary_dkk", "monthly_cost_dkk",
                           "city", "employment_type"],
    "gold_dim_item": ["item_key", "item_name", "item_type", "category_code",
                       "unit_price", "unit_cost", "inventory_qty", "margin_pct",
                       "revenue_category"],
    "gold_fact_budget": ["budget_id", "year", "month", "period", "category", "account",
                          "budget_dkk", "actual_dkk", "variance_dkk", "department",
                          "date_key", "variance_pct"],
    "gold_fact_hr": ["timesheet_id", "employee_id", "department", "period",
                      "billable_hours", "internal_hours", "total_hours",
                      "utilization_pct", "monthly_cost_dkk", "cost_per_billable_hour"],
    "gold_fact_marketing": ["campaign_id", "total_leads", "qualified_leads",
                             "converted_leads", "avg_score", "conversion_rate",
                             "campaign_type", "budget_dkk", "spent_dkk",
                             "cost_per_lead", "cost_per_conversion"],
    "gold_fact_nps": ["survey_id", "bc_customer_number", "company_name", "survey_date",
                       "year", "quarter", "nps_score", "nps_category", "comment",
                       "date_key", "customer_key", "is_promoter", "is_detractor"],
    "gold_fact_pipeline": ["deal_id", "customer_key", "crm_company_id", "deal_name",
                            "amount_dkk", "weighted_amount_dkk", "stage", "probability",
                            "deal_status", "is_won", "is_lost", "created_date_key",
                            "close_date_key", "days_in_pipeline", "deal_owner",
                            "deal_source"],
    "gold_fact_sales": ["line_id", "invoice_number", "date_key", "item_key",
                         "customer_key", "item_name", "category_code", "quantity",
                         "unit_price", "revenue_dkk", "discount_dkk", "vat_dkk",
                         "cogs_dkk", "gross_profit_dkk", "gross_margin_pct"],
    "gold_fact_tickets": ["ticket_id", "bc_customer_number", "company_name", "category",
                           "priority", "status", "created_date", "resolved_date",
                           "response_time_hours", "sla_target_hours", "sla_met",
                           "satisfaction_rating", "assigned_to", "created_date_key",
                           "customer_key", "resolution_days"],
    "gold_fact_web_sessions": ["session_month", "source", "sessions", "new_users",
                                "bounce_rate", "pages_per_session", "avg_duration_sec",
                                "conversions", "conversion_rate", "date_key"],
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Write apply.json + hide.json")
    args = ap.parse_args()

    renames: list[dict] = []
    hides: list[dict] = []
    skipped: list[str] = []

    for table, cols in TABLES.items():
        for col in cols:
            if "_" not in col:
                # Already clean — only hide if it's a flag like 'status' (no need)
                continue
            if is_hidden(col):
                hides.append({"tableName": table, "name": col, "isHidden": True})
                continue
            new_name = title_case(col)
            if new_name != col:
                renames.append({"tableName": table, "currentName": col, "newName": new_name})
            else:
                skipped.append(f"{table}.{col}")

    print(f"Renames: {len(renames)}")
    print(f"Hides:   {len(hides)}")
    print(f"Skipped: {len(skipped)}")
    if args.apply:
        (ROOT / "apply.json").write_text(json.dumps({"renameDefinitions": renames}, indent=2))
        (ROOT / "hide.json").write_text(json.dumps({"definitions": hides}, indent=2))
        print(f"Wrote apply.json + hide.json")
    else:
        print("\nSample renames (first 10):")
        for r in renames[:10]:
            print(f"  {r['tableName']}.{r['currentName']:30} → {r['newName']}")
        print("\nSample hides (first 10):")
        for h in hides[:10]:
            print(f"  {h['tableName']}.{h['name']}")


if __name__ == "__main__":
    main()
