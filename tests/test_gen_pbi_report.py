"""Tests for gen_pbi_report — validate spec contract + JSON output structure.

The renderer is now spec-driven (see templates/report_spec.example.yaml).
These tests verify:
  • The module imports and exposes the new contract (`load_spec`, `validate_spec`, …)
  • The bundled example spec validates and renders without errors
  • Every projection has queryRef + nativeQueryRef (required by PBI)
  • No visual extends past the 1280×720 canvas
  • Spec validation rejects malformed input loudly (not silently)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


# ─── FIXTURES ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def regenerate() -> Path:
    """Trigger gen_pbi_report.main() and return path to the pages folder."""
    import gen_pbi_report
    gen_pbi_report.main()
    pages = ROOT / "output" / "AkseDemoDW" / "AkseDemoDW_v2.Report" / "definition" / "pages"
    assert pages.exists()
    return pages


@pytest.fixture(scope="module")
def example_spec() -> dict:
    """Load the bundled example spec as a dict."""
    import yaml
    return yaml.safe_load((ROOT / "templates" / "report_spec.example.yaml").read_text(encoding="utf-8"))


# ─── UNIT TESTS ───────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_imports() -> None:
    """Module imports cleanly and exposes the new spec-driven API."""
    import gen_pbi_report
    assert hasattr(gen_pbi_report, "main")
    assert hasattr(gen_pbi_report, "load_spec")
    assert hasattr(gen_pbi_report, "validate_spec")
    assert hasattr(gen_pbi_report, "render_page")
    assert hasattr(gen_pbi_report, "_DEFAULT_KPIS")


@pytest.mark.unit
def test_default_kpis_have_5_entries() -> None:
    """Each page key in _DEFAULT_KPIS has exactly 5 KPI definitions."""
    from gen_pbi_report import _DEFAULT_KPIS
    for page, kpis in _DEFAULT_KPIS.items():
        assert len(kpis) == 5, f"{page}: {len(kpis)} KPIs (expected 5)"


@pytest.mark.unit
def test_example_spec_validates(example_spec: dict) -> None:
    """The bundled example spec must pass validation. If this fails, the
    refactor has broken the regression baseline."""
    from gen_pbi_report import validate_spec
    validate_spec(example_spec, source=Path("templates/report_spec.example.yaml"))


@pytest.mark.unit
def test_example_spec_covers_default_kpi_pages(example_spec: dict) -> None:
    """Every page key in _DEFAULT_KPIS appears in the example spec, and
    every spec page has KPIs defined. This catches drift between the two."""
    from gen_pbi_report import _DEFAULT_KPIS
    spec_keys = {p["key"] for p in example_spec["pages"]}
    kpi_keys = set(_DEFAULT_KPIS.keys())
    missing_in_spec = kpi_keys - spec_keys
    missing_kpis = spec_keys - kpi_keys
    assert not missing_in_spec, f"_DEFAULT_KPIS has keys not in example spec: {missing_in_spec}"
    assert not missing_kpis, f"Example spec has pages without _DEFAULT_KPIS: {missing_kpis}"


@pytest.mark.unit
def test_validate_rejects_overflow() -> None:
    """A visual outside the canvas must be rejected with SpecError."""
    from gen_pbi_report import validate_spec, SpecError
    bad = {
        "version": 1,
        "pages": [{
            "key": "p", "display_name": "P", "visuals": [
                {"type": "lineChart", "id": "v", "x": 1000, "y": 200, "w": 400, "h": 240,
                 "category": {"table": "t", "column": "c"},
                 "values": [{"table": "_Measures", "measure": "m"}]}
            ]
        }]
    }
    with pytest.raises(SpecError, match="overflows"):
        validate_spec(bad, source=Path("/test"))


@pytest.mark.unit
def test_validate_rejects_overlap() -> None:
    """Two visuals overlapping on the same page must be rejected."""
    from gen_pbi_report import validate_spec, SpecError
    bad = {
        "version": 1,
        "pages": [{
            "key": "p", "display_name": "P", "visuals": [
                {"type": "lineChart", "id": "a", "x": 20, "y": 200, "w": 400, "h": 240,
                 "category": {"table": "t", "column": "c"},
                 "values": [{"table": "_Measures", "measure": "m"}]},
                {"type": "lineChart", "id": "b", "x": 100, "y": 300, "w": 400, "h": 240,
                 "category": {"table": "t", "column": "c"},
                 "values": [{"table": "_Measures", "measure": "m"}]},
            ]
        }]
    }
    with pytest.raises(SpecError, match="overlap"):
        validate_spec(bad, source=Path("/test"))


@pytest.mark.unit
def test_validate_rejects_unsupported_type() -> None:
    """Unknown visual types must be rejected."""
    from gen_pbi_report import validate_spec, SpecError
    bad = {
        "version": 1,
        "pages": [{
            "key": "p", "display_name": "P", "visuals": [
                {"type": "fancyChart", "id": "v", "x": 20, "y": 200, "w": 400, "h": 240}
            ]
        }]
    }
    with pytest.raises(SpecError, match="unsupported type"):
        validate_spec(bad, source=Path("/test"))


@pytest.mark.unit
def test_validate_rejects_duplicate_page_keys() -> None:
    """Reusing a page key must fail."""
    from gen_pbi_report import validate_spec, SpecError
    bad = {
        "version": 1,
        "pages": [
            {"key": "p", "display_name": "P1", "visuals": []},
            {"key": "p", "display_name": "P2", "visuals": []},
        ],
    }
    with pytest.raises(SpecError, match="duplicate page key"):
        validate_spec(bad, source=Path("/test"))


@pytest.mark.unit
def test_validate_rejects_field_with_both_column_and_measure() -> None:
    """A field cannot be both column and measure."""
    from gen_pbi_report import validate_spec, SpecError
    bad = {
        "version": 1,
        "pages": [{
            "key": "p", "display_name": "P", "visuals": [
                {"type": "lineChart", "id": "v", "x": 20, "y": 200, "w": 400, "h": 240,
                 "category": {"table": "t", "column": "c", "measure": "m"},
                 "values": [{"table": "_Measures", "measure": "m"}]},
            ]
        }]
    }
    with pytest.raises(SpecError, match="exactly one of"):
        validate_spec(bad, source=Path("/test"))


# ─── INTEGRATION TESTS ────────────────────────────────────────────────────────

@pytest.mark.integration
def test_pages_json_valid(regenerate: Path) -> None:
    """pages.json is valid JSON and references all generated page folders."""
    pages_json = regenerate / "pages.json"
    data = json.loads(pages_json.read_text(encoding="utf-8"))
    assert "pageOrder" in data
    assert "activePageName" in data
    for hex_id in data["pageOrder"]:
        assert (regenerate / hex_id).is_dir(), f"page folder missing for {hex_id}"


@pytest.mark.integration
def test_every_projection_has_queryref(regenerate: Path) -> None:
    """Every chart visual must have queryRef in its projections.
    docs/PBI_PATTERNS.md: 'Required property queryRef was not included' = fatal."""
    failures: list[str] = []
    for page_dir in regenerate.iterdir():
        if not page_dir.is_dir():
            continue
        vis_dir = page_dir / "visuals"
        if not vis_dir.exists():
            continue
        for vd in vis_dir.iterdir():
            v = json.loads((vd / "visual.json").read_text(encoding="utf-8"))
            visual_type = v["visual"]["visualType"]
            if visual_type in ("textbox", "image"):
                continue
            query = v["visual"].get("query", {}).get("queryState", {})
            for role, val in query.items():
                for i, proj in enumerate(val.get("projections", [])):
                    if "queryRef" not in proj or "nativeQueryRef" not in proj:
                        failures.append(f"{page_dir.name}/{vd.name} {visual_type}.{role}[{i}]")
    assert not failures, f"{len(failures)} projections missing queryRef/nativeQueryRef:\n  " + "\n  ".join(failures[:10])


@pytest.mark.integration
def test_no_visual_outside_canvas(regenerate: Path) -> None:
    """No visual extends past 1280×720 canvas (renderer applies title-shift —
    titled charts get +28px in y and -28px in height; renderer must keep them in bounds)."""
    failures: list[str] = []
    for page_dir in regenerate.iterdir():
        if not page_dir.is_dir():
            continue
        vis_dir = page_dir / "visuals"
        if not vis_dir.exists():
            continue
        for vd in vis_dir.iterdir():
            v = json.loads((vd / "visual.json").read_text(encoding="utf-8"))
            pos = v["position"]
            right = pos["x"] + pos["width"]
            bottom = pos["y"] + pos["height"]
            if right > 1280 + 1 or bottom > 720 + 1:
                failures.append(f"{page_dir.name}/{vd.name}: ends at ({right},{bottom})")
    assert not failures, "Visuals outside canvas:\n  " + "\n  ".join(failures)


@pytest.mark.integration
def test_slicer_uses_field_role(regenerate: Path) -> None:
    """Slicers must use the singular 'Field' role, NOT 'Values'.
    docs/PBI_PATTERNS.md: wrong role = 'Select or drag fields to populate visual'."""
    failures: list[str] = []
    for page_dir in regenerate.iterdir():
        if not page_dir.is_dir():
            continue
        vis_dir = page_dir / "visuals"
        if not vis_dir.exists():
            continue
        for vd in vis_dir.iterdir():
            v = json.loads((vd / "visual.json").read_text(encoding="utf-8"))
            if v["visual"]["visualType"] != "slicer":
                continue
            states = set(v["visual"].get("query", {}).get("queryState", {}).keys())
            if states != {"Field"}:
                failures.append(f"{page_dir.name}/{vd.name}: roles={states}")
    assert not failures, "Slicers with wrong role:\n  " + "\n  ".join(failures)
