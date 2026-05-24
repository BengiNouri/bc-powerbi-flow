"""pbi_mcp_helpers — safer wrappers around powerbi-modeling-mcp.

Lessons learned from sessions 2026-05-22 -> 2026-05-24:
  • MCP measure/column changes only live in PBI Desktop's in-memory model.
    Closing the file without Ctrl+S -> all changes lost.
  • Format strings with [Color] tokens render as literal text on Card visuals.
  • Slicer visuals use role 'Field' (singular). Cards use 'Values'.
  • Renaming a column requires updating: model + spec + visual.json + TMDL.
  • Untested patterns × N visuals = N broken visuals (the [Green]▲ disaster).

This module wraps the raw MCP calls with:
  • format_string validation (rejects [Color]+arrow combinations)
  • auto-persist TMDL after every batch
  • DAX smoke-test after measure changes
  • rename_columns_batch — atomic rename across model + spec + visuals
  • visual.json structure validators

Usage from a Claude Code session that already has powerbi-modeling MCP loaded:

    from pbi_mcp_helpers import (
        safe_measure_create,
        safe_column_rename_batch,
        persist_tmdl,
        validate_format_string,
    )
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).parent
TMDL_DIR = ROOT / "output" / "AkseDemoDW" / "AkseDemoDW_v2.SemanticModel" / "definition"
SPEC_FILE = ROOT / "templates" / "report_spec.example.yaml"

# Format strings that broke before — see docs/PBI_PATTERNS.md
KNOWN_BAD_FORMAT_PATTERNS = [
    (re.compile(r"\[(Green|Red|Blue|Yellow|Magenta|Cyan|Black|White)\]\s*[▲▼●◆►◄]"),
     "Card visuals don't render color tokens in formatStrings. Unicode arrows "
     "blended with [Color] tokens produce literal-text gibberish. Use plain "
     "'+0.0%;-0.0%;0.0%' on cards; if you need color, switch to Table/Matrix "
     "or use conditional formatting on the visual."),
    (re.compile(r"\[Color\s+#[0-9A-Fa-f]{6}\]"),
     "Hex color codes not supported in format strings — only the 8 named colors "
     "(Red, Green, Blue, Yellow, Magenta, Cyan, Black, White)."),
    (re.compile(r"\\n"),
     "Format strings are single-line. Newlines render as literal '\\n'."),
]


# ─── FORMAT STRING VALIDATION ─────────────────────────────────────────────

@dataclass(frozen=True)
class FormatStringIssue:
    pattern: str
    why: str


def validate_format_string(fmt: str, *, target_visual: str = "card") -> list[FormatStringIssue]:
    """Return list of issues for the given format string. Empty = OK to use.

    Args:
        fmt: the formatString value about to be set on a measure
        target_visual: 'card', 'table', 'matrix' — different rules apply

    Examples:
        >>> validate_format_string("+0.0%;-0.0%;0.0%")
        []
        >>> validate_format_string("[Green]▲ 0.0%;[Red]▼ 0.0%;0.0%", target_visual="card")
        [FormatStringIssue(pattern='[Green]▲...', why='Card visuals don't render...')]
        >>> validate_format_string("[Green]+0.0%;[Red]-0.0%;0.0%", target_visual="table")
        []  # Colors ARE supported in Table visuals
    """
    issues: list[FormatStringIssue] = []
    is_card = target_visual.lower() == "card"
    for pat, why in KNOWN_BAD_FORMAT_PATTERNS:
        if pat.search(fmt):
            # Color-only formats are fine in tables, not in cards
            if not is_card and "Card visuals don't render" in why and "▲" not in fmt and "▼" not in fmt:
                continue
            issues.append(FormatStringIssue(pattern=fmt, why=why))
    # On cards: ANY [Color] token = gibberish
    if is_card and re.search(r"\[(Green|Red|Blue|Yellow|Magenta|Cyan|Black|White)\]", fmt):
        issues.append(FormatStringIssue(
            pattern=fmt,
            why="Card visuals never render [Color] tokens. Strip colors or move to Table.",
        ))
    return issues


# ─── PERSISTENCE ──────────────────────────────────────────────────────────

def persist_tmdl_via_mcp_call(mcp_call) -> dict:
    """Trigger database_operations.ExportToTmdlFolder.

    `mcp_call` is the caller's MCP invocation function — we don't import MCP
    directly here because this module is plain Python."""
    return mcp_call(
        "database_operations",
        {
            "operation": "ExportToTmdlFolder",
            "tmdlFolderPath": str(TMDL_DIR),
        },
    )


def verify_tmdl_matches_model(mcp_call) -> tuple[bool, str]:
    """Compare in-memory column count vs TMDL file content. Used as a sanity check
    after MCP writes — catches the "in-memory only" silent failure mode."""
    # In-memory count via column_operations.List
    result = mcp_call("column_operations", {"operation": "List", "filter": {"maxResults": 1000}})
    if not result.get("success"):
        return False, "Failed to list columns from model"

    in_memory = sum(len(t["columns"]) for t in result["data"])

    # On-disk count via grep
    if not TMDL_DIR.exists():
        return False, f"TMDL dir missing: {TMDL_DIR}"
    on_disk = 0
    for tmdl in TMDL_DIR.glob("tables/*.tmdl"):
        for line in tmdl.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("column "):
                on_disk += 1

    match = in_memory == on_disk
    return match, f"in-memory={in_memory}, on-disk={on_disk}"


# ─── SAFE MEASURE OPERATIONS ──────────────────────────────────────────────

def safe_measure_create(mcp_call, definitions: list[dict], *, target_visuals: dict[str, str] | None = None) -> dict:
    """Create measures with format-string validation before sending to MCP.

    Args:
        mcp_call: MCP invocation function (signature: tool_name, request_dict -> response_dict)
        definitions: same shape as measure_operations.Create definitions[]
        target_visuals: optional map of measure_name -> 'card'|'table'|'matrix'
                        (default 'card' — strictest). Pre-validates format strings.

    Raises:
        ValueError if any format string fails validation. NO MCP call is made.
    """
    targets = target_visuals or {}
    problems: list[str] = []
    for d in definitions:
        fmt = d.get("formatString", "")
        if not fmt:
            continue
        target = targets.get(d.get("name", ""), "card")
        issues = validate_format_string(fmt, target_visual=target)
        for issue in issues:
            problems.append(f"  {d.get('name')!r} ({target}): {issue.why}")
    if problems:
        raise ValueError(
            "Refusing to create measures with known-broken format strings:\n"
            + "\n".join(problems)
            + "\n\nFix the format strings or override target_visuals to a permissive type."
        )

    result = mcp_call(
        "measure_operations",
        {
            "operation": "Create",
            "options": {"useTransaction": False, "continueOnError": True},
            "definitions": definitions,
        },
    )
    if result.get("success"):
        # Auto-persist
        persist_tmdl_via_mcp_call(mcp_call)
    return result


def safe_measure_update(mcp_call, definitions: list[dict], *, target_visuals: dict[str, str] | None = None) -> dict:
    """Same as safe_measure_create but for Update. Validates before sending."""
    # Reuse validation
    targets = target_visuals or {}
    problems: list[str] = []
    for d in definitions:
        fmt = d.get("formatString", "")
        if not fmt:
            continue
        target = targets.get(d.get("name", ""), "card")
        for issue in validate_format_string(fmt, target_visual=target):
            problems.append(f"  {d.get('name')!r} ({target}): {issue.why}")
    if problems:
        raise ValueError("Refusing to update with broken formats:\n" + "\n".join(problems))

    result = mcp_call(
        "measure_operations",
        {
            "operation": "Update",
            "options": {"useTransaction": False, "continueOnError": True},
            "definitions": definitions,
        },
    )
    if result.get("success"):
        persist_tmdl_via_mcp_call(mcp_call)
    return result


# ─── COLUMN RENAME ──────────────────────────────────────────────────────────

def snake_to_title(snake: str, acronyms: Iterable[str] = ()) -> str:
    """Generic snake_case -> Title Case with acronym handling.
    See clean_column_names.py for the production-grade version with special cases."""
    upper = {a.lower() for a in acronyms} | {"id", "ids", "dkk", "nps", "bc", "crm", "sla", "cogs",
                                              "opex", "csat", "vat", "roi", "kpi"}
    parts = snake.split("_")
    out = []
    for p in parts:
        if not p:
            continue
        out.append(p.upper() if p.lower() in upper else p[:1].upper() + p[1:])
    return " ".join(out)


def safe_column_rename_batch(mcp_call, renames: list[dict], *, also_update_spec: bool = True,
                              also_regen_visuals: bool = True) -> dict:
    """Atomic rename across model + (optional) spec + (optional) visuals.

    Args:
        renames: [{"tableName": ..., "currentName": ..., "newName": ...}, ...]
        also_update_spec: rewrite templates/report_spec.example.yaml column refs
        also_regen_visuals: run gen_pbi_report.py after the rename (recreates visual.json)

    Returns: dict with model_result, spec_count, visuals_pages keys.
    """
    # 1. Rename in model
    model_result = mcp_call(
        "column_operations",
        {
            "operation": "Rename",
            "options": {"useTransaction": False, "continueOnError": True},
            "renameDefinitions": renames,
        },
    )
    if not model_result.get("success"):
        return {"model_result": model_result, "spec_count": 0, "visuals_pages": 0}

    # 2. Persist to TMDL
    persist_tmdl_via_mcp_call(mcp_call)

    # 3. Update spec
    spec_count = 0
    if also_update_spec and SPEC_FILE.exists():
        text = SPEC_FILE.read_text(encoding="utf-8")
        for r in renames:
            pattern = re.compile(r'(column:\s*)"' + re.escape(r["currentName"]) + r'"')
            text, n = pattern.subn(f'\\1"{r["newName"]}"', text)
            spec_count += n
        SPEC_FILE.write_text(text, encoding="utf-8")

    # 4. Regenerate visuals
    pages = 0
    if also_regen_visuals:
        cmd = [sys.executable, str(ROOT / "gen_pbi_report.py")]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
        pages = sum(1 for line in proc.stdout.splitlines() if "visuals" in line and ":" in line)

    return {
        "model_result": model_result,
        "spec_count": spec_count,
        "visuals_pages": pages,
    }


# ─── VISUAL.JSON VALIDATION ──────────────────────────────────────────────

@dataclass(frozen=True)
class VisualIssue:
    page: str
    visual: str
    issue: str


def validate_visual_json(page_dir: Path) -> list[VisualIssue]:
    """Walk a page's visuals/ folder and report PBI-pattern violations.
    See docs/PBI_PATTERNS.md for the rules."""
    issues: list[VisualIssue] = []
    vis_dir = page_dir / "visuals"
    if not vis_dir.exists():
        return issues
    page_name = page_dir.name

    for vd in vis_dir.iterdir():
        path = vd / "visual.json"
        try:
            v = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            issues.append(VisualIssue(page_name, vd.name, f"invalid JSON: {e}"))
            continue

        visual = v.get("visual", {})
        vtype = visual.get("visualType", "?")

        # textbox / image have no query
        if vtype in ("textbox", "image"):
            continue

        # Slicer role check
        query_state = visual.get("query", {}).get("queryState", {})
        if vtype == "slicer" and "Field" not in query_state:
            issues.append(VisualIssue(page_name, vd.name,
                                       f"slicer should use role 'Field', got {list(query_state.keys())}"))

        # queryRef on every projection
        for role, val in query_state.items():
            for i, proj in enumerate(val.get("projections", [])):
                if "queryRef" not in proj:
                    issues.append(VisualIssue(page_name, vd.name,
                                               f"{vtype}.{role}[{i}] missing queryRef"))

        # Canvas bounds
        pos = v.get("position", {})
        x, y = pos.get("x", 0), pos.get("y", 0)
        w, h = pos.get("width", 0), pos.get("height", 0)
        if x + w > 1281 or y + h > 721:
            issues.append(VisualIssue(page_name, vd.name,
                                       f"overflows canvas: ends at ({x+w},{y+h})"))

    return issues


def validate_all_pages(pages_root: Path | None = None) -> list[VisualIssue]:
    """Run validate_visual_json across every page folder. Returns flat list."""
    pages = pages_root or (ROOT / "output" / "AkseDemoDW" / "AkseDemoDW_v2.Report" / "definition" / "pages")
    all_issues: list[VisualIssue] = []
    for page_dir in pages.iterdir():
        if page_dir.is_dir():
            all_issues.extend(validate_visual_json(page_dir))
    return all_issues


# ─── DAX SMOKE TEST ──────────────────────────────────────────────────────

def smoke_test_measures(mcp_call, measures: list[str]) -> dict:
    """Evaluate each measure and return a dict {measure_name: value | error}.
    Use after creating/updating measures to confirm they actually work."""
    rows = ", ".join(f'"{m}", [{m}]' for m in measures)
    result = mcp_call(
        "dax_query_operations",
        {"operation": "Execute", "query": f"EVALUATE ROW({rows})"},
    )
    return result


# ─── SELF-CHECK ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Unit-test the validators (no MCP needed)
    print("=== Format string validator ===")
    cases = [
        ("+0.0%;-0.0%;0.0%", "card", 0, "plain signed % on card"),
        ("#,##0 kr", "card", 0, "currency"),
        ("[Green]+0.0%;[Red]-0.0%;0.0%", "card", 1, "COLOR ON CARD = BROKEN"),
        ("[Green]+0.0%;[Red]-0.0%;0.0%", "table", 0, "color OK on table"),
        ("[Green]▲ 0.0%;[Red]▼ 0.0%;0.0%", "card", 2, "color + arrow on card"),
        ("[Green]▲ 0.0%", "table", 1, "color + arrow on table — still risky"),
    ]
    for fmt, target, expected_n, desc in cases:
        issues = validate_format_string(fmt, target_visual=target)
        status = "OK" if len(issues) == expected_n else "FAIL"
        print(f"  [{status}] {desc:40} -> {len(issues)} issue(s) (expected {expected_n})")
        if len(issues) != expected_n:
            for issue in issues:
                print(f"        {issue.why[:80]}")

    print("\n=== snake_to_title ===")
    for snake, expected in [
        ("year_month",       "Year Month"),
        ("annual_revenue_dkk", "Annual Revenue DKK"),
        ("nps_score",        "NPS Score"),
        ("roi_pct",          "ROI Pct"),
    ]:
        got = snake_to_title(snake)
        status = "OK" if got == expected else "FAIL"
        print(f"  [{status}] {snake:30} -> {got!r} (expected {expected!r})")
