"""
CRONUS DW -- Full Medallion Pipeline (Fabric Notebook Version)
==============================================================
Copy-paste each numbered section into a separate Fabric notebook cell.
Designed for PySpark in Microsoft Fabric Lakehouse.

Sources: Business Central ERP + HubSpot CRM (mock)
Layers: Bronze -> Silver -> Gold (5 tables)
Built by Lodværket with AI assistance
"""

# ============================================================
# CELL 1: Configuration
# ============================================================
CELL_1 = '''
import traceback, sys, requests as req_lib
from pyspark.sql.functions import *
from pyspark.sql.types import StructType, StructField, StringType, DecimalType, IntegerType

def run(label, fn):
    try:
        fn()
        print(f'OK: {label}')
    except Exception as e:
        print(f'\\nFAILED: {label}')
        print(f'  {type(e).__name__}: {e}')
        traceback.print_exc(file=sys.stdout)
        raise

# --- UPDATE THESE VALUES ---
BC_TENANT_ID    = '<YOUR_TENANT_ID>'
BC_ENVIRONMENT  = 'Production'
BC_COMPANY_ID   = '<YOUR_COMPANY_ID>'
BC_CLIENT_ID    = '<YOUR_CLIENT_ID>'
BC_CLIENT_SECRET = '<YOUR_CLIENT_SECRET>'

# --- Fabric Lakehouse paths (auto-detected) ---
WORKSPACE_ID  = '<YOUR_WORKSPACE_ID>'
LAKEHOUSE_ID  = '<YOUR_LAKEHOUSE_ID>'
BRONZE = f'abfss://{WORKSPACE_ID}@onelake.dfs.fabric.microsoft.com/{LAKEHOUSE_ID}/Files/bronze'
SILVER = f'abfss://{WORKSPACE_ID}@onelake.dfs.fabric.microsoft.com/{LAKEHOUSE_ID}/Tables/silver'

print('Config loaded')
'''

# ============================================================
# CELL 2: Extractor functions
# ============================================================
CELL_2 = '''
def get_bc_token():
    r = req_lib.post(f'https://login.microsoftonline.com/{BC_TENANT_ID}/oauth2/v2.0/token',
        data={'grant_type':'client_credentials','client_id':BC_CLIENT_ID,
              'client_secret':BC_CLIENT_SECRET,'scope':'https://api.businesscentral.dynamics.com/.default'})
    r.raise_for_status(); return r.json()['access_token']

def bc_get(ep, token, params=None):
    base = f'https://api.businesscentral.dynamics.com/v2.0/{BC_TENANT_ID}/{BC_ENVIRONMENT}/api/v2.0/companies({BC_COMPANY_ID})/'
    hdrs = {'Authorization':f'Bearer {token}','Accept':'application/json'}
    url, recs = base+ep, []
    while url:
        r = req_lib.get(url, headers=hdrs, params=params); r.raise_for_status()
        d = r.json(); recs.extend(d.get('value',[])); url, params = d.get('@odata.nextLink'), None
    return recs

def stringify(data):
    return [{k: str(v) if v is not None else None for k,v in row.items()} for row in data]

def write_bronze(data, name):
    clean = stringify(data)
    if not clean: print(f'  WARN {name}: empty'); return
    keys = list(dict.fromkeys(k for r in clean for k in r))
    df = spark.createDataFrame([{k:r.get(k) for k in keys} for r in clean],
                               StructType([StructField(k,StringType(),True) for k in keys]))
    (df.withColumn('_extracted_at',current_timestamp()).withColumn('_source',lit(name))
       .write.format('delta').mode('overwrite').option('overwriteSchema','true').save(f'{BRONZE}/{name}'))
    print(f'  Bronze {name}: {df.count()} rows')

run('Extractor functions ready', lambda: None)
'''

# ============================================================
# CELL 3: Extract from Business Central
# ============================================================
CELL_3 = '''
def extract_bc():
    global bc_customers,bc_items,bc_vendors,bc_invoices,bc_orders,bc_token
    bc_token = get_bc_token()
    bc_customers = bc_get('customers',bc_token,{'$select':'id,number,displayName,email,city,country,currencyCode,blocked'})
    bc_items     = bc_get('items',bc_token,{'$select':'id,number,displayName,type,itemCategoryCode,unitPrice,unitCost,inventory'})
    bc_vendors   = bc_get('vendors',bc_token,{'$select':'id,number,displayName,city,country,currencyCode'})
    bc_invoices  = bc_get('salesInvoices',bc_token,{'$select':'id,number,invoiceDate,customerNumber,customerName,status,totalAmountExcludingTax,totalAmountIncludingTax,currencyCode'})
    bc_orders    = bc_get('salesOrders',bc_token,{'$select':'id,number,orderDate,customerNumber,customerName,status,totalAmountExcludingTax,totalAmountIncludingTax,currencyCode'})
    print(f'  Customers:{len(bc_customers)} Items:{len(bc_items)} Vendors:{len(bc_vendors)} Invoices:{len(bc_invoices)} Orders:{len(bc_orders)}')

run('Extract from Business Central', extract_bc)
'''

# ============================================================
# CELL 4: Fetch invoice lines
# ============================================================
CELL_4 = '''
def fetch_lines():
    global all_lines
    t = get_bc_token()
    base = f'https://api.businesscentral.dynamics.com/v2.0/{BC_TENANT_ID}/{BC_ENVIRONMENT}/api/v2.0/companies({BC_COMPANY_ID})/'
    hdrs = {'Authorization':f'Bearer {t}','Accept':'application/json'}
    all_lines = []
    for i,inv in enumerate(bc_invoices):
        r = req_lib.get(f'{base}salesInvoices({inv["id"]})/salesInvoiceLines',headers=hdrs)
        for ln in r.json().get('value',[]):
            ln.update({'_invoiceId':inv['id'],'_invoiceNumber':inv['number'],
                       '_invoiceDate':inv.get('invoiceDate'),'customerNumber':inv.get('customerNumber'),
                       '_customerName':inv.get('customerName')})
            all_lines.append(ln)
        if (i+1)%50==0: print(f'  {i+1}/{len(bc_invoices)} -- {len(all_lines)} lines')
    print(f'  Total: {len(all_lines)} invoice lines')

run('Fetch invoice lines (~1 min)', fetch_lines)
'''

# ============================================================
# CELL 5: Write Bronze layer
# ============================================================
CELL_5 = '''
def write_all_bronze():
    write_bronze(bc_customers,'bc_customers'); write_bronze(bc_items,'bc_items')
    write_bronze(bc_vendors,'bc_vendors');     write_bronze(bc_invoices,'bc_invoices')
    write_bronze(bc_orders,'bc_orders');       write_bronze(all_lines,'bc_invoice_lines')

run('Write BC Bronze layer', write_all_bronze)
'''

# ============================================================
# CELL 6: Silver — Customers
# ============================================================
CELL_6 = '''
from pyspark.sql import functions as F
from pyspark.sql.types import *

def silver_customers():
    spark.read.format('delta').load(f'{BRONZE}/bc_customers').select(
        F.col('number').alias('customer_key'), F.col('displayName').alias('customer_name'),
        F.col('email'), F.col('city'), F.col('country'), F.col('currencyCode').alias('currency_code'),
        F.when(F.lower(F.col('blocked')).isin('true','1'),True).otherwise(False).alias('is_blocked'),
        F.col('_extracted_at').alias('extracted_at')
    ).write.format('delta').mode('overwrite').option('overwriteSchema','true').save(f'{SILVER}/customers')
    print(f'  {spark.read.format("delta").load(f"{SILVER}/customers").count()} rows')

run('Silver: customers', silver_customers)
'''

# ============================================================
# CELL 7: Silver — Items
# ============================================================
CELL_7 = '''
def silver_items():
    spark.read.format('delta').load(f'{BRONZE}/bc_items').select(
        F.col('number').alias('item_key'), F.col('displayName').alias('item_name'),
        F.col('type').alias('item_type'), F.col('itemCategoryCode').alias('category_code'),
        F.col('unitPrice').cast(DecimalType(18,2)).alias('unit_price'),
        F.col('unitCost').cast(DecimalType(18,2)).alias('unit_cost'),
        F.when(F.col('unitPrice').cast(DoubleType())>0,
            (F.col('unitPrice').cast(DoubleType())-F.col('unitCost').cast(DoubleType()))/F.col('unitPrice').cast(DoubleType())
        ).alias('margin_pct'),
        F.col('inventory').cast(IntegerType()).alias('inventory_qty'),
        F.col('_extracted_at').alias('extracted_at')
    ).write.format('delta').mode('overwrite').option('overwriteSchema','true').save(f'{SILVER}/items')
    print(f'  {spark.read.format("delta").load(f"{SILVER}/items").count()} rows')

run('Silver: items', silver_items)
'''

# ============================================================
# CELL 8: Silver — Invoice Lines
# ============================================================
CELL_8 = '''
def silver_invoice_lines():
    spark.read.format('delta').load(f'{BRONZE}/bc_invoice_lines')\\
        .filter(F.col('lineType')=='Item').select(
        F.col('id').alias('line_id'), F.col('_invoiceNumber').alias('invoice_number'),
        F.to_date('_invoiceDate').alias('invoice_date'),
        F.col('customerNumber').alias('customer_key'), F.col('_customerName').alias('customer_name'),
        F.col('lineObjectNumber').alias('item_key'), F.col('description').alias('item_description'),
        F.col('quantity').cast(DecimalType(18,4)).alias('quantity'),
        F.col('unitPrice').cast(DecimalType(18,2)).alias('unit_price'),
        F.col('amountExcludingTax').cast(DecimalType(18,2)).alias('revenue_dkk'),
        F.col('discountAmount').cast(DecimalType(18,2)).alias('discount_dkk'),
        F.col('totalTaxAmount').cast(DecimalType(18,2)).alias('vat_dkk'),
        F.col('amountIncludingTax').cast(DecimalType(18,2)).alias('revenue_incl_vat_dkk'),
        F.col('_extracted_at').alias('extracted_at')
    ).write.format('delta').mode('overwrite').option('overwriteSchema','true').save(f'{SILVER}/invoice_lines')
    print(f'  {spark.read.format("delta").load(f"{SILVER}/invoice_lines").count()} rows')

run('Silver: invoice lines', silver_invoice_lines)
'''

# ============================================================
# CELL 9: Create schemas
# ============================================================
CELL_9 = '''
def create_schemas():
    spark.sql('CREATE SCHEMA IF NOT EXISTS silver')
    spark.sql('CREATE SCHEMA IF NOT EXISTS gold')
    print('  Schemas: silver, gold')

run('Create schemas', create_schemas)
'''

# ============================================================
# CELL 10: Gold — dim_date
# ============================================================
CELL_10 = '''
def dim_date():
    spark.sql("""
        CREATE OR REPLACE TABLE gold.dim_date AS
        SELECT CAST(DATE_FORMAT(d,'yyyyMMdd') AS INT) AS date_key, d AS date,
               YEAR(d) year, QUARTER(d) quarter, MONTH(d) month, DAY(d) day,
               DATE_FORMAT(d,'MMMM') month_name, DATE_FORMAT(d,'EEEE') day_name,
               DAYOFWEEK(d) day_of_week, WEEKOFYEAR(d) week_of_year,
               CONCAT(YEAR(d),'-Q',QUARTER(d)) year_quarter_label,
               CASE WHEN DAYOFWEEK(d) IN (1,7) THEN TRUE ELSE FALSE END is_weekend
        FROM (SELECT EXPLODE(SEQUENCE(DATE'2020-01-01',DATE'2027-12-31',INTERVAL 1 DAY)) AS d)""")
    print(f'  {spark.table("gold.dim_date").count()} rows')

run('Gold: dim_date', dim_date)
'''

# ============================================================
# CELL 11: Gold — dim_item
# ============================================================
CELL_11 = '''
def dim_item():
    spark.read.format('delta').load(f'{SILVER}/items')\\
        .withColumn('revenue_category',
            F.when(F.col('item_type')=='Service','Service Revenue')
             .when(F.col('item_type')=='Inventory','Product Revenue')
             .otherwise('Other'))\\
        .write.format('delta').mode('overwrite').saveAsTable('gold.dim_item')
    print(f'  {spark.table("gold.dim_item").count()} rows')

run('Gold: dim_item', dim_item)
'''

# ============================================================
# CELL 12: Gold — fact_sales
# ============================================================
CELL_12 = '''
def fact_sales():
    lines = spark.read.format('delta').load(f'{SILVER}/invoice_lines')
    items_lu = spark.read.format('delta').load(f'{SILVER}/items').select('item_key','item_name','category_code','unit_cost')
    lines.join(items_lu, lines.item_key==items_lu.item_key,'left').select(
        F.col('line_id'), F.col('invoice_number'),
        F.coalesce(F.date_format('invoice_date','yyyyMMdd').cast('int'),F.lit(19000101)).alias('date_key'),
        lines['item_key'], F.col('customer_key'),
        F.col('item_name'), F.col('category_code'),
        F.col('quantity'), F.col('unit_price'),
        F.col('revenue_dkk'), F.col('discount_dkk'), F.col('vat_dkk'),
        (F.col('quantity').cast('double')*F.col('unit_cost').cast('double')).alias('cogs_dkk'),
        (F.col('revenue_dkk').cast('double')-F.col('quantity').cast('double')*F.col('unit_cost').cast('double')).alias('gross_profit_dkk'),
        F.when(F.col('revenue_dkk').cast('double')>0,
            (F.col('revenue_dkk').cast('double')-F.col('quantity').cast('double')*F.col('unit_cost').cast('double'))
            /F.col('revenue_dkk').cast('double')).alias('gross_margin_pct')
    ).write.format('delta').mode('overwrite').saveAsTable('gold.fact_sales')
    print(f'  {spark.table("gold.fact_sales").count()} rows')

run('Gold: fact_sales', fact_sales)
'''

# ============================================================
# CELL 13: Gold — dim_customer + fact_pipeline (CRM)
# ============================================================
CELL_13 = '''
# Mock HubSpot CRM data — swap for live API when ready
hs_raw = {
    "hs_companies": [
        {"id":"hs_comp_1","bc_customer_number":"10000","name":"Kontorcentralen A/S","city":"Nyborg","country":"DK","industry":"Government","annualrevenue":6112000.0,"numberofemployees":77,"lifecyclestage":"customer"},
        {"id":"hs_comp_2","bc_customer_number":"20000","name":"Ravel Mobler","city":"Holbaek","country":"DK","industry":"Manufacturing","annualrevenue":2855000.0,"numberofemployees":91,"lifecyclestage":"customer"},
        {"id":"hs_comp_3","bc_customer_number":"30000","name":"Lauritzen Kontormobler A/S","city":"Koge","country":"DK","industry":"Office Supplies","annualrevenue":5598000.0,"numberofemployees":236,"lifecyclestage":"customer"},
        {"id":"hs_comp_4","bc_customer_number":"40000","name":"Deerfield Graphics Company","city":"Hilliard","country":"US","industry":"Manufacturing","annualrevenue":2718000.0,"numberofemployees":278,"lifecyclestage":"customer"},
        {"id":"hs_comp_5","bc_customer_number":"50000","name":"Guildford Water Department","city":"Guildford","country":"GB","industry":"Technology","annualrevenue":2741000.0,"numberofemployees":299,"lifecyclestage":"customer"},
        {"id":"hs_prospect_1","bc_customer_number":None,"name":"Nordic Office Solutions","city":"Aarhus","country":"DK","industry":"Office Supplies","annualrevenue":14000000,"numberofemployees":10,"lifecyclestage":"lead"},
        {"id":"hs_prospect_2","bc_customer_number":None,"name":"Scandinavian Interiors","city":"Odense","country":"DK","industry":"Office Supplies","annualrevenue":7000000,"numberofemployees":45,"lifecyclestage":"lead"},
        {"id":"hs_prospect_3","bc_customer_number":None,"name":"Baltic Workspace Group","city":"Copenhagen","country":"DK","industry":"Office Supplies","annualrevenue":7000000,"numberofemployees":23,"lifecyclestage":"lead"},
    ],
    "hs_deals": [
        {"id":"deal_1","hs_company_id":"hs_comp_1","bc_customer_number":"10000","dealname":"Servicekontrakt 2026","amount":58000,"dealstage":"closedwon","closedate":"2026-06-21","probability":1.0,"is_won":True,"is_lost":False},
        {"id":"deal_2","hs_company_id":"hs_comp_1","bc_customer_number":"10000","dealname":"Whiteboard-losning","amount":136000,"dealstage":"closedwon","closedate":"2026-05-05","probability":1.0,"is_won":True,"is_lost":False},
        {"id":"deal_3","hs_company_id":"hs_comp_2","bc_customer_number":"20000","dealname":"Mobelpakke - Nyt kontor","amount":108000,"dealstage":"appointmentscheduled","closedate":"2026-06-28","probability":0.2,"is_won":False,"is_lost":False},
        {"id":"deal_4","hs_company_id":"hs_comp_3","bc_customer_number":"30000","dealname":"Mobelpakke - Nyt kontor","amount":93000,"dealstage":"closedwon","closedate":"2026-08-29","probability":1.0,"is_won":True,"is_lost":False},
        {"id":"deal_5","hs_company_id":"hs_comp_3","bc_customer_number":"30000","dealname":"Whiteboard-losning","amount":182000,"dealstage":"contractsent","closedate":"2026-06-10","probability":0.85,"is_won":False,"is_lost":False},
        {"id":"deal_6","hs_company_id":"hs_comp_4","bc_customer_number":"40000","dealname":"Udvidelse af eksisterende aftale","amount":98000,"dealstage":"closedwon","closedate":"2026-06-21","probability":1.0,"is_won":True,"is_lost":False},
        {"id":"deal_7","hs_company_id":"hs_comp_5","bc_customer_number":"50000","dealname":"Whiteboard-losning","amount":75000,"dealstage":"contractsent","closedate":"2026-08-23","probability":0.85,"is_won":False,"is_lost":False},
        {"id":"deal_8","hs_company_id":"hs_prospect_1","bc_customer_number":None,"dealname":"Ergonomipakke 50 pladser","amount":85000,"dealstage":"closedlost","closedate":"2026-05-14","probability":0.0,"is_won":False,"is_lost":True},
        {"id":"deal_9","hs_company_id":"hs_prospect_2","bc_customer_number":None,"dealname":"Servicekontrakt 2026","amount":41000,"dealstage":"closedwon","closedate":"2026-05-13","probability":1.0,"is_won":True,"is_lost":False},
    ]
}

def load_crm():
    write_bronze(hs_raw['hs_companies'], 'hs_companies')
    write_bronze(hs_raw['hs_deals'], 'hs_deals')

run('CRM Bronze (mock HubSpot)', load_crm)
'''

# ============================================================
# CELL 14: Silver CRM + Gold dim_customer + fact_pipeline
# ============================================================
CELL_14 = '''
def silver_and_gold_crm():
    # Silver CRM companies
    spark.read.format('delta').load(f'{BRONZE}/hs_companies').select(
        F.col('id').alias('crm_company_id'), F.col('bc_customer_number'),
        F.col('name').alias('company_name'), F.col('city'), F.col('country'),
        F.col('industry'), F.col('annualrevenue').cast(DecimalType(18,2)).alias('annual_revenue'),
        F.col('numberofemployees').cast(IntegerType()).alias('employees'),
        F.col('lifecyclestage'), F.col('_extracted_at').alias('extracted_at')
    ).write.format('delta').mode('overwrite').option('overwriteSchema','true').save(f'{SILVER}/crm_companies')

    # Silver CRM deals
    spark.read.format('delta').load(f'{BRONZE}/hs_deals').select(
        F.col('id').alias('deal_id'), F.col('hs_company_id'),
        F.col('bc_customer_number').alias('customer_key'),
        F.col('dealname').alias('deal_name'), F.col('amount').cast(DecimalType(18,2)),
        F.col('dealstage').alias('stage'),
        F.to_date('closedate').alias('close_date'),
        F.col('probability').cast(DecimalType(6,4)),
        F.when(F.col('is_won')=='true',True).otherwise(False).alias('is_won'),
        F.when(F.col('is_lost')=='true',True).otherwise(False).alias('is_lost'),
        F.col('_extracted_at').alias('extracted_at')
    ).write.format('delta').mode('overwrite').option('overwriteSchema','true').save(f'{SILVER}/crm_deals')

    # Gold dim_customer (BC enriched with CRM)
    bc_cust  = spark.read.format('delta').load(f'{SILVER}/customers')
    crm_comp = spark.read.format('delta').load(f'{SILVER}/crm_companies')
    bc_cust.alias('bc').join(
        crm_comp.alias('crm'), F.col('bc.customer_key')==F.col('crm.bc_customer_number'), 'left'
    ).select(
        F.col('bc.customer_key'), F.col('crm.crm_company_id'),
        F.col('bc.customer_name'), F.col('bc.email'), F.col('bc.city'), F.col('bc.country'),
        F.col('bc.currency_code'), F.col('bc.is_blocked'),
        F.col('crm.industry'), F.col('crm.annual_revenue').alias('crm_annual_revenue'),
        F.col('crm.employees').alias('crm_employees'), F.col('crm.lifecyclestage'),
        F.when(F.col('bc.is_blocked'),'Blocked').otherwise('Active').alias('customer_status'),
        F.when(F.col('bc.country')=='DK','Denmark').when(F.col('bc.country').isin('GB','US'),'International')
         .otherwise('Other').alias('country_group'),
        F.when(F.col('crm.annual_revenue')>=5000000,'Enterprise')
         .when(F.col('crm.annual_revenue')>=1000000,'Mid-Market').otherwise('SMB').alias('revenue_segment')
    ).write.format('delta').mode('overwrite').saveAsTable('gold.dim_customer')
    print(f'  dim_customer (BC+CRM): {spark.table("gold.dim_customer").count()} rows')

    # Gold fact_pipeline
    spark.read.format('delta').load(f'{SILVER}/crm_deals').select(
        F.col('deal_id'), F.col('deal_name'), F.col('customer_key'),
        F.coalesce(F.date_format('close_date','yyyyMMdd').cast('int'),F.lit(19000101)).alias('close_date_key'),
        F.col('amount').alias('deal_amount_dkk'),
        (F.col('amount')*F.col('probability')).alias('weighted_amount_dkk'),
        F.col('probability'), F.col('stage'), F.col('is_won'), F.col('is_lost'),
        F.when(F.col('is_won'),'Won').when(F.col('is_lost'),'Lost')
         .when(F.col('close_date')<F.current_date(),'Overdue').otherwise('Open').alias('deal_status')
    ).write.format('delta').mode('overwrite').saveAsTable('gold.fact_pipeline')
    print(f'  fact_pipeline: {spark.table("gold.fact_pipeline").count()} rows')

run('Gold: dim_customer (enriched) + fact_pipeline', silver_and_gold_crm)
'''

# ============================================================
# CELL 15: Verification
# ============================================================
CELL_15 = '''
def verify():
    print('=== Gold Layer ===')
    for t in ['gold.dim_date','gold.dim_customer','gold.dim_item','gold.fact_sales','gold.fact_pipeline']:
        print(f'  {t:<35}: {spark.table(t).count():>6,} rows')
    print()
    print('=== Customer 360: ERP Revenue + CRM Pipeline ===')
    spark.sql("""
        SELECT c.customer_name, c.revenue_segment, c.industry,
               ROUND(SUM(f.revenue_dkk),0) AS erp_revenue_dkk,
               COUNT(p.deal_id) AS open_deals,
               ROUND(SUM(p.deal_amount_dkk),0) AS pipeline_dkk
        FROM gold.dim_customer c
        LEFT JOIN gold.fact_sales f ON c.customer_key = f.customer_key
        LEFT JOIN gold.fact_pipeline p ON c.customer_key = p.customer_key AND p.deal_status='Open'
        GROUP BY c.customer_name, c.revenue_segment, c.industry
        ORDER BY erp_revenue_dkk DESC NULLS LAST
    """).show(truncate=False)
    print('DW complete -- BC ERP + HubSpot CRM -> 5 Gold tables -> Power BI ready')

run('Final verification -- Customer 360', verify)
'''


if __name__ == "__main__":
    print("=" * 60)
    print("  FABRIC NOTEBOOK CELLS")
    print("  Copy each cell into a Fabric notebook")
    print("=" * 60)
    cells = [
        ("Config", CELL_1), ("Extractor functions", CELL_2),
        ("Extract from BC", CELL_3), ("Fetch invoice lines", CELL_4),
        ("Write Bronze", CELL_5), ("Silver: customers", CELL_6),
        ("Silver: items", CELL_7), ("Silver: invoice lines", CELL_8),
        ("Create schemas", CELL_9), ("Gold: dim_date", CELL_10),
        ("Gold: dim_item", CELL_11), ("Gold: fact_sales", CELL_12),
        ("CRM Bronze", CELL_13), ("CRM Silver+Gold", CELL_14),
        ("Verification", CELL_15),
    ]
    for i, (name, code) in enumerate(cells, 1):
        print(f"\n{'─' * 60}")
        print(f"  Cell {i}: {name}")
        print(f"{'─' * 60}")
        print(code.strip())
