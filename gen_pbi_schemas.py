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


def fmt(dtype: str, col: str) -> str:
    if dtype == "int64":
        return "#,##0"
    if dtype == "double":
        if "pct" in col or "rate" in col:
            return "0.00%"
        if "dkk" in col:
            return "#,##0.00"
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
        f = fmt(dt, c)
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
