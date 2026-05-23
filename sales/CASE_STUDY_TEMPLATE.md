# Case study template

> Brug efter hvert engagement. 1-2 sider. Klient-godkendelse påkrævet før publicering.

## {Client name} — fra spredte systemer til ét branded dashboard

> En sætnings tagline der fanger den specifikke pain vi løste.

### Kunden

- **Industri:** {fx Medical / B2B SaaS / Manufacturing / Retail}
- **Størrelse:** {antal ansatte, omsætning hvis offentligt}
- **Sponsor:** {titel — fx COO / Head of Operations / Data Lead}

### Pain før

> "{verbatim quote fra Phase B discovery — den smerte de selv beskrev}"

3-4 punkter om den specifikke pain:
- Data spredt over BC + HubSpot + Excel = ingen samlet KPI-overview
- Månedlig "Excel-update" tog 2 dage manuel arbejde
- Forskellige tal i forskellige rapporter — ingen tillid
- Ledelse efterlyste real-time data men teknisk gæld blokerede

### Hvad vi gjorde

**Discovery + design (uge 1):**
- Phase A discovery møde — kortlagde sources + KPIs
- Phase 0c auto-extracted brand fra {client_url}
- Phase 0d 60-min design session — pinpointede {N} KPI-prioriteter

**Build (uge 2):**
- {N} sources integreret: {BC, HubSpot, ...}
- {M} gold-tabeller i star schema
- {K} DAX measures
- {P} rapport-sider inkl. {client-specific page if any}
- WCAG AA tilgængelighed

### Resultater

> Konkrete tal — kvantificér hvor det er muligt:

- Månedlig rapportering: fra 2 dage manuel arbejde → 0 minutter (auto-refresh)
- Tid fra spørgsmål til svar: fra "vent på Q3-rapporten" → 5 sekunder
- Antal rapporter konsolideret: {X} Excel-filer + {Y} ad-hoc queries → 1 sandhedskilde
- ROI på Lodværket-engagement: {dage til payback}

### Hvad kunden siger

> "{verbatim quote efter levering — godkendt af sponsor}"
>
> — {Name}, {Title}, {Client}

### Hvordan det fungerer fremad

- Live data: refreshes via Fabric notebook hver nat
- Ændringer: kundens team bruger Claude Code til at tilføje measures / sider
- Support: {Retainer-plan, fx "Active retainer — 16 timer/måned"}

### Vil I se hvordan jeres ville se ud?

Send os jeres URL — vi har en preview på 30 sekunder.

---

## Internal notes (slet før udgivelse)

- Project ref: bc-powerbi-flow-{slug}
- Build commits: {git log --oneline-til-tag}
- Phase D credentials: BC OAuth + HubSpot Private App + Fabric workspace owner
- Phase 0d decisions: {link til design_decisions.yaml}
- Known follow-ups: {hvad blev parket}
- Sales-quoting feedback: {hvad fungerede / virkede ikke i tilbuddet}
