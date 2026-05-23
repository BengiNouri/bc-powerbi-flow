# ============================================================
# PASTE THIS CODE INTO THE Akse_Load_Supabase NOTEBOOK IN FABRIC
# ============================================================
# Cell 1: Load all 14 gold tables from Supabase REST API
# into the Akse_Demo_DW Lakehouse as Delta tables.
#
# BEFORE RUNNING:
#   1. Replace SUPABASE_KEY below with your service_role key
#   2. Click "Tilfoej dataelementer" and attach Akse_Demo_DW Lakehouse
# ============================================================

import requests
import json

# --- CONFIGURATION ---
SUPABASE_URL = "https://mudmhjwtezizwkjasoqu.supabase.co"
SUPABASE_KEY = "PASTE_YOUR_SERVICE_ROLE_KEY_HERE"

TABLES = [
    "gold_dim_campaign",
    "gold_dim_customer",
    "gold_dim_date",
    "gold_dim_department",
    "gold_dim_employee",
    "gold_dim_item",
    "gold_fact_budget",
    "gold_fact_hr",
    "gold_fact_marketing",
    "gold_fact_nps",
    "gold_fact_pipeline",
    "gold_fact_sales",
    "gold_fact_tickets",
    "gold_fact_web_sessions",
]

# Lakehouse OneLake path
WS = "f23f5a32-7f8e-4d1f-b0a6-3f94fcc8860a"
LH = "9de09f31-c0de-4eb8-bcfa-a5a1766718d9"
BASE_PATH = f"abfss://{WS}@onelake.dfs.fabric.microsoft.com/{LH}/Tables"

# Supabase REST headers
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

print("=" * 60)
print("Loading gold tables from Supabase -> Lakehouse")
print("=" * 60)

total_rows = 0

for table_name in TABLES:
    try:
        # Fetch all rows from Supabase REST API
        url = f"{SUPABASE_URL}/rest/v1/{table_name}?select=*"
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()

        if not data:
            print(f"  {table_name:.<45} SKIP (empty)")
            continue

        # Create Spark DataFrame and save as Delta
        df = spark.createDataFrame(data)
        save_path = f"{BASE_PATH}/{table_name}"
        df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(save_path)

        n = df.count()
        total_rows += n
        print(f"  {table_name:.<45} {n:>5} rows  OK")

    except Exception as e:
        print(f"  {table_name:.<45} FAILED: {str(e)[:100]}")

print(f"\nDone! {total_rows:,} total rows loaded across {len(TABLES)} tables.")
print("Tables are now available in the Akse_Demo_DW Lakehouse.")
