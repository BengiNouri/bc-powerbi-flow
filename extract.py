"""
Bronze Layer — Extract from Business Central API (or synthetic data).
Outputs raw JSON + Parquet files to output/bronze/
"""
import json
import os
import time
from pathlib import Path

import requests

from config import (
    BC_API_BASE, BC_CLIENT_ID, BC_CLIENT_SECRET,
    BC_SCOPE, BC_TOKEN_URL, OUTPUT_DIR, USE_SYNTHETIC,
)


def get_token() -> str:
    r = requests.post(BC_TOKEN_URL, data={
        "grant_type": "client_credentials",
        "client_id": BC_CLIENT_ID,
        "client_secret": BC_CLIENT_SECRET,
        "scope": BC_SCOPE,
    })
    r.raise_for_status()
    return r.json()["access_token"]


def bc_get(endpoint: str, token: str, params: dict | None = None) -> list[dict]:
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    url = f"{BC_API_BASE}/{endpoint}"
    records: list[dict] = []

    while url:
        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()
        data = r.json()
        records.extend(data.get("value", []))
        url = data.get("@odata.nextLink")
        params = None

    return records


ENTITIES = {
    "customers": {
        "$select": "id,number,displayName,email,city,country,currencyCode,blocked",
    },
    "items": {
        "$select": "id,number,displayName,type,itemCategoryCode,unitPrice,unitCost,inventory",
    },
    "vendors": {
        "$select": "id,number,displayName,city,country,currencyCode",
    },
    "salesInvoices": {
        "$select": "id,number,invoiceDate,customerNumber,customerName,status,"
                   "totalAmountExcludingTax,totalAmountIncludingTax,currencyCode",
    },
    "salesOrders": {
        "$select": "id,number,orderDate,customerNumber,customerName,status,"
                   "totalAmountExcludingTax,totalAmountIncludingTax,currencyCode",
    },
}


def fetch_invoice_lines(invoices: list[dict], token: str) -> list[dict]:
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    all_lines: list[dict] = []
    total = len(invoices)

    for i, inv in enumerate(invoices):
        url = f"{BC_API_BASE}/salesInvoices({inv['id']})/salesInvoiceLines"
        r = requests.get(url, headers=headers)
        r.raise_for_status()

        for ln in r.json().get("value", []):
            ln["_invoiceId"] = inv["id"]
            ln["_invoiceNumber"] = inv["number"]
            ln["_invoiceDate"] = inv.get("invoiceDate")
            ln["_customerNumber"] = inv.get("customerNumber")
            ln["_customerName"] = inv.get("customerName")
            all_lines.append(ln)

        if (i + 1) % 50 == 0:
            print(f"  {i + 1}/{total} — {len(all_lines)} lines")

    print(f"  Total: {len(all_lines)} invoice lines")
    return all_lines


def save_bronze(name: str, data: list[dict]) -> None:
    bronze_dir = Path(OUTPUT_DIR) / "bronze"
    bronze_dir.mkdir(parents=True, exist_ok=True)

    json_path = bronze_dir / f"{name}.json"
    json_path.write_text(json.dumps(data, default=str, ensure_ascii=False), encoding="utf-8")
    print(f"  bronze/{name}.json — {len(data)} rows")


def extract_from_bc() -> dict[str, list[dict]]:
    print("Authenticating...")
    token = get_token()
    print("Token OK\n")

    results: dict[str, list[dict]] = {}

    for entity, params in ENTITIES.items():
        print(f"Extracting {entity}...")
        data = bc_get(entity, token, params)
        results[entity] = data
        save_bronze(entity, data)

    print(f"\nFetching invoice lines (~{len(results['salesInvoices']) // 5}s)...")
    lines = fetch_invoice_lines(results["salesInvoices"], token)
    results["invoice_lines"] = lines
    save_bronze("invoice_lines", lines)

    return results


def generate_synthetic() -> dict[str, list[dict]]:
    """Generate realistic BC-like test data without hitting the API."""
    from synthetic import generate_all
    data = generate_all()
    for name, rows in data.items():
        save_bronze(name, rows)
    return data


def run_extract() -> dict[str, list[dict]]:
    if USE_SYNTHETIC:
        print("=== SYNTHETIC MODE ===\n")
        return generate_synthetic()

    print("=== EXTRACT FROM BUSINESS CENTRAL ===\n")
    return extract_from_bc()


if __name__ == "__main__":
    start = time.time()
    data = run_extract()
    elapsed = time.time() - start
    print(f"\nBronze extract complete in {elapsed:.1f}s")
    for name, rows in data.items():
        print(f"  {name}: {len(rows)} rows")
