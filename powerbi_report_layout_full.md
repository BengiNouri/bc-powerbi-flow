# Akse Demo DW -- Power BI Report Layout (Full Stack)

## Report Structure: 6 pages

---

## Page 1: Executive Dashboard

**Purpose:** C-level overview across all business domains.

**Row 1 -- KPI Cards (6 cards across):**
| Card             | Measure              | Format     |
|------------------|----------------------|------------|
| Pipeline Value   | [Pipeline Value]     | #,##0 kr   |
| Win Rate         | [Win Rate]           | 0.0%       |
| Revenue (Actual) | [Revenue Actual]     | #,##0 kr   |
| NPS Score        | [NPS Score]          | +#;-#;0    |
| Headcount        | [Total Headcount]    | #,##0      |
| SLA Met          | [SLA Met Rate]       | 0.0%       |

**Row 2 -- Two charts side by side:**
- **Left: Clustered column chart**
  - Axis: gold_dim_date[year_quarter]
  - Values: [Revenue Actual], [Gross Profit Actual]
  - Title: "Revenue & Profit by Quarter"

- **Right: Donut chart**
  - Legend: gold_fact_pipeline[deal_status]
  - Values: [Pipeline Value]
  - Colors: Won=#107C10, Lost=#D13438, Open=#0078D4
  - Title: "Pipeline by Status"

**Row 3 -- Two charts side by side:**
- **Left: Line chart**
  - Axis: gold_dim_date[year_month]
  - Values: [Revenue Actual], [Revenue Budget]
  - Title: "Budget vs Actual Revenue (Monthly)"

- **Right: Gauge**
  - Value: [Avg Utilization]
  - Target: 85
  - Min: 0, Max: 100
  - Title: "Team Utilization %"

---

## Page 2: Pipeline & CRM

**Purpose:** Sales pipeline performance and deal tracking.

**Row 1 -- KPI Cards (5 cards):**
| Card            | Measure              |
|-----------------|----------------------|
| Pipeline Value  | [Pipeline Value]     |
| Weighted Pipe.  | [Weighted Pipeline]  |
| Win Rate        | [Win Rate]           |
| Open Deals      | [Open Deals]         |
| Avg Deal Size   | [Avg Deal Size]      |

**Row 2:**
- **Left: Funnel chart**
  - Category: gold_fact_pipeline[stage]
  - Values: [Pipeline Value]
  - Sort: stage order (lead -> qualified -> meeting_booked -> proposal_sent -> negotiation -> contract_sent -> closed_won)
  - Title: "Deal Funnel"

- **Right: Stacked bar chart**
  - Axis: gold_dim_customer[customer_name]
  - Legend: gold_fact_pipeline[deal_status] (Open/Won/Lost)
  - Values: [Pipeline Value]
  - Title: "Pipeline by Customer & Status"

**Row 3:**
- **Full width: Table**
  - Columns: deal_name, customer_name (via dim_customer), amount_dkk, weighted_amount_dkk,
             stage, deal_status, probability, close_date, days_in_pipeline, deal_owner
  - Conditional formatting: deal_status color (Won=green, Lost=red, Open=blue)
  - Sort: amount_dkk DESC
  - Title: "Deal Detail"

---

## Page 3: Marketing Performance

**Purpose:** Campaign ROI, lead generation, and web analytics.

**Row 1 -- KPI Cards (5 cards):**
| Card               | Measure                |
|--------------------|------------------------|
| Total Leads        | [Total Leads]          |
| Conversion Rate    | [Lead Conversion Rate] |
| Avg CPL            | [Avg Cost Per Lead]    |
| Total Sessions     | [Total Sessions]       |
| Web Conv. Rate     | [Web Conversion Rate]  |

**Row 2:**
- **Left: Clustered bar chart (horizontal)**
  - Axis: gold_dim_campaign[campaign_type]
  - Values: [Total Leads], [Converted Leads]
  - Title: "Leads by Campaign Type"

- **Right: Scatter plot**
  - X: gold_fact_marketing[spent_dkk]
  - Y: gold_fact_marketing[converted_leads]
  - Details: gold_dim_campaign[campaign_name]
  - Size: gold_fact_marketing[total_leads]
  - Title: "Campaign Spend vs Conversions"

**Row 3:**
- **Left: Line chart**
  - Axis: gold_fact_web_sessions[session_month]
  - Values: [Total Sessions], [Total Web Conversions]
  - Title: "Web Traffic Trend"

- **Right: Stacked column chart**
  - Axis: gold_fact_web_sessions[session_month]
  - Legend: gold_fact_web_sessions[source]
  - Values: sessions
  - Title: "Sessions by Source"

---

## Page 4: Finance & Budget

**Purpose:** Budget vs actual, cost breakdown, P&L overview.

**Row 1 -- KPI Cards (5 cards):**
| Card               | Measure                |
|--------------------|------------------------|
| Revenue Actual     | [Revenue Actual]       |
| Gross Margin       | [Gross Margin %]       |
| Operating Profit   | [Operating Profit]     |
| Budget Variance    | [Budget Variance]      |
| Variance %         | [Budget Variance %]    |

**Row 2:**
- **Left: Clustered column chart**
  - Axis: gold_fact_budget[period] (filter: category = "Revenue")
  - Values: [Budget Total], [Actual Total]
  - Title: "Revenue: Budget vs Actual by Month"

- **Right: Waterfall chart**
  - Category: account names (Revenue, COGS, OpEx sub-items)
  - Values: [Actual Total]
  - Title: "P&L Waterfall"

**Row 3:**
- **Left: Matrix table**
  - Rows: gold_fact_budget[account]
  - Columns: gold_fact_budget[year]
  - Values: [Budget Total], [Actual Total], [Budget Variance %]
  - Conditional formatting: color scale on variance
  - Title: "Budget Matrix"

- **Right: Donut chart**
  - Legend: gold_fact_budget[category]
  - Values: ABS([Actual Total])
  - Title: "Cost Distribution"

---

## Page 5: HR & People

**Purpose:** Workforce analytics, utilization, and cost efficiency.

**Row 1 -- KPI Cards (5 cards):**
| Card                | Measure                    |
|---------------------|----------------------------|
| Headcount           | [Total Headcount]          |
| Avg Utilization     | [Avg Utilization]          |
| Revenue/Employee    | [Revenue Per Employee]     |
| Avg Tenure          | [Avg Tenure Years]         |
| Turnover Rate       | [Turnover Rate]            |

**Row 2:**
- **Left: Stacked bar chart**
  - Axis: gold_dim_employee[department]
  - Legend: gold_dim_employee[status] (Active/Terminated)
  - Values: count of employee_id
  - Title: "Headcount by Department"

- **Right: Clustered column chart**
  - Axis: gold_fact_hr[department]
  - Values: [Avg Utilization], target line at 85%
  - Title: "Utilization by Department"

**Row 3:**
- **Left: Line chart**
  - Axis: gold_fact_hr[period]
  - Values: [Total Billable Hours], [Total Internal Hours]
  - Title: "Hours Trend (Monthly)"

- **Right: Matrix**
  - Rows: gold_dim_employee[department]
  - Values: headcount, [Avg Utilization], [Avg Cost Per Billable Hour], [Total Salary Cost]
  - Title: "Department Scorecard"

---

## Page 6: Customer Satisfaction

**Purpose:** NPS trends, support performance, customer health.

**Row 1 -- KPI Cards (5 cards):**
| Card               | Measure                    |
|--------------------|----------------------------|
| NPS Score          | [NPS Score]                |
| Total Tickets      | [Total Tickets]            |
| Resolution Rate    | [Resolution Rate]          |
| Avg Response Time  | [Avg Response Time Hours]  |
| SLA Met Rate       | [SLA Met Rate]             |

**Row 2:**
- **Left: Line chart**
  - Axis: gold_fact_nps[year] + [quarter]
  - Values: [NPS Score]
  - Reference line at 0
  - Title: "NPS Score Trend"

- **Right: Stacked bar chart**
  - Axis: gold_dim_customer[customer_name]
  - Legend: gold_fact_nps[nps_category] (Promoter/Passive/Detractor)
  - Values: count
  - Colors: Promoter=#107C10, Passive=#FFB900, Detractor=#D13438
  - Title: "NPS by Customer"

**Row 3:**
- **Left: Clustered bar chart**
  - Axis: gold_fact_tickets[category]
  - Values: [Total Tickets]
  - Conditional formatting: color by count
  - Title: "Tickets by Category"

- **Right: Table**
  - Columns: ticket_id, customer_name, category, priority, status,
             created_date, response_time_hours, sla_met, satisfaction_rating
  - Conditional formatting: priority color, sla_met (green/red)
  - Sort: created_date DESC
  - Title: "Recent Tickets"

---

## Theme & Formatting

- **Theme file:** CRONUS_DW_Theme.json (import via View -> Themes -> Browse)
- **Color palette:**
  - Primary: #0078D4 (blue)
  - Secondary: #00B294 (teal)
  - Positive: #107C10 (green)
  - Negative: #D13438 (red)
  - Warning: #FFB900 (amber)
  - Neutral: #605E5C (gray)

- **Fonts:** Segoe UI, 10pt body, 14pt headers, 24pt KPI values
- **All currency:** DKK format: #,##0 kr
- **All percentages:** 0.0%

- **Slicers on every page:**
  - gold_dim_date[year] (dropdown)
  - gold_dim_date[quarter] (buttons)
  - gold_dim_customer[country_group] (buttons)

---

## Semantic Model Relationships

| From (fact)              | From Column        | To (dimension)      | To Column      | Cardinality |
|--------------------------|--------------------|---------------------|----------------|-------------|
| gold_fact_pipeline       | customer_key       | gold_dim_customer   | customer_key   | Many:1      |
| gold_fact_pipeline       | created_date_key   | gold_dim_date       | date_key       | Many:1      |
| gold_fact_nps            | customer_key       | gold_dim_customer   | customer_key   | Many:1      |
| gold_fact_nps            | date_key           | gold_dim_date       | date_key       | Many:1      |
| gold_fact_tickets        | customer_key       | gold_dim_customer   | customer_key   | Many:1      |
| gold_fact_tickets        | created_date_key   | gold_dim_date       | date_key       | Many:1      |
| gold_fact_marketing      | campaign_id        | gold_dim_campaign   | campaign_id    | Many:1      |
| gold_fact_web_sessions   | date_key           | gold_dim_date       | date_key       | Many:1      |
| gold_fact_budget         | date_key           | gold_dim_date       | date_key       | Many:1      |
| gold_fact_hr             | employee_id        | gold_dim_employee   | employee_id    | Many:1      |

---

## Quick Setup in Power BI / Fabric

1. In Fabric workspace, click **"New report"** on the semantic model
2. Add 6 pages, name them as above
3. Import theme: View -> Themes -> Browse -> CRONUS_DW_Theme.json
4. For each page, drag visuals from the Visualizations pane
5. Add measures from the field list
6. Add slicers from gold_dim_date and gold_dim_customer
7. Apply conditional formatting via Format -> Conditional formatting
8. Publish to workspace
