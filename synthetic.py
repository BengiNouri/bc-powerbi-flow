"""
Synthetic data generator — realistic BC CRONUS-like data for testing.
Generates customers, items, vendors, invoices, orders, and invoice lines.
"""
import random
import uuid
from datetime import date, timedelta

random.seed(42)

DK_CITIES = ["København", "Aarhus", "Odense", "Aalborg", "Esbjerg", "Randers", "Kolding", "Horsens"]
INDUSTRIES = ["Manufacturing", "Office Supplies", "Technology", "Government", "Retail", "Logistics"]
ITEM_CATEGORIES = ["FURNITURE", "OFFICE", "IT", "SERVICE", "MISC"]
ITEM_NAMES = [
    "Skrivebord Standard", "Kontorstol Ergo", "Whiteboard 120x90", "Monitor Arm Dual",
    "Hæve-sænke bord", "Reol 4-hylde", "Mødebord 8-pers", "Skrivebordslampe LED",
    "Tastatur Ergonomisk", "Headset Pro", "Webcam HD", "Docking Station USB-C",
    "Printerpapir A4 5pk", "Kuglepen Sort 50pk", "Notesbog A5", "Mappesæt 10pk",
    "IT-service pr. time", "Installation Møbler", "Rengøring kontor", "Konsulenttime",
    "Gulvmåtte 200x300", "Gardiner Mørklæg.", "Plantekasse Stor", "Affaldsspand 60L",
]
CUSTOMER_NAMES = [
    "Kontorcentralen A/S", "Ravel Møbler", "Lauritzen Kontormøbler A/S",
    "Deerfield Graphics Company", "Guildford Water Department",
    "Nordic Office Solutions", "Scandinavian Interiors", "Baltic Workspace Group",
    "Dansk Erhverv Kontor", "Aarhus Kommune IT", "Odense Universitet",
    "Copenhagen Business Hub", "Vejle Kontorservice", "Roskilde Facility Mgmt",
    "Silkeborg Erhvervscenter",
]
VENDOR_NAMES = [
    "Scan Office Import", "Ergonomisk Design ApS", "Nordic Wood Products",
    "IT-Løsninger DK", "Copenhagen Supply Co", "Jysk Kontorforsyning",
    "Euro Office Wholesale", "Danish Furniture Group", "Tech Parts Denmark",
    "Green Office Solutions",
]


def _uid() -> str:
    return str(uuid.uuid4())


def _date_range(start_year: int = 2024, end_date: date | None = None) -> date:
    start = date(start_year, 1, 1)
    end = end_date or date(2026, 5, 22)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def gen_customers(n: int = 15) -> list[dict]:
    rows = []
    for i in range(n):
        rows.append({
            "id": _uid(),
            "number": str(10000 + i * 10000),
            "displayName": CUSTOMER_NAMES[i % len(CUSTOMER_NAMES)],
            "email": f"info@{CUSTOMER_NAMES[i % len(CUSTOMER_NAMES)].split()[0].lower()}.dk",
            "city": random.choice(DK_CITIES),
            "country": "DK" if i < 12 else random.choice(["GB", "US", "DE"]),
            "currencyCode": "DKK",
            "blocked": " " if random.random() > 0.1 else "All",
        })
    return rows


def gen_items(n: int = 80) -> list[dict]:
    rows = []
    for i in range(n):
        name = ITEM_NAMES[i % len(ITEM_NAMES)]
        cat = ITEM_CATEGORIES[i % len(ITEM_CATEGORIES)]
        item_type = "Service" if cat == "SERVICE" else "Inventory"
        unit_price = round(random.uniform(50, 15000), 2)
        unit_cost = round(unit_price * random.uniform(0.3, 0.75), 2)

        rows.append({
            "id": _uid(),
            "number": str(1000 + i),
            "displayName": f"{name} v{i // len(ITEM_NAMES) + 1}" if i >= len(ITEM_NAMES) else name,
            "type": item_type,
            "itemCategoryCode": cat,
            "unitPrice": unit_price,
            "unitCost": unit_cost,
            "inventory": random.randint(0, 500) if item_type == "Inventory" else 0,
        })
    return rows


def gen_vendors(n: int = 10) -> list[dict]:
    rows = []
    for i in range(n):
        rows.append({
            "id": _uid(),
            "number": str(20000 + i * 10000),
            "displayName": VENDOR_NAMES[i % len(VENDOR_NAMES)],
            "city": random.choice(DK_CITIES),
            "country": "DK" if i < 8 else random.choice(["DE", "SE"]),
            "currencyCode": "DKK",
        })
    return rows


def gen_invoices(customers: list[dict], n: int = 300) -> list[dict]:
    rows = []
    for i in range(n):
        cust = random.choice(customers)
        inv_date = _date_range()
        excl_tax = round(random.uniform(500, 80000), 2)
        vat = round(excl_tax * 0.25, 2)

        rows.append({
            "id": _uid(),
            "number": f"PSI-{100000 + i}",
            "invoiceDate": inv_date.isoformat(),
            "customerNumber": cust["number"],
            "customerName": cust["displayName"],
            "status": random.choice(["Paid", "Open", "Draft"]),
            "totalAmountExcludingTax": excl_tax,
            "totalAmountIncludingTax": round(excl_tax + vat, 2),
            "currencyCode": "DKK",
        })
    return rows


def gen_orders(customers: list[dict], n: int = 25) -> list[dict]:
    rows = []
    for i in range(n):
        cust = random.choice(customers)
        order_date = _date_range(2025)
        excl_tax = round(random.uniform(1000, 50000), 2)
        vat = round(excl_tax * 0.25, 2)

        rows.append({
            "id": _uid(),
            "number": f"PSO-{200000 + i}",
            "orderDate": order_date.isoformat(),
            "customerNumber": cust["number"],
            "customerName": cust["displayName"],
            "status": random.choice(["Open", "Released"]),
            "totalAmountExcludingTax": excl_tax,
            "totalAmountIncludingTax": round(excl_tax + vat, 2),
            "currencyCode": "DKK",
        })
    return rows


def gen_invoice_lines(invoices: list[dict], items: list[dict]) -> list[dict]:
    all_lines = []
    for inv in invoices:
        n_lines = random.randint(1, 5)
        for j in range(n_lines):
            item = random.choice(items)
            qty = random.randint(1, 20)
            unit_price = item["unitPrice"]
            amount = round(qty * unit_price, 2)
            discount = round(amount * random.choice([0, 0, 0, 0.05, 0.10]), 2)
            tax = round((amount - discount) * 0.25, 2)

            all_lines.append({
                "id": _uid(),
                "lineType": "Item",
                "lineObjectNumber": item["number"],
                "description": item["displayName"],
                "quantity": qty,
                "unitPrice": unit_price,
                "amountExcludingTax": round(amount - discount, 2),
                "discountAmount": discount,
                "totalTaxAmount": tax,
                "amountIncludingTax": round(amount - discount + tax, 2),
                "_invoiceId": inv["id"],
                "_invoiceNumber": inv["number"],
                "_invoiceDate": inv["invoiceDate"],
                "_customerNumber": inv["customerNumber"],
                "_customerName": inv["customerName"],
            })
    return all_lines


def generate_all() -> dict[str, list[dict]]:
    customers = gen_customers()
    items = gen_items()
    vendors = gen_vendors()
    invoices = gen_invoices(customers)
    orders = gen_orders(customers)
    invoice_lines = gen_invoice_lines(invoices, items)

    result = {
        "customers": customers,
        "items": items,
        "vendors": vendors,
        "salesInvoices": invoices,
        "salesOrders": orders,
        "invoice_lines": invoice_lines,
    }

    for name, rows in result.items():
        print(f"  Generated {name}: {len(rows)} rows")

    return result
