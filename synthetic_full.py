"""
Full Stack Synthetic Data Generator for Lodværket Demo DW
=====================================================
Generates realistic, interconnected data for 6 sources:
BC ERP, CRM, Marketing, Finance, HR, Customer Satisfaction

All data is aligned to CRONUS Danmark A/S customers from BC.
Dates span 2024-01-01 to 2026-05-22 for trend analysis.
Currency: DKK throughout.
"""
import random
import uuid
from datetime import date, timedelta, datetime
from typing import Any

random.seed(42)

# ── Shared reference data ──────────────────────────────────

BC_CUSTOMERS = [
    {"number": "10000", "name": "Kontorcentralen A/S", "city": "Nyborg", "country": "DK", "industry": "Government", "size": "Enterprise"},
    {"number": "20000", "name": "Ravel Mobler", "city": "Holbaek", "country": "DK", "industry": "Manufacturing", "size": "Mid-Market"},
    {"number": "30000", "name": "Lauritzen Kontormobler A/S", "city": "Koge", "country": "DK", "industry": "Office Supplies", "size": "Enterprise"},
    {"number": "40000", "name": "Deerfield Graphics Company", "city": "Hilliard", "country": "US", "industry": "Manufacturing", "size": "Mid-Market"},
    {"number": "50000", "name": "Guildford Water Department", "city": "Guildford", "country": "GB", "industry": "Technology", "size": "Enterprise"},
]

PROSPECTS = [
    {"number": None, "name": "Nordic Office Solutions", "city": "Aarhus", "country": "DK", "industry": "Office Supplies", "size": "Enterprise"},
    {"number": None, "name": "Scandinavian Interiors", "city": "Odense", "country": "DK", "industry": "Retail", "size": "Mid-Market"},
    {"number": None, "name": "Baltic Workspace Group", "city": "Copenhagen", "country": "DK", "industry": "Logistics", "size": "SMB"},
    {"number": None, "name": "Green Office Denmark", "city": "Aalborg", "country": "DK", "industry": "Sustainability", "size": "SMB"},
    {"number": None, "name": "TechHub Scandinavia", "city": "Aarhus", "country": "DK", "industry": "Technology", "size": "Mid-Market"},
]

ALL_COMPANIES = BC_CUSTOMERS + PROSPECTS

DEPARTMENTS = ["Sales", "Marketing", "Finance", "Operations", "IT", "HR", "Management"]

DEAL_STAGES = [
    ("lead", 0.05),
    ("qualified", 0.15),
    ("meeting_booked", 0.30),
    ("proposal_sent", 0.50),
    ("negotiation", 0.70),
    ("contract_sent", 0.85),
    ("closed_won", 1.0),
    ("closed_lost", 0.0),
]

CAMPAIGN_TYPES = ["Email", "LinkedIn", "Google Ads", "Webinar", "Event", "Content", "Referral"]
TICKET_CATEGORIES = ["Billing", "Delivery", "Product Quality", "Technical", "Returns", "General"]


def _uid() -> str:
    return str(uuid.uuid4())[:12]


def _rand_date(start: date = date(2024, 1, 1), end: date = date(2026, 5, 22)) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, max(delta, 1)))


def _rand_date_after(d: date, max_days: int = 90) -> date:
    return d + timedelta(days=random.randint(1, max_days))


# ── 1. CRM Data ────────────────────────────────────────────

def gen_crm_companies() -> list[dict]:
    rows = []
    for i, c in enumerate(ALL_COMPANIES):
        annual_rev = random.randint(1_000_000, 20_000_000) if c["size"] == "Enterprise" else \
                     random.randint(500_000, 5_000_000) if c["size"] == "Mid-Market" else \
                     random.randint(100_000, 1_000_000)
        rows.append({
            "crm_company_id": f"comp_{i+1:03d}",
            "bc_customer_number": c["number"],
            "company_name": c["name"],
            "city": c["city"],
            "country": c["country"],
            "industry": c["industry"],
            "segment": c["size"],
            "annual_revenue_dkk": annual_rev,
            "employees": random.randint(5, 300),
            "lifecycle_stage": "customer" if c["number"] else "lead",
            "lead_source": random.choice(CAMPAIGN_TYPES),
            "created_date": _rand_date(date(2023, 1, 1), date(2025, 6, 1)).isoformat(),
            "owner": random.choice(["Maria Jensen", "Anders Holm", "Sophie Nielsen", "Lars Pedersen"]),
        })
    return rows


def gen_crm_contacts(companies: list[dict]) -> list[dict]:
    first_names = ["Maria", "Anders", "Sophie", "Lars", "Mette", "Thomas", "Camilla", "Peter", "Anne", "Mikkel",
                   "Christine", "Henrik", "Louise", "Nikolaj", "Katrine", "Frederik"]
    last_names = ["Jensen", "Nielsen", "Hansen", "Pedersen", "Andersen", "Christensen", "Larsen", "Sorensen",
                  "Rasmussen", "Petersen", "Madsen", "Kristensen", "Olsen", "Thomsen"]
    titles = ["CEO", "CFO", "COO", "VP Sales", "Head of Procurement", "Office Manager", "IT Director",
              "Facility Manager", "Project Manager", "Buyer"]

    rows = []
    for comp in companies:
        n_contacts = random.randint(1, 4)
        for j in range(n_contacts):
            first = random.choice(first_names)
            last = random.choice(last_names)
            domain = comp["company_name"].split()[0].lower().replace(".", "")
            rows.append({
                "contact_id": _uid(),
                "crm_company_id": comp["crm_company_id"],
                "first_name": first,
                "last_name": last,
                "email": f"{first.lower()}.{last.lower()}@{domain}.dk",
                "title": random.choice(titles),
                "phone": f"+45 {random.randint(20,99)} {random.randint(10,99)} {random.randint(10,99)} {random.randint(10,99)}",
                "is_decision_maker": j == 0,
                "created_date": comp["created_date"],
            })
    return rows


def gen_crm_deals(companies: list[dict]) -> list[dict]:
    deal_names = [
        "Kontorindretning {year}", "Mobelfornyelse", "IT-udstyr pakke",
        "Servicekontrakt {year}", "Ergonomipakke {n} pladser",
        "Whiteboard-losning", "Moderumslosning", "Hojborde {n} stk",
        "Flytteservice", "Rengoeringspakke", "Designprojekt kontor",
    ]
    rows = []
    for comp in companies:
        n_deals = random.randint(1, 5)
        for _ in range(n_deals):
            created = _rand_date(date(2024, 6, 1), date(2026, 5, 1))
            close = _rand_date_after(created, 120)
            stage_idx = random.randint(0, len(DEAL_STAGES) - 1)
            stage_name, prob = DEAL_STAGES[stage_idx]

            # Force some closed deals
            is_won = stage_name == "closed_won"
            is_lost = stage_name == "closed_lost"

            amount = random.choice([25000, 45000, 68000, 95000, 120000, 185000, 250000, 350000, 500000])
            deal_template = random.choice(deal_names)
            deal_name = deal_template.format(year=close.year, n=random.choice([10, 20, 30, 50]))

            rows.append({
                "deal_id": _uid(),
                "crm_company_id": comp["crm_company_id"],
                "bc_customer_number": comp["bc_customer_number"],
                "deal_name": f"{comp['company_name']} - {deal_name}",
                "amount_dkk": amount,
                "weighted_amount_dkk": round(amount * prob),
                "stage": stage_name,
                "probability": prob,
                "is_won": is_won,
                "is_lost": is_lost,
                "created_date": created.isoformat(),
                "close_date": close.isoformat(),
                "deal_owner": comp.get("owner", "Maria Jensen"),
                "deal_source": random.choice(CAMPAIGN_TYPES),
            })
    return rows


def gen_crm_activities(contacts: list[dict], deals: list[dict]) -> list[dict]:
    activity_types = ["Email", "Call", "Meeting", "Note", "Task", "Demo"]
    rows = []
    for deal in deals:
        n_activities = random.randint(2, 8)
        deal_contacts = [c for c in contacts if c["crm_company_id"] == deal["crm_company_id"]]
        if not deal_contacts:
            continue
        for _ in range(n_activities):
            contact = random.choice(deal_contacts)
            act_type = random.choice(activity_types)
            act_date = _rand_date(
                date.fromisoformat(deal["created_date"]),
                min(date.fromisoformat(deal["close_date"]), date(2026, 5, 22))
            )
            rows.append({
                "activity_id": _uid(),
                "deal_id": deal["deal_id"],
                "contact_id": contact["contact_id"],
                "crm_company_id": deal["crm_company_id"],
                "activity_type": act_type,
                "activity_date": act_date.isoformat(),
                "duration_minutes": random.choice([5, 15, 30, 45, 60, 90]) if act_type in ("Call", "Meeting", "Demo") else 0,
                "outcome": random.choice(["Completed", "No answer", "Follow-up needed", "Positive", "Rescheduled"]),
                "owner": deal["deal_owner"],
            })
    return rows


# ── 2. Marketing Data ──────────────────────────────────────

def gen_campaigns() -> list[dict]:
    rows = []
    for i in range(20):
        start = _rand_date(date(2024, 1, 1), date(2026, 3, 1))
        end = _rand_date_after(start, 60)
        budget = random.choice([5000, 10000, 15000, 25000, 40000, 60000, 100000])
        spent = round(budget * random.uniform(0.6, 1.1))
        camp_type = random.choice(CAMPAIGN_TYPES)
        rows.append({
            "campaign_id": f"camp_{i+1:03d}",
            "campaign_name": f"{camp_type} - {start.strftime('%b %Y')} - {''.join(random.choices('ABCDEFGHIJ', k=3))}",
            "campaign_type": camp_type,
            "status": "Completed" if end < date(2026, 5, 1) else "Active",
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "budget_dkk": budget,
            "spent_dkk": spent,
            "target_audience": random.choice(["Enterprise DK", "Mid-Market DK", "All segments", "New leads"]),
            "owner": random.choice(["Marketing Team", "Sophie Nielsen", "Camilla Berg"]),
        })
    return rows


def gen_leads(campaigns: list[dict]) -> list[dict]:
    rows = []
    for camp in campaigns:
        n_leads = random.randint(5, 40)
        for j in range(n_leads):
            created = _rand_date(
                date.fromisoformat(camp["start_date"]),
                min(date.fromisoformat(camp["end_date"]), date(2026, 5, 22))
            )
            status = random.choices(
                ["new", "contacted", "qualified", "converted", "disqualified"],
                weights=[10, 20, 30, 25, 15]
            )[0]
            rows.append({
                "lead_id": _uid(),
                "campaign_id": camp["campaign_id"],
                "lead_name": f"Lead {_uid()[:4]}",
                "company_name": random.choice([c["name"] for c in ALL_COMPANIES] + ["Unknown Co", "Anonym ApS", "Test Firma"]),
                "lead_source": camp["campaign_type"],
                "status": status,
                "score": random.randint(10, 100),
                "created_date": created.isoformat(),
                "converted_date": _rand_date_after(created, 30).isoformat() if status == "converted" else None,
            })
    return rows


def gen_web_sessions(campaigns: list[dict]) -> list[dict]:
    rows = []
    for month_offset in range(28):  # Jan 2024 - May 2026
        year = 2024 + (month_offset // 12)
        month = (month_offset % 12) + 1
        if year == 2026 and month > 5:
            break

        sessions = random.randint(500, 3000)
        bounce_rate = round(random.uniform(0.25, 0.65), 3)
        pages_per_session = round(random.uniform(1.5, 5.5), 1)
        avg_duration_sec = random.randint(30, 300)

        for source in ["Organic", "Paid", "Social", "Direct", "Referral", "Email"]:
            source_pct = random.uniform(0.05, 0.4)
            source_sessions = int(sessions * source_pct)
            conversions = int(source_sessions * random.uniform(0.01, 0.08))
            rows.append({
                "session_month": f"{year}-{month:02d}-01",
                "source": source,
                "sessions": source_sessions,
                "new_users": int(source_sessions * random.uniform(0.4, 0.8)),
                "bounce_rate": bounce_rate,
                "pages_per_session": pages_per_session,
                "avg_duration_sec": avg_duration_sec,
                "conversions": conversions,
                "conversion_rate": round(conversions / max(source_sessions, 1), 4),
            })
    return rows


# ── 3. Finance Data ────────────────────────────────────────

def gen_budget() -> list[dict]:
    rows = []
    accounts = [
        ("Revenue", "Sales Revenue", 1),
        ("Revenue", "Service Revenue", 1),
        ("COGS", "Cost of Goods Sold", -1),
        ("COGS", "Direct Labor", -1),
        ("OpEx", "Marketing", -1),
        ("OpEx", "Salaries", -1),
        ("OpEx", "Rent & Facilities", -1),
        ("OpEx", "IT & Software", -1),
        ("OpEx", "Travel", -1),
        ("OpEx", "Other", -1),
    ]

    for year in [2024, 2025, 2026]:
        for month in range(1, 13):
            if year == 2026 and month > 12:
                break
            for category, account, sign in accounts:
                if category == "Revenue":
                    base = random.randint(300_000, 800_000)
                elif category == "COGS":
                    base = random.randint(150_000, 400_000)
                else:
                    base = random.randint(20_000, 200_000)

                # Growth trend
                growth = 1 + (year - 2024) * 0.08 + month * 0.005
                budget_amt = round(base * growth)
                actual_amt = round(budget_amt * random.uniform(0.85, 1.15)) if (year < 2026 or month <= 5) else None

                rows.append({
                    "budget_id": _uid(),
                    "year": year,
                    "month": month,
                    "period": f"{year}-{month:02d}",
                    "category": category,
                    "account": account,
                    "budget_dkk": budget_amt * sign,
                    "actual_dkk": actual_amt * sign if actual_amt else None,
                    "variance_dkk": (actual_amt - budget_amt) * sign if actual_amt else None,
                    "department": random.choice(DEPARTMENTS[:4]),
                })
    return rows


def gen_cost_centers() -> list[dict]:
    return [
        {"cost_center_id": f"cc_{i+1:02d}", "name": dept, "manager": f"Manager {dept}",
         "annual_budget_dkk": random.randint(500_000, 5_000_000)}
        for i, dept in enumerate(DEPARTMENTS)
    ]


# ── 4. HR Data ─────────────────────────────────────────────

def gen_employees() -> list[dict]:
    first_names = ["Maria", "Anders", "Sophie", "Lars", "Mette", "Thomas", "Camilla", "Peter",
                   "Anne", "Mikkel", "Christine", "Henrik", "Louise", "Nikolaj", "Katrine",
                   "Frederik", "Emma", "Oliver", "Ida", "Victor", "Clara", "Magnus",
                   "Sofie", "Sebastian", "Freja", "Noah", "Alma", "Oscar", "Ella", "William"]
    last_names = ["Jensen", "Nielsen", "Hansen", "Pedersen", "Andersen", "Christensen", "Larsen",
                  "Sorensen", "Rasmussen", "Petersen", "Madsen", "Kristensen"]
    roles = {
        "Sales": ["Account Executive", "Sales Manager", "SDR", "VP Sales"],
        "Marketing": ["Marketing Manager", "Content Specialist", "Digital Marketing", "CMO"],
        "Finance": ["Controller", "Accountant", "CFO", "Financial Analyst"],
        "Operations": ["Operations Manager", "Logistics Coordinator", "Warehouse Lead"],
        "IT": ["Developer", "IT Manager", "Data Engineer", "CTO"],
        "HR": ["HR Manager", "Recruiter", "HR Coordinator"],
        "Management": ["CEO", "COO", "Office Manager"],
    }

    rows = []
    emp_id = 1000
    for dept in DEPARTMENTS:
        n_emps = random.randint(3, 8)
        dept_roles = roles.get(dept, ["Specialist"])
        for _ in range(n_emps):
            emp_id += 1
            hire_date = _rand_date(date(2018, 1, 1), date(2026, 1, 1))
            is_active = random.random() > 0.08
            salary = random.randint(25_000, 75_000) * 12  # Annual
            rows.append({
                "employee_id": f"EMP-{emp_id}",
                "first_name": random.choice(first_names),
                "last_name": random.choice(last_names),
                "department": dept,
                "role": random.choice(dept_roles),
                "hire_date": hire_date.isoformat(),
                "termination_date": _rand_date_after(hire_date, 365).isoformat() if not is_active else None,
                "is_active": is_active,
                "annual_salary_dkk": salary,
                "monthly_cost_dkk": round(salary / 12 * 1.3),  # incl. social costs
                "city": random.choice(["Copenhagen", "Aarhus", "Odense", "Aalborg"]),
                "employment_type": random.choices(["Full-time", "Part-time", "Contract"], weights=[80, 10, 10])[0],
            })
    return rows


def gen_timesheets(employees: list[dict]) -> list[dict]:
    rows = []
    active_emps = [e for e in employees if e["is_active"]]
    for emp in active_emps:
        for month_offset in range(6):  # Last 6 months
            d = date(2026, 5, 22) - timedelta(days=30 * month_offset)
            period = f"{d.year}-{d.month:02d}"
            billable = random.randint(100, 160)
            internal = random.randint(10, 40)
            rows.append({
                "timesheet_id": _uid(),
                "employee_id": emp["employee_id"],
                "department": emp["department"],
                "period": period,
                "billable_hours": billable,
                "internal_hours": internal,
                "total_hours": billable + internal,
                "utilization_pct": round(billable / (billable + internal) * 100, 1),
            })
    return rows


# ── 5. Customer Satisfaction ───────────────────────────────

def gen_nps_surveys(companies: list[dict]) -> list[dict]:
    rows = []
    for comp in companies:
        if not comp.get("bc_customer_number"):
            continue
        for q in range(1, 9):  # Q1 2024 - Q4 2025 + Q1-Q2 2026
            year = 2024 + (q - 1) // 4
            quarter = ((q - 1) % 4) + 1
            if year > 2026 or (year == 2026 and quarter > 2):
                break
            score = random.randint(1, 10)
            rows.append({
                "survey_id": _uid(),
                "bc_customer_number": comp["bc_customer_number"],
                "company_name": comp["company_name"],
                "survey_date": f"{year}-{(quarter-1)*3+2:02d}-15",
                "year": year,
                "quarter": quarter,
                "nps_score": score,
                "nps_category": "Promoter" if score >= 9 else "Passive" if score >= 7 else "Detractor",
                "comment": random.choice([
                    None, "Great service", "Slow delivery", "Good quality",
                    "Price too high", "Very satisfied", "Could improve support",
                    "Excellent products", "Average experience",
                ]),
            })
    return rows


def gen_support_tickets(companies: list[dict]) -> list[dict]:
    rows = []
    for comp in companies:
        if not comp.get("bc_customer_number"):
            continue
        n_tickets = random.randint(3, 20)
        for _ in range(n_tickets):
            created = _rand_date(date(2024, 6, 1), date(2026, 5, 20))
            resolved = _rand_date_after(created, 14) if random.random() > 0.1 else None
            priority = random.choices(["Low", "Medium", "High", "Critical"], weights=[30, 40, 20, 10])[0]
            sla_hours = {"Low": 48, "Medium": 24, "High": 8, "Critical": 2}[priority]
            response_hours = random.uniform(0.5, sla_hours * 1.5)
            rows.append({
                "ticket_id": f"TKT-{_uid()[:6].upper()}",
                "bc_customer_number": comp["bc_customer_number"],
                "company_name": comp["company_name"],
                "category": random.choice(TICKET_CATEGORIES),
                "priority": priority,
                "status": "Resolved" if resolved else "Open",
                "created_date": created.isoformat(),
                "resolved_date": resolved.isoformat() if resolved else None,
                "response_time_hours": round(response_hours, 1),
                "sla_target_hours": sla_hours,
                "sla_met": response_hours <= sla_hours,
                "satisfaction_rating": random.randint(1, 5) if resolved else None,
                "assigned_to": random.choice(["Support Team", "Maria Jensen", "Anders Holm"]),
            })
    return rows


# ── Main generator ─────────────────────────────────────────

def generate_full_stack() -> dict[str, list[dict]]:
    print("Generating full stack demo data...\n")

    # CRM
    crm_companies = gen_crm_companies()
    crm_contacts = gen_crm_contacts(crm_companies)
    crm_deals = gen_crm_deals(crm_companies)
    crm_activities = gen_crm_activities(crm_contacts, crm_deals)

    # Marketing
    campaigns = gen_campaigns()
    leads = gen_leads(campaigns)
    web_sessions = gen_web_sessions(campaigns)

    # Finance
    budget = gen_budget()
    cost_centers = gen_cost_centers()

    # HR
    employees = gen_employees()
    timesheets = gen_timesheets(employees)

    # Customer Satisfaction (use crm_companies which has bc_customer_number)
    customer_companies = [c for c in crm_companies if c["bc_customer_number"]]
    nps_surveys = gen_nps_surveys(customer_companies)
    support_tickets = gen_support_tickets(customer_companies)

    result = {
        # CRM
        "crm_companies": crm_companies,
        "crm_contacts": crm_contacts,
        "crm_deals": crm_deals,
        "crm_activities": crm_activities,
        # Marketing
        "campaigns": campaigns,
        "leads": leads,
        "web_sessions": web_sessions,
        # Finance
        "budget": budget,
        "cost_centers": cost_centers,
        # HR
        "employees": employees,
        "timesheets": timesheets,
        # Customer Satisfaction
        "nps_surveys": nps_surveys,
        "support_tickets": support_tickets,
    }

    for name, rows in result.items():
        print(f"  {name:.<30} {len(rows):>5} rows")

    print(f"\n  Total: {sum(len(r) for r in result.values()):,} rows across {len(result)} tables")
    return result


if __name__ == "__main__":
    data = generate_full_stack()
