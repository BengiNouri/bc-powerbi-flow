# CRONUS DW Semantic Model — Star Schema

## How to create in Fabric

1. Go to your Lakehouse **CRONUS_Lakehouse**
2. Click **"New semantic model"** (top right)
3. Select these Gold tables: `dim_date`, `dim_customer`, `dim_item`, `fact_sales`, `fact_pipeline`
4. Click **"Confirm"**
5. Open the semantic model and create relationships + measures below

---

## Relationships

| From (Fact)                | To (Dimension)           | Cardinality  | Direction |
|---------------------------|--------------------------|-------------|-----------|
| fact_sales.date_key       | dim_date.date_key        | Many-to-One | Single    |
| fact_sales.customer_key   | dim_customer.customer_key| Many-to-One | Single    |
| fact_sales.item_key       | dim_item.item_key        | Many-to-One | Single    |
| fact_pipeline.close_date_key | dim_date.date_key     | Many-to-One | Single    |
| fact_pipeline.customer_key| dim_customer.customer_key| Many-to-One | Single    |

**Important:** The fact_pipeline -> dim_date relationship should be INACTIVE (since fact_sales already uses dim_date as active). Use USERELATIONSHIP() in DAX for pipeline date filtering.

---

## Star Schema Diagram

```
                    dim_date
                   (date_key)
                   /        \
                  /          \
    fact_sales --+            +-- fact_pipeline
   (date_key,    |            |  (close_date_key,
    customer_key,|            |   customer_key)
    item_key)    |            |
                  \          /
                   \        /
                 dim_customer
                (customer_key)
                      |
                  dim_item
                 (item_key)
```
