"""Generate PBI report pages and visuals as JSON in PBIP format.

Reads design_decisions.yaml (if present) to drive page enablement, top KPIs,
client name in titles, slicer placement, and chart style.

Layout: 1280x720 canvas
  - Title row:   y=0,   h=60
  - KPI row:     y=70,  h=110
  - Content:     y=200, h=490
"""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
REPORT = ROOT / "output" / "AkseDemoDW" / "AkseDemoDW_v2.Report"
PAGES = REPORT / "definition" / "pages"
DECISIONS_FILE = ROOT / "output" / "branding" / "design_decisions.yaml"


def load_decisions() -> dict:
    """Load design_decisions.yaml if present, else return defaults."""
    if not DECISIONS_FILE.exists():
        return {"client_name": "Lodværket", "pages": [], "kpi_cards": {}, "slicers": {}}
    try:
        import yaml
        return yaml.safe_load(DECISIONS_FILE.read_text(encoding="utf-8")) or {}
    except ImportError:
        # PyYAML not installed — fall back gracefully
        return {"client_name": "Lodværket", "pages": [], "kpi_cards": {}, "slicers": {}}


DECISIONS = load_decisions()
CLIENT_NAME = DECISIONS.get("client_name", "Lodværket")

SCHEMA_PAGE = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"
SCHEMA_VISUAL = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.7.0/schema.json"
SCHEMA_PAGES = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json"


def hex_id(name: str) -> str:
    return hashlib.md5(name.encode()).hexdigest()[:20]


def measure_field(table: str, measure: str) -> dict:
    return {
        "field": {
            "Measure": {
                "Expression": {"SourceRef": {"Entity": table}},
                "Property": measure,
            },
            "Name": f"{table}.{measure}",
            "NativeReferenceName": measure,
        },
        "queryRef": f"{table}.{measure}",
        "nativeQueryRef": measure,
    }


def column_field(table: str, column: str) -> dict:
    return {
        "field": {
            "Column": {
                "Expression": {"SourceRef": {"Entity": table}},
                "Property": column,
            },
            "Name": f"{table}.{column}",
            "NativeReferenceName": column,
        },
        "queryRef": f"{table}.{column}",
        "nativeQueryRef": column,
    }


def make_card(measure: str, x: int, y: int, w: int = 228, h: int = 110, label: str = None) -> dict:
    return {
        "$schema": SCHEMA_VISUAL,
        "name": hex_id(f"card_{measure}_{x}_{y}"),
        "position": {"x": x, "y": y, "z": 0, "height": h, "width": w, "tabOrder": 0},
        "visual": {
            "visualType": "card",
            "query": {
                "queryState": {
                    "Values": {
                        "projections": [measure_field("_Measures", measure)]
                    }
                }
            },
            "objects": {
                "labels": [{"properties": {"fontSize": {"expr": {"Literal": {"Value": "32D"}}}}}],
                "categoryLabels": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "text": {"expr": {"Literal": {"Value": f"'{label or measure}'"}}}}}],
            },
            "drillFilterOtherVisuals": True,
        },
    }


def make_textbox(text: str, x: int, y: int, w: int, h: int = 60, size: int = 24, bold: bool = True) -> dict:
    return {
        "$schema": SCHEMA_VISUAL,
        "name": hex_id(f"text_{text}_{x}_{y}"),
        "position": {"x": x, "y": y, "z": 0, "height": h, "width": w, "tabOrder": 0},
        "visual": {
            "visualType": "textbox",
            "objects": {
                "general": [{
                    "properties": {
                        "paragraphs": [{
                            "textRuns": [{
                                "value": text,
                                "textStyle": {
                                    "fontSize": f"{size}pt",
                                    "fontWeight": "bold" if bold else "normal",
                                    "color": "#0E1A2B",
                                }
                            }],
                            "horizontalTextAlignment": "left",
                        }]
                    }
                }]
            }
        },
    }


def _no_auto_title() -> dict:
    """Force-disable PBI's auto-generated chart title. We emit titles via textboxes instead."""
    return {"title": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}]}


def make_chart(visual_type: str, name_suffix: str, category: dict, values: list[dict],
               x: int, y: int, w: int, h: int, title: str = None) -> dict:
    projections_cat = [category]
    projections_y = values
    visual = {
        "visualType": visual_type,
        "query": {
            "queryState": {
                "Category": {"projections": projections_cat},
                "Y": {"projections": projections_y},
            }
        },
        "drillFilterOtherVisuals": True,
    }
    visual["objects"] = _no_auto_title()
    result = {
        "$schema": SCHEMA_VISUAL,
        "name": hex_id(f"{visual_type}_{name_suffix}_{x}_{y}"),
        "position": {"x": x, "y": y, "z": 0, "height": h, "width": w, "tabOrder": 0},
        "visual": visual,
    }
    if title:
        result["_label"] = title
    return result


def make_donut(name_suffix: str, category: dict, value: dict, x: int, y: int, w: int, h: int, title: str = None) -> dict:
    visual = {
        "visualType": "donutChart",
        "query": {
            "queryState": {
                "Category": {"projections": [category]},
                "Y": {"projections": [value]},
            }
        },
        "drillFilterOtherVisuals": True,
    }
    visual["objects"] = _no_auto_title()
    result = {
        "$schema": SCHEMA_VISUAL,
        "name": hex_id(f"donut_{name_suffix}_{x}_{y}"),
        "position": {"x": x, "y": y, "z": 0, "height": h, "width": w, "tabOrder": 0},
        "visual": visual,
    }
    if title:
        result["_label"] = title
    return result


def make_image(image_name: str, x: int, y: int, w: int, h: int) -> dict:
    """Logo / static image visual. image_name is the file name inside Report/StaticResources/RegisteredResources/."""
    return {
        "$schema": SCHEMA_VISUAL,
        "name": hex_id(f"image_{image_name}_{x}_{y}"),
        "position": {"x": x, "y": y, "z": 0, "height": h, "width": w, "tabOrder": 0},
        "visual": {
            "visualType": "image",
            "objects": {
                "general": [{"properties": {"imageUrl": {"image": {"name": image_name, "url": image_name}}}}],
                "imageScaling": [{"properties": {"imageScalingType": {"expr": {"Literal": {"Value": "'Fit'"}}}}}],
            },
            "drillFilterOtherVisuals": True,
        },
    }


def make_slicer(field: dict, x: int, y: int, w: int = 240, h: int = 70, title: str = None) -> dict:
    return {
        "$schema": SCHEMA_VISUAL,
        "name": hex_id(f"slicer_{field['queryRef']}_{x}_{y}"),
        "position": {"x": x, "y": y, "z": 0, "height": h, "width": w, "tabOrder": 0},
        "visual": {
            "visualType": "slicer",
            "query": {
                "queryState": {
                    "Values": {"projections": [field]}
                }
            },
            "objects": {
                "data": [{"properties": {"mode": {"expr": {"Literal": {"Value": "'Dropdown'"}}}}}],
                "general": [{"properties": {"orientation": {"expr": {"Literal": {"Value": "1D"}}}}}],
            },
            "drillFilterOtherVisuals": True,
        },
    }


def make_table(name_suffix: str, fields: list[dict], x: int, y: int, w: int, h: int, title: str = None) -> dict:
    visual = {
        "visualType": "tableEx",
        "query": {
            "queryState": {
                "Values": {"projections": fields}
            }
        },
        "drillFilterOtherVisuals": True,
    }
    visual["objects"] = _no_auto_title()
    result = {
        "$schema": SCHEMA_VISUAL,
        "name": hex_id(f"table_{name_suffix}_{x}_{y}"),
        "position": {"x": x, "y": y, "z": 0, "height": h, "width": w, "tabOrder": 0},
        "visual": visual,
    }
    if title:
        result["_label"] = title
    return result


# ─── PAGE DEFINITIONS ──────────────────────────────────────
PAGE_DEFS = [
    {
        "key": "exec",
        "displayName": "1. Executive Dashboard",
        "title": f"{CLIENT_NAME} — Executive Dashboard",
        "subtitle": "Cross-functional KPIs across Sales, Pipeline, Finance, HR and Customers",
    },
    {
        "key": "pipeline",
        "displayName": "2. Pipeline & CRM",
        "title": "Pipeline & CRM",
        "subtitle": "Deal flow, win rate, customer segments",
    },
    {
        "key": "marketing",
        "displayName": "3. Marketing & Web",
        "title": "Marketing & Web Analytics",
        "subtitle": "Lead generation, campaign ROI, web traffic",
    },
    {
        "key": "finance",
        "displayName": "4. Finance & Budget",
        "title": "Finance & Budget",
        "subtitle": "Revenue vs Budget, P&L, variance analysis",
    },
    {
        "key": "hr",
        "displayName": "5. HR & People",
        "title": "HR & People",
        "subtitle": "Headcount, utilization, salary cost",
    },
    {
        "key": "csat",
        "displayName": "6. NPS & Support",
        "title": "Customer Satisfaction & Support",
        "subtitle": "NPS score, ticket flow, SLA performance",
    },
    {
        "key": "quality",
        "displayName": "7. Quality & Compliance",
        "title": "Quality & Compliance",
        "subtitle": "SLA performance, critical issues, ticket category trends",
    },
]


def _decisions_page(key: str) -> dict:
    """Find this page's decision config in design_decisions.yaml (or empty dict)."""
    for p in DECISIONS.get("pages", []):
        if p.get("key") == key:
            return p
    return {}


def _is_page_enabled(key: str) -> bool:
    """Default true; YAML can disable individual pages."""
    pages = DECISIONS.get("pages", [])
    if not pages:
        # No decisions yaml — only include the original 6 default pages
        return key != "quality"
    pd = _decisions_page(key)
    return pd.get("enabled", False) if pd else False


def _top_kpis_for_exec() -> list[tuple[str, str]]:
    """Read Side 1 top KPIs from decisions, fall back to defaults."""
    pd = _decisions_page("exec")
    if pd and pd.get("top_kpis"):
        return [(k["measure"], k.get("label", k["measure"])) for k in pd["top_kpis"][:5]]
    return [
        ("Revenue", "Revenue"),
        ("Gross Margin", "Gross Margin"),
        ("Pipeline Value", "Pipeline"),
        ("NPS Score", "NPS"),
        ("Total Headcount", "Headcount"),
    ]


# Right-sidebar slicer (240px wide). Content area shrinks accordingly.
SIDEBAR_W = 0  # 0 = no sidebar. Updated by main() based on decisions.yaml
CONTENT_W = 1280

# KPI card widths for 5 cards
KPI_W, KPI_H, KPI_Y = 228, 110, 70
KPI_LAST_W = 248
CONTENT_Y = 200
CONTENT_H = 490
CHART_TITLE_H = 28


def labeled(label: str, chart: dict) -> list[dict]:
    """Emit [title textbox, chart] pair, shifting chart down 30px so label sits above.
    The chart's height is reduced by 30 to keep within original bounds."""
    pos = chart["position"]
    x, y, w = pos["x"], pos["y"], pos["width"]
    title_box = make_textbox(label, x, y, w, CHART_TITLE_H - 4, size=12)
    chart["position"]["y"] = y + CHART_TITLE_H
    chart["position"]["height"] = max(80, pos["height"] - CHART_TITLE_H)
    return [title_box, chart]


KPI_TARGET_MAP = {
    "Revenue":                "Revenue vs Target %",
    "Pipeline Value":         "Pipeline vs Target %",
    "Gross Margin":           "Margin vs Target %",
    "Total Tickets":          "Tickets vs Target",
    "Avg Satisfaction Rating": None,  # no target defined
}


def kpi_row(measures: list[tuple[str, str]]) -> list[dict]:
    """measures: list of (measure_name, label). x positions: 20,268,516,764,1012.

    Emits 2 visuals per slot when a vs-target measure exists:
      - the main KPI card (118px high)
      - a small textbox below showing vs-target % (28px high)
    Otherwise emits just the card."""
    xs = [20, 268, 516, 764, 1012]
    show_target = DECISIONS.get("kpi_cards", {}).get("show_target", False)
    out: list[dict] = []
    for i, (m, label) in enumerate(measures[:5]):
        w = KPI_LAST_W if i == 4 else KPI_W
        x = xs[i]
        if show_target and KPI_TARGET_MAP.get(m):
            # Stacked: card (top 80px) + vs-target card (bottom 28px)
            out.append(make_card(m, x, KPI_Y, w, KPI_H - 30, label))
            out.append(make_card(KPI_TARGET_MAP[m], x, KPI_Y + KPI_H - 28, w, 26, "vs Target"))
        else:
            out.append(make_card(m, x, KPI_Y, w, KPI_H, label))
    return out


def page_exec() -> list[dict]:
    visuals = []
    # Logo top-left (if available)
    logo_path = DECISIONS.get("logo", {}).get("path_light")
    if logo_path and (ROOT / logo_path).exists():
        visuals.append(make_image("Logo", 20, 10, 140, 48))
        title_x = 180
    else:
        title_x = 20
    # title — uses client name from design_decisions.yaml (reserve right side for global slicer)
    visuals.append(make_textbox(f"{CLIENT_NAME} — Executive Dashboard", title_x, 10, 1080 - title_x, 48, size=24))
    # KPIs — top 5 from design_decisions.yaml
    visuals += kpi_row(_top_kpis_for_exec())
    # Revenue by month (line chart)
    visuals.append(make_chart(
        "lineChart", "rev_month",
        column_field("gold_dim_date", "year_month"),
        [measure_field("_Measures", "Revenue")],
        20, CONTENT_Y, 620, 240, "Revenue by Month",
    ))
    # Revenue by industry (bar chart)
    visuals.append(make_chart(
        "clusteredBarChart", "rev_industry",
        column_field("gold_dim_customer", "industry"),
        [measure_field("_Measures", "Revenue")],
        660, CONTENT_Y, 600, 240, "Revenue by Industry",
    ))
    # Pipeline by stage donut
    visuals.append(make_donut(
        "pipe_stage",
        column_field("gold_fact_pipeline", "deal_status"),
        measure_field("_Measures", "Pipeline Value"),
        20, CONTENT_Y + 250, 410, 240, "Pipeline by Status",
    ))
    # Budget Variance by category
    visuals.append(make_chart(
        "clusteredColumnChart", "budget_cat",
        column_field("gold_fact_budget", "category"),
        [measure_field("_Measures", "Budget Total"), measure_field("_Measures", "Actual Total")],
        450, CONTENT_Y + 250, 420, 240, "Budget vs Actual",
    ))
    # NPS over time
    visuals.append(make_chart(
        "lineChart", "nps_quarter",
        column_field("gold_fact_nps", "quarter"),
        [measure_field("_Measures", "NPS Score")],
        890, CONTENT_Y + 250, 370, 240, "NPS by Quarter",
    ))
    return visuals


def page_pipeline() -> list[dict]:
    visuals = [make_textbox("Pipeline & CRM", 20, 10, 1240, 48, size=24)]
    visuals += kpi_row([
        ("Pipeline Value", "Pipeline"),
        ("Open Pipeline", "Open"),
        ("Won Revenue", "Won"),
        ("Win Rate", "Win Rate"),
        ("Deal Count", "Deals"),
    ])
    # Slicer: country
    visuals.append(make_slicer(column_field("gold_dim_customer", "country_group"), 20, CONTENT_Y, 240, 70))
    # Pipeline by stage
    visuals.append(make_donut(
        "stage", column_field("gold_fact_pipeline", "stage"),
        measure_field("_Measures", "Pipeline Value"),
        280, CONTENT_Y, 380, 240, "Pipeline by Stage",
    ))
    # Pipeline by owner
    visuals.append(make_chart(
        "clusteredBarChart", "owner",
        column_field("gold_fact_pipeline", "deal_owner"),
        [measure_field("_Measures", "Pipeline Value")],
        680, CONTENT_Y, 580, 240, "Pipeline by Owner",
    ))
    # Deals table
    visuals.append(make_table(
        "deals",
        [
            column_field("gold_fact_pipeline", "deal_name"),
            column_field("gold_dim_customer", "customer_name"),
            column_field("gold_fact_pipeline", "stage"),
            measure_field("_Measures", "Pipeline Value"),
            measure_field("_Measures", "Weighted Pipeline"),
        ],
        20, CONTENT_Y + 250, 800, 240, "Open Deals",
    ))
    # Win rate by source
    visuals.append(make_chart(
        "clusteredColumnChart", "win_source",
        column_field("gold_fact_pipeline", "deal_source"),
        [measure_field("_Measures", "Win Rate")],
        840, CONTENT_Y + 250, 420, 240, "Win Rate by Source",
    ))
    return visuals


def page_marketing() -> list[dict]:
    visuals = [make_textbox("Marketing & Web Analytics", 20, 10, 1240, 48, size=24)]
    visuals += kpi_row([
        ("Total Leads", "Leads"),
        ("Lead Conversion Rate", "Conv Rate"),
        ("Marketing Spend", "Spend"),
        ("Total Sessions", "Sessions"),
        ("Web Conversion Rate", "Web Conv"),
    ])
    # Campaign type donut
    visuals.append(make_donut(
        "camp_type", column_field("gold_dim_campaign", "campaign_type"),
        measure_field("_Measures", "Marketing Spend"),
        20, CONTENT_Y, 400, 240, "Spend by Campaign Type",
    ))
    # Leads by campaign
    visuals.append(make_chart(
        "clusteredBarChart", "leads_campaign",
        column_field("gold_dim_campaign", "campaign_name"),
        [measure_field("_Measures", "Total Leads"), measure_field("_Measures", "Converted Leads")],
        440, CONTENT_Y, 820, 240, "Leads by Campaign",
    ))
    # Sessions by source
    visuals.append(make_chart(
        "clusteredColumnChart", "sess_source",
        column_field("gold_fact_web_sessions", "source"),
        [measure_field("_Measures", "Total Sessions"), measure_field("_Measures", "Total Web Conversions")],
        20, CONTENT_Y + 250, 620, 240, "Web Sessions by Source",
    ))
    # ROI table
    visuals.append(make_table(
        "campaigns",
        [
            column_field("gold_dim_campaign", "campaign_name"),
            column_field("gold_dim_campaign", "campaign_type"),
            measure_field("_Measures", "Marketing Spend"),
            measure_field("_Measures", "Total Leads"),
            measure_field("_Measures", "Avg Cost Per Lead"),
        ],
        660, CONTENT_Y + 250, 600, 240, "Campaign Performance",
    ))
    return visuals


def page_finance() -> list[dict]:
    visuals = [make_textbox("Finance & Budget", 20, 10, 1240, 48, size=24)]
    visuals += kpi_row([
        ("Revenue Actual", "Revenue"),
        ("Gross Profit Actual", "Gross Profit"),
        ("Gross Margin %", "Margin"),
        ("Operating Profit", "Op Profit"),
        ("Budget Variance %", "Variance"),
    ])
    # Slicer year
    visuals.append(make_slicer(column_field("gold_dim_date", "year"), 20, CONTENT_Y, 240, 70))
    # Budget vs Actual by month
    visuals.append(make_chart(
        "lineChart", "ba_month",
        column_field("gold_dim_date", "year_month"),
        [measure_field("_Measures", "Budget Total"), measure_field("_Measures", "Actual Total")],
        280, CONTENT_Y, 980, 240, "Budget vs Actual by Month",
    ))
    # P&L breakdown
    visuals.append(make_table(
        "pnl",
        [
            column_field("gold_fact_budget", "category"),
            measure_field("_Measures", "Budget Total"),
            measure_field("_Measures", "Actual Total"),
            measure_field("_Measures", "Budget Variance"),
            measure_field("_Measures", "Budget Variance %"),
        ],
        20, CONTENT_Y + 250, 620, 240, "P&L by Category",
    ))
    # Department spend
    visuals.append(make_chart(
        "clusteredBarChart", "dept_spend",
        column_field("gold_fact_budget", "department"),
        [measure_field("_Measures", "Actual Total")],
        660, CONTENT_Y + 250, 600, 240, "Actual Spend by Department",
    ))
    return visuals


def page_hr() -> list[dict]:
    visuals = [make_textbox("HR & People", 20, 10, 1240, 48, size=24)]
    visuals += kpi_row([
        ("Total Headcount", "Headcount"),
        ("Total Salary Cost", "Salary Cost"),
        ("Avg Utilization", "Utilization"),
        ("Avg Tenure Years", "Tenure"),
        ("Turnover Rate", "Turnover"),
    ])
    # Headcount by department
    visuals.append(make_chart(
        "clusteredBarChart", "head_dept",
        column_field("gold_dim_employee", "department"),
        [measure_field("_Measures", "Total Headcount")],
        20, CONTENT_Y, 620, 240, "Headcount by Department",
    ))
    # Utilization by department
    visuals.append(make_chart(
        "clusteredColumnChart", "util_dept",
        column_field("gold_fact_hr", "department"),
        [measure_field("_Measures", "Avg Utilization")],
        660, CONTENT_Y, 600, 240, "Utilization by Department",
    ))
    # Salary by role
    visuals.append(make_chart(
        "clusteredBarChart", "sal_role",
        column_field("gold_dim_employee", "role"),
        [measure_field("_Measures", "Total Salary Cost")],
        20, CONTENT_Y + 250, 620, 240, "Salary Cost by Role",
    ))
    # Employee table
    visuals.append(make_table(
        "emp",
        [
            column_field("gold_dim_employee", "first_name"),
            column_field("gold_dim_employee", "last_name"),
            column_field("gold_dim_employee", "department"),
            column_field("gold_dim_employee", "role"),
            column_field("gold_dim_employee", "annual_salary_dkk"),
        ],
        660, CONTENT_Y + 250, 600, 240, "Employee Directory",
    ))
    return visuals


def page_csat() -> list[dict]:
    visuals = [make_textbox("Customer Satisfaction & Support", 20, 10, 1240, 48, size=24)]
    visuals += kpi_row([
        ("NPS Score", "NPS"),
        ("Promoter %", "Promoters"),
        ("Total Tickets", "Tickets"),
        ("SLA Met Rate", "SLA Met"),
        ("Avg Satisfaction Rating", "CSAT"),
    ])
    # NPS by category donut
    visuals.append(make_donut(
        "nps_cat", column_field("gold_fact_nps", "nps_category"),
        measure_field("_Measures", "NPS Responses"),
        20, CONTENT_Y, 400, 240, "NPS Distribution",
    ))
    # Tickets by priority
    visuals.append(make_chart(
        "clusteredColumnChart", "tk_prio",
        column_field("gold_fact_tickets", "priority"),
        [measure_field("_Measures", "Total Tickets")],
        440, CONTENT_Y, 400, 240, "Tickets by Priority",
    ))
    # Tickets by category
    visuals.append(make_donut(
        "tk_cat", column_field("gold_fact_tickets", "category"),
        measure_field("_Measures", "Total Tickets"),
        860, CONTENT_Y, 400, 240, "Tickets by Category",
    ))
    # Ticket detail table
    visuals.append(make_table(
        "tk_table",
        [
            column_field("gold_fact_tickets", "ticket_id"),
            column_field("gold_fact_tickets", "company_name"),
            column_field("gold_fact_tickets", "category"),
            column_field("gold_fact_tickets", "priority"),
            column_field("gold_fact_tickets", "status"),
            measure_field("_Measures", "Avg Response Time Hours"),
        ],
        20, CONTENT_Y + 250, 1240, 240, "Open Tickets",
    ))
    return visuals


def page_quality() -> list[dict]:
    """Medical/regulatory Quality & Compliance page — built from gold_fact_tickets."""
    visuals = [make_textbox("Quality & Compliance", 20, 10, 1240, 48, size=24)]
    visuals += kpi_row([
        ("Critical Tickets",       "Critical"),
        ("SLA Met Rate",           "SLA Met"),
        ("Avg Response Time Hours", "Avg Response"),
        ("Resolution Rate",        "Resolution"),
        ("Avg Resolution Days",    "Avg Days"),
    ])
    # Tickets by category over time
    visuals.append(make_chart(
        "lineChart", "tk_cat_month",
        column_field("gold_dim_date", "year_month"),
        [measure_field("_Measures", "Total Tickets")],
        20, CONTENT_Y, 620, 240, "Tickets over Time",
    ))
    # SLA met by category
    visuals.append(make_chart(
        "clusteredBarChart", "sla_cat",
        column_field("gold_fact_tickets", "category"),
        [measure_field("_Measures", "SLA Met Rate")],
        660, CONTENT_Y, 600, 240, "SLA Met Rate by Category",
    ))
    # Critical / Open ticket table
    visuals.append(make_table(
        "critical_tk",
        [
            column_field("gold_fact_tickets", "ticket_id"),
            column_field("gold_fact_tickets", "company_name"),
            column_field("gold_fact_tickets", "category"),
            column_field("gold_fact_tickets", "priority"),
            column_field("gold_fact_tickets", "status"),
            column_field("gold_fact_tickets", "sla_met"),
            measure_field("_Measures", "Avg Resolution Days"),
        ],
        20, CONTENT_Y + 250, 1240, 240, "Critical Issues",
    ))
    return visuals


PAGE_BUILDERS = {
    "exec":      page_exec,
    "pipeline":  page_pipeline,
    "marketing": page_marketing,
    "finance":   page_finance,
    "hr":        page_hr,
    "csat":      page_csat,
    "quality":   page_quality,
}


def main():
    # Clean existing pages folder (keep only the structure)
    if PAGES.exists():
        for p in PAGES.iterdir():
            if p.is_dir():
                shutil.rmtree(p)

    page_hex_names = []
    enabled_defs = [d for d in PAGE_DEFS if _is_page_enabled(d["key"])]

    for pdef in enabled_defs:
        page_hex = hex_id(f"page_{pdef['key']}")
        page_hex_names.append(page_hex)
        page_dir = PAGES / page_hex
        page_dir.mkdir(parents=True, exist_ok=True)

        # page.json
        page_json = {
            "$schema": SCHEMA_PAGE,
            "name": page_hex,
            "displayName": pdef["displayName"],
            "displayOption": "FitToPage",
            "height": 720,
            "width": 1280,
        }
        (page_dir / "page.json").write_text(json.dumps(page_json, indent=2))

        # visuals — split any visual with _label into [title textbox, shifted chart]
        raw = PAGE_BUILDERS[pdef["key"]]()
        visuals: list[dict] = []
        for v in raw:
            if v.get("_label"):
                label = v.pop("_label")
                pos = v["position"]
                x, y, w = pos["x"], pos["y"], pos["width"]
                visuals.append(make_textbox(label, x, y, w, CHART_TITLE_H - 4, size=12))
                pos["y"] = y + CHART_TITLE_H
                pos["height"] = max(80, pos["height"] - CHART_TITLE_H)
                visuals.append(v)
            else:
                visuals.append(v)
        # Global slicer (top-right corner) — from design_decisions.yaml
        global_slicer = DECISIONS.get("slicers", {}).get("global", {})
        if global_slicer.get("enabled"):
            try:
                tbl, col = global_slicer["field"].split(".", 1)
                visuals.append(make_slicer(column_field(tbl, col), 1100, 10, 160, 48))
            except (KeyError, ValueError):
                pass
        vis_dir = page_dir / "visuals"
        vis_dir.mkdir(exist_ok=True)
        for v in visuals:
            v_dir = vis_dir / v["name"]
            v_dir.mkdir(exist_ok=True)
            (v_dir / "visual.json").write_text(json.dumps(v, indent=2))
        print(f"  {pdef['displayName']}: {len(visuals)} visuals")

    # pages.json
    pages_json = {
        "$schema": SCHEMA_PAGES,
        "pageOrder": page_hex_names,
        "activePageName": page_hex_names[0],
    }
    (PAGES / "pages.json").write_text(json.dumps(pages_json, indent=2))
    print(f"\nWrote {len(PAGE_DEFS)} pages to {PAGES}")


if __name__ == "__main__":
    main()
