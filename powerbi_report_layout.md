# CRONUS DW -- Power BI Report Layout

## Report Structure: 4 pages

---

## Page 1: Executive Dashboard

### Layout (top to bottom, left to right)

**Row 1 — KPI Cards (top strip, 5 cards across):**
| Card             | Measure            | Format    |
|------------------|--------------------|-----------|
| Total Revenue    | [Total Revenue]    | #,##0 kr  |
| Gross Margin     | [Gross Margin %]   | 0.0%      |
| Invoice Count    | [Invoice Count]    | #,##0     |
| Open Pipeline    | [Open Pipeline]    | #,##0 kr  |
| Win Rate         | [Win Rate]         | 0.0%      |

**Row 2 — Two charts side by side:**
- **Left: Clustered column chart**
  - Axis: dim_date[year_quarter_label]
  - Values: [Total Revenue], [Gross Profit]
  - Title: "Revenue & Profit by Quarter"

- **Right: Donut chart**
  - Legend: dim_item[category_code]
  - Values: [Total Revenue]
  - Title: "Revenue by Category"

**Row 3 — Two charts side by side:**
- **Left: Line chart**
  - Axis: dim_date[month_name] (sorted by month number)
  - Values: [Total Revenue], [Revenue Previous Year]
  - Title: "Monthly Revenue vs Last Year"

- **Right: Bar chart (horizontal)**
  - Axis: dim_customer[customer_name]
  - Values: [Total Revenue]
  - Top N filter: 10
  - Title: "Top 10 Customers"

---

## Page 2: Sales Analysis

**Row 1 — KPI Cards:**
| Card              | Measure              |
|-------------------|----------------------|
| Avg Order Value   | [Avg Order Value]    |
| Avg Lines/Invoice | [Avg Lines per Invoice]|
| Total Quantity    | [Total Quantity]     |
| Revenue YTD       | [Revenue YTD]        |

**Row 2:**
- **Left: Matrix table**
  - Rows: dim_item[category_code]
  - Columns: dim_date[year]
  - Values: [Total Revenue], [Gross Margin %], [Total Quantity]
  - Conditional formatting: data bars on Revenue, color scale on Margin

- **Right: Scatter plot**
  - X: [Total Revenue]
  - Y: [Gross Margin %]
  - Details: dim_item[item_name]
  - Size: [Total Quantity]
  - Title: "Item Revenue vs Margin"

**Row 3:**
- **Full width: Table**
  - Columns: invoice_number, invoice_date, customer_name, item_description,
             quantity, unit_price, revenue_dkk, gross_profit_dkk, gross_margin_pct
  - Sort: invoice_date DESC
  - Title: "Invoice Line Detail"

---

## Page 3: Customer 360

**Row 1 — KPI Cards:**
| Card               | Measure               |
|--------------------|-----------------------|
| Customer Count     | [Customer Count]      |
| Revenue/Customer   | [Revenue per Customer]|
| Top Customer       | [Top Customer Revenue]|

**Row 2:**
- **Left: Stacked bar chart**
  - Axis: dim_customer[customer_name]
  - Legend: dim_customer[revenue_segment] (Enterprise/Mid-Market/SMB)
  - Values: [Total Revenue]
  - Title: "Revenue by Customer & Segment"

- **Right: Map visualization**
  - Location: dim_customer[country_group]
  - Size: [Total Revenue]
  - Title: "Revenue by Geography"

**Row 3:**
- **Full width: Matrix**
  - Rows: dim_customer[customer_name]
  - Values: [Total Revenue], [Gross Margin %], [Invoice Count],
            [Open Pipeline], [Weighted Pipeline]
  - Conditional formatting: color scale on all value columns
  - Title: "Customer 360 Scorecard"

---

## Page 4: Pipeline & CRM

**Row 1 — KPI Cards:**
| Card            | Measure            |
|-----------------|--------------------|
| Pipeline Value  | [Pipeline Value]   |
| Weighted Pipe.  | [Weighted Pipeline]|
| Win Rate        | [Win Rate]         |
| Open Deals      | [Open Deals]       |
| Avg Deal Size   | [Avg Deal Size]    |

**Row 2:**
- **Left: Funnel chart**
  - Category: fact_pipeline[stage]
  - Values: [Pipeline Value]
  - Sort: stage order (appointmentscheduled -> presentationscheduled -> contractsent -> closedwon)
  - Title: "Deal Funnel"

- **Right: Stacked bar chart**
  - Axis: dim_customer[customer_name]
  - Legend: fact_pipeline[deal_status] (Open/Won/Lost/Overdue)
  - Values: [Pipeline Value]
  - Title: "Pipeline by Customer & Status"

**Row 3:**
- **Full width: Table**
  - Columns: deal_name, customer_key, deal_amount_dkk, weighted_amount_dkk,
             stage, deal_status, probability, close_date
  - Conditional formatting: deal_status color (Won=green, Lost=red, Open=blue, Overdue=orange)
  - Sort: deal_amount_dkk DESC
  - Title: "Deal Detail"

---

## Theme & Formatting

- **Color palette:** Reeach brand or default Fabric theme
  - Primary: #0078D4 (blue)
  - Secondary: #00B294 (teal)
  - Positive: #107C10 (green)
  - Negative: #D13438 (red)
  - Neutral: #605E5C (gray)

- **Fonts:** Segoe UI, 10pt body, 14pt headers, 24pt KPI values
- **All currency:** DKK format: #,##0 kr
- **All percentages:** 0.0%
- **Slicers on every page:**
  - dim_date[year] (dropdown)
  - dim_date[quarter] (buttons)
  - dim_customer[country_group] (buttons)

---

## Quick Setup Steps in Power BI

1. In Fabric workspace, click **"New report"** on the semantic model
2. Add 4 pages, name them as above
3. For each page, drag visuals from the Visualizations pane
4. Add measures from the field list (they appear under fact_sales / fact_pipeline)
5. Add slicers from dim_date and dim_customer
6. Apply conditional formatting via Format > Conditional formatting
7. Publish to workspace
