"""Generate PBI table schemas from parquet files for MCP table creation."""
import json
from pathlib import Path

import pandas as pd

GOLD = Path(__file__).parent / "output" / "gold"

# pandas dtype -> PBI dataType
DTYPE_MAP = {
    "int64": "int64",
    "Int64": "int64",
    "int32": "int64",
    "float64": "double",
    "float32": "double",
    "bool": "boolean",
    "object": "string",
    "datetime64[ns]": "dateTime",
}


def pbi_type(dtype: str, col_name: str) -> str:
    s = str(dtype)
    if "date" in s.lower():
        return "dateTime"
    if s in DTYPE_MAP:
        return DTYPE_MAP[s]
    # heuristics by name
    if col_name.endswith("_dkk") or col_name.endswith("_pct") or col_name.endswith("_rate"):
        return "double"
    if col_name.endswith("_key") or col_name.endswith("_id") or col_name in ("year", "month", "day", "quarter", "headcount"):
        return "int64"
    return "string"


def fmt(dtype: str, col: str, sample: "pd.Series | None" = None) -> str:
    """Pick a PBI formatString for a column.

    The trick with percent columns: `0.00%` *multiplies the displayed value by
    100* — so a column already storing percent points as plain numbers
    (e.g. `15.5` meaning 15.5%) renders as `0.00%` when value*100 = 1550. The
    fix is to inspect actual values: a fraction stays a fraction (max ≤ 1.0),
    a percent-points column gets a plain number format. See
    PLAYBOOK_DRYRUN.md gap #14 for the original incident.

    Edge cases:
      • All-NaN sample → plain number (defensive: wrong plain format is ugly,
        wrong percent format silently multiplies by 100).
      • Empty sample / no sample → legacy behaviour (percent format on
        pct/rate names) so existing callers don't break.
    """
    if dtype == "int64":
        return "#,##0"
    if dtype == "double":
        # Currency wins over percent on name match — finance columns ending in
        # _dkk are always plain numbers.
        if "dkk" in col:
            return "#,##0.00"
        if "pct" in col or "rate" in col:
            if sample is not None and not sample.empty:
                try:
                    max_abs = float(sample.dropna().abs().max())
                except (ValueError, TypeError):
                    max_abs = 0.0
                # Fractions live in [-1, 1]; percent-point columns exceed that.
                # Treat NaN/empty as "fraction" — safer default for new clients.
                if max_abs <= 1.0:
                    return "0.00%"
                return "#,##0.00"
            # Sample unavailable — fall through to old behaviour (legacy callers)
            return "0.00%"
        return "#,##0.00"
    if dtype == "dateTime":
        return "dd/MM/yyyy"
    return ""


tables = []
for pq in sorted(GOLD.glob("*.parquet")):
    df = pd.read_parquet(pq)
    cols = []
    for c in df.columns:
        dt = pbi_type(df[c].dtype, c)
        col_def = {
            "name": c,
            "dataType": dt,
            "sourceColumn": c,
        }
        f = fmt(dt, c, sample=df[c])
        if f:
            col_def["formatString"] = f
        cols.append(col_def)
    tables.append({
        "name": f"gold_{pq.stem}",
        "path": str(pq.resolve()).replace("\\", "\\\\"),
        "columns": cols,
    })

out = Path(__file__).parent / "pbi_schemas.json"
out.write_text(json.dumps(tables, indent=2))
print(f"Wrote {out} -- {len(tables)} tables")
