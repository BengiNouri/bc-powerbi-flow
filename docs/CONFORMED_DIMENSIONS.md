# Conformed dimensions — pattern guide

> **Når en kunde har data fra flere systemer (BC + HubSpot + Mailchimp + …),
> skal de fysiske entiteter (kunder, medarbejdere, produkter) konsolideres
> til ÉN dimension i gold-laget. Det er det der gør at Pipeline-siden kan
> filtrere på den samme kunde som Sales-siden.**
>
> Dette dokument samler de patterns der virker, sorteret efter "lette
> tilfælde først".

---

## Når har du brug for conformed dimensions?

Symptomer der peger på behovet:

- Klienten har 2+ datasystemer (typisk BC + CRM)
- Pipeline-siden viser kundenavne fra HubSpot, men Sales-siden viser kundenavne fra BC — og de samme kunder fremstår dobbelt
- Slicer på "Customer" giver to versioner af hver kunde
- DAX `DISTINCTCOUNT(customer_key)` returnerer dobbelt så meget som virkeligheden

Hvis du ser noget af det → brug patterns nedenfor i transform-laget,
ikke i DAX. Conformede dimensioner skal eksistere i gold før Power BI
overhovedet bygger sin model.

---

## Pattern 1 — Direct key match (90% af tilfældene)

**Forudsætning:** Det ene system har en kolonne med det andet systems
primary key. Eksempel: HubSpot Company har et custom property
`bc_customer_number` der ER nøglen i BC.

**Implementation** (allerede i `transform_lib.py`):

```python
from transform_lib import conformed_customer_key

# silver_companies har både crm_company_id (HubSpot) og bc_customer_number (BC)
df["customer_key"] = conformed_customer_key(df, bc_col="bc_customer_number", crm_col="crm_company_id")
```

`conformed_customer_key` fungerer som:
1. Hvis `bc_customer_number` er populated → brug den (BC vinder)
2. Ellers fallback til `crm_company_id`

**Survivorship rule:** BC vinder fordi:
- BC er ofte system of record for accounting
- BC kundenummer er det der står på fakturaer
- HubSpot kontakter mod uknown BC kunder ofte er prospects (= ikke-kunder endnu)

**Verify:**
```python
from transform_lib import assert_unique_key
assert_unique_key(dim_customer, "customer_key", "gold_dim_customer")
```

---

## Pattern 2 — Fuzzy name match (når key-link mangler)

**Forudsætning:** Klienten har IKKE indsat BC-nummeret i HubSpot.
Eneste link er virksomhedsnavn — og det matcher kun ofte, ikke altid.

**Strategi:**
1. Normaliser navne (lowercase, strip whitespace, fjern "ApS"/"A/S"/"Ltd")
2. Brug `rapidfuzz` til at finde par med similarity > 90
3. Manuelt valider de >85 men <95 par i en SQL eller spreadsheet
4. Gem mappingen i en hand-curated `customer_mapping.csv` så fremtidige
   ingest-runs ikke skal genvalidere

**Skitse:**

```python
from rapidfuzz import process, fuzz

def normalize(name: str) -> str:
    s = name.lower().strip()
    for suffix in ("aps", "a/s", "ltd", "ltd.", "inc", "inc.", "gmbh"):
        s = s.removesuffix(" " + suffix)
    return s

bc_names = bc_df["customer_name"].apply(normalize)
crm_names = crm_df["company_name"].apply(normalize)

matches = []
for i, crm in enumerate(crm_names):
    best = process.extractOne(crm, bc_names, scorer=fuzz.ratio)
    if best and best[1] >= 90:
        matches.append((crm_df.iloc[i]["crm_company_id"],
                       bc_df.iloc[best[2]]["bc_customer_number"],
                       best[1]))
```

**Verify gate:** Send `matches.csv` til klientens sponsor for godkendelse
INDEN du bygger gold-laget. Falske matches på navne er en stor data quality
risk og bør aldrig være Claude's beslutning alene.

---

## Pattern 3 — Master Data Management (MDM) reference table

**Forudsætning:** Klienten har **både** BC + HubSpot + Mailchimp + et 4. system,
ingen direkte nøgler mellem dem, og en data steward som ejer datakvalitet.

**Strategi:**
- Opret en separat `gold_dim_customer_master` tabel med:
  - `master_customer_key` (surrogate UUID — vi opretter den)
  - `bc_customer_number` (nullable)
  - `crm_company_id` (nullable)
  - `mailchimp_list_member_id` (nullable)
  - `is_canonical` flag (når flere systemer har samme kunde, hvilken er sandheden?)
- Klienten vedligeholder denne tabel — fra Excel, fra en SaaS som Reltio,
  eller fra en custom Streamlit-app vi bygger
- Vores transform_lib læser den som en CSV-snapshot per run

**Når ikke at gøre det:** Hvis klienten ikke har en data steward der vil
eje denne tabel, så lav den IKKE. Den bliver forældet på 3 måneder og
forværrer datakvaliteten.

---

## Pattern 4 — One-to-many bridge (rare)

**Forudsætning:** Den samme fysiske kunde har flere HubSpot company IDs
(typisk fordi sælgere har lavet duplikater i CRM).

**Strategi:**
- Lav en `gold_bridge_customer_crm` tabel: `(customer_key, crm_company_id)`
  med many-to-one relation til `gold_dim_customer`
- Relate fact_pipeline til BRIDGE'en (ikke direkte til dim_customer)
- DAX skal bruge `USERELATIONSHIP` eller `TREATAS` for at navigere korrekt

**Cost:** Markant mere kompleks model. Brug kun hvis BCC har bekræftet
duplikatproblemet ikke kan løses i CRM-systemet selv.

---

## Survivorship rules — når 2 systemer har samme felt

For kunder hvor begge systemer har data, hvem vinder pr. felt?

| Felt | Vinder | Hvorfor |
|---|---|---|
| `customer_name` | BC | Står på fakturaer; det juridiske navn |
| `industry` | HubSpot | Sælgere kategoriserer mere granulart |
| `country` | BC | Bookings/billing-adresse |
| `annual_revenue_dkk` | BC | Verificeret tal |
| `lifecycle_stage` | HubSpot | CRM er sandhed for sales-stage |
| `customer_status` | BC | "Aktiv kunde" defineres af om der er fakturaer |
| `lead_source` | HubSpot | Sales tracking owner |

**Implementation:** I `transform_<client>.py`, lav en merge med eksplicit
suffix og pluk det rigtige felt per kolonne:

```python
merged = bc_df.merge(crm_df, on="customer_key", how="outer", suffixes=("_bc", "_crm"))
dim = pd.DataFrame({
    "customer_key":         merged["customer_key"],
    "customer_name":        merged["customer_name_bc"].fillna(merged["customer_name_crm"]),
    "industry":             merged["industry_crm"].fillna(merged["industry_bc"]),
    "country":              merged["country_bc"].fillna(merged["country_crm"]),
    "annual_revenue_dkk":   merged["annual_revenue_dkk_bc"].fillna(0),
    "lifecycle_stage":      merged["lifecycle_stage_crm"],
    "customer_status":      merged["customer_status_bc"].fillna("Prospect"),
    "lead_source":          merged["lead_source_crm"],
})
```

---

## Anti-patterns (lad være)

- ❌ **"Vi bruger bare customer_name som key"** — Navne ændrer sig (Acme A/S
  → Acme Group A/S), så history breaker. Brug surrogate keys.
- ❌ **Lave conformity i DAX med `LOOKUPVALUE`/`RELATED`** — Det skjuler
  data quality problemer og gør Refresh langsom. Gør det i transform-laget.
- ❌ **Stol på "fuzzy match score > 80%"** — Det matcher "Carlsberg" med
  "Carlsbergs Bryggerier" — ikke nødvendigvis samme entity. Klient skal
  validere.
- ❌ **Lade conformed dim drive af det største system** — F.eks. "vi har
  10.000 kunder i HubSpot men kun 200 i BC, så vi tager HubSpot som base".
  Du ender med 9.800 prospects der ikke er kunder. Brug aktivitet
  (last invoice date, last deal date) til at filtrere.

---

## Phase 0a checklist for multi-source clients

Når du opdager i Phase 0a at klienten har 2+ systemer:

- [ ] Spørg klient: "Har CRM jeres BC-nummer som property?"
- [ ] Hvis ja → Pattern 1, gå videre
- [ ] Hvis nej → spørg: "Har I et navn-match-script eller MDM-system?"
- [ ] Hvis nej → Pattern 2 + bed klient om data steward til validering
- [ ] Hvis stadig nej → reducer scope: byg rapporten på ÉT system først,
      conformity som Phase 2 engagement senere
- [ ] Dokumentér beslutning + survivorship rules i `semantic_model.md`
- [ ] Klient signerer survivorship reglerne FØR Phase 1 starter — ellers
      bliver det en konflikt i Phase F handover

---

## Hvor det er implementeret i koden

| Hvor | Hvad |
|---|---|
| `transform_lib.conformed_customer_key()` | Pattern 1 helper — BC wins, CRM fallback |
| `transform_lib.assert_unique_key()` | Verify gate til at fange duplikater |
| `transform_lib.assert_fk_coverage()` | Fanger fact-rows der peger på ikke-eksisterende dim |
| `transform_demo.gold_dim_customer()` | Worked example der bruger conformed_customer_key |
| `scan_all.py` | Multi-source scanner — bruges i Phase 0a til at opdage hvilke systemer der er i scope |

## Hvor dette dokument refereres

- `WORKFLOW.md` Phase 0a + 0b checklist
- `PLAYBOOK.md` Phase 2 (Silver → Gold) transformations
- `CREDENTIALS.md` "Multi-source clients" section
- `PLAYBOOK_DRYRUN.md` gap #5 — dette dokument lukker det gap
