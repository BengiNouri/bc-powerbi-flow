"""Convert gold parquet -> CSV for PBI Desktop import."""
from pathlib import Path

import pandas as pd

GOLD = Path(__file__).parent / "output" / "gold"
CSV_DIR = Path(__file__).parent / "output" / "gold_csv"
CSV_DIR.mkdir(parents=True, exist_ok=True)

for pq in sorted(GOLD.glob("*.parquet")):
    df = pd.read_parquet(pq)
    out = CSV_DIR / f"gold_{pq.stem}.csv"
    df.to_csv(out, index=False, encoding="utf-8")
    print(f"{out.name}: {len(df)} rows, {len(df.columns)} cols -- {list(df.columns)}")
