# DAX-mønstre — kogebog

> **Formål.** Når Claude (eller et menneske) skal skrive measures for kunde nr.
> 2, 3, 4 fra bunden, er det her listen at slå op i. Hvert mønster er
> kategoriseret efter *hvad det måler*, ikke hvad det hedder hos en specifik
> kunde. Konkrete eksempler er taget fra `dax_measures_full.dax`
> (CRONUS-demoen).
>
> **Læseguide.** Hvert mønster har samme struktur:
> - **Hvornår**: hvilken slags spørgsmål svarer mønstret på
> - **Skabelon**: abstrakt DAX med `<pladsholdere>`
> - **Eksempel**: konkret kode fra `dax_measures_full.dax`
> - **Format string**: anbefalet `formatString` — se også `docs/PBI_PATTERNS.md`
> - **Display folder**: hvor det hører hjemme i `_Measures`-tabellen

> ⚠️ **Læs altid `docs/PBI_PATTERNS.md` før du skriver format strings.** Card
> visuals understøtter ikke farvetokens; brug plain `+0.0%;-0.0%;0.0%` på
> cards, og `[Green]+0.0%;[Red]-0.0%` kun i Table/Matrix.

---

## Indhold

1. [Aggregeringer (sum, count, average)](#1-aggregeringer)
2. [Filtreret aggregering](#2-filtreret-aggregering)
3. [Forhold og rater (DIVIDE)](#3-forhold-og-rater)
4. [Tællere med betingelse](#4-tællere-med-betingelse)
5. [Sammensatte KPI'er (VAR + RETURN)](#5-sammensatte-kpier)
6. [Tidsintelligens (YTD, MTD, YoY)](#6-tidsintelligens)
7. [Sammenligning mod budget/mål (variance)](#7-variance)
8. [Distinct count](#8-distinct-count)
9. [Vægtede beregninger](#9-vægtede-beregninger)
10. [Ranglister og top-N](#10-ranglister)
11. [Format strings — opslagsbord](#11-format-strings-opslagsbord)
12. [Display folder-konvention](#12-display-folder-konvention)

---

## 1. Aggregeringer

### 1A · Sum af en faktakolonne

**Hvornår.** Du har en fakta-tabel hvor hver række repræsenterer en transaktion,
og du vil summere et beløb (omsætning, omkostning, mængde).

**Skabelon.**
```dax
<Måle-navn> =
SUMX ( <fact_tabel>, <fact_tabel>[<beløbskolonne>] )
```

**Eksempel.**
```dax
Pipeline Value =
SUMX ( gold_fact_pipeline, gold_fact_pipeline[amount_dkk] )

Marketing Spend =
SUMX ( gold_fact_marketing, gold_fact_marketing[spent_dkk] )
```

**Hvorfor SUMX og ikke SUM?** SUMX itererer pr. række i kontekst — virker også
korrekt når rækken kommer fra en sammensat udtryk (fx FILTER). SUM er ren
kolonneaggregering. SUMX er sikrere som default når du komponerer measures
ovenpå measures.

**Format string.** `#,##0 kr` (DKK), `#,##0.00` (decimaler), `#,##0` (heltal).
**Display folder.** Følger forretningsområdet (Sales / Marketing / HR / …).

---

### 1B · Antal rækker (count)

**Hvornår.** Antal transaktioner, leads, tickets, deals.

**Skabelon.**
```dax
<Antal> = COUNTROWS ( <fact_tabel> )
```

**Eksempel.**
```dax
Deal Count = COUNTROWS ( gold_fact_pipeline )
Campaign Count = COUNTROWS ( gold_fact_marketing )
```

**Format string.** `#,##0`

---

### 1C · Gennemsnit (AVERAGEX)

**Hvornår.** Gennemsnit på række-niveau af en numerisk kolonne (dage,
varighed, score, procent).

**Skabelon.**
```dax
<Avg ...> =
AVERAGEX ( <fact_tabel>, <fact_tabel>[<numerisk_kolonne>] )
```

**Eksempel.**
```dax
Avg Days in Pipeline =
AVERAGEX ( gold_fact_pipeline, gold_fact_pipeline[days_in_pipeline] )

Avg Bounce Rate =
AVERAGEX ( gold_fact_web_sessions, gold_fact_web_sessions[bounce_rate] )
```

**Format string.** `#,##0.0` for dage/score, `0.0%` for rater (men *kun* hvis
kolonnen er en fraction 0-1 — se gap #14 i PLAYBOOK_DRYRUN.md). For
procent-værdier der allerede ligger 0-100 brug `#,##0.00`.

---

## 2. Filtreret aggregering

**Hvornår.** Du vil have summen *under et bestemt forhold* (status, kategori,
flag).

**Skabelon.**
```dax
<Måle> =
CALCULATE (
    [<Base måle>],
    <tabel>[<kolonne>] = "<værdi>"
)
```

**Eksempel.**
```dax
Won Revenue =
CALCULATE (
    [Pipeline Value],
    gold_fact_pipeline[deal_status] = "Won"
)

Open Pipeline =
CALCULATE (
    [Pipeline Value],
    gold_fact_pipeline[deal_status] = "Open"
)
```

**Variant — flere værdier med IN.**
```dax
Closed Deals =
CALCULATE (
    [Deal Count],
    gold_fact_pipeline[deal_status] IN { "Won", "Lost" }
)
```

**Hvornår CALCULATE ikke er nok.** Hvis filtret skal afhænge af *andet* end en
kolonneværdi (fx flere kolonner kombineret), brug FILTER inde i CALCULATE:
```dax
CALCULATE ( [Pipeline Value], FILTER ( gold_fact_pipeline,
    gold_fact_pipeline[is_open] && gold_fact_pipeline[amount_dkk] > 100000 ) )
```

---

## 3. Forhold og rater

**Hvornår.** Win rate, conversion rate, margin, hvilken som helst procent der
er én ting delt med en anden.

**Skabelon — altid DIVIDE, aldrig `/`.**
```dax
<Rate> = DIVIDE ( [<tæller>], [<nævner>], 0 )
```

**Eksempel.**
```dax
Lead Conversion Rate =
DIVIDE ( [Converted Leads], [Total Leads], 0 )

Web Conversion Rate =
DIVIDE ( [Total Web Conversions], [Total Sessions], 0 )

Gross Margin % =
DIVIDE ( [Gross Profit Actual], [Revenue Actual], 0 )
```

**Hvorfor DIVIDE og ikke `/`?** DIVIDE returnerer 3. argument (her `0`) i stedet
for at fejle på division med nul. Den tomme nævner er **aldrig** en grund til
at lade rapporten gå i stykker.

**Format string.**
- På cards: `0.0%` eller `0.00%` (input er fraction 0-1).
- I tabeller hvor man ønsker farve: `[Green]+0.0%;[Red]-0.0%;0.0%`.

⚠️ Hvis input er allerede skaleret (15.5 i stedet for 0.155), brug
`#,##0.00 %` eller `#,##0.0` — se PLAYBOOK_DRYRUN.md gap #14.

---

## 4. Tællere med betingelse

**Hvornår.** "Hvor mange [X] havde [betingelse]?" — fx antal aktive
medarbejdere, antal kritiske tickets, antal vundne deals.

**Skabelon A — flag-kolonne (TRUE/FALSE).**
```dax
<Antal X> =
CALCULATE (
    COUNTROWS ( <fact_tabel> ),
    <fact_tabel>[<flag>] = TRUE
)
```

**Skabelon B — kategori-værdi.**
```dax
<Antal X> =
CALCULATE (
    COUNTROWS ( <fact_tabel> ),
    <fact_tabel>[<kolonne>] = "<værdi>"
)
```

**Eksempel.**
```dax
Open Deals =
CALCULATE ( [Deal Count], gold_fact_pipeline[deal_status] = "Open" )

Critical Tickets =
CALCULATE ( [Total Tickets], gold_fact_tickets[priority] = "Critical" )
```

**Format string.** `#,##0`

---

## 5. Sammensatte KPI'er (VAR + RETURN)

**Hvornår.** Når en KPI kræver flere mellemregninger der ikke kan udtrykkes
som en enkelt CALCULATE. Brug VAR til at navngive hvert mellemtrin — det
gør formlen *læselig* og kan debugges trin for trin.

**Skabelon.**
```dax
<KPI> =
VAR <_a> = <delberegning A>
VAR <_b> = <delberegning B>
VAR <_c> = <delberegning C>
RETURN
    <kombination af _a, _b, _c>
```

**Eksempel — Win Rate.**
```dax
Win Rate =
VAR _won = CALCULATE ( COUNTROWS ( gold_fact_pipeline ),
                       gold_fact_pipeline[is_won] = TRUE )
VAR _closed = CALCULATE ( COUNTROWS ( gold_fact_pipeline ),
                          gold_fact_pipeline[deal_status] IN { "Won", "Lost" } )
RETURN
    DIVIDE ( _won, _closed, 0 )
```

**Eksempel — NPS Score (klassisk NPS-formel).**
```dax
NPS Score =
VAR _promoters = SUMX ( gold_fact_nps, gold_fact_nps[is_promoter] )
VAR _detractors = SUMX ( gold_fact_nps, gold_fact_nps[is_detractor] )
VAR _total = COUNTROWS ( gold_fact_nps )
RETURN
    DIVIDE ( _promoters - _detractors, _total, 0 ) * 100
```

**Eksempel — Turnover Rate.**
```dax
Turnover Rate =
VAR _terminated = CALCULATE ( COUNTROWS ( gold_dim_employee ),
                              gold_dim_employee[status] = "Terminated" )
VAR _total = COUNTROWS ( gold_dim_employee )
RETURN
    DIVIDE ( _terminated, _total, 0 )
```

**Konvention.** VAR-navne starter med `_` så de er lette at adskille fra
tabel- og kolonnenavne i komplekse formler.

---

## 6. Tidsintelligens

> **Forudsætning.** En markeret date-dimension. Brug
> `table_operations.MarkAsDateTable` på `gold_dim_date` med `date`-kolonnen.
> Uden den fejler tidsintelligens-funktioner stille (returnerer blank).

### 6A · Year-To-Date (YTD)

**Skabelon.**
```dax
<Måle> YTD =
TOTALYTD ( [<Base måle>], gold_dim_date[date] )
```

**Eksempel.**
```dax
Revenue YTD =
TOTALYTD ( [Revenue], gold_dim_date[date] )
```

### 6B · Forrige år (samme periode)

```dax
<Måle> LY =
CALCULATE ( [<Base måle>], SAMEPERIODLASTYEAR ( gold_dim_date[date] ) )
```

### 6C · Vækst år-over-år

```dax
<Måle> YoY % =
VAR _now = [<Base måle>]
VAR _ly  = CALCULATE ( [<Base måle>], SAMEPERIODLASTYEAR ( gold_dim_date[date] ) )
RETURN
    DIVIDE ( _now - _ly, _ly, 0 )
```

**Format string.** `+0.0%;-0.0%;0.0%` (på cards — ingen farvetokens). I
tabel/matrix kan du tilføje `[Green]`/`[Red]`.

**Display folder.** `Time Intelligence` (alle YTD/LY/YoY-measures hører sammen).

---

## 7. Variance — actual mod budget/mål

### 7A · Variance i kroner

```dax
<Variance> = [Actual Total] - [Budget Total]
```

### 7B · Variance i procent

```dax
<Variance %> = DIVIDE ( [Variance], ABS ( [Budget Total] ), 0 )
```

> **Bemærk ABS.** Hvis budgettet kan være negativt (fx COGS som kostpost),
> giver `DIVIDE (variance, budget)` forkerte fortegn på resultatet.
> ABS sikrer at variance-procenten altid har samme fortegn som variance
> i kroner.

**Format string** på cards: `+0.0%;-0.0%;0.0%`. I tabel:
`[Green]+0.0%;[Red]-0.0%;0.0%`.

---

## 8. Distinct count

**Hvornår.** "Hvor mange unikke kunder/produkter/medarbejdere?" — ikke antal
rækker, men antal unikke værdier i en kolonne.

**Skabelon.**
```dax
<Antal unikke X> =
DISTINCTCOUNT ( <tabel>[<id-kolonne>] )
```

**Eksempel.**
```dax
Total Headcount =
CALCULATE (
    DISTINCTCOUNT ( gold_dim_employee[employee_id] ),
    gold_dim_employee[status] = "Active"
)
```

> **Performance-note.** DISTINCTCOUNT er dyr i memory. På store fact-tabeller
> (millioner af rækker) overvej at lade gold-laget pre-aggregere unikke ID'er
> ind i en dimensionel kolonne i stedet.

---

## 9. Vægtede beregninger

**Hvornår.** Pipeline-værdi vægtet med vinder-sandsynlighed, omkostning vægtet
med tid, score vægtet med antal responder.

**Skabelon — vægt på række-niveau allerede i gold-laget.**
```dax
<Vægtet sum> =
SUMX ( <fact_tabel>, <fact_tabel>[<vægtet_kolonne>] )
```

**Eksempel.**
```dax
Weighted Pipeline =
SUMX ( gold_fact_pipeline, gold_fact_pipeline[weighted_amount_dkk] )
```

> **Designanbefaling.** Beregn helst vægtningen i gold-laget (én kolonne pr.
> række: `weighted_amount = amount × probability`). DAX-versionen
> `SUMX(fact, fact[amount] * fact[prob])` virker også, men flytter beregning
> til query-time og bliver langsommere på store rapporter.

---

## 10. Ranglister og top-N

**Hvornår.** "Top 5 kunder efter omsætning", "Top 10 produkter med højst
margin", "Bundlinje pr. afdeling sorteret".

**Skabelon.**
```dax
<Måle> Rank =
RANKX (
    ALL ( <dim>[<id-kolonne>] ),
    [<Base måle>],
    ,
    DESC,
    DENSE
)
```

**Eksempel.**
```dax
Customer Revenue Rank =
RANKX (
    ALL ( gold_dim_customer[customer_id] ),
    [Revenue],
    ,
    DESC,
    DENSE
)
```

**Visning af top N** — brug `TOPN` direkte i en tabel-måling, eller filtrer
visualen med rank ≤ N i visual-niveau filter.

---

## 11. Format strings — opslagsbord

| Datatype / kontekst | formatString | Eksempel-output |
|---|---|---|
| Heltal | `#,##0` | `1.234` |
| Decimaltal (1 decimal) | `#,##0.0` | `73,4` |
| Decimaltal (2 decimaler) | `#,##0.00` | `73,42` |
| DKK på card | `#,##0 kr` | `5.000.000 kr` |
| DKK alternativ | `#,##0 DKK` | `5.000.000 DKK` |
| Procent på card (input 0-1) | `0.0%` | `24,5%` |
| Signed % på card | `+0.0%;-0.0%;0.0%` | `+5,2%` / `-3,1%` |
| Signed % i tabel/matrix (med farve) | `[Green]+0.0%;[Red]-0.0%;0.0%` | grøn `+5,2%`, rød `-3,1%` |
| Signed antal | `+0;-0;0` | `+5`, `-3`, `0` |
| Dato (dansk) | `dd-MM-yyyy` | `24-05-2026` |

⚠️ **Forbudte mønstre:**
- `[Green]...` *på card visuals* — rendereres som rå tekst, ikke farve.
- Hex-koder i farvetokens: `[#003F5C]...` — virker ikke; kun de 8 navngivne
  farver (`Red`, `Green`, `Blue`, `Yellow`, `Magenta`, `Cyan`, `Black`,
  `White`).
- Unicode-pile (`▲▼`) i format strings — locale-afhængigt parserchaos.
  Brug en separat tekst-måling der returnerer pilen og placér den ved siden
  af tallet.

> Se `docs/PBI_PATTERNS.md` for det fulde sæt af DO/DON'T patterns og
> lessons learned (2026-05-23-sessionen).

---

## 12. Display folder-konvention

Læg measures i `_Measures`-tabellen med følgende `displayFolder`-værdi for at
holde modellen overskuelig for forretningsbrugere:

| Folder | Indhold | Eksempel |
|---|---|---|
| `Sales` | Omsætning, ordrer, fakturalinjer | `Revenue`, `Order Count`, `Avg Order Value` |
| `Pipeline` | CRM deals, stadier, win-rates | `Pipeline Value`, `Win Rate`, `Weighted Pipeline` |
| `Marketing` | Leads, kampagner, web | `Total Leads`, `Lead Conversion Rate`, `Marketing Spend` |
| `Finance` | Budget, actual, P&L | `Budget Total`, `Operating Profit`, `Budget Variance %` |
| `HR` | Headcount, utilization, løn | `Total Headcount`, `Avg Utilization`, `Turnover Rate` |
| `Customer Support` | NPS, tickets, SLA | `NPS Score`, `Total Tickets`, `SLA Met Rate` |
| `Time Intelligence` | YTD, LY, YoY-varianter | `Revenue YTD`, `Revenue YoY %`, `Revenue LY` |

**Navnekonvention.** Display-navn på engelsk i Title Case ("Revenue", "Pipeline
Value"). Display folder også engelsk. Det matcher PBI's UI og holder
modellen sprogagnostisk — lokalisering håndteres i visual-titler og
labels via `design_decisions.yaml`.

---

## Tjekliste — før du committer en ny måling

1. **Format string er i tabellen ovenfor.** Hvis ikke, har du tilføjet en ny —
   verifér i PBI Desktop først, før du genererer 50 measures med samme mønster.
2. **DIVIDE bruges altid hvor der kan opstå division med nul.** Aldrig `/`.
3. **VAR-navne starter med underscore.** `_won`, `_total`, `_promoters`.
4. **Display folder er sat** på alle measures.
5. **Tidsintelligens har MarkAsDateTable** — kør det igen hvis du ikke er sikker.
6. **Eksporter TMDL efter MCP-ændringer** — eller måle-definitionen forsvinder
   når PBI Desktop lukker uden Ctrl+S (se `docs/PBI_PATTERNS.md`).
