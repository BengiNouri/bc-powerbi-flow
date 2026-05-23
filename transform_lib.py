"""transform_lib — Reusable silver + gold helpers for the BC Power BI Flow.

Per-client transform scripts (e.g. transform_<client>.py) import from this lib
and only contain the table-specific orchestration.

Helpers are deliberately small and pure:
- No global state
- No file I/O except save_parquet()
- Type-coerce input dataframes; never mutate
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


# ─── PATHS ──────────────────────────────────────────────────────────────────

def layer_dir(output_root: Path, layer: str) -> Path:
    p = output_root / layer
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_parquet(df: pd.DataFrame, layer_path: Path, name: str) -> None:
    """Write a dataframe to <layer_path>/<name>.parquet and print a 1-line summary."""
    out = layer_path / f"{name}.parquet"
    df.to_parquet(out, index=False)
    print(f"  {layer_path.name}/{name}.parquet -- {len(df):>5} rows, {len(df.columns):>3} cols")


def from_records(records: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(records)


# ─── SILVER — type coercion + cleanup ──────────────────────────────────────

def coerce_numeric(df: pd.DataFrame, cols: Iterable[str], fill: float = 0) -> pd.DataFrame:
    """Coerce columns to numeric, filling NaN with `fill`. Returns a new copy."""
    df = df.copy()
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(fill)
    return df


def coerce_int(df: pd.DataFrame, cols: Iterable[str], fill: int = 0) -> pd.DataFrame:
    """Coerce columns to int64, filling NaN with `fill`. Returns a new copy."""
    df = df.copy()
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(fill).astype(int)
    return df


def coerce_date(df: pd.DataFrame, cols: Iterable[str]) -> pd.DataFrame:
    """Coerce columns to datetime (NaT on parse failure). Returns a new copy."""
    df = df.copy()
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


def derive_date_key(date_col: pd.Series, fallback: int = 19000101) -> pd.Series:
    """Convert a datetime series to YYYYMMDD int (gold dim_date join key)."""
    return date_col.apply(lambda d: int(d.strftime("%Y%m%d")) if pd.notna(d) else fallback)


# ─── GOLD — common derived fields ──────────────────────────────────────────

def derive_status_from_stage(stage: pd.Series, won: str = "closed_won", lost: str = "closed_lost") -> pd.Series:
    """CRM deal stage -> {Won, Lost, Open}."""
    return stage.apply(
        lambda s: "Won" if s == won else "Lost" if s == lost else "Open"
    )


def derive_country_group(country: pd.Series, mapping: dict | None = None) -> pd.Series:
    """ISO country code -> friendly group label."""
    default = {"DK": "Denmark", "GB": "UK", "US": "USA"}
    m = mapping or default
    return country.apply(lambda c: m.get(c, "Other"))


def derive_revenue_segment(revenue: pd.Series, *, enterprise: float = 5_000_000, mid: float = 1_000_000) -> pd.Series:
    """Annual revenue (in DKK) -> Enterprise / Mid-Market / SMB."""
    return revenue.apply(
        lambda r: "Enterprise" if r >= enterprise
        else "Mid-Market" if r >= mid
        else "SMB"
    )


def conformed_customer_key(df: pd.DataFrame, bc_col: str = "bc_customer_number", crm_col: str = "crm_company_id") -> pd.Series:
    """Single customer_key: BC number wins, fallback CRM ID.
    Standard conformed-dimension pattern when client has both BC + HubSpot."""
    if bc_col in df.columns:
        return df[bc_col].fillna(df[crm_col] if crm_col in df.columns else "")
    return df[crm_col] if crm_col in df.columns else pd.Series([""] * len(df))


def compute_tenure_years(hire_date: pd.Series, now: pd.Timestamp | None = None) -> pd.Series:
    """Years between hire_date and now."""
    now = now or pd.Timestamp.now()
    return hire_date.apply(lambda d: round((now - d).days / 365.25, 1) if pd.notna(d) else 0)


def active_status(is_active: pd.Series) -> pd.Series:
    """Boolean is_active -> 'Active' / 'Terminated' string for dim tables."""
    return is_active.apply(lambda a: "Active" if a else "Terminated")


# ─── GOLD — dim_date builder ───────────────────────────────────────────────

def build_dim_date(start_date: str | pd.Timestamp, end_date: str | pd.Timestamp) -> pd.DataFrame:
    """Standard date dimension between [start, end]. Generated per-client based on data range.

    Columns: date, date_key (YYYYMMDD int), year, quarter, month, day, day_name,
             month_name, day_of_week, week_of_year, year_quarter, year_month, is_weekend
    """
    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    df = pd.DataFrame({"date": dates})
    df["date_key"] = derive_date_key(df["date"])
    df["year"] = df["date"].dt.year
    df["quarter"] = df["date"].dt.quarter
    df["month"] = df["date"].dt.month
    df["day"] = df["date"].dt.day
    df["day_name"] = df["date"].dt.day_name()
    df["month_name"] = df["date"].dt.month_name()
    df["day_of_week"] = df["date"].dt.dayofweek
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)
    df["year_quarter"] = df["year"].astype(str) + "-Q" + df["quarter"].astype(str)
    df["year_month"] = df["date"].dt.strftime("%Y-%m")
    df["is_weekend"] = df["day_of_week"].isin([5, 6])
    return df


# ─── VALIDATION ─────────────────────────────────────────────────────────────

def assert_unique_key(df: pd.DataFrame, col: str, table_name: str = "<unknown>") -> None:
    """Raise if `col` isn't a unique surrogate key for the table. Use as a sanity check."""
    if not df[col].is_unique:
        dupes = df[col][df[col].duplicated()].head(5).tolist()
        raise ValueError(f"{table_name}.{col} must be unique; duplicates: {dupes}")


def assert_fk_coverage(fact: pd.DataFrame, dim: pd.DataFrame, fact_col: str, dim_col: str,
                       fact_name: str = "fact", dim_name: str = "dim", min_coverage: float = 0.95) -> None:
    """Warn if more than (1 - min_coverage) of fact rows have no matching dim row."""
    fact_keys = set(fact[fact_col].dropna())
    dim_keys = set(dim[dim_col])
    missing = fact_keys - dim_keys
    if missing:
        coverage = 1 - len(missing) / max(len(fact_keys), 1)
        msg = f"{fact_name}.{fact_col} -> {dim_name}.{dim_col}: {coverage:.1%} coverage ({len(missing)} unmatched)"
        if coverage < min_coverage:
            raise ValueError(f"FK coverage below {min_coverage:.0%}: {msg}")
        print(f"  WARN {msg}")
