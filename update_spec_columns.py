"""Rewrite templates/report_spec.example.yaml to use the new clean column names.

Run AFTER the MCP rename batch — keeps spec in sync with model.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parent
SPEC = ROOT / "templates" / "report_spec.example.yaml"

# Map of snake_case → "New Display Name" (from clean_column_names.py)
RENAME = {
    "day_name": "Day Name",
    "month_name": "Month Name",
    "day_of_week": "Day of Week",
    "week_of_year": "Week of Year",
    "year_quarter": "Year-Quarter",
    "year_month": "Year-Month",
    "campaign_name": "Campaign Name",
    "campaign_type": "Campaign Type",
    "start_date": "Start Date",
    "end_date": "End Date",
    "budget_dkk": "Budget (DKK)",
    "spent_dkk": "Spent (DKK)",
    "target_audience": "Target Audience",
    "roi_pct": "ROI %",
    "customer_name": "Customer Name",
    "country_group": "Country Group",
    "revenue_segment": "Revenue Segment",
    "customer_status": "Customer Status",
    "annual_revenue_dkk": "Annual Revenue (DKK)",
    "lead_source": "Lead Source",
    "avg_salary": "Avg Salary (DKK)",
    "total_cost": "Total Cost (DKK)",
    "first_name": "First Name",
    "last_name": "Last Name",
    "hire_date": "Hire Date",
    "termination_date": "Termination Date",
    "tenure_years": "Tenure (years)",
    "annual_salary_dkk": "Annual Salary (DKK)",
    "monthly_cost_dkk": "Monthly Cost (DKK)",
    "employment_type": "Employment Type",
    "item_name": "Item Name",
    "item_type": "Item Type",
    "unit_price": "Unit Price (DKK)",
    "unit_cost": "Unit Cost (DKK)",
    "inventory_qty": "Inventory Qty",
    "margin_pct": "Margin %",
    "revenue_category": "Revenue Category",
    "actual_dkk": "Actual (DKK)",
    "variance_dkk": "Variance (DKK)",
    "variance_pct": "Variance %",
    "billable_hours": "Billable Hours",
    "internal_hours": "Internal Hours",
    "total_hours": "Total Hours",
    "utilization_pct": "Utilization %",
    "cost_per_billable_hour": "Cost per Billable Hour (DKK)",
    "total_leads": "Total Leads",
    "qualified_leads": "Qualified Leads",
    "converted_leads": "Converted Leads",
    "avg_score": "Avg Score",
    "conversion_rate": "Conversion Rate %",
    "cost_per_lead": "Cost per Lead (DKK)",
    "cost_per_conversion": "Cost per Conversion (DKK)",
    "company_name": "Company Name",
    "survey_date": "Survey Date",
    "nps_score": "NPS Score",
    "nps_category": "NPS Category",
    "deal_name": "Deal Name",
    "amount_dkk": "Amount (DKK)",
    "weighted_amount_dkk": "Weighted Amount (DKK)",
    "deal_status": "Deal Status",
    "days_in_pipeline": "Days in Pipeline",
    "deal_owner": "Deal Owner",
    "deal_source": "Deal Source",
    "revenue_dkk": "Revenue (DKK)",
    "discount_dkk": "Discount (DKK)",
    "vat_dkk": "VAT (DKK)",
    "cogs_dkk": "COGS (DKK)",
    "gross_profit_dkk": "Gross Profit (DKK)",
    "gross_margin_pct": "Gross Margin %",
    "created_date": "Created Date",
    "resolved_date": "Resolved Date",
    "response_time_hours": "Response Time (hrs)",
    "sla_target_hours": "SLA Target (hrs)",
    "satisfaction_rating": "Satisfaction Rating",
    "assigned_to": "Assigned to",
    "resolution_days": "Resolution (days)",
    "session_month": "Session Month",
    "new_users": "New Users",
    "bounce_rate": "Bounce Rate %",
    "pages_per_session": "Pages per Session",
    "avg_duration_sec": "Avg Duration (sec)",
}


def main() -> None:
    text = SPEC.read_text(encoding="utf-8")
    changes = 0
    for snake, display in RENAME.items():
        # Match column: "snake_name" with quotes
        pattern = re.compile(r'(column:\s*)"' + re.escape(snake) + r'"')
        new = f'\\1"{display}"'
        text, n = pattern.subn(new, text)
        changes += n
    SPEC.write_text(text, encoding="utf-8")
    print(f"Updated {SPEC.relative_to(ROOT)}: {changes} column references rewritten")


if __name__ == "__main__":
    main()
