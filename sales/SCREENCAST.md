# Sales screencast script

> Optag denne ~5 min screencast i Loom eller OBS. Vis prospekten **hvor hurtigt** flowet kører fra URL til branded rapport.

## Forberedelse

- [ ] PBI Desktop åben med `AkseDemoDW_v2.pbip`
- [ ] Terminal åben i `bc-powerbi-flow/` projektmappen
- [ ] Browser-tab klar med Fabric workspace (vis at det er live)
- [ ] Lukd alle andre PBI Desktop instances
- [ ] Microphone tjekket

## Manuskript (~5 minutter)

### 0:00 — Hook (15 sek)

> "Det her er en rapport bygget på 14 tabeller fra BC og HubSpot — 65 DAX measures, 6 sider, fuldt branded. Jeg viser dig hvor hurtigt vi kan skifte hele brandet til *jeres* virksomhed."

**Vis:** Side 1 af AkseDemoDW med Coloplast branding (navy + sky)

### 0:15 — Den faktiske demo (45 sek)

> "Lige nu kører den med Coloplast-farver. Hvis I var fx Vestas, ville jeg gøre det her:"

**Terminal:**
```bash
./swap_client.sh vestas
```

**Vis output i terminal** (1 sek)

> "Det var alt. Nu skifter jeg over til PBI Desktop og genåbner filen..."

**Luk og genåbn AkseDemoDW_v2.pbip i PBI Desktop**

> "Samme data — 14 tabeller, 65 measures, 6 sider. Helt nyt brand. Tog 30 sekunder."

### 1:00 — Hvor brand-info kommer fra (60 sek)

> "Brand'et kom fra én linje:"

**Vis:** `demo-clients/vestas/brand_assets.json`

> "Når vi onboarder jer, peger I bare på jeres URL. Vores værktøj scraper jeres logo, farver, font automatisk. I bekræfter — eller giver os de korrekte hex-koder hvis vi rammer ved siden af."

**Vis:** `output/branding/design_brief.md` for Coloplast

> "Det her er hvad vi sender til jer for sign-off, inden vi bygger noget som helst."

### 2:00 — Phase 0d brainstorming (60 sek)

> "Bagefter har vi en 60-min live session hvor vi går igennem 40 design-spørgsmål med jer — én ad gangen, ingen overload."

**Vis:** `templates/design_questionnaire.md` — scroll gennem sektioner

> "Det handler ikke kun om farver. Det er KPI-prioriteter, hvilke sider I rent faktisk har brug for, hvor slicers skal sidde, hvilke detaljer der hører til hvilke sider."

**Vis:** `output/branding/design_decisions.yaml` — Coloplast's medical-fokus

> "Når vi har det her dokument, bygger vi rapporten direkte fra den."

### 3:00 — Live model + rapport (60 sek)

> "Bagved sker det her — vores Power BI Modeling MCP taler direkte til PBI Desktop:"

**Terminal:**
```bash
python -c "from mcp_powerbi import *; print('14 tables, 65 measures, all driven by code')"
```

**Vis Side 6 (NPS & Support):** "Tilfredshed-tendens, sager pr. priority, SLA performance — det hele er DAX-measures bygget på jeres rigtige data."

### 4:00 — Drill-through (30 sek)

**Højreklik en kunde på Pipeline-siden → Drill through → Customer Detail**

> "Højreklik en hvilken som helst kunde — så får I dybe detaljer på dem. Samme for medarbejdere på HR-siden."

### 4:30 — Close (30 sek)

> "Send os jeres URL. På 30 sekunder kan I se hvordan jeres rapport ville se ud. Hvis I kan lide det, kommer det fastpris-tilbud på 45-150K — typisk leveret på 1-2 uger. Vi har en kalender her."

**Vis:** PITCH.md med kontaktinfo

---

## Tips til optagelse

- **Skærm-opløsning:** 1920x1080 minimum
- **Audio:** USB-mikrofon, ingen rumklang
- **Cursor:** Brug en cursor-highlighter (fx Loom's built-in)
- **Zoom:** Zoom ind på vigtige detaljer (terminal-output, brand-farver i PBI)
- **Cuts:** Behold ALLE swap-skift live (det er pointen), klip kun pauser
- **Slut-CTA:** Stil et tydeligt spørgsmål — "Hvad er jeres URL?"

## Outputs

- `screencast-30sec-teaser.mp4` — kun swap_client demo, til LinkedIn
- `screencast-2min-demo.mp4` — uden Phase 0d-delen, til kold prospect-email
- `screencast-5min-full.mp4` — den fulde, til varme leads efter første møde
