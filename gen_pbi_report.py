"""Generate PBI report pages and visuals as JSON in PBIP format.

Spec-driven (v2):
  • Page structure lives in templates/report_spec.example.yaml (or
    output/report_spec.yaml for the current client).
  • design_decisions.yaml still owns colours, fonts, slicers and top-KPIs.
  • All low-level visual builders (make_card, make_chart, ...) follow the
    DO patterns in docs/PBI_PATTERNS.md. They have not changed.

Canvas layout (1280×720):
  • Title row:   y=10,  h=48
  • KPI row:     y=70,  h=110
  • Content:     y=200, h=490
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent
REPORT = ROOT / "output" / "AkseDemoDW" / "AkseDemoDW_v2.Report"
PAGES = REPORT / "definition" / "pages"
DECISIONS_FILE = ROOT / "output" / "branding" / "design_decisions.yaml"

# Spec lookup order: explicit override → client-specific → example fallback
SPEC_CANDIDATES = [
    ROOT / "output" / "report_spec.yaml",
    ROOT / "templates" / "report_spec.example.yaml",
]

SCHEMA_PAGE = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"
SCHEMA_VISUAL = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.7.0/schema.json"
SCHEMA_PAGES = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json"

SUPPORTED_VISUAL_TYPES = {
    "lineChart",
    "clusteredBarChart",
    "clusteredColumnChart",
    "donutChart",
    "tableEx",
    "slicer",
}

# Canvas / KPI defaults — overridable via spec.canvas
DEFAULT_CANVAS = {
    "width": 1280,
    "height": 720,
    "margin_x": 20,
    "title_y": 10,
    "title_h": 48,
    "kpi_y": 70,
    "kpi_h": 110,
    "content_y": 200,
    "content_h": 490,
}

# 5-KPI row geometry — first 4 cards 228px, last 248px (covers right edge)
KPI_X_POSITIONS = [20, 268, 516, 764, 1012]
KPI_W = 228
KPI_LAST_W = 248
KPI_H = 110
KPI_Y = 70
CHART_TITLE_H = 28


# ─── DECISION + SPEC LOADING ──────────────────────────────────────────────────

def load_decisions() -> dict:
    """Load design_decisions.yaml if present, else return defaults."""
    if not DECISIONS_FILE.exists():
        return {"client_name": "Lodværket", "pages": [], "kpi_cards": {}, "slicers": {}}
    try:
        import yaml
    except ImportError:
        return {"client_name": "Lodværket", "pages": [], "kpi_cards": {}, "slicers": {}}
    return yaml.safe_load(DECISIONS_FILE.read_text(encoding="utf-8")) or {}


def load_spec() -> dict:
    """Load the report spec — client override first, then bundled example."""
    try:
        import yaml
    except ImportError:
        raise SystemExit("PyYAML required: pip install pyyaml")

    for candidate in SPEC_CANDIDATES:
        if candidate.exists():
            spec = yaml.safe_load(candidate.read_text(encoding="utf-8"))
            validate_spec(spec, source=candidate)
            return spec

    raise SystemExit(
        f"No report spec found. Looked for:\n  " + "\n  ".join(str(c) for c in SPEC_CANDIDATES)
    )


# ─── SPEC VALIDATION ──────────────────────────────────────────────────────────

class SpecError(ValueError):
    """Raised when report_spec.yaml violates the contract."""


def validate_spec(spec: dict, source: Path) -> None:
    """Enforce the rules documented in templates/report_spec.schema.yaml.

    Fail loudly with the file path and the offending path inside the YAML.
    Silent fallback would produce broken visuals downstream — see
    docs/PBI_PATTERNS.md "Lessons learned" on cost of bad patterns × N visuals.
    """
    if not isinstance(spec, dict):
        raise SpecError(f"{source}: top-level must be a mapping")

    version = spec.get("version")
    if version != 1:
        raise SpecError(f"{source}: unsupported version {version!r} (only v1)")

    canvas = {**DEFAULT_CANVAS, **(spec.get("canvas") or {})}
    width, height = canvas["width"], canvas["height"]

    pages = spec.get("pages") or []
    if not pages:
        raise SpecError(f"{source}: pages[] is empty")

    seen_keys: set[str] = set()
    for pi, page in enumerate(pages):
        ppath = f"pages[{pi}]"
        if "key" not in page or "display_name" not in page or "visuals" not in page:
            raise SpecError(f"{source}: {ppath} missing key/display_name/visuals")
        key = page["key"]
        if key in seen_keys:
            raise SpecError(f"{source}: duplicate page key {key!r}")
        seen_keys.add(key)

        positions: list[tuple[int, int, int, int, str]] = []
        for vi, v in enumerate(page["visuals"]):
            vpath = f"{ppath}.visuals[{vi}]"
            vtype = v.get("type")
            if vtype not in SUPPORTED_VISUAL_TYPES:
                raise SpecError(f"{source}: {vpath} unsupported type {vtype!r}")

            for k in ("id", "x", "y", "w", "h"):
                if k not in v:
                    raise SpecError(f"{source}: {vpath} missing {k!r}")

            x, y, w, h = v["x"], v["y"], v["w"], v["h"]
            if x + w > width or y + h > height:
                raise SpecError(
                    f"{source}: {vpath} ({v['id']}) overflows canvas "
                    f"(x+w={x+w}, y+h={y+h}; canvas={width}×{height})"
                )

            if vtype == "slicer":
                if not v.get("field"):
                    raise SpecError(f"{source}: {vpath} slicer needs `field`")
            elif vtype == "tableEx":
                if not v.get("values"):
                    raise SpecError(f"{source}: {vpath} tableEx needs non-empty `values`")
            else:
                if not v.get("category"):
                    raise SpecError(f"{source}: {vpath} {vtype} needs `category`")
                if not v.get("values"):
                    raise SpecError(f"{source}: {vpath} {vtype} needs non-empty `values`")

            # Field mutual-exclusion (column XOR measure)
            fields_to_check: list[dict] = []
            if v.get("category"):
                fields_to_check.append(v["category"])
            fields_to_check.extend(v.get("values") or [])
            if v.get("field"):
                fields_to_check.append(v["field"])
            for fi, f in enumerate(fields_to_check):
                has_col = "column" in f
                has_meas = "measure" in f
                if has_col == has_meas:
                    raise SpecError(
                        f"{source}: {vpath} field[{fi}] must have exactly one of "
                        f"`column` or `measure` (got column={has_col}, measure={has_meas})"
                    )

            positions.append((x, y, w, h, v["id"]))

        # Overlap detection (axis-aligned rectangle intersection)
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                ax, ay, aw, ah, aid = positions[i]
                bx, by, bw, bh, bid = positions[j]
                if ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by:
                    raise SpecError(
                        f"{source}: {ppath} visuals {aid!r} and {bid!r} overlap"
                    )


# ─── LOW-LEVEL VISUAL BUILDERS (unchanged shape — see docs/PBI_PATTERNS.md) ──

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


def spec_field_to_pbi(spec_field: dict) -> dict:
    """Translate a {table, column} or {table, measure} mapping to a PBI projection."""
    if "measure" in spec_field:
        return measure_field(spec_field["table"], spec_field["measure"])
    return column_field(spec_field["table"], spec_field["column"])


def make_card(measure: str, x: int, y: int, w: int = 228, h: int = 110, label: str | None = None) -> dict:
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
               x: int, y: int, w: int, h: int, title: str | None = None) -> dict:
    visual = {
        "visualType": visual_type,
        "query": {
            "queryState": {
                "Category": {"projections": [category]},
                "Y": {"projections": values},
            }
        },
        "drillFilterOtherVisuals": True,
        "objects": _no_auto_title(),
    }
    result = {
        "$schema": SCHEMA_VISUAL,
        "name": hex_id(f"{visual_type}_{name_suffix}_{x}_{y}"),
        "position": {"x": x, "y": y, "z": 0, "height": h, "width": w, "tabOrder": 0},
        "visual": visual,
    }
    if title:
        result["_label"] = title
    return result


def make_donut(name_suffix: str, category: dict, value: dict, x: int, y: int, w: int, h: int, title: str | None = None) -> dict:
    visual = {
        "visualType": "donutChart",
        "query": {
            "queryState": {
                "Category": {"projections": [category]},
                "Y": {"projections": [value]},
            }
        },
        "drillFilterOtherVisuals": True,
        "objects": _no_auto_title(),
    }
    result = {
        "$schema": SCHEMA_VISUAL,
        "name": hex_id(f"donut_{name_suffix}_{x}_{y}"),
        "position": {"x": x, "y": y, "z": 0, "height": h, "width": w, "tabOrder": 0},
        "visual": visual,
    }
    if title:
        result["_label"] = title
    return result


def make_table(name_suffix: str, fields: list[dict], x: int, y: int, w: int, h: int, title: str | None = None) -> dict:
    visual = {
        "visualType": "tableEx",
        "query": {
            "queryState": {
                "Values": {"projections": fields}
            }
        },
        "drillFilterOtherVisuals": True,
        "objects": _no_auto_title(),
    }
    result = {
        "$schema": SCHEMA_VISUAL,
        "name": hex_id(f"table_{name_suffix}_{x}_{y}"),
        "position": {"x": x, "y": y, "z": 0, "height": h, "width": w, "tabOrder": 0},
        "visual": visual,
    }
    if title:
        result["_label"] = title
    return result


def make_slicer(field: dict, x: int, y: int, w: int = 240, h: int = 70, title: str | None = None) -> dict:
    """PBI slicer uses data role 'Field' (singular), not 'Values'.
    Wrong role = 'Select or drag fields to populate visual'. See PBI_PATTERNS.md."""
    return {
        "$schema": SCHEMA_VISUAL,
        "name": hex_id(f"slicer_{field['queryRef']}_{x}_{y}"),
        "position": {"x": x, "y": y, "z": 0, "height": h, "width": w, "tabOrder": 0},
        "visual": {
            "visualType": "slicer",
            "query": {
                "queryState": {
                    "Field": {"projections": [field]}
                }
            },
            "objects": {
                "data": [{"properties": {"mode": {"expr": {"Literal": {"Value": "'Dropdown'"}}}}}],
                "general": [{"properties": {"orientation": {"expr": {"Literal": {"Value": "1D"}}}}}],
            },
            "drillFilterOtherVisuals": True,
        },
    }


# ─── KPI ROW ──────────────────────────────────────────────────────────────────

_DEFAULT_KPIS: dict[str, list[tuple[str, str]]] = {
    "exec": [
        ("Revenue", "Revenue"),
        ("Gross Margin", "Gross Margin"),
        ("Pipeline Value", "Pipeline"),
        ("NPS Score", "NPS"),
        ("Total Headcount", "Headcount"),
    ],
    "pipeline": [
        ("Pipeline Value", "Pipeline"),
        ("Open Pipeline", "Open"),
        ("Won Revenue", "Won"),
        ("Win Rate", "Win Rate"),
        ("Deal Count", "Deals"),
    ],
    "marketing": [
        ("Total Leads", "Leads"),
        ("Lead Conversion Rate", "Conv Rate"),
        ("Marketing Spend", "Spend"),
        ("Total Sessions", "Sessions"),
        ("Web Conversion Rate", "Web Conv"),
    ],
    "finance": [
        ("Revenue Actual", "Revenue"),
        ("Gross Profit Actual", "Gross Profit"),
        ("Gross Margin %", "Margin"),
        ("Operating Profit", "Op Profit"),
        ("Budget Variance %", "Variance"),
    ],
    "hr": [
        ("Total Headcount", "Headcount"),
        ("Total Salary Cost", "Salary Cost"),
        ("Avg Utilization", "Utilization"),
        ("Avg Tenure Years", "Tenure"),
        ("Turnover Rate", "Turnover"),
    ],
    "csat": [
        ("NPS Score", "NPS"),
        ("Promoter %", "Promoters"),
        ("Total Tickets", "Tickets"),
        ("SLA Met Rate", "SLA Met"),
        ("Avg Satisfaction Rating", "CSAT"),
    ],
    "quality": [
        ("Critical Tickets", "Critical"),
        ("SLA Met Rate", "SLA Met"),
        ("Avg Response Time Hours", "Avg Response"),
        ("Resolution Rate", "Resolution"),
        ("Avg Resolution Days", "Avg Days"),
    ],
    "customer_detail": [
        ("Revenue", "Revenue"),
        ("Pipeline Value", "Pipeline"),
        ("Total Tickets", "Tickets"),
        ("NPS Responses", "NPS Surveys"),
        ("Avg Satisfaction Rating", "CSAT"),
    ],
    "employee_detail": [
        ("Avg Utilization", "Utilization"),
        ("Total Billable Hours", "Billable hrs"),
        ("Total Internal Hours", "Internal hrs"),
        ("Avg Cost Per Billable Hour", "Cost/hr"),
        ("Avg Tenure Years", "Tenure"),
    ],
}


def _decisions_page(decisions: dict, key: str) -> dict:
    for p in decisions.get("pages", []):
        if p.get("key") == key:
            return p
    return {}


def _top_kpis_for(decisions: dict, page_key: str) -> list[tuple[str, str]]:
    pd = _decisions_page(decisions, page_key)
    if pd and pd.get("top_kpis"):
        return [(k["measure"], k.get("label", k["measure"])) for k in pd["top_kpis"][:5]]
    return _DEFAULT_KPIS.get(page_key, _DEFAULT_KPIS["exec"])


def kpi_row(measures: list[tuple[str, str]]) -> list[dict]:
    out: list[dict] = []
    for i, (m, label) in enumerate(measures[:5]):
        w = KPI_LAST_W if i == 4 else KPI_W
        out.append(make_card(m, KPI_X_POSITIONS[i], KPI_Y, w, KPI_H, label))
    return out


# ─── PAGE / VISUAL RENDERING FROM SPEC ────────────────────────────────────────

def render_visual(v: dict) -> dict:
    """Translate one spec visual dict into a PBI visual.json object."""
    vtype = v["type"]
    x, y, w, h = v["x"], v["y"], v["w"], v["h"]
    title = v.get("title")
    vid = v["id"]

    if vtype == "slicer":
        return make_slicer(spec_field_to_pbi(v["field"]), x, y, w, h, title)

    if vtype == "tableEx":
        return make_table(
            vid,
            [spec_field_to_pbi(f) for f in v["values"]],
            x, y, w, h, title,
        )

    if vtype == "donutChart":
        return make_donut(
            vid,
            spec_field_to_pbi(v["category"]),
            spec_field_to_pbi(v["values"][0]),
            x, y, w, h, title,
        )

    # lineChart / clusteredBarChart / clusteredColumnChart
    return make_chart(
        vtype, vid,
        spec_field_to_pbi(v["category"]),
        [spec_field_to_pbi(val) for val in v["values"]],
        x, y, w, h, title,
    )


def render_page(page: dict, client_name: str, decisions: dict) -> list[dict]:
    """Build the full visual list for one page (title, KPIs, then spec visuals)."""
    title_text = page.get("title", page["display_name"]).replace("{client_name}", client_name)
    visuals: list[dict] = [make_textbox(title_text, 20, 10, 1080, 48, size=24)]
    visuals += kpi_row(_top_kpis_for(decisions, page["key"]))
    for v in page.get("visuals", []):
        visuals.append(render_visual(v))
    return visuals


def split_titled_visuals(raw: list[dict]) -> list[dict]:
    """Visuals with `_label` get split into [12pt title textbox, shifted chart].
    Mirrors the behaviour of the old gen_pbi_report.main() loop so structural
    output stays identical."""
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
    return visuals


def append_global_slicer(visuals: list[dict], decisions: dict) -> None:
    """If design_decisions.yaml enables a global slicer, drop it top-right."""
    g = (decisions.get("slicers") or {}).get("global") or {}
    if not g.get("enabled") or not g.get("field"):
        return
    try:
        tbl, col = g["field"].split(".", 1)
    except ValueError:
        return
    visuals.append(make_slicer(column_field(tbl, col), 1100, 10, 160, 48))


def _drill_through_enabled(decisions: dict, key: str) -> bool:
    return key in (decisions.get("interactivity") or {}).get("drill_through_pages", [])


# Pages that are NOT rendered by default when no design_decisions.yaml is
# present. Matches the legacy gating in the pre-spec renderer so output is
# byte-stable across the refactor. The client opts in to these via
# design_decisions.yaml (drill_through pages via interactivity.drill_through_pages;
# quality via pages[] with enabled: true).
DEFAULT_OFF_PAGES = {"quality", "customer_detail", "employee_detail"}


def is_page_enabled(page: dict, decisions: dict) -> bool:
    """Page is rendered if:
      • drill-through page → only when listed in interactivity.drill_through_pages
      • quality (or other DEFAULT_OFF_PAGES) → only when decisions explicitly enables it
      • otherwise → either no decisions.pages[] at all (default-on), or
        decisions.pages[key].enabled == true
    """
    key = page["key"]
    drill_through = bool(page.get("drill_through"))
    if drill_through:
        return _drill_through_enabled(decisions, key)

    dec_pages = decisions.get("pages") or []
    if not dec_pages:
        # No decisions yaml — match the legacy default: quality stays off.
        return key not in DEFAULT_OFF_PAGES
    pd = _decisions_page(decisions, key)
    return bool(pd.get("enabled", False)) if pd else False


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main() -> None:
    decisions = load_decisions()
    spec = load_spec()
    client_name = decisions.get("client_name", "Lodværket")

    if PAGES.exists():
        for p in PAGES.iterdir():
            if p.is_dir():
                shutil.rmtree(p)
    PAGES.mkdir(parents=True, exist_ok=True)

    rendered: list[tuple[str, str]] = []   # (page_hex, display_name)
    for page in spec["pages"]:
        if not is_page_enabled(page, decisions):
            continue

        page_hex = hex_id(f"page_{page['key']}")
        page_dir = PAGES / page_hex
        page_dir.mkdir(parents=True, exist_ok=True)

        page_json = {
            "$schema": SCHEMA_PAGE,
            "name": page_hex,
            "displayName": page["display_name"],
            "displayOption": "FitToPage",
            "height": 720,
            "width": 1280,
        }
        if page.get("drill_through"):
            page_json["visibility"] = "HiddenInViewMode"
        (page_dir / "page.json").write_text(json.dumps(page_json, indent=2))

        raw_visuals = render_page(page, client_name, decisions)
        visuals = split_titled_visuals(raw_visuals)
        append_global_slicer(visuals, decisions)

        vis_dir = page_dir / "visuals"
        vis_dir.mkdir(exist_ok=True)
        for v in visuals:
            v_dir = vis_dir / v["name"]
            v_dir.mkdir(exist_ok=True)
            (v_dir / "visual.json").write_text(json.dumps(v, indent=2))

        rendered.append((page_hex, page["display_name"]))
        print(f"  {page['display_name']}: {len(visuals)} visuals")

    if not rendered:
        print("WARNING: no pages rendered — check design_decisions.yaml enablement", file=sys.stderr)
        return

    pages_json = {
        "$schema": SCHEMA_PAGES,
        "pageOrder": [h for h, _ in rendered],
        "activePageName": rendered[0][0],
    }
    (PAGES / "pages.json").write_text(json.dumps(pages_json, indent=2))
    print(f"\nWrote {len(rendered)} pages to {PAGES}")


if __name__ == "__main__":
    main()
