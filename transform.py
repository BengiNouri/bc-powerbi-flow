"""
Silver + Gold Layers — Transform bronze data into star schema.
Reads from output/bronze/*.json, writes to output/silver/ and output/gold/ as Parquet.
"""
import json
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from config import OUTPUT_DIR

BRONZE = Path(OUTPUT_DIR) / "bronze"
SILVER = Path(OUTPUT_DIR) / "silver"
GOLD = Path(OUTPUT_DIR) / "gold"


def load_bronze(name: str) -> pd.DataFrame:
    path = BRONZE / f"{name}.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)


def save_layer(df: pd.DataFrame, layer: Path, name: str) -> None:
    layer.mkdir(parents=True, exist_ok=True)
    path = layer / f"{name}.parquet"
    df.to_parquet(path, index=False)
    print(f"  {layer.name}/{name}.parquet — {len(df)} rows")


# ── Silver ──────────────────────────────────────────────

def silver_customers() -> pd.DataFrame:
    df = load_bronze("customers")
    silver = df.rename(columns={
        "number": "customer_key",
        "displayName": "customer_name",
        "currencyCode": "currency_code",
    })[["customer_key", "customer_name", "email", "city", "country", "currency_code", "blocked"]]

    silver["is_blocked"] = silver["blocked"].str.strip().ne("").fillna(False)
    silver = silver.drop(columns=["blocked"])

    save_layer(silver, SILVER, "customers")
    return silver


def silver_items() -> pd.DataFrame:
    df = load_bronze("items")
    silver = df.rename(columns={
        "number": "item_key",
        "displayName": "item_name",
        "type": "item_type",
        "itemCategoryCode": "category_code",
        "unitPrice": "unit_price",
        "unitCost": "unit_cost",
        "inventory": "inventory_qty",
    })[["item_key", "item_name", "item_type", "category_code",
        "unit_price", "unit_cost", "inventory_qty"]]

    silver["unit_price"] = pd.to_numeric(silver["unit_price"], errors="coerce").fillna(0)
    silver["unit_cost"] = pd.to_numeric(silver["unit_cost"], errors="coerce").fillna(0)
    silver["margin_pct"] = silver.apply(
        lambda r: (r["unit_price"] - r["unit_cost"]) / r["unit_price"]
        if r["unit_price"] > 0 else 0, axis=1,
    )

    save_layer(silver, SILVER, "items")
    return silver


def silver_invoice_lines() -> pd.DataFrame:
    df = load_bronze("invoice_lines")
    if "lineType" in df.columns:
        df = df[df["lineType"] == "Item"]

    silver = pd.DataFrame({
        "line_id": df["id"],
        "invoice_number": df["_invoiceNumber"],
        "invoice_date": pd.to_datetime(df["_invoiceDate"], errors="coerce"),
        "customer_key": df["_customerNumber"],
        "customer_name": df["_customerName"],
        "item_key": df.get("lineObjectNumber", df.get("lineObjectNumber", "")),
        "item_description": df.get("description", ""),
        "quantity": pd.to_numeric(df["quantity"], errors="coerce").fillna(0),
        "unit_price": pd.to_numeric(df["unitPrice"], errors="coerce").fillna(0),
        "revenue_dkk": pd.to_numeric(df["amountExcludingTax"], errors="coerce").fillna(0),
        "discount_dkk": pd.to_numeric(df.get("discountAmount", 0), errors="coerce").fillna(0),
        "vat_dkk": pd.to_numeric(df.get("totalTaxAmount", 0), errors="coerce").fillna(0),
        "revenue_incl_vat_dkk": pd.to_numeric(df.get("amountIncludingTax", 0), errors="coerce").fillna(0),
    })

    save_layer(silver, SILVER, "invoice_lines")
    return silver


def run_silver() -> dict[str, pd.DataFrame]:
    print("=== SILVER LAYER ===\n")
    return {
        "customers": silver_customers(),
        "items": silver_items(),
        "invoice_lines": silver_invoice_lines(),
    }


# ── Gold ────────────────────────────────────────────────

def gold_dim_date() -> pd.DataFrame:
    start = date(2020, 1, 1)
    end = date(2027, 12, 31)
    dates = [start + timedelta(days=i) for i in range((end - start).days + 1)]

    df = pd.DataFrame({"date": dates})
    df["date_key"] = df["date"].apply(lambda d: int(d.strftime("%Y%m%d")))
    df["year"] = df["date"].apply(lambda d: d.year)
    df["quarter"] = df["date"].apply(lambda d: (d.month - 1) // 3 + 1)
    df["month"] = df["date"].apply(lambda d: d.month)
    df["day"] = df["date"].apply(lambda d: d.day)
    df["day_name"] = df["date"].apply(lambda d: d.strftime("%A"))
    df["month_name"] = df["date"].apply(lambda d: d.strftime("%B"))
    df["day_of_week"] = df["date"].apply(lambda d: d.isoweekday())
    df["week_of_year"] = df["date"].apply(lambda d: d.isocalendar()[1])
    df["year_quarter"] = df.apply(lambda r: f"{r['year']}-Q{r['quarter']}", axis=1)
    df["is_weekend"] = df["day_of_week"].isin([6, 7])

    save_layer(df, GOLD, "dim_date")
    return df


def gold_dim_customer(silver_customers: pd.DataFrame) -> pd.DataFrame:
    df = silver_customers.copy()

    df["customer_status"] = df["is_blocked"].apply(lambda b: "Blocked" if b else "Active")
    df["country_group"] = df["country"].apply(
        lambda c: "Denmark" if c == "DK"
        else "International" if c in ("GB", "US")
        else "Other"
    )

    save_layer(df, GOLD, "dim_customer")
    return df


def gold_dim_item(silver_items: pd.DataFrame) -> pd.DataFrame:
    df = silver_items.copy()
    df["revenue_category"] = df["item_type"].apply(
        lambda t: "Service Revenue" if t == "Service"
        else "Product Revenue" if t == "Inventory"
        else "Other"
    )

    save_layer(df, GOLD, "dim_item")
    return df


def gold_fact_sales(silver_lines: pd.DataFrame, silver_items: pd.DataFrame) -> pd.DataFrame:
    items_lu = silver_items[["item_key", "item_name", "category_code", "unit_cost"]].copy()

    fact = silver_lines.merge(items_lu, on="item_key", how="left", suffixes=("", "_item"))

    fact["date_key"] = fact["invoice_date"].apply(
        lambda d: int(d.strftime("%Y%m%d")) if pd.notna(d) else 19000101
    )
    fact["cogs_dkk"] = fact["quantity"] * fact["unit_cost"].fillna(0)
    fact["gross_profit_dkk"] = fact["revenue_dkk"] - fact["cogs_dkk"]
    fact["gross_margin_pct"] = fact.apply(
        lambda r: r["gross_profit_dkk"] / r["revenue_dkk"] if r["revenue_dkk"] > 0 else 0,
        axis=1,
    )

    cols = [
        "line_id", "invoice_number", "date_key", "item_key", "customer_key",
        "item_name", "category_code", "quantity", "unit_price",
        "revenue_dkk", "discount_dkk", "vat_dkk",
        "cogs_dkk", "gross_profit_dkk", "gross_margin_pct",
    ]
    fact = fact[[c for c in cols if c in fact.columns]]

    save_layer(fact, GOLD, "fact_sales")
    return fact


def run_gold(silver: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    print("\n=== GOLD LAYER (Star Schema) ===\n")
    return {
        "dim_date": gold_dim_date(),
        "dim_customer": gold_dim_customer(silver["customers"]),
        "dim_item": gold_dim_item(silver["items"]),
        "fact_sales": gold_fact_sales(silver["invoice_lines"], silver["items"]),
    }


if __name__ == "__main__":
    silver = run_silver()
    gold = run_gold(silver)
    print("\nTransform complete.")
