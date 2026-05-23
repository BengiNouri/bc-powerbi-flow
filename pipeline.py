"""
CRONUS DW — Full Medallion Pipeline
Sources: Business Central ERP (or synthetic)
Layers: Bronze → Silver → Gold (star schema)

Usage:
    python pipeline.py                    # Live BC API
    python pipeline.py --synthetic        # Synthetic test data
    python pipeline.py --verify           # Run verification queries
"""
import argparse
import os
import time

import pandas as pd


def main():
    parser = argparse.ArgumentParser(description="CRONUS DW Pipeline")
    parser.add_argument("--synthetic", action="store_true", help="Use synthetic data")
    parser.add_argument("--verify", action="store_true", help="Run verification after pipeline")
    args = parser.parse_args()

    if args.synthetic:
        os.environ["USE_SYNTHETIC"] = "true"

    start = time.time()
    print("=" * 44)
    print("   CRONUS DW -- Full Medallion Pipeline")
    print("=" * 44 + "\n")

    # Bronze
    from extract import run_extract
    bronze_data = run_extract()

    # Silver + Gold
    from transform import run_silver, run_gold
    silver = run_silver()
    gold = run_gold(silver)

    elapsed = time.time() - start
    print(f"\n{'=' * 44}")
    print(f"Pipeline complete in {elapsed:.1f}s")
    print(f"{'=' * 44}")

    if args.verify:
        verify(gold)


def verify(gold: dict[str, pd.DataFrame]):
    print("\n=== VERIFICATION ===\n")

    print("Gold tables:")
    for name, df in gold.items():
        print(f"  {name:.<30} {len(df):>6,} rows")

    fact = gold["fact_sales"]
    dim_cust = gold["dim_customer"]

    print("\n--- Top Customers by Revenue ---")
    revenue_by_cust = (
        fact.groupby("customer_key")
        .agg(revenue_dkk=("revenue_dkk", "sum"), lines=("line_id", "count"))
        .reset_index()
        .merge(dim_cust[["customer_key", "customer_name", "country_group"]], on="customer_key", how="left")
        .sort_values("revenue_dkk", ascending=False)
        .head(10)
    )
    print(revenue_by_cust[["customer_name", "country_group", "revenue_dkk", "lines"]].to_string(index=False))

    print("\n--- Revenue by Year ---")
    fact["year"] = fact["date_key"] // 10000
    yearly = fact.groupby("year").agg(
        revenue_dkk=("revenue_dkk", "sum"),
        cogs_dkk=("cogs_dkk", "sum"),
        gross_profit=("gross_profit_dkk", "sum"),
    ).reset_index()
    yearly["margin_pct"] = (yearly["gross_profit"] / yearly["revenue_dkk"] * 100).round(1)
    print(yearly.to_string(index=False))

    print("\n--- Top Categories ---")
    cat_rev = (
        fact.groupby("category_code")
        .agg(revenue_dkk=("revenue_dkk", "sum"))
        .reset_index()
        .sort_values("revenue_dkk", ascending=False)
    )
    print(cat_rev.to_string(index=False))

    print("\nDW verification complete — Power BI ready")


if __name__ == "__main__":
    main()
