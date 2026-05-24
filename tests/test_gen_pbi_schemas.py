"""Tests for gen_pbi_schemas — focuses on the fmt() heuristic.

PLAYBOOK_DRYRUN.md gap #14: `roi_pct` values like 15.5 (percent points)
were being formatted as '0.00%' which renders as 1550%. Fix: inspect actual
values; fractions (max abs ≤ 1) keep percent format, percent-point columns
get plain number format.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


@pytest.mark.unit
def test_fraction_pct_gets_percent_format() -> None:
    """A column storing fractions (0-1) for percent display keeps 0.00%."""
    from gen_pbi_schemas import fmt
    sample = pd.Series([0.12, 0.34, 0.78, 0.91])
    assert fmt("double", "conversion_rate", sample=sample) == "0.00%"
    assert fmt("double", "win_pct", sample=sample) == "0.00%"


@pytest.mark.unit
def test_percent_points_get_plain_format() -> None:
    """A column already in percent-points (e.g. 15.5 meaning 15.5%) must NOT
    get the 0.00% format string — that would render 1550%."""
    from gen_pbi_schemas import fmt
    sample = pd.Series([15.5, 32.0, 8.2, 47.9])
    fmtstr = fmt("double", "roi_pct", sample=sample)
    assert fmtstr != "0.00%", f"roi_pct=15.5 must not use 0.00% format (got {fmtstr!r})"
    assert fmtstr == "#,##0.00"


@pytest.mark.unit
def test_dkk_wins_over_pct_in_name() -> None:
    """If a column has both 'pct' and 'dkk' in its name, currency wins.
    Edge case but real — e.g. `budget_pct_dkk` is a kroner amount."""
    from gen_pbi_schemas import fmt
    sample = pd.Series([1000.0, 2500.0])
    assert fmt("double", "budget_pct_dkk", sample=sample) == "#,##0.00"


@pytest.mark.unit
def test_fmt_handles_missing_sample() -> None:
    """Backwards compatibility: callers that don't pass a sample still get a
    result (default to the old behaviour — percent format for pct/rate names)."""
    from gen_pbi_schemas import fmt
    assert fmt("double", "conversion_rate") == "0.00%"
    assert fmt("int64", "deal_count") == "#,##0"


@pytest.mark.unit
def test_fmt_handles_empty_sample() -> None:
    """An empty Series shouldn't crash — should fall back to the legacy default."""
    from gen_pbi_schemas import fmt
    sample = pd.Series([], dtype="float64")
    assert fmt("double", "conversion_rate", sample=sample) == "0.00%"


@pytest.mark.unit
def test_fmt_handles_all_nan_sample() -> None:
    """A Series of only NaN shouldn't crash. We default to plain number — that's
    the safer choice: a falsely-applied 0.00% format multiplies the displayed
    value by 100, which is the bug we set out to fix. A falsely-applied plain
    number format just shows the number, which is at worst ugly, never wrong."""
    from gen_pbi_schemas import fmt
    sample = pd.Series([float("nan"), float("nan")])
    assert fmt("double", "conversion_rate", sample=sample) == "#,##0.00"


@pytest.mark.unit
def test_boundary_value_one_treated_as_fraction() -> None:
    """A column with max value exactly 1.0 stays a fraction.
    Edge case: a rate that hit 100% once (e.g. SLA met = 1.0)."""
    from gen_pbi_schemas import fmt
    sample = pd.Series([0.5, 0.8, 1.0, 0.9])
    assert fmt("double", "sla_met_rate", sample=sample) == "0.00%"


@pytest.mark.unit
def test_negative_percent_points_detected() -> None:
    """Variance percentages can be negative — abs() ensures detection works."""
    from gen_pbi_schemas import fmt
    sample = pd.Series([-15.5, 2.3, -47.0, 8.1])  # max abs = 47 > 1
    assert fmt("double", "variance_pct", sample=sample) == "#,##0.00"
