"""
Generate Power BI Project (PBIP) for Akse Demo DW
==================================================
Creates a complete PBIP folder that PBI Desktop can open directly.
Includes: data model, PostgreSQL connection, DAX measures, relationships,
          and 6-page report layout with visuals.

Usage:
    python generate_pbip.py

Then open: output/AkseDemoDW.pbip in Power BI Desktop
(Enable PBIP: Options -> Preview features -> Power BI Project save format)
"""
import json
import os
import uuid
from pathlib import Path
from config import OUTPUT_DIR

OUT = Path(OUTPUT_DIR) / "AkseDemoDW"


def _guid() -> str:
    return str(uuid.uuid4())


# ============================================================
# TABLE DEFINITIONS
# ============================================================

TABLES = {
    "gold_dim_date": {
        "columns": [
            ("date", "string"), ("date_key", "int64"), ("year", "int64"),
            ("quarter", "int64"), ("month", "int64"), ("day", "int64"),
            ("day_name", "string"), ("month_name", "string"),
            ("day_of_week", "int64"), ("week_of_year", "int64"),
            ("year_quarter", "string"), ("year_month", "string"),
            ("is_weekend", "boolean"),
        ],
        "measures": [],
    },
    "gold_dim_customer": {
        "columns": [
            ("customer_key", "string"), ("crm_company_id", "string"),
            ("bc_customer_number", "string"), ("customer_name", "string"),
            ("city", "string"), ("country", "string"), ("country_group", "string"),
            ("industry", "string"), ("segment", "string"),
            ("revenue_segment", "string"), ("customer_status", "string"),
            ("annual_revenue_dkk", "int64"), ("employees", "int64"),
            ("lead_source", "string"), ("owner", "string"),
        ],
        "measures": [],
    },
    "gold_dim_employee": {
        "columns": [
            ("employee_id", "string"), ("first_name", "string"),
            ("last_name", "string"), ("department", "string"),
            ("role", "string"), ("hire_date", "dateTime"),
            ("termination_date", "dateTime"), ("status", "string"),
            ("tenure_years", "double"), ("annual_salary_dkk", "int64"),
            ("monthly_cost_dkk", "int64"), ("city", "string"),
            ("employment_type", "string"),
        ],
        "measures": [],
    },
    "gold_dim_campaign": {
        "columns": [
            ("campaign_id", "string"), ("campaign_name", "string"),
            ("campaign_type", "string"), ("status", "string"),
            ("start_date", "dateTime"), ("end_date", "dateTime"),
            ("budget_dkk", "int64"), ("spent_dkk", "int64"),
            ("target_audience", "string"), ("owner", "string"),
            ("roi_pct", "double"),
        ],
        "measures": [],
    },
    "gold_dim_department": {
        "columns": [
            ("department", "string"), ("headcount", "int64"),
            ("avg_salary", "int64"), ("total_cost", "int64"),
            ("department_id", "string"),
        ],
        "measures": [],
    },
    "gold_dim_item": {
        "columns": [
            ("item_key", "string"), ("item_name", "string"),
            ("item_type", "string"), ("category_code", "string"),
            ("unit_price", "int64"), ("unit_cost", "double"),
            ("inventory_qty", "int64"), ("margin_pct", "double"),
            ("revenue_category", "string"),
        ],
        "measures": [],
    },
    "gold_fact_pipeline": {
        "columns": [
            ("deal_id", "string"), ("customer_key", "string"),
            ("crm_company_id", "string"), ("deal_name", "string"),
            ("amount_dkk", "int64"), ("weighted_amount_dkk", "int64"),
            ("stage", "string"), ("probability", "double"),
            ("deal_status", "string"), ("is_won", "boolean"),
            ("is_lost", "boolean"), ("created_date_key", "int64"),
            ("close_date_key", "int64"), ("days_in_pipeline", "int64"),
            ("deal_owner", "string"), ("deal_source", "string"),
        ],
        "measures": [],
    },
    "gold_fact_marketing": {
        "columns": [
            ("campaign_id", "string"), ("total_leads", "int64"),
            ("qualified_leads", "int64"), ("converted_leads", "int64"),
            ("avg_score", "double"), ("conversion_rate", "double"),
            ("campaign_type", "string"), ("budget_dkk", "int64"),
            ("spent_dkk", "int64"), ("cost_per_lead", "int64"),
            ("cost_per_conversion", "int64"),
        ],
        "measures": [],
    },
    "gold_fact_web_sessions": {
        "columns": [
            ("session_month", "dateTime"), ("source", "string"),
            ("sessions", "int64"), ("new_users", "int64"),
            ("bounce_rate", "double"), ("pages_per_session", "double"),
            ("avg_duration_sec", "int64"), ("conversions", "int64"),
            ("conversion_rate", "double"), ("date_key", "int64"),
        ],
        "measures": [],
    },
    "gold_fact_budget": {
        "columns": [
            ("budget_id", "string"), ("year", "int64"), ("month", "int64"),
            ("period", "string"), ("category", "string"),
            ("account", "string"), ("budget_dkk", "int64"),
            ("actual_dkk", "double"), ("variance_dkk", "double"),
            ("department", "string"), ("date_key", "int64"),
            ("variance_pct", "double"),
        ],
        "measures": [],
    },
    "gold_fact_hr": {
        "columns": [
            ("timesheet_id", "string"), ("employee_id", "string"),
            ("department", "string"), ("period", "string"),
            ("billable_hours", "int64"), ("internal_hours", "int64"),
            ("total_hours", "int64"), ("utilization_pct", "double"),
            ("monthly_cost_dkk", "int64"), ("cost_per_billable_hour", "int64"),
        ],
        "measures": [],
    },
    "gold_fact_nps": {
        "columns": [
            ("survey_id", "string"), ("bc_customer_number", "string"),
            ("company_name", "string"), ("survey_date", "dateTime"),
            ("year", "int64"), ("quarter", "int64"),
            ("nps_score", "int64"), ("nps_category", "string"),
            ("comment", "string"), ("date_key", "int64"),
            ("customer_key", "string"), ("is_promoter", "int64"),
            ("is_detractor", "int64"),
        ],
        "measures": [],
    },
    "gold_fact_sales": {
        "columns": [
            ("line_id", "string"), ("invoice_number", "string"),
            ("date_key", "int64"), ("item_key", "string"),
            ("customer_key", "string"), ("item_name", "string"),
            ("category_code", "string"), ("quantity", "int64"),
            ("unit_price", "int64"), ("revenue_dkk", "double"),
            ("discount_dkk", "double"), ("vat_dkk", "double"),
            ("cogs_dkk", "double"), ("gross_profit_dkk", "double"),
            ("gross_margin_pct", "double"),
        ],
        "measures": [],
    },
    "gold_fact_tickets": {
        "columns": [
            ("ticket_id", "string"), ("bc_customer_number", "string"),
            ("company_name", "string"), ("category", "string"),
            ("priority", "string"), ("status", "string"),
            ("created_date", "dateTime"), ("resolved_date", "dateTime"),
            ("response_time_hours", "double"), ("sla_target_hours", "int64"),
            ("sla_met", "boolean"), ("satisfaction_rating", "double"),
            ("assigned_to", "string"), ("created_date_key", "int64"),
            ("customer_key", "string"), ("resolution_days", "double"),
        ],
        "measures": [],
    },
}

# ============================================================
# DAX MEASURES
# ============================================================

MEASURES = {
    "gold_fact_pipeline": [
        ("Pipeline Value", 'SUMX ( gold_fact_pipeline, gold_fact_pipeline[amount_dkk] )', "#,##0"),
        ("Weighted Pipeline", 'SUMX ( gold_fact_pipeline, gold_fact_pipeline[weighted_amount_dkk] )', "#,##0"),
        ("Open Pipeline", 'CALCULATE ( [Pipeline Value], gold_fact_pipeline[deal_status] = "Open" )', "#,##0"),
        ("Won Revenue", 'CALCULATE ( [Pipeline Value], gold_fact_pipeline[deal_status] = "Won" )', "#,##0"),
        ("Lost Revenue", 'CALCULATE ( [Pipeline Value], gold_fact_pipeline[deal_status] = "Lost" )', "#,##0"),
        ("Win Rate", 'VAR _won = CALCULATE ( COUNTROWS ( gold_fact_pipeline ), gold_fact_pipeline[is_won] = TRUE )\nVAR _closed = CALCULATE ( COUNTROWS ( gold_fact_pipeline ), gold_fact_pipeline[deal_status] IN { "Won", "Lost" } )\nRETURN DIVIDE ( _won, _closed, 0 )', "0.0%"),
        ("Deal Count", 'COUNTROWS ( gold_fact_pipeline )', "#,##0"),
        ("Open Deals", 'CALCULATE ( [Deal Count], gold_fact_pipeline[deal_status] = "Open" )', "#,##0"),
        ("Avg Deal Size", 'DIVIDE ( [Pipeline Value], [Deal Count], 0 )', "#,##0"),
        ("Avg Days in Pipeline", 'AVERAGEX ( gold_fact_pipeline, gold_fact_pipeline[days_in_pipeline] )', "0.0"),
    ],
    "gold_fact_marketing": [
        ("Total Leads", 'SUMX ( gold_fact_marketing, gold_fact_marketing[total_leads] )', "#,##0"),
        ("Qualified Leads", 'SUMX ( gold_fact_marketing, gold_fact_marketing[qualified_leads] )', "#,##0"),
        ("Converted Leads", 'SUMX ( gold_fact_marketing, gold_fact_marketing[converted_leads] )', "#,##0"),
        ("Lead Conversion Rate", 'DIVIDE ( [Converted Leads], [Total Leads], 0 )', "0.0%"),
        ("Avg Cost Per Lead", 'DIVIDE ( SUMX ( gold_fact_marketing, gold_fact_marketing[spent_dkk] ), [Total Leads], 0 )', "#,##0"),
        ("Cost Per Conversion", 'DIVIDE ( SUMX ( gold_fact_marketing, gold_fact_marketing[spent_dkk] ), [Converted Leads], 0 )', "#,##0"),
        ("Marketing Spend", 'SUMX ( gold_fact_marketing, gold_fact_marketing[spent_dkk] )', "#,##0"),
        ("Campaign Count", 'COUNTROWS ( gold_fact_marketing )', "#,##0"),
    ],
    "gold_fact_web_sessions": [
        ("Total Sessions", 'SUMX ( gold_fact_web_sessions, gold_fact_web_sessions[sessions] )', "#,##0"),
        ("Total New Users", 'SUMX ( gold_fact_web_sessions, gold_fact_web_sessions[new_users] )', "#,##0"),
        ("Total Web Conversions", 'SUMX ( gold_fact_web_sessions, gold_fact_web_sessions[conversions] )', "#,##0"),
        ("Web Conversion Rate", 'DIVIDE ( [Total Web Conversions], [Total Sessions], 0 )', "0.0%"),
        ("Avg Bounce Rate", 'AVERAGEX ( gold_fact_web_sessions, gold_fact_web_sessions[bounce_rate] )', "0.0%"),
    ],
    "gold_fact_budget": [
        ("Budget Total", 'SUMX ( gold_fact_budget, gold_fact_budget[budget_dkk] )', "#,##0"),
        ("Actual Total", 'SUMX ( gold_fact_budget, gold_fact_budget[actual_dkk] )', "#,##0"),
        ("Budget Variance", '[Actual Total] - [Budget Total]', "#,##0"),
        ("Budget Variance %", 'DIVIDE ( [Budget Variance], ABS ( [Budget Total] ), 0 )', "0.0%"),
        ("Revenue Budget", 'CALCULATE ( [Budget Total], gold_fact_budget[category] = "Revenue" )', "#,##0"),
        ("Revenue Actual", 'CALCULATE ( [Actual Total], gold_fact_budget[category] = "Revenue" )', "#,##0"),
        ("Gross Margin %", 'VAR _rev = CALCULATE ( [Actual Total], gold_fact_budget[category] = "Revenue" )\nVAR _cogs = CALCULATE ( ABS([Actual Total]), gold_fact_budget[category] = "COGS" )\nRETURN DIVIDE ( _rev - _cogs, _rev, 0 )', "0.0%"),
        ("Operating Profit", 'VAR _rev = CALCULATE ( [Actual Total], gold_fact_budget[category] = "Revenue" )\nVAR _cogs = CALCULATE ( ABS([Actual Total]), gold_fact_budget[category] = "COGS" )\nVAR _opex = CALCULATE ( ABS([Actual Total]), gold_fact_budget[category] = "OpEx" )\nRETURN _rev - _cogs - _opex', "#,##0"),
    ],
    "gold_fact_hr": [
        ("Avg Utilization", 'AVERAGEX ( gold_fact_hr, gold_fact_hr[utilization_pct] )', "0.0"),
        ("Total Billable Hours", 'SUMX ( gold_fact_hr, gold_fact_hr[billable_hours] )', "#,##0"),
        ("Total Internal Hours", 'SUMX ( gold_fact_hr, gold_fact_hr[internal_hours] )', "#,##0"),
        ("Avg Cost Per Billable Hour", 'DIVIDE ( SUMX ( gold_fact_hr, gold_fact_hr[monthly_cost_dkk] ), [Total Billable Hours], 0 )', "#,##0"),
    ],
    "gold_dim_employee": [
        ("Total Headcount", 'CALCULATE ( DISTINCTCOUNT ( gold_dim_employee[employee_id] ), gold_dim_employee[status] = "Active" )', "#,##0"),
        ("Avg Tenure Years", 'AVERAGEX ( FILTER ( gold_dim_employee, gold_dim_employee[status] = "Active" ), gold_dim_employee[tenure_years] )', "0.0"),
        ("Total Salary Cost", 'SUMX ( FILTER ( gold_dim_employee, gold_dim_employee[status] = "Active" ), gold_dim_employee[annual_salary_dkk] )', "#,##0"),
        ("Turnover Rate", 'VAR _termed = CALCULATE ( COUNTROWS ( gold_dim_employee ), gold_dim_employee[status] = "Terminated" )\nVAR _total = COUNTROWS ( gold_dim_employee )\nRETURN DIVIDE ( _termed, _total, 0 )', "0.0%"),
    ],
    "gold_fact_nps": [
        ("NPS Score", 'VAR _p = SUMX ( gold_fact_nps, gold_fact_nps[is_promoter] )\nVAR _d = SUMX ( gold_fact_nps, gold_fact_nps[is_detractor] )\nVAR _t = COUNTROWS ( gold_fact_nps )\nRETURN DIVIDE ( _p - _d, _t, 0 ) * 100', "+#;-#;0"),
        ("NPS Responses", 'COUNTROWS ( gold_fact_nps )', "#,##0"),
        ("Avg NPS Score", 'AVERAGEX ( gold_fact_nps, gold_fact_nps[nps_score] )', "0.0"),
    ],
    "gold_fact_tickets": [
        ("Total Tickets", 'COUNTROWS ( gold_fact_tickets )', "#,##0"),
        ("Open Tickets", 'CALCULATE ( [Total Tickets], gold_fact_tickets[status] = "Open" )', "#,##0"),
        ("Resolved Tickets", 'CALCULATE ( [Total Tickets], gold_fact_tickets[status] = "Resolved" )', "#,##0"),
        ("Resolution Rate", 'DIVIDE ( [Resolved Tickets], [Total Tickets], 0 )', "0.0%"),
        ("Avg Response Time Hours", 'AVERAGEX ( gold_fact_tickets, gold_fact_tickets[response_time_hours] )', "0.0"),
        ("SLA Met Rate", 'VAR _met = CALCULATE ( COUNTROWS ( gold_fact_tickets ), gold_fact_tickets[sla_met] = TRUE )\nRETURN DIVIDE ( _met, [Total Tickets], 0 )', "0.0%"),
        ("Avg Satisfaction Rating", 'AVERAGEX ( FILTER ( gold_fact_tickets, NOT ISBLANK ( gold_fact_tickets[satisfaction_rating] ) ), gold_fact_tickets[satisfaction_rating] )', "0.0"),
    ],
    "gold_fact_sales": [
        ("Total Revenue", 'SUMX ( gold_fact_sales, gold_fact_sales[revenue_dkk] )', "#,##0"),
        ("Total COGS", 'SUMX ( gold_fact_sales, gold_fact_sales[cogs_dkk] )', "#,##0"),
        ("Gross Profit", '[Total Revenue] - [Total COGS]', "#,##0"),
        ("Sales Margin %", 'DIVIDE ( [Gross Profit], [Total Revenue], 0 )', "0.0%"),
        ("Total Quantity", 'SUMX ( gold_fact_sales, gold_fact_sales[quantity] )', "#,##0"),
        ("Invoice Count", 'DISTINCTCOUNT ( gold_fact_sales[invoice_number] )', "#,##0"),
        ("Avg Order Value", 'DIVIDE ( [Total Revenue], [Invoice Count], 0 )', "#,##0"),
    ],
}

# ============================================================
# RELATIONSHIPS
# ============================================================

RELATIONSHIPS = [
    ("gold_fact_pipeline", "customer_key", "gold_dim_customer", "customer_key"),
    ("gold_fact_pipeline", "created_date_key", "gold_dim_date", "date_key"),
    ("gold_fact_nps", "customer_key", "gold_dim_customer", "customer_key"),
    ("gold_fact_nps", "date_key", "gold_dim_date", "date_key"),
    ("gold_fact_tickets", "customer_key", "gold_dim_customer", "customer_key"),
    ("gold_fact_tickets", "created_date_key", "gold_dim_date", "date_key"),
    ("gold_fact_marketing", "campaign_id", "gold_dim_campaign", "campaign_id"),
    ("gold_fact_web_sessions", "date_key", "gold_dim_date", "date_key"),
    ("gold_fact_budget", "date_key", "gold_dim_date", "date_key"),
    ("gold_fact_hr", "employee_id", "gold_dim_employee", "employee_id"),
    ("gold_fact_sales", "date_key", "gold_dim_date", "date_key"),
    ("gold_fact_sales", "customer_key", "gold_dim_customer", "customer_key"),
    ("gold_fact_sales", "item_key", "gold_dim_item", "item_key"),
]

PG_SERVER = "db.mudmhjwtezizwkjasoqu.supabase.co:5432"
PG_DB = "postgres"


# ============================================================
# BUILD model.bim (Tabular Model JSON)
# ============================================================

def build_model_bim() -> dict:
    tables = []
    for tbl_name, tbl_def in TABLES.items():
        columns = []
        for col_name, col_type in tbl_def["columns"]:
            col = {
                "name": col_name,
                "dataType": col_type,
                "sourceColumn": col_name,
                "lineageTag": _guid(),
            }
            if col_type == "int64":
                col["formatString"] = "0"
                col["summarizeBy"] = "sum" if "dkk" in col_name or col_name in ("quantity", "sessions", "conversions", "new_users") else "none"
            elif col_type == "double":
                col["formatString"] = "0.00"
                col["summarizeBy"] = "sum" if "dkk" in col_name else "none"
            else:
                col["summarizeBy"] = "none"
            columns.append(col)

        measures = []
        for m_name, m_expr, m_fmt in MEASURES.get(tbl_name, []):
            measures.append({
                "name": m_name,
                "expression": m_expr,
                "formatString": m_fmt,
                "lineageTag": _guid(),
            })

        m_expr = (
            f'let\n'
            f'    Source = PostgreSQL.Database("{PG_SERVER}", "{PG_DB}"),\n'
            f'    public_tbl = Source{{[Schema="public",Item="{tbl_name}"]}}[Data]\n'
            f'in\n'
            f'    public_tbl'
        )

        table = {
            "name": tbl_name,
            "lineageTag": _guid(),
            "columns": columns,
            "measures": measures,
            "partitions": [{
                "name": tbl_name,
                "mode": "import",
                "source": {
                    "type": "m",
                    "expression": m_expr.split("\n"),
                },
            }],
        }
        tables.append(table)

    relationships = []
    for from_tbl, from_col, to_tbl, to_col in RELATIONSHIPS:
        # Handle multiple relationships to same table (inactive)
        is_active = True
        for existing in relationships:
            if existing["toTable"] == to_tbl and existing["toColumn"] == to_col and existing.get("isActive", True):
                is_active = False
                break

        relationships.append({
            "name": _guid(),
            "fromTable": from_tbl,
            "fromColumn": from_col,
            "toTable": to_tbl,
            "toColumn": to_col,
            "crossFilteringBehavior": "oneDirection" if is_active else "oneDirection",
            "isActive": is_active,
        })

    return {
        "compatibilityLevel": 1567,
        "model": {
            "culture": "da-DK",
            "dataAccessOptions": {
                "legacyRedirects": True,
                "returnErrorValuesAsNull": True,
            },
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "sourceQueryCulture": "da-DK",
            "tables": tables,
            "relationships": relationships,
            "annotations": [
                {"name": "PBI_QueryOrder", "value": json.dumps(list(TABLES.keys()))},
                {"name": "PBIDesktopVersion", "value": "2.140.1000.0"},
            ],
        },
    }


# ============================================================
# BUILD report.json
# ============================================================

def _visual_config(visual_type: str, title: str, data_bindings: dict) -> str:
    """Build a visual config JSON string."""
    config = {
        "name": _guid()[:8],
        "layouts": [{"id": 0, "position": {}}],
        "singleVisual": {
            "visualType": visual_type,
            "projections": data_bindings,
            "objects": {
                "title": [{"properties": {"text": {"expr": {"Literal": {"Value": f"'{title}'"}}}}}],
            },
        },
    }
    return json.dumps(config, ensure_ascii=False)


def _card_visual(x: int, y: int, w: int, h: int, measure_table: str, measure_name: str, title: str) -> dict:
    config = {
        "name": _guid()[:8],
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "width": w, "height": h}}],
        "singleVisual": {
            "visualType": "card",
            "projections": {
                "Values": [{"queryRef": f"{measure_table}.{measure_name}"}],
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "t", "Entity": measure_table, "Type": 0}],
                "Select": [{"Measure": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": measure_name}, "Name": f"{measure_table}.{measure_name}"}],
            },
        },
    }
    return {
        "x": x, "y": y, "z": 0, "width": w, "height": h,
        "config": json.dumps(config, ensure_ascii=False),
        "filters": "[]",
        "tabOrder": 0,
    }


def _slicer_visual(x: int, y: int, w: int, h: int, table: str, column: str) -> dict:
    config = {
        "name": _guid()[:8],
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "width": w, "height": h}}],
        "singleVisual": {
            "visualType": "slicer",
            "projections": {
                "Values": [{"queryRef": f"{table}.{column}"}],
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "d", "Entity": table, "Type": 0}],
                "Select": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": column}, "Name": f"{table}.{column}"}],
            },
        },
    }
    return {
        "x": x, "y": y, "z": 0, "width": w, "height": h,
        "config": json.dumps(config, ensure_ascii=False),
        "filters": "[]",
        "tabOrder": 0,
    }


def build_report() -> dict:
    pages = []

    # Page 1: Executive Dashboard
    p1_visuals = [
        _card_visual(20, 20, 190, 100, "gold_fact_pipeline", "Pipeline Value", "Pipeline Value"),
        _card_visual(220, 20, 190, 100, "gold_fact_pipeline", "Win Rate", "Win Rate"),
        _card_visual(420, 20, 190, 100, "gold_fact_budget", "Revenue Actual", "Revenue (Actual)"),
        _card_visual(620, 20, 190, 100, "gold_fact_nps", "NPS Score", "NPS Score"),
        _card_visual(820, 20, 190, 100, "gold_dim_employee", "Total Headcount", "Headcount"),
        _card_visual(1020, 20, 190, 100, "gold_fact_tickets", "SLA Met Rate", "SLA Met"),
        _slicer_visual(20, 640, 200, 60, "gold_dim_date", "year"),
        _slicer_visual(230, 640, 200, 60, "gold_dim_date", "quarter"),
        _slicer_visual(440, 640, 200, 60, "gold_dim_customer", "country_group"),
    ]

    # Page 2: Pipeline & CRM
    p2_visuals = [
        _card_visual(20, 20, 230, 100, "gold_fact_pipeline", "Pipeline Value", "Pipeline Value"),
        _card_visual(260, 20, 230, 100, "gold_fact_pipeline", "Weighted Pipeline", "Weighted Pipeline"),
        _card_visual(500, 20, 230, 100, "gold_fact_pipeline", "Win Rate", "Win Rate"),
        _card_visual(740, 20, 230, 100, "gold_fact_pipeline", "Open Deals", "Open Deals"),
        _card_visual(980, 20, 230, 100, "gold_fact_pipeline", "Avg Deal Size", "Avg Deal Size"),
        _slicer_visual(20, 640, 200, 60, "gold_dim_date", "year"),
        _slicer_visual(230, 640, 200, 60, "gold_dim_customer", "country_group"),
    ]

    # Page 3: Marketing
    p3_visuals = [
        _card_visual(20, 20, 230, 100, "gold_fact_marketing", "Total Leads", "Total Leads"),
        _card_visual(260, 20, 230, 100, "gold_fact_marketing", "Lead Conversion Rate", "Conversion Rate"),
        _card_visual(500, 20, 230, 100, "gold_fact_marketing", "Avg Cost Per Lead", "Avg CPL"),
        _card_visual(740, 20, 230, 100, "gold_fact_web_sessions", "Total Sessions", "Total Sessions"),
        _card_visual(980, 20, 230, 100, "gold_fact_web_sessions", "Web Conversion Rate", "Web Conv. Rate"),
        _slicer_visual(20, 640, 200, 60, "gold_dim_date", "year"),
    ]

    # Page 4: Finance
    p4_visuals = [
        _card_visual(20, 20, 230, 100, "gold_fact_budget", "Revenue Actual", "Revenue Actual"),
        _card_visual(260, 20, 230, 100, "gold_fact_budget", "Gross Margin %", "Gross Margin"),
        _card_visual(500, 20, 230, 100, "gold_fact_budget", "Operating Profit", "Operating Profit"),
        _card_visual(740, 20, 230, 100, "gold_fact_budget", "Budget Variance", "Variance"),
        _card_visual(980, 20, 230, 100, "gold_fact_budget", "Budget Variance %", "Variance %"),
        _slicer_visual(20, 640, 200, 60, "gold_dim_date", "year"),
    ]

    # Page 5: HR
    p5_visuals = [
        _card_visual(20, 20, 230, 100, "gold_dim_employee", "Total Headcount", "Headcount"),
        _card_visual(260, 20, 230, 100, "gold_fact_hr", "Avg Utilization", "Avg Utilization"),
        _card_visual(500, 20, 230, 100, "gold_dim_employee", "Avg Tenure Years", "Avg Tenure"),
        _card_visual(740, 20, 230, 100, "gold_dim_employee", "Turnover Rate", "Turnover"),
        _card_visual(980, 20, 230, 100, "gold_dim_employee", "Total Salary Cost", "Salary Cost"),
        _slicer_visual(20, 640, 200, 60, "gold_dim_date", "year"),
    ]

    # Page 6: Customer Satisfaction
    p6_visuals = [
        _card_visual(20, 20, 230, 100, "gold_fact_nps", "NPS Score", "NPS Score"),
        _card_visual(260, 20, 230, 100, "gold_fact_tickets", "Total Tickets", "Total Tickets"),
        _card_visual(500, 20, 230, 100, "gold_fact_tickets", "Resolution Rate", "Resolution Rate"),
        _card_visual(740, 20, 230, 100, "gold_fact_tickets", "Avg Response Time Hours", "Avg Response"),
        _card_visual(980, 20, 230, 100, "gold_fact_tickets", "SLA Met Rate", "SLA Met Rate"),
        _slicer_visual(20, 640, 200, 60, "gold_dim_date", "year"),
        _slicer_visual(230, 640, 200, 60, "gold_dim_customer", "customer_name"),
    ]

    page_defs = [
        ("Executive Dashboard", p1_visuals),
        ("Pipeline & CRM", p2_visuals),
        ("Marketing", p3_visuals),
        ("Finance & Budget", p4_visuals),
        ("HR & People", p5_visuals),
        ("Customer Satisfaction", p6_visuals),
    ]

    for display_name, visuals in page_defs:
        page_config = {
            "name": _guid()[:8],
            "displayName": display_name,
            "displayOption": 1,
            "width": 1280,
            "height": 720,
        }
        pages.append({
            "name": page_config["name"],
            "displayName": display_name,
            "displayOption": 1,
            "height": 720,
            "width": 1280,
            "config": json.dumps(page_config, ensure_ascii=False),
            "visualContainers": visuals,
            "filters": "[]",
            "ordinal": len(pages),
        })

    theme = {
        "name": "Akse Demo",
        "dataColors": ["#0078D4", "#00B294", "#FFB900", "#D13438", "#881798", "#107C10", "#005A9E", "#767676"],
        "background": "#FFFFFF",
        "foreground": "#252423",
        "tableAccent": "#0078D4",
    }

    report_config = {
        "version": "5.50",
        "themeCollection": {"baseTheme": theme},
        "activeSectionIndex": 0,
        "defaultDrillFilterOtherVisuals": True,
    }

    return {
        "config": json.dumps(report_config, ensure_ascii=False),
        "layoutOptimization": 0,
        "pages": pages,
        "publicCustomVisuals": [],
    }


# ============================================================
# WRITE PBIP PROJECT
# ============================================================

def generate() -> None:
    # Create folder structure
    sm_dir = OUT / "AkseDemoDW.SemanticModel" / "definition"
    rpt_dir = OUT / "AkseDemoDW.Report" / "definition"
    sm_dir.mkdir(parents=True, exist_ok=True)
    rpt_dir.mkdir(parents=True, exist_ok=True)

    # 1. Root .pbip file
    pbip = {
        "version": "1.0",
        "artifacts": [
            {"report": {"path": "AkseDemoDW.Report"}},
        ],
        "settings": {
            "enableAutoRecovery": True,
        },
    }
    (OUT / "AkseDemoDW.pbip").write_text(json.dumps(pbip, indent=2, ensure_ascii=False), encoding="utf-8")

    # 2. Semantic Model
    pbism = {
        "version": "1.0",
        "compatibilityLevel": 1567,
    }
    (OUT / "AkseDemoDW.SemanticModel" / "definition.pbism").write_text(
        json.dumps(pbism, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    model = build_model_bim()
    (sm_dir / "model.bim").write_text(json.dumps(model, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  model.bim: {len(model['model']['tables'])} tables, "
          f"{sum(len(m.get('measures', [])) for m in model['model']['tables'])} measures, "
          f"{len(model['model']['relationships'])} relationships")

    # 3. Report
    pbir = {
        "version": "1.0",
        "datasetReference": {
            "byPath": {"path": "../AkseDemoDW.SemanticModel",},
        },
    }
    (OUT / "AkseDemoDW.Report" / "definition.pbir").write_text(
        json.dumps(pbir, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    report = build_report()
    (rpt_dir / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  report.json: {len(report['pages'])} pages")

    print(f"\nPBIP project saved to: {OUT}")
    print(f"\nAabn i Power BI Desktop:")
    print(f"  File -> Open report -> Browse -> vaelg AkseDemoDW.pbip")
    print(f"  (Aktiver PBIP: Options -> Preview features -> Power BI Project)")


if __name__ == "__main__":
    print("Generating PBIP project...\n")
    generate()
