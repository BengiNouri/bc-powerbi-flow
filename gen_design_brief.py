"""Phase 0c — Generate design_brief.md for client review.

Output:  output/branding/design_brief.md
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
BRAND_FILE = ROOT / "output" / "branding" / "brand_assets.json"
OUT = ROOT / "output" / "branding" / "design_brief.md"

CONFIDENCE_BADGE = {
    "high":   "✅ Høj",
    "medium": "🟡 Medium — bekræft venligst",
    "low":    "🔴 Lav — vi har brug for jeres input",
}

PAGE_TEMPLATE = [
    {
        "title": "1. Executive Dashboard",
        "kpis":  "Revenue · Gross Margin · Pipeline · NPS · Headcount",
        "charts": "Revenue trend, Revenue by industry, Pipeline by status, Budget vs Actual, NPS by quarter",
        "slicer": "Year",
    },
    {
        "title": "2. Pipeline & CRM",
        "kpis":  "Pipeline Value · Open · Won · Win Rate · Deals",
        "charts": "Stage donut, Owner bar, Open deals table, Win rate by source",
        "slicer": "Country",
    },
    {
        "title": "3. Marketing & Web",
        "kpis":  "Leads · Conv Rate · Spend · Sessions · Web Conv",
        "charts": "Spend by type donut, Leads by campaign, Sessions by source, Campaign ROI table",
        "slicer": "Campaign type",
    },
    {
        "title": "4. Finance & Budget",
        "kpis":  "Revenue · Gross Profit · Margin · Op Profit · Variance",
        "charts": "Budget vs Actual trend, P&L by category, Spend by department",
        "slicer": "Year, Department",
    },
    {
        "title": "5. HR & People",
        "kpis":  "Headcount · Salary Cost · Utilization · Tenure · Turnover",
        "charts": "Headcount by dept, Utilization by dept, Salary by role, Employee directory",
        "slicer": "Department",
    },
    {
        "title": "6. NPS & Support",
        "kpis":  "NPS · Promoters · Tickets · SLA Met · CSAT",
        "charts": "NPS donut, Tickets by priority, Tickets by category, Open tickets table",
        "slicer": "Priority",
    },
]


def swatch(hex_color: str) -> str:
    return f"`{hex_color}` ![swatch](https://img.shields.io/badge/-{hex_color[1:]}-{hex_color[1:]}?style=flat-square)"


def main() -> None:
    if not BRAND_FILE.exists():
        raise SystemExit(f"Missing {BRAND_FILE}. Run extract_brand.py first.")
    b = json.loads(BRAND_FILE.read_text(encoding="utf-8"))

    lines: list[str] = []
    lines.append(f"# {b['client_name']} — Power BI rapport design brief")
    lines.append("")
    lines.append(f"> Auto-genereret fra {b['client_url']} den {date.today().isoformat()}.")
    lines.append("> Læs igennem og marker hvad der skal justeres inden vi går videre.")
    lines.append("")
    lines.append("## Brand")
    lines.append("")
    lines.append("| Element     | Opdaget                              | Sikkerhed |")
    lines.append("|-------------|--------------------------------------|-----------|")
    logo_md = f"![logo]({b['logo_local']})" if b.get("logo_local") else "*(ingen logo fundet)*"
    lines.append(f"| Logo        | {logo_md}                            | {CONFIDENCE_BADGE.get(b['confidence'].get('logo'), '—')} |")
    lines.append(f"| Primær      | {swatch(b['colors']['primary'])}     | {CONFIDENCE_BADGE.get(b['confidence'].get('primary_color'), '—')} |")
    lines.append(f"| Sekundær    | {swatch(b['colors']['secondary'])}   | {CONFIDENCE_BADGE.get(b['confidence'].get('secondary_color'), '—')} |")
    lines.append(f"| Font        | **{b['fonts']['heading']}**          | {CONFIDENCE_BADGE.get(b['confidence'].get('fonts'), '—')} |")
    lines.append(f"| Sprog       | {b.get('language', 'da-DK')}         | — |")
    lines.append("")

    medium_or_low = [k for k, v in b["confidence"].items() if v in ("medium", "low")]
    if medium_or_low:
        lines.append("> ⚠️ **Bekræft venligst:**")
        for k in medium_or_low:
            human = k.replace("_", " ").capitalize()
            lines.append(f"> - {human} — {CONFIDENCE_BADGE.get(b['confidence'][k])}")
        lines.append("")

    if b.get("warnings"):
        lines.append("## Advarsler fra auto-extraction")
        lines.append("")
        for w in b["warnings"]:
            lines.append(f"- ⚠️ {w}")
        lines.append("")

    lines.append("## Rapport-struktur (6 sider)")
    lines.append("")
    for p in PAGE_TEMPLATE:
        lines.append(f"### {p['title']}")
        lines.append(f"**KPIs:** {p['kpis']}  ")
        lines.append(f"**Charts:** {p['charts']}  ")
        lines.append(f"**Slicer:** {p['slicer']}")
        lines.append("")

    lines.append("## Hvad du kan ændre")
    lines.append("")
    lines.append("- **Farver:** Send os de korrekte hex-koder hvis vi har ramt forkert")
    lines.append("- **Sider/KPIs:** Skal en KPI byttes ud eller en side fjernes?")
    lines.append("- **Logo:** Skal vi bruge en anden version (lys/mørk)?")
    lines.append("- **Sprog:** Dansk eller engelsk labels?")
    lines.append("")
    lines.append("Svar pr. mail eller marker direkte i denne fil. Vi bygger rapporten færdig når du har godkendt.")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}  ({len(lines)} lines)")


if __name__ == "__main__":
    main()
