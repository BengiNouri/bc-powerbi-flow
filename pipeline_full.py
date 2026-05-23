"""
Akse Demo DW -- Full Stack Medallion Pipeline
==============================================
Sources: BC ERP (synthetic) + CRM + Marketing + Finance + HR + CSAT
Layers: Bronze (JSON) -> Silver (Parquet) -> Gold (Star Schema Parquet)

Usage:
    python pipeline_full.py               # Generate + transform
    python pipeline_full.py --verify      # Include verification
"""
import argparse
import json
import time
from pathlib import Path

from config import OUTPUT_DIR
from synthetic_full import generate_full_stack
from transform_full import run_silver, run_gold, verify

BRONZE = Path(OUTPUT_DIR) / "bronze"


def save_bronze(data: dict[str, list[dict]]) -> None:
    BRONZE.mkdir(parents=True, exist_ok=True)
    print("\n=== BRONZE LAYER ===\n")
    for name, rows in data.items():
        path = BRONZE / f"{name}.json"
        path.write_text(json.dumps(rows, default=str, ensure_ascii=False), encoding="utf-8")
        print(f"  bronze/{name}.json -- {len(rows)} rows")


def main() -> None:
    parser = argparse.ArgumentParser(description="Akse Demo DW Pipeline")
    parser.add_argument("--verify", action="store_true", help="Run verification after pipeline")
    args = parser.parse_args()

    start = time.time()
    print("=" * 48)
    print("   Akse Demo DW -- Full Stack Pipeline")
    print("=" * 48)

    # 1. Generate synthetic data
    raw = generate_full_stack()

    # 2. Bronze: persist raw JSON
    save_bronze(raw)

    # 3. Silver: clean + type
    silver = run_silver(raw)

    # 4. Gold: star schema
    gold = run_gold(silver)

    elapsed = time.time() - start
    print(f"\n{'=' * 48}")
    print(f"Pipeline complete in {elapsed:.1f}s")

    # Count all output files
    output = Path(OUTPUT_DIR)
    for layer in ["bronze", "silver", "gold"]:
        layer_path = output / layer
        if layer_path.exists():
            files = list(layer_path.iterdir())
            print(f"  {layer}: {len(files)} files")

    print(f"{'=' * 48}")

    if args.verify:
        verify(gold)


if __name__ == "__main__":
    main()
