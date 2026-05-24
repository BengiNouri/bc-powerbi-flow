# Visual QA checklist

> Kør denne **inden hver Phase 7 publish**. Åbn `.pbip` i PBI Desktop og gå sider igennem.

## Pr. side (gentag for hver af de 6-7 hovedsider)

### Layout & spacing
- [ ] Logo synligt øverst venstre (kun Side 1, eller alle hvis yaml siger det)
- [ ] Titel læselig, ikke afkortet
- [ ] Global Year-slicer i top-højre hjørne, ikke overlappet af titel
- [ ] KPI-cards på en lige række, lige høje
- [ ] vs-Target cards under KPIs (hvis enabled) — pænt aligned
- [ ] Charts har 12pt overskrifter (ikke 24pt auto-titler med rå column-navne)
- [ ] Ingen visuals der løber ud over canvas (x>1280 eller y>720)
- [ ] Ingen overlap mellem visuals

### Farver
- [ ] Brand primary brugt i KPI callouts + chart series 1
- [ ] Brand secondary brugt i multi-series charts (synlig forskel fra primary)
- [ ] vs-Target deltas: ▲ grøn / ▼ rød (ikke sort tekst)
- [ ] Baggrund hvid (eller dark-mode hvis valgt)
- [ ] Tekst-kontrast >= 4.5:1 (WCAG AA)

### Data
- [ ] Alle KPI-cards viser tal (ikke "(Blank)")
- [ ] Charts har data (ikke tom plot-area)
- [ ] Datoer i dansk format (dd-MM-yyyy) hvis lang=da-DK
- [ ] Currency-suffix korrekt (DKK / kr som valgt)
- [ ] Decimal-separator korrekt (komma for da-DK)

### Interaktivitet
- [ ] Klik en bar i et chart → andre visuals filtreres (cross-filter)
- [ ] **Slicer cross-filter virker**: Vælg en værdi i Year-slicer eller
      Country-slicer → mindst ét chart OG mindst ét KPI-card opdateres.
      En slicer der renderes uden at filtrere er en stille bug — som regel
      en manglende relation i modellen eller forkert crossFilter-retning.
      (PLAYBOOK_DRYRUN.md gap #17)
- [ ] Brug global Year-slicer → ALLE charts/KPIs på siden opdateres
- [ ] Højreklik en customer (på Pipeline-siden) → Drill through → Customer Detail (hvis enabled)
- [ ] Højreklik en employee (på HR-siden) → Drill through → Employee Detail (hvis enabled)

### Typografi
- [ ] Side-titel 24pt, brand-primær farve
- [ ] KPI callout 36pt, brand-primær
- [ ] Chart-titler 12pt
- [ ] Kolonne-headers i tabeller bold + brand-primær baggrund
- [ ] Body-tekst 11-12pt

## På tværs af sider

- [ ] Page nav i bunden viser kun synlige sider (drill-through hidden)
- [ ] Side-navne har konsistent nummerering (1. Exec, 2. Pipeline, ...)
- [ ] Samme layout-paradigme på alle sider (title-bar + KPI-række + content-grid)
- [ ] Klik mellem sider — global Year-slicer beholder valg
- [ ] Logo + theme konsistent på tværs af sider

## Performance

- [ ] Refresh tager < 30 sekunder (Direct Lake på Fabric)
- [ ] Side-loading < 2 sekunder
- [ ] Cross-filter response < 1 sekund

## Tilgængelighed (WCAG AA)

- [ ] Alle visuals har alt-text
- [ ] Tab-rækkefølge logisk (KPI cards → charts → tables)
- [ ] Ingen kun-farve information (status også med ikon/tekst)
- [ ] Skærmlæser kan læse KPI-værdier

## Sign-off

- [ ] Alle ovenstående er ✅
- [ ] Klient har set screenshots eller live demo og godkendt skriftligt
- [ ] Date: ___________  Signed: ___________

→ Klar til Phase 7 publish.
