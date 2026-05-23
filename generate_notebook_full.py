"""
Generate Akse Demo DW Fabric Notebook (ipynb)
=============================================
Creates a Jupyter notebook with PySpark cells for Microsoft Fabric.
Covers all 6 data sources: BC ERP, CRM, Marketing, Finance, HR, CSAT.
Medallion: Bronze -> Silver -> Gold star schema in Delta Lake.

Import in Fabric: Workspace -> Import -> Notebook -> select .ipynb
Then attach the Lakehouse before running.
"""
import json
from pathlib import Path
from config import OUTPUT_DIR


def _md_cell(source: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [source],
    }


def _code_cell(source: str) -> dict:
    return {
        "cell_type": "code",
        "metadata": {"microsoft": {"language": "python"}},
        "source": [source],
        "outputs": [],
        "execution_count": None,
    }


CELLS = [
    # ── Header ────────────────────────────────────────────
    _md_cell(
        "# Akse Demo DW -- Full Stack Pipeline\n"
        "**Medallion Architecture:** Bronze -> Silver -> Gold (Star Schema)\n\n"
        "**Sources:** BC ERP (synthetic), CRM, Marketing, Finance, HR, Customer Satisfaction\n\n"
        "**Attach Lakehouse** before running: click 'Add' in left panel -> select your Lakehouse"
    ),

    # ── Cell 1: Imports + Config ─────────────────────────
    _code_cell(
        "# Cell 1: Imports & Config\n"
        "from pyspark.sql import SparkSession\n"
        "from pyspark.sql.functions import (\n"
        "    col, lit, when, year, month, dayofmonth, dayofweek,\n"
        "    quarter, date_format, to_date, round as spark_round,\n"
        "    concat, datediff, current_date, sum as spark_sum,\n"
        "    count, avg, max as spark_max, min as spark_min,\n"
        "    weekofyear, expr\n"
        ")\n"
        "from pyspark.sql.types import *\n"
        "from datetime import date, timedelta\n"
        "import random\n"
        "import uuid\n\n"
        "spark = SparkSession.builder.getOrCreate()\n"
        "random.seed(42)\n\n"
        "LAKEHOUSE = 'abfss://YOUR_WORKSPACE@onelake.dfs.fabric.microsoft.com/YOUR_LAKEHOUSE.Lakehouse'\n"
        "# ^^ Replace or use the default Lakehouse path from the attached Lakehouse\n"
        "print('Spark ready')"
    ),

    _md_cell("## Bronze Layer -- Generate Raw Data"),

    # ── Cell 2: Shared Reference Data ───────────────────
    _code_cell(
        "# Cell 2: Shared Reference Data\n\n"
        "BC_CUSTOMERS = [\n"
        "    {'number': '10000', 'name': 'Kontorcentralen A/S', 'city': 'Nyborg', 'country': 'DK', 'industry': 'Government', 'size': 'Enterprise'},\n"
        "    {'number': '20000', 'name': 'Ravel Mobler', 'city': 'Holbaek', 'country': 'DK', 'industry': 'Manufacturing', 'size': 'Mid-Market'},\n"
        "    {'number': '30000', 'name': 'Lauritzen Kontormobler A/S', 'city': 'Koge', 'country': 'DK', 'industry': 'Office Supplies', 'size': 'Enterprise'},\n"
        "    {'number': '40000', 'name': 'Deerfield Graphics Company', 'city': 'Hilliard', 'country': 'US', 'industry': 'Manufacturing', 'size': 'Mid-Market'},\n"
        "    {'number': '50000', 'name': 'Guildford Water Department', 'city': 'Guildford', 'country': 'GB', 'industry': 'Technology', 'size': 'Enterprise'},\n"
        "]\n\n"
        "PROSPECTS = [\n"
        "    {'number': None, 'name': 'Nordic Office Solutions', 'city': 'Aarhus', 'country': 'DK', 'industry': 'Office Supplies', 'size': 'Enterprise'},\n"
        "    {'number': None, 'name': 'Scandinavian Interiors', 'city': 'Odense', 'country': 'DK', 'industry': 'Retail', 'size': 'Mid-Market'},\n"
        "    {'number': None, 'name': 'Baltic Workspace Group', 'city': 'Copenhagen', 'country': 'DK', 'industry': 'Logistics', 'size': 'SMB'},\n"
        "    {'number': None, 'name': 'Green Office Denmark', 'city': 'Aalborg', 'country': 'DK', 'industry': 'Sustainability', 'size': 'SMB'},\n"
        "    {'number': None, 'name': 'TechHub Scandinavia', 'city': 'Aarhus', 'country': 'DK', 'industry': 'Technology', 'size': 'Mid-Market'},\n"
        "]\n\n"
        "ALL_COMPANIES = BC_CUSTOMERS + PROSPECTS\n"
        "DEPARTMENTS = ['Sales', 'Marketing', 'Finance', 'Operations', 'IT', 'HR', 'Management']\n"
        "DEAL_STAGES = [\n"
        "    ('lead', 0.05), ('qualified', 0.15), ('meeting_booked', 0.30),\n"
        "    ('proposal_sent', 0.50), ('negotiation', 0.70), ('contract_sent', 0.85),\n"
        "    ('closed_won', 1.0), ('closed_lost', 0.0),\n"
        "]\n"
        "CAMPAIGN_TYPES = ['Email', 'LinkedIn', 'Google Ads', 'Webinar', 'Event', 'Content', 'Referral']\n"
        "TICKET_CATEGORIES = ['Billing', 'Delivery', 'Product Quality', 'Technical', 'Returns', 'General']\n\n"
        "def _uid():\n"
        "    return str(uuid.uuid4())[:12]\n\n"
        "def _rand_date(start=date(2024,1,1), end=date(2026,5,22)):\n"
        "    delta = (end - start).days\n"
        "    return start + timedelta(days=random.randint(0, max(delta,1)))\n\n"
        "def _rand_date_after(d, max_days=90):\n"
        "    return d + timedelta(days=random.randint(1, max_days))\n\n"
        "print(f'Reference data: {len(ALL_COMPANIES)} companies, {len(DEPARTMENTS)} departments')"
    ),

    # ── Cell 3: CRM Data Generation ─────────────────────
    _code_cell(
        "# Cell 3: Generate CRM Data (Companies, Contacts, Deals, Activities)\n\n"
        "crm_companies = []\n"
        "for i, c in enumerate(ALL_COMPANIES):\n"
        "    ann_rev = random.randint(1_000_000, 20_000_000) if c['size'] == 'Enterprise' else \\\n"
        "             random.randint(500_000, 5_000_000) if c['size'] == 'Mid-Market' else \\\n"
        "             random.randint(100_000, 1_000_000)\n"
        "    crm_companies.append({\n"
        "        'crm_company_id': f'comp_{i+1:03d}',\n"
        "        'bc_customer_number': c['number'],\n"
        "        'company_name': c['name'],\n"
        "        'city': c['city'], 'country': c['country'],\n"
        "        'industry': c['industry'], 'segment': c['size'],\n"
        "        'annual_revenue_dkk': ann_rev,\n"
        "        'employees': random.randint(5, 300),\n"
        "        'lifecycle_stage': 'customer' if c['number'] else 'lead',\n"
        "        'lead_source': random.choice(CAMPAIGN_TYPES),\n"
        "        'created_date': str(_rand_date(date(2023,1,1), date(2025,6,1))),\n"
        "        'owner': random.choice(['Maria Jensen', 'Anders Holm', 'Sophie Nielsen', 'Lars Pedersen']),\n"
        "    })\n\n"
        "# Contacts\n"
        "first_names = ['Maria','Anders','Sophie','Lars','Mette','Thomas','Camilla','Peter','Anne','Mikkel']\n"
        "last_names = ['Jensen','Nielsen','Hansen','Pedersen','Andersen','Christensen','Larsen','Sorensen']\n"
        "titles = ['CEO','CFO','COO','VP Sales','Head of Procurement','Office Manager','IT Director']\n\n"
        "crm_contacts = []\n"
        "for comp in crm_companies:\n"
        "    for j in range(random.randint(1, 4)):\n"
        "        first = random.choice(first_names)\n"
        "        last = random.choice(last_names)\n"
        "        domain = comp['company_name'].split()[0].lower().replace('.', '')\n"
        "        crm_contacts.append({\n"
        "            'contact_id': _uid(), 'crm_company_id': comp['crm_company_id'],\n"
        "            'first_name': first, 'last_name': last,\n"
        "            'email': f'{first.lower()}.{last.lower()}@{domain}.dk',\n"
        "            'title': random.choice(titles),\n"
        "            'is_decision_maker': j == 0,\n"
        "            'created_date': comp['created_date'],\n"
        "        })\n\n"
        "# Deals\n"
        "deal_templates = ['Kontorindretning','Mobelfornyelse','IT-udstyr pakke','Servicekontrakt','Ergonomipakke','Designprojekt']\n"
        "crm_deals = []\n"
        "for comp in crm_companies:\n"
        "    for _ in range(random.randint(1, 5)):\n"
        "        created = _rand_date(date(2024,6,1), date(2026,5,1))\n"
        "        close = _rand_date_after(created, 120)\n"
        "        si = random.randint(0, len(DEAL_STAGES)-1)\n"
        "        stage, prob = DEAL_STAGES[si]\n"
        "        amount = random.choice([25000,45000,68000,95000,120000,185000,250000,350000,500000])\n"
        "        crm_deals.append({\n"
        "            'deal_id': _uid(), 'crm_company_id': comp['crm_company_id'],\n"
        "            'bc_customer_number': comp['bc_customer_number'],\n"
        "            'deal_name': f\"{comp['company_name']} - {random.choice(deal_templates)}\",\n"
        "            'amount_dkk': amount, 'weighted_amount_dkk': round(amount * prob),\n"
        "            'stage': stage, 'probability': prob,\n"
        "            'is_won': stage == 'closed_won', 'is_lost': stage == 'closed_lost',\n"
        "            'created_date': str(created), 'close_date': str(close),\n"
        "            'deal_owner': comp.get('owner', 'Maria Jensen'),\n"
        "            'deal_source': random.choice(CAMPAIGN_TYPES),\n"
        "        })\n\n"
        "# Activities\n"
        "act_types = ['Email','Call','Meeting','Note','Task','Demo']\n"
        "crm_activities = []\n"
        "for deal in crm_deals:\n"
        "    deal_contacts = [c for c in crm_contacts if c['crm_company_id'] == deal['crm_company_id']]\n"
        "    if not deal_contacts: continue\n"
        "    for _ in range(random.randint(2, 8)):\n"
        "        contact = random.choice(deal_contacts)\n"
        "        act_type = random.choice(act_types)\n"
        "        crm_activities.append({\n"
        "            'activity_id': _uid(), 'deal_id': deal['deal_id'],\n"
        "            'contact_id': contact['contact_id'], 'crm_company_id': deal['crm_company_id'],\n"
        "            'activity_type': act_type,\n"
        "            'activity_date': str(_rand_date(date.fromisoformat(deal['created_date']),\n"
        "                                           min(date.fromisoformat(deal['close_date']), date(2026,5,22)))),\n"
        "            'duration_minutes': random.choice([5,15,30,45,60,90]) if act_type in ('Call','Meeting','Demo') else 0,\n"
        "            'outcome': random.choice(['Completed','No answer','Follow-up needed','Positive','Rescheduled']),\n"
        "            'owner': deal['deal_owner'],\n"
        "        })\n\n"
        "print(f'CRM: {len(crm_companies)} companies, {len(crm_contacts)} contacts, {len(crm_deals)} deals, {len(crm_activities)} activities')"
    ),

    # ── Cell 4: Marketing Data ──────────────────────────
    _code_cell(
        "# Cell 4: Generate Marketing Data (Campaigns, Leads, Web Sessions)\n\n"
        "campaigns = []\n"
        "for i in range(20):\n"
        "    start = _rand_date(date(2024,1,1), date(2026,3,1))\n"
        "    end = _rand_date_after(start, 60)\n"
        "    budget = random.choice([5000,10000,15000,25000,40000,60000,100000])\n"
        "    spent = round(budget * random.uniform(0.6, 1.1))\n"
        "    ct = random.choice(CAMPAIGN_TYPES)\n"
        "    campaigns.append({\n"
        "        'campaign_id': f'camp_{i+1:03d}', 'campaign_name': f'{ct} - {start.strftime(\"%b %Y\")}',\n"
        "        'campaign_type': ct, 'status': 'Completed' if end < date(2026,5,1) else 'Active',\n"
        "        'start_date': str(start), 'end_date': str(end),\n"
        "        'budget_dkk': budget, 'spent_dkk': spent,\n"
        "        'target_audience': random.choice(['Enterprise DK','Mid-Market DK','All segments','New leads']),\n"
        "        'owner': random.choice(['Marketing Team','Sophie Nielsen','Camilla Berg']),\n"
        "    })\n\n"
        "leads = []\n"
        "for camp in campaigns:\n"
        "    for j in range(random.randint(5, 40)):\n"
        "        created = _rand_date(date.fromisoformat(camp['start_date']),\n"
        "                            min(date.fromisoformat(camp['end_date']), date(2026,5,22)))\n"
        "        status = random.choices(['new','contacted','qualified','converted','disqualified'],\n"
        "                               weights=[10,20,30,25,15])[0]\n"
        "        leads.append({\n"
        "            'lead_id': _uid(), 'campaign_id': camp['campaign_id'],\n"
        "            'lead_name': f'Lead {_uid()[:4]}',\n"
        "            'company_name': random.choice([c['name'] for c in ALL_COMPANIES] + ['Unknown Co','Anonym ApS']),\n"
        "            'lead_source': camp['campaign_type'], 'status': status,\n"
        "            'score': random.randint(10, 100),\n"
        "            'created_date': str(created),\n"
        "            'converted_date': str(_rand_date_after(created, 30)) if status == 'converted' else None,\n"
        "        })\n\n"
        "web_sessions = []\n"
        "for mo in range(28):\n"
        "    yr = 2024 + (mo // 12)\n"
        "    mn = (mo % 12) + 1\n"
        "    if yr == 2026 and mn > 5: break\n"
        "    sessions = random.randint(500, 3000)\n"
        "    for source in ['Organic','Paid','Social','Direct','Referral','Email']:\n"
        "        s_pct = random.uniform(0.05, 0.4)\n"
        "        s_sess = int(sessions * s_pct)\n"
        "        convs = int(s_sess * random.uniform(0.01, 0.08))\n"
        "        web_sessions.append({\n"
        "            'session_month': f'{yr}-{mn:02d}-01', 'source': source,\n"
        "            'sessions': s_sess, 'new_users': int(s_sess * random.uniform(0.4, 0.8)),\n"
        "            'bounce_rate': round(random.uniform(0.25, 0.65), 3),\n"
        "            'pages_per_session': round(random.uniform(1.5, 5.5), 1),\n"
        "            'avg_duration_sec': random.randint(30, 300),\n"
        "            'conversions': convs,\n"
        "            'conversion_rate': round(convs / max(s_sess, 1), 4),\n"
        "        })\n\n"
        "print(f'Marketing: {len(campaigns)} campaigns, {len(leads)} leads, {len(web_sessions)} web session rows')"
    ),

    # ── Cell 5: Finance Data ────────────────────────────
    _code_cell(
        "# Cell 5: Generate Finance Data (Budget vs Actual, Cost Centers)\n\n"
        "accounts = [\n"
        "    ('Revenue', 'Sales Revenue', 1), ('Revenue', 'Service Revenue', 1),\n"
        "    ('COGS', 'Cost of Goods Sold', -1), ('COGS', 'Direct Labor', -1),\n"
        "    ('OpEx', 'Marketing', -1), ('OpEx', 'Salaries', -1),\n"
        "    ('OpEx', 'Rent & Facilities', -1), ('OpEx', 'IT & Software', -1),\n"
        "    ('OpEx', 'Travel', -1), ('OpEx', 'Other', -1),\n"
        "]\n\n"
        "budget_rows = []\n"
        "for yr in [2024, 2025, 2026]:\n"
        "    for mn in range(1, 13):\n"
        "        for category, account, sign in accounts:\n"
        "            base = random.randint(300_000, 800_000) if category == 'Revenue' else \\\n"
        "                   random.randint(150_000, 400_000) if category == 'COGS' else \\\n"
        "                   random.randint(20_000, 200_000)\n"
        "            growth = 1 + (yr - 2024) * 0.08 + mn * 0.005\n"
        "            budget_amt = round(base * growth)\n"
        "            actual_amt = round(budget_amt * random.uniform(0.85, 1.15)) if (yr < 2026 or mn <= 5) else None\n"
        "            budget_rows.append({\n"
        "                'budget_id': _uid(), 'year': yr, 'month': mn,\n"
        "                'period': f'{yr}-{mn:02d}', 'category': category,\n"
        "                'account': account,\n"
        "                'budget_dkk': budget_amt * sign,\n"
        "                'actual_dkk': actual_amt * sign if actual_amt else None,\n"
        "                'variance_dkk': (actual_amt - budget_amt) * sign if actual_amt else None,\n"
        "                'department': random.choice(DEPARTMENTS[:4]),\n"
        "            })\n\n"
        "cost_centers = [\n"
        "    {'cost_center_id': f'cc_{i+1:02d}', 'name': dept, 'manager': f'Manager {dept}',\n"
        "     'annual_budget_dkk': random.randint(500_000, 5_000_000)}\n"
        "    for i, dept in enumerate(DEPARTMENTS)\n"
        "]\n\n"
        "print(f'Finance: {len(budget_rows)} budget rows, {len(cost_centers)} cost centers')"
    ),

    # ── Cell 6: HR Data ─────────────────────────────────
    _code_cell(
        "# Cell 6: Generate HR Data (Employees, Timesheets)\n\n"
        "hr_first = ['Maria','Anders','Sophie','Lars','Mette','Thomas','Camilla','Peter',\n"
        "            'Anne','Mikkel','Christine','Henrik','Louise','Nikolaj','Katrine',\n"
        "            'Frederik','Emma','Oliver','Ida','Victor','Clara','Magnus',\n"
        "            'Sofie','Sebastian','Freja','Noah','Alma','Oscar','Ella','William']\n"
        "hr_last = ['Jensen','Nielsen','Hansen','Pedersen','Andersen','Christensen','Larsen','Sorensen']\n"
        "dept_roles = {\n"
        "    'Sales': ['Account Executive','Sales Manager','SDR','VP Sales'],\n"
        "    'Marketing': ['Marketing Manager','Content Specialist','Digital Marketing','CMO'],\n"
        "    'Finance': ['Controller','Accountant','CFO','Financial Analyst'],\n"
        "    'Operations': ['Operations Manager','Logistics Coordinator','Warehouse Lead'],\n"
        "    'IT': ['Developer','IT Manager','Data Engineer','CTO'],\n"
        "    'HR': ['HR Manager','Recruiter','HR Coordinator'],\n"
        "    'Management': ['CEO','COO','Office Manager'],\n"
        "}\n\n"
        "employees = []\n"
        "emp_id = 1000\n"
        "for dept in DEPARTMENTS:\n"
        "    for _ in range(random.randint(3, 8)):\n"
        "        emp_id += 1\n"
        "        hire = _rand_date(date(2018,1,1), date(2026,1,1))\n"
        "        active = random.random() > 0.08\n"
        "        salary = random.randint(25_000, 75_000) * 12\n"
        "        employees.append({\n"
        "            'employee_id': f'EMP-{emp_id}',\n"
        "            'first_name': random.choice(hr_first), 'last_name': random.choice(hr_last),\n"
        "            'department': dept, 'role': random.choice(dept_roles.get(dept, ['Specialist'])),\n"
        "            'hire_date': str(hire),\n"
        "            'termination_date': str(_rand_date_after(hire, 365)) if not active else None,\n"
        "            'is_active': active, 'annual_salary_dkk': salary,\n"
        "            'monthly_cost_dkk': round(salary / 12 * 1.3),\n"
        "            'city': random.choice(['Copenhagen','Aarhus','Odense','Aalborg']),\n"
        "            'employment_type': random.choices(['Full-time','Part-time','Contract'], weights=[80,10,10])[0],\n"
        "        })\n\n"
        "timesheets = []\n"
        "for emp in [e for e in employees if e['is_active']]:\n"
        "    for mo in range(6):\n"
        "        d = date(2026,5,22) - timedelta(days=30*mo)\n"
        "        billable = random.randint(100, 160)\n"
        "        internal = random.randint(10, 40)\n"
        "        timesheets.append({\n"
        "            'timesheet_id': _uid(), 'employee_id': emp['employee_id'],\n"
        "            'department': emp['department'], 'period': f'{d.year}-{d.month:02d}',\n"
        "            'billable_hours': billable, 'internal_hours': internal,\n"
        "            'total_hours': billable + internal,\n"
        "            'utilization_pct': round(billable / (billable + internal) * 100, 1),\n"
        "        })\n\n"
        "print(f'HR: {len(employees)} employees, {len(timesheets)} timesheet rows')"
    ),

    # ── Cell 7: Customer Satisfaction ───────────────────
    _code_cell(
        "# Cell 7: Generate Customer Satisfaction (NPS, Support Tickets)\n\n"
        "customer_companies = [c for c in crm_companies if c['bc_customer_number']]\n\n"
        "nps_surveys = []\n"
        "for comp in customer_companies:\n"
        "    for q in range(1, 11):\n"
        "        yr = 2024 + (q - 1) // 4\n"
        "        qtr = ((q - 1) % 4) + 1\n"
        "        if yr > 2026 or (yr == 2026 and qtr > 2): break\n"
        "        score = random.randint(1, 10)\n"
        "        nps_surveys.append({\n"
        "            'survey_id': _uid(),\n"
        "            'bc_customer_number': comp['bc_customer_number'],\n"
        "            'company_name': comp['company_name'],\n"
        "            'survey_date': f'{yr}-{(qtr-1)*3+2:02d}-15',\n"
        "            'year': yr, 'quarter': qtr,\n"
        "            'nps_score': score,\n"
        "            'nps_category': 'Promoter' if score >= 9 else 'Passive' if score >= 7 else 'Detractor',\n"
        "            'comment': random.choice([None,'Great service','Slow delivery','Good quality',\n"
        "                                     'Price too high','Very satisfied','Could improve support']),\n"
        "        })\n\n"
        "support_tickets = []\n"
        "for comp in customer_companies:\n"
        "    for _ in range(random.randint(3, 20)):\n"
        "        created = _rand_date(date(2024,6,1), date(2026,5,20))\n"
        "        resolved = _rand_date_after(created, 14) if random.random() > 0.1 else None\n"
        "        priority = random.choices(['Low','Medium','High','Critical'], weights=[30,40,20,10])[0]\n"
        "        sla_hrs = {'Low': 48, 'Medium': 24, 'High': 8, 'Critical': 2}[priority]\n"
        "        resp_hrs = random.uniform(0.5, sla_hrs * 1.5)\n"
        "        support_tickets.append({\n"
        "            'ticket_id': f'TKT-{_uid()[:6].upper()}',\n"
        "            'bc_customer_number': comp['bc_customer_number'],\n"
        "            'company_name': comp['company_name'],\n"
        "            'category': random.choice(TICKET_CATEGORIES),\n"
        "            'priority': priority,\n"
        "            'status': 'Resolved' if resolved else 'Open',\n"
        "            'created_date': str(created),\n"
        "            'resolved_date': str(resolved) if resolved else None,\n"
        "            'response_time_hours': round(resp_hrs, 1),\n"
        "            'sla_target_hours': sla_hrs,\n"
        "            'sla_met': resp_hrs <= sla_hrs,\n"
        "            'satisfaction_rating': random.randint(1, 5) if resolved else None,\n"
        "            'assigned_to': random.choice(['Support Team','Maria Jensen','Anders Holm']),\n"
        "        })\n\n"
        "print(f'CSAT: {len(nps_surveys)} NPS surveys, {len(support_tickets)} support tickets')"
    ),

    # ── Cell 8: Write Bronze ────────────────────────────
    _code_cell(
        "# Cell 8: Write Bronze Delta Tables\n\n"
        "bronze_tables = {\n"
        "    'crm_companies': crm_companies,\n"
        "    'crm_contacts': crm_contacts,\n"
        "    'crm_deals': crm_deals,\n"
        "    'crm_activities': crm_activities,\n"
        "    'campaigns': campaigns,\n"
        "    'leads': leads,\n"
        "    'web_sessions': web_sessions,\n"
        "    'budget': budget_rows,\n"
        "    'cost_centers': cost_centers,\n"
        "    'employees': employees,\n"
        "    'timesheets': timesheets,\n"
        "    'nps_surveys': nps_surveys,\n"
        "    'support_tickets': support_tickets,\n"
        "}\n\n"
        "for name, rows in bronze_tables.items():\n"
        "    df = spark.createDataFrame(rows)\n"
        "    df.write.format('delta').mode('overwrite').saveAsTable(f'bronze_{name}')\n"
        "    print(f'  bronze_{name}: {df.count()} rows')\n\n"
        "print(f'\\nBronze complete: {len(bronze_tables)} tables')"
    ),

    _md_cell("## Silver Layer -- Clean & Type"),

    # ── Cell 9: Silver transforms ───────────────────────
    _code_cell(
        "# Cell 9: Silver Transforms -- All Tables\n\n"
        "# CRM Companies\n"
        "df = spark.table('bronze_crm_companies')\n"
        "df = df.withColumn('annual_revenue_dkk', col('annual_revenue_dkk').cast('long'))\n"
        "df = df.withColumn('employees', col('employees').cast('int'))\n"
        "df = df.withColumn('created_date', to_date('created_date'))\n"
        "df.write.format('delta').mode('overwrite').saveAsTable('silver_crm_companies')\n"
        "print(f'silver_crm_companies: {df.count()}')\n\n"
        "# CRM Deals\n"
        "df = spark.table('bronze_crm_deals')\n"
        "df = df.withColumn('amount_dkk', col('amount_dkk').cast('long'))\n"
        "df = df.withColumn('weighted_amount_dkk', col('weighted_amount_dkk').cast('long'))\n"
        "df = df.withColumn('probability', col('probability').cast('double'))\n"
        "df = df.withColumn('created_date', to_date('created_date'))\n"
        "df = df.withColumn('close_date', to_date('close_date'))\n"
        "df = df.withColumn('deal_status',\n"
        "    when(col('stage') == 'closed_won', 'Won')\n"
        "    .when(col('stage') == 'closed_lost', 'Lost')\n"
        "    .otherwise('Open'))\n"
        "df.write.format('delta').mode('overwrite').saveAsTable('silver_crm_deals')\n"
        "print(f'silver_crm_deals: {df.count()}')\n\n"
        "# CRM Contacts & Activities\n"
        "for tbl in ['crm_contacts', 'crm_activities']:\n"
        "    df = spark.table(f'bronze_{tbl}')\n"
        "    df.write.format('delta').mode('overwrite').saveAsTable(f'silver_{tbl}')\n"
        "    print(f'silver_{tbl}: {df.count()}')\n\n"
        "# Campaigns\n"
        "df = spark.table('bronze_campaigns')\n"
        "df = df.withColumn('budget_dkk', col('budget_dkk').cast('long'))\n"
        "df = df.withColumn('spent_dkk', col('spent_dkk').cast('long'))\n"
        "df = df.withColumn('start_date', to_date('start_date'))\n"
        "df = df.withColumn('end_date', to_date('end_date'))\n"
        "df.write.format('delta').mode('overwrite').saveAsTable('silver_campaigns')\n"
        "print(f'silver_campaigns: {df.count()}')\n\n"
        "# Leads\n"
        "df = spark.table('bronze_leads')\n"
        "df = df.withColumn('score', col('score').cast('int'))\n"
        "df = df.withColumn('created_date', to_date('created_date'))\n"
        "df = df.withColumn('converted_date', to_date('converted_date'))\n"
        "df.write.format('delta').mode('overwrite').saveAsTable('silver_leads')\n"
        "print(f'silver_leads: {df.count()}')\n\n"
        "# Web Sessions\n"
        "df = spark.table('bronze_web_sessions')\n"
        "df = df.withColumn('session_month', to_date('session_month'))\n"
        "df = df.withColumn('sessions', col('sessions').cast('int'))\n"
        "df = df.withColumn('conversions', col('conversions').cast('int'))\n"
        "df.write.format('delta').mode('overwrite').saveAsTable('silver_web_sessions')\n"
        "print(f'silver_web_sessions: {df.count()}')\n\n"
        "# Budget\n"
        "df = spark.table('bronze_budget')\n"
        "for c in ['budget_dkk','actual_dkk','variance_dkk']:\n"
        "    df = df.withColumn(c, col(c).cast('long'))\n"
        "df.write.format('delta').mode('overwrite').saveAsTable('silver_budget')\n"
        "print(f'silver_budget: {df.count()}')\n\n"
        "# Employees\n"
        "df = spark.table('bronze_employees')\n"
        "df = df.withColumn('hire_date', to_date('hire_date'))\n"
        "df = df.withColumn('termination_date', to_date('termination_date'))\n"
        "df = df.withColumn('annual_salary_dkk', col('annual_salary_dkk').cast('long'))\n"
        "df.write.format('delta').mode('overwrite').saveAsTable('silver_employees')\n"
        "print(f'silver_employees: {df.count()}')\n\n"
        "# Timesheets\n"
        "df = spark.table('bronze_timesheets')\n"
        "df.write.format('delta').mode('overwrite').saveAsTable('silver_timesheets')\n"
        "print(f'silver_timesheets: {df.count()}')\n\n"
        "# NPS & Tickets\n"
        "df = spark.table('bronze_nps_surveys')\n"
        "df = df.withColumn('survey_date', to_date('survey_date'))\n"
        "df.write.format('delta').mode('overwrite').saveAsTable('silver_nps_surveys')\n"
        "print(f'silver_nps_surveys: {df.count()}')\n\n"
        "df = spark.table('bronze_support_tickets')\n"
        "df = df.withColumn('created_date', to_date('created_date'))\n"
        "df = df.withColumn('resolved_date', to_date('resolved_date'))\n"
        "df.write.format('delta').mode('overwrite').saveAsTable('silver_support_tickets')\n"
        "print(f'silver_support_tickets: {df.count()}')\n\n"
        "print('\\nSilver complete')"
    ),

    _md_cell("## Gold Layer -- Star Schema"),

    # ── Cell 10: dim_date ───────────────────────────────
    _code_cell(
        "# Cell 10: Gold -- dim_date\n\n"
        "from pyspark.sql import Row\n\n"
        "dates = []\n"
        "d = date(2023, 1, 1)\n"
        "end = date(2027, 12, 31)\n"
        "while d <= end:\n"
        "    dates.append(Row(\n"
        "        date_key=int(d.strftime('%Y%m%d')),\n"
        "        full_date=d,\n"
        "        year=d.year,\n"
        "        quarter=(d.month - 1) // 3 + 1,\n"
        "        month=d.month,\n"
        "        day=d.day,\n"
        "        day_name=d.strftime('%A'),\n"
        "        month_name=d.strftime('%B'),\n"
        "        day_of_week=d.isoweekday(),\n"
        "        week_of_year=d.isocalendar()[1],\n"
        "        year_quarter=f'{d.year}-Q{(d.month-1)//3+1}',\n"
        "        year_month=d.strftime('%Y-%m'),\n"
        "        is_weekend=d.isoweekday() >= 6,\n"
        "    ))\n"
        "    d += timedelta(days=1)\n\n"
        "dim_date = spark.createDataFrame(dates)\n"
        "dim_date.write.format('delta').mode('overwrite').saveAsTable('gold_dim_date')\n"
        "print(f'gold_dim_date: {dim_date.count()} rows')"
    ),

    # ── Cell 11: dim_customer ───────────────────────────
    _code_cell(
        "# Cell 11: Gold -- dim_customer\n\n"
        "comp = spark.table('silver_crm_companies')\n"
        "dim_cust = comp.withColumn('customer_key',\n"
        "    when(col('bc_customer_number').isNotNull(), col('bc_customer_number'))\n"
        "    .otherwise(col('crm_company_id')))\n"
        "dim_cust = dim_cust.withColumn('customer_status',\n"
        "    when(col('lifecycle_stage') == 'customer', 'Customer').otherwise('Prospect'))\n"
        "dim_cust = dim_cust.withColumn('country_group',\n"
        "    when(col('country') == 'DK', 'Denmark')\n"
        "    .when(col('country') == 'GB', 'UK')\n"
        "    .when(col('country') == 'US', 'USA')\n"
        "    .otherwise('Other'))\n"
        "dim_cust = dim_cust.withColumn('revenue_segment',\n"
        "    when(col('annual_revenue_dkk') >= 5_000_000, 'Enterprise')\n"
        "    .when(col('annual_revenue_dkk') >= 1_000_000, 'Mid-Market')\n"
        "    .otherwise('SMB'))\n"
        "dim_cust = dim_cust.withColumnRenamed('company_name', 'customer_name')\n"
        "dim_cust = dim_cust.select(\n"
        "    'customer_key', 'crm_company_id', 'bc_customer_number',\n"
        "    'customer_name', 'city', 'country', 'country_group',\n"
        "    'industry', 'segment', 'revenue_segment', 'customer_status',\n"
        "    'annual_revenue_dkk', 'employees', 'lead_source', 'owner')\n"
        "dim_cust.write.format('delta').mode('overwrite').saveAsTable('gold_dim_customer')\n"
        "print(f'gold_dim_customer: {dim_cust.count()} rows')"
    ),

    # ── Cell 12: dim_employee ───────────────────────────
    _code_cell(
        "# Cell 12: Gold -- dim_employee\n\n"
        "emp = spark.table('silver_employees')\n"
        "dim_emp = emp.withColumn('tenure_years',\n"
        "    spark_round(datediff(current_date(), col('hire_date')) / 365.25, 1))\n"
        "dim_emp = dim_emp.withColumn('status',\n"
        "    when(col('is_active') == True, 'Active').otherwise('Terminated'))\n"
        "dim_emp = dim_emp.select(\n"
        "    'employee_id', 'first_name', 'last_name', 'department', 'role',\n"
        "    'hire_date', 'termination_date', 'status', 'tenure_years',\n"
        "    'annual_salary_dkk', 'monthly_cost_dkk', 'city', 'employment_type')\n"
        "dim_emp.write.format('delta').mode('overwrite').saveAsTable('gold_dim_employee')\n"
        "print(f'gold_dim_employee: {dim_emp.count()} rows')"
    ),

    # ── Cell 13: dim_campaign + dim_department ──────────
    _code_cell(
        "# Cell 13: Gold -- dim_campaign + dim_department\n\n"
        "# dim_campaign\n"
        "camp = spark.table('silver_campaigns')\n"
        "dim_camp = camp.withColumn('roi_pct',\n"
        "    spark_round((col('spent_dkk') - col('budget_dkk')) / col('budget_dkk') * 100, 1))\n"
        "dim_camp.write.format('delta').mode('overwrite').saveAsTable('gold_dim_campaign')\n"
        "print(f'gold_dim_campaign: {dim_camp.count()} rows')\n\n"
        "# dim_department\n"
        "emp = spark.table('silver_employees').filter(col('is_active') == True)\n"
        "dim_dept = emp.groupBy('department').agg(\n"
        "    count('employee_id').alias('headcount'),\n"
        "    spark_round(avg('annual_salary_dkk'), 0).alias('avg_salary'),\n"
        "    spark_sum('monthly_cost_dkk').alias('total_monthly_cost'))\n"
        "dim_dept.write.format('delta').mode('overwrite').saveAsTable('gold_dim_department')\n"
        "print(f'gold_dim_department: {dim_dept.count()} rows')"
    ),

    # ── Cell 14: fact_pipeline ──────────────────────────
    _code_cell(
        "# Cell 14: Gold -- fact_pipeline\n\n"
        "deals = spark.table('silver_crm_deals')\n"
        "fact_pipe = deals.withColumn('customer_key',\n"
        "    when(col('bc_customer_number').isNotNull(), col('bc_customer_number'))\n"
        "    .otherwise(col('crm_company_id')))\n"
        "fact_pipe = fact_pipe.withColumn('created_date_key',\n"
        "    date_format(col('created_date'), 'yyyyMMdd').cast('int'))\n"
        "fact_pipe = fact_pipe.withColumn('close_date_key',\n"
        "    date_format(col('close_date'), 'yyyyMMdd').cast('int'))\n"
        "fact_pipe = fact_pipe.withColumn('days_in_pipeline',\n"
        "    datediff(col('close_date'), col('created_date')))\n"
        "fact_pipe = fact_pipe.select(\n"
        "    'deal_id', 'customer_key', 'crm_company_id',\n"
        "    'deal_name', 'amount_dkk', 'weighted_amount_dkk',\n"
        "    'stage', 'probability', 'deal_status',\n"
        "    'is_won', 'is_lost',\n"
        "    'created_date_key', 'close_date_key', 'days_in_pipeline',\n"
        "    'deal_owner', 'deal_source')\n"
        "fact_pipe.write.format('delta').mode('overwrite').saveAsTable('gold_fact_pipeline')\n"
        "print(f'gold_fact_pipeline: {fact_pipe.count()} rows')"
    ),

    # ── Cell 15: fact_marketing ─────────────────────────
    _code_cell(
        "# Cell 15: Gold -- fact_marketing\n\n"
        "from pyspark.sql.functions import sum as spark_sum, count, avg\n\n"
        "leads_df = spark.table('silver_leads')\n"
        "lead_agg = leads_df.groupBy('campaign_id').agg(\n"
        "    count('lead_id').alias('total_leads'),\n"
        "    spark_sum(when(col('status') == 'qualified', 1).otherwise(0)).alias('qualified_leads'),\n"
        "    spark_sum(when(col('status') == 'converted', 1).otherwise(0)).alias('converted_leads'),\n"
        "    spark_round(avg('score'), 1).alias('avg_score'))\n"
        "lead_agg = lead_agg.withColumn('conversion_rate',\n"
        "    spark_round(col('converted_leads') / col('total_leads'), 4))\n\n"
        "camp_spend = spark.table('silver_campaigns').select(\n"
        "    'campaign_id', 'campaign_type', 'budget_dkk', 'spent_dkk')\n\n"
        "fact_mkt = lead_agg.join(camp_spend, 'campaign_id', 'left')\n"
        "fact_mkt = fact_mkt.withColumn('cost_per_lead',\n"
        "    spark_round(col('spent_dkk') / col('total_leads'), 0).cast('int'))\n"
        "fact_mkt = fact_mkt.withColumn('cost_per_conversion',\n"
        "    when(col('converted_leads') > 0,\n"
        "         spark_round(col('spent_dkk') / col('converted_leads'), 0).cast('int'))\n"
        "    .otherwise(lit(0)))\n"
        "fact_mkt.write.format('delta').mode('overwrite').saveAsTable('gold_fact_marketing')\n"
        "print(f'gold_fact_marketing: {fact_mkt.count()} rows')"
    ),

    # ── Cell 16: fact_web_sessions ──────────────────────
    _code_cell(
        "# Cell 16: Gold -- fact_web_sessions\n\n"
        "web = spark.table('silver_web_sessions')\n"
        "fact_web = web.withColumn('date_key',\n"
        "    date_format(col('session_month'), 'yyyyMMdd').cast('int'))\n"
        "fact_web.write.format('delta').mode('overwrite').saveAsTable('gold_fact_web_sessions')\n"
        "print(f'gold_fact_web_sessions: {fact_web.count()} rows')"
    ),

    # ── Cell 17: fact_budget ────────────────────────────
    _code_cell(
        "# Cell 17: Gold -- fact_budget\n\n"
        "bgt = spark.table('silver_budget')\n"
        "fact_bgt = bgt.withColumn('date_key',\n"
        "    (col('year') * 10000 + col('month') * 100 + 1).cast('int'))\n"
        "fact_bgt = fact_bgt.withColumn('variance_pct',\n"
        "    when((col('actual_dkk').isNotNull()) & (col('budget_dkk') != 0),\n"
        "         spark_round((col('actual_dkk') - col('budget_dkk')) / expr('abs(budget_dkk)') * 100, 1))\n"
        "    .otherwise(lit(None)))\n"
        "fact_bgt.write.format('delta').mode('overwrite').saveAsTable('gold_fact_budget')\n"
        "print(f'gold_fact_budget: {fact_bgt.count()} rows')"
    ),

    # ── Cell 18: fact_hr ────────────────────────────────
    _code_cell(
        "# Cell 18: Gold -- fact_hr\n\n"
        "ts = spark.table('silver_timesheets')\n"
        "emp_costs = spark.table('silver_employees').select(\n"
        "    'employee_id', col('department').alias('emp_department'), 'monthly_cost_dkk')\n"
        "fact_hr = ts.join(emp_costs, 'employee_id', 'left')\n"
        "fact_hr = fact_hr.withColumn('cost_per_billable_hour',\n"
        "    when(col('billable_hours') > 0,\n"
        "         spark_round(col('monthly_cost_dkk') / col('billable_hours'), 0).cast('int'))\n"
        "    .otherwise(lit(0)))\n"
        "fact_hr = fact_hr.drop('emp_department')\n"
        "fact_hr.write.format('delta').mode('overwrite').saveAsTable('gold_fact_hr')\n"
        "print(f'gold_fact_hr: {fact_hr.count()} rows')"
    ),

    # ── Cell 19: fact_nps + fact_tickets ────────────────
    _code_cell(
        "# Cell 19: Gold -- fact_nps + fact_tickets\n\n"
        "# NPS\n"
        "nps = spark.table('silver_nps_surveys')\n"
        "fact_nps = nps.withColumn('date_key',\n"
        "    date_format(col('survey_date'), 'yyyyMMdd').cast('int'))\n"
        "fact_nps = fact_nps.withColumn('customer_key', col('bc_customer_number'))\n"
        "fact_nps = fact_nps.withColumn('is_promoter',\n"
        "    when(col('nps_category') == 'Promoter', 1).otherwise(0))\n"
        "fact_nps = fact_nps.withColumn('is_detractor',\n"
        "    when(col('nps_category') == 'Detractor', 1).otherwise(0))\n"
        "fact_nps.write.format('delta').mode('overwrite').saveAsTable('gold_fact_nps')\n"
        "print(f'gold_fact_nps: {fact_nps.count()} rows')\n\n"
        "# Tickets\n"
        "tkt = spark.table('silver_support_tickets')\n"
        "fact_tkt = tkt.withColumn('created_date_key',\n"
        "    date_format(col('created_date'), 'yyyyMMdd').cast('int'))\n"
        "fact_tkt = fact_tkt.withColumn('customer_key', col('bc_customer_number'))\n"
        "fact_tkt = fact_tkt.withColumn('resolution_days',\n"
        "    datediff(col('resolved_date'), col('created_date')))\n"
        "fact_tkt.write.format('delta').mode('overwrite').saveAsTable('gold_fact_tickets')\n"
        "print(f'gold_fact_tickets: {fact_tkt.count()} rows')"
    ),

    _md_cell("## Verification"),

    # ── Cell 20: Verification ───────────────────────────
    _code_cell(
        "# Cell 20: Verification\n\n"
        "gold_tables = [\n"
        "    'gold_dim_date', 'gold_dim_customer', 'gold_dim_employee',\n"
        "    'gold_dim_campaign', 'gold_dim_department',\n"
        "    'gold_fact_pipeline', 'gold_fact_marketing', 'gold_fact_web_sessions',\n"
        "    'gold_fact_budget', 'gold_fact_hr', 'gold_fact_nps', 'gold_fact_tickets',\n"
        "]\n\n"
        "print('=== GOLD TABLES ===')\n"
        "total = 0\n"
        "for tbl in gold_tables:\n"
        "    cnt = spark.table(tbl).count()\n"
        "    total += cnt\n"
        "    print(f'  {tbl:.<40} {cnt:>6,} rows')\n"
        "print(f'\\n  Total: {total:,} rows in {len(gold_tables)} tables')\n\n"
        "# Pipeline summary\n"
        "pipe = spark.table('gold_fact_pipeline')\n"
        "print(f'\\n--- Pipeline ---')\n"
        "pipe.groupBy('deal_status').agg(\n"
        "    count('deal_id').alias('deals'),\n"
        "    spark_sum('amount_dkk').alias('total_dkk')\n"
        ").show()\n\n"
        "# Marketing summary\n"
        "mkt = spark.table('gold_fact_marketing')\n"
        "print('--- Marketing ---')\n"
        "mkt.select(\n"
        "    spark_sum('total_leads').alias('total_leads'),\n"
        "    spark_sum('converted_leads').alias('converted'),\n"
        "    spark_round(avg('cost_per_lead'), 0).alias('avg_cpl')\n"
        ").show()\n\n"
        "print('Pipeline complete -- ready for semantic model')"
    ),
]


def generate() -> None:
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Synapse PySpark",
                "name": "synapse_pyspark",
            },
            "language_info": {
                "name": "python",
                "version": "3.10",
            },
            "microsoft": {
                "language": "python",
                "ms_spell_check": {"ms_spell_check_language": "en"},
            },
        },
        "cells": CELLS,
    }

    output_path = Path(OUTPUT_DIR) / "Akse_Demo_DW.ipynb"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(notebook, indent=1, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Notebook saved: {output_path}")
    print(f"Cells: {len(CELLS)} ({sum(1 for c in CELLS if c['cell_type'] == 'code')} code, "
          f"{sum(1 for c in CELLS if c['cell_type'] == 'markdown')} markdown)")
    print("\nImport in Fabric: Workspace -> Import -> Notebook -> select Akse_Demo_DW.ipynb")


if __name__ == "__main__":
    generate()
