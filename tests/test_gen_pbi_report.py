"""Tests for gen_pbi_report — validate JSON output structure + yaml wiring."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="module")
def regenerate() -> Path:
    """Trigger gen_pbi_report and return path to the pages folder."""
    import gen_pbi_report  # noqa
    gen_pbi_report.main()
    pages = ROOT / "output" / "AkseDemoDW" / "AkseDemoDW_v2.Report" / "definition" / "pages"
    assert pages.exists()
    return pages


@pytest.mark.unit
def test_imports() -> None:
    """Module imports cleanly."""
    import gen_pbi_report
    assert hasattr(gen_pbi_report, "main")
    assert hasattr(gen_pbi_report, "PAGE_BUILDERS")
    assert hasattr(gen_pbi_report, "_top_kpis_for")


@pytest.mark.unit
def test_default_kpis_complete() -> None:
    """Every page in PAGE_BUILDERS has default KPIs defined."""
    from gen_pbi_report import _DEFAULT_KPIS, PAGE_BUILDERS
    # Drill-through pages have hardcoded KPIs in their builders — exclude
    main_pages = {k for k in PAGE_BUILDERS if "detail" not in k}
    missing = main_pages - set(_DEFAULT_KPIS)
    assert not missing, f"Missing default KPIs for: {missing}"


@pytest.mark.unit
def test_all_default_kpis_have_5_entries() -> None:
    """Each page has exactly 5 KPI definitions."""
    from gen_pbi_report import _DEFAULT_KPIS
    for page, kpis in _DEFAULT_KPIS.items():
        assert len(kpis) == 5, f"{page}: {len(kpis)} KPIs (expected 5)"


@pytest.mark.unit
def test_yaml_loads() -> None:
    """If design_decisions.yaml exists, it loads as a dict."""
    from gen_pbi_report import DECISIONS
    assert isinstance(DECISIONS, dict)


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
def test_every_visual_has_queryref_or_textbox(regenerate: Path) -> None:
    """Every chart visual must have queryRef in its projections (else PBI fails to load)."""
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
                    if "queryRef" not in proj:
                        failures.append(f"{page_dir.name}/{vd.name} {visual_type}.{role}[{i}]")
    assert not failures, f"{len(failures)} projections missing queryRef:\n  " + "\n  ".join(failures[:10])


@pytest.mark.integration
def test_page_count_matches_decisions(regenerate: Path) -> None:
    """Number of enabled pages in pages.json matches what design_decisions.yaml says."""
    from gen_pbi_report import DECISIONS, PAGE_DEFS, _is_page_enabled
    expected = sum(1 for d in PAGE_DEFS if _is_page_enabled(d["key"]))
    data = json.loads((regenerate / "pages.json").read_text(encoding="utf-8"))
    assert len(data["pageOrder"]) == expected, f"pages.json has {len(data['pageOrder'])}, expected {expected}"


@pytest.mark.integration
def test_no_visual_outside_canvas(regenerate: Path) -> None:
    """No visual extends past 1280x720 canvas."""
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
            if right > 1280 + 1 or bottom > 720 + 1:  # 1px tolerance
                failures.append(f"{page_dir.name}/{vd.name}: ends at ({right},{bottom})")
    assert not failures, "Visuals outside canvas:\n  " + "\n  ".join(failures)


@pytest.mark.integration
def test_global_slicer_present_when_enabled(regenerate: Path) -> None:
    """If decisions yaml enables global slicer, every page should have it."""
    from gen_pbi_report import DECISIONS
    if not DECISIONS.get("slicers", {}).get("global", {}).get("enabled"):
        pytest.skip("Global slicer not enabled")
    for page_dir in regenerate.iterdir():
        if not page_dir.is_dir():
            continue
        # Skip drill-through pages
        page_json = json.loads((page_dir / "page.json").read_text(encoding="utf-8"))
        if page_json.get("visibility") == "HiddenInViewMode":
            continue
        vis_dir = page_dir / "visuals"
        slicers = [
            v for v in vis_dir.iterdir()
            if json.loads((v / "visual.json").read_text(encoding="utf-8"))["visual"]["visualType"] == "slicer"
        ]
        assert slicers, f"{page_dir.name}: no slicer visual"
