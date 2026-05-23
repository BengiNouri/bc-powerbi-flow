# Lodværket BI Accelerator

> Branded Power BI dashboard på 1-2 uger fra BC + CRM + andre systemer.

## Hvad vi leverer

En komplet data warehouse + Power BI rapport, branded med jeres logo og farver, live i jeres Microsoft Fabric workspace — typisk 1-2 uger fra kontrakt til lancering.

**6-7 standard rapport-sider:**
1. Executive Dashboard — top-KPIs på tværs af forretningen
2. Pipeline & CRM — deal flow, win rate, kunde-segmenter
3. Marketing & Web — leads, kampagne-ROI, web-trafik
4. Finance & Budget — omsætning vs budget, P&L, varians
5. HR & People — headcount, udnyttelse, lønomkostninger
6. NPS & Support — kundetilfredshed, sager, SLA
7. (Valgfri) Quality & Compliance — for medical/regulated industries

**Bag scenen:**
- Medallion-arkitektur (Bronze → Silver → Gold)
- 14+ stjerne-skema tabeller (dimensions + facts)
- 65+ DAX measures med danske labels
- Direct Lake på Microsoft Fabric — sub-sekund refresh
- WCAG AA tilgængelighed garanteret

## Hvorfor Lodværket

**Vi kører flowet med en AI-assistent (Claude Code).** Det betyder:

- **Hurtigere:** Hvad andre konsulenter bruger 3-6 måneder på, leverer vi på 1-2 uger
- **Billigere:** Mindre manuel kode = mindre timer på regningen
- **Bedre dokumenteret:** Hver beslutning er nedfældet i versioneret markdown, så jeres team kan iterere selv
- **AI-enablement med på købet:** Vi viser jeres team hvordan de bruger Claude til at vedligeholde rapporten efter levering

## Vores stack

| Lag | Værktøj |
|---|---|
| Kilde | BC SaaS / on-prem · HubSpot · Salesforce · Mailchimp · CSV · MS SQL · PostgreSQL |
| Staging | Supabase PostgreSQL |
| Lakehouse | Microsoft Fabric (Direct Lake mode) |
| Semantic model | PowerBI Modeling MCP — programmatisk authoring |
| Rapport | Power BI Project (.pbip) — versioneret i Git |
| AI orchestration | Claude Code med branded design brainstorming |

## Tilgang i 8 faser

| Fase | Hvad | Tid |
|---|---|---|
| A. Discovery | 1-time møde — pain points, KPIs, decision-makers | 1t |
| B. Proposal | Skriftligt tilbud + preview af jeres branded rapport | 2-3d |
| C. Kickoff | Credential-tjekliste + adgang til jeres systemer | 1d |
| D. Branding & design | Auto-extract jeres brand + 60-min design session | 1d |
| E. Build | Vi bygger pipeline + model + rapport | 3-5d |
| F. Handover | 1-time gennemgang + dokumentation | 1d |
| G. Support | 1 måned med småændringer | løbende |
| H. (Valgfri) Claude-enablement | Vi træner jeres team på AI-tools | separat aftale |

## Reference-demos

Vi har færdige brand-themes klar til at vise jer hvordan jeres rapport vil se ud:

| Brand | Stil |
|---|---|
| Coloplast | Medical navy + sky, 7 sider inkl. Quality & Compliance |
| Vestas | Industri navy + sky, B2B/produktion |
| Lego | Bold red + gul, retail/SKU-tung |
| Toms | Chocolate red, FMCG |
| Lakrids by Bülow | Premium sort + guld, luxury FMCG |

**Send os jeres URL — vi har en preview klar på 30 sekunder.**

## Pricing

Se [PRICING.md](./PRICING.md).

## Kontakt

Benjamin Nouri · benjamin_nouri@outlook.dk · Lodværket
