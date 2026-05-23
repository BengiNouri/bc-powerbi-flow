# Design brainstorming — questionnaire

> **Use this in Phase 0d.** Open this file with the client (or their design contact)
> on a 45–60 min call. Claude orchestrates the conversation using
> `superpowers:brainstorming` — one question at a time, captures answers into
> `output/branding/design_decisions.yaml`.
>
> The auto-extracted brand from Phase 0c is the starting point.
> This session is about refining and going beyond pure colours.

---

## 1. Colours (refine from auto-extract)

1. The auto-extracted **primary** is `{{primary}}`. Correct, or send the right hex?
2. The auto-extracted **secondary** is `{{secondary}}`. Correct?
3. Do you have a defined **status palette** for good/warning/bad? Or use our defaults?
4. Light theme or dark theme background?

## 2. Typography

5. Heading font — auto-extracted `{{heading_font}}`. Confirm, or change?
6. Body font — same `{{body_font}}` or different?
7. KPI callout number size — pick one:
   - 28pt (subtle)
   - 36pt (default — what we ship)
   - 48pt (bold, executive feel)
8. Page title size: 20pt | 24pt (default) | 32pt
9. Bold all KPI labels, or only the numbers?

## 3. Logos

10. Do you have a logo? (auto-detected: `{{logo_local}}`)
11. Send the **vector source** (SVG or AI) if possible — better than PNG.
12. Do you have a **light-on-dark variant**? (needed if some pages have dark backgrounds)
13. Logo position on Page 1:
    - Top-left corner (default)
    - Top-right corner
    - Center (above title)
    - Watermark in body (subtle)
14. Show logo on every page, or only Page 1?
15. Approximate logo width: 100px | 140px (default) | 200px

## 4. Slicers (filters on each page)

For each of the 6 default pages, pick which dimensions to filter on. Defaults shown.

| Page | Default slicer(s) | Replace with? |
|---|---|---|
| 1. Executive Dashboard | Year | |
| 2. Pipeline & CRM | Country | |
| 3. Marketing & Web | Campaign type | |
| 4. Finance & Budget | Year + Department | |
| 5. HR & People | Department | |
| 6. NPS & Support | Priority | |

16. Slicer style: **Dropdown** (default — compact) | **List** (visible options) | **Button strip** (toggle look)
17. Slicer position: **Top of page** (default) | **Left sidebar** | **Right sidebar**
18. Do you want a **global slicer** (year/date) that filters all pages at once?

## 5. Page structure

19. Number of pages — default 6. Reduce to 4? Add 2 more? Reasons:
    - "We don't have marketing data" → drop page 3
    - "We need a Quality / Compliance page" → add page 7
20. Page navigation — bottom tabs (default) or top nav bar?
21. **Page 1 priority order** — confirm the 5 top KPIs (from Phase B discovery):
    1. ?
    2. ?
    3. ?
    4. ?
    5. ?

## 6. Charts

22. Default colour for single-series bars/columns — **primary** (default) or **brand secondary**?
23. Line chart thickness: thin (1px) | medium (2px — default) | thick (3px)
24. Show data labels on bars? Always | On hover only (default) | Top 3 only
25. Donut vs pie for category breakdowns: **donut** (default — modern) | **pie**
26. Tooltip style: default tooltip | rich tooltip with extra measures

## 7. KPI cards

27. Card style:
    - Minimal (white bg, just number + label — default)
    - Framed (subtle border)
    - Coloured (primary background, white text — bold look, low contrast risk)
28. Show **trend arrow** vs prior period? Yes | No (default)
29. Show **target** below the KPI? Yes | No (default — only if client has targets set)

## 8. Language & locale

30. Report language: Danish (default) | English | Both (bilingual labels)
31. Decimal separator: comma `4.959.761,30` (da-DK default) | period `4,959,761.30` (en-US)
32. Currency suffix: "kr" (default) | "DKK" | "€" | other

## 9. Interactivity

33. Cross-filter on click — default on. Turn off for any visual? (rare)
34. Drill-through pages — enabled? (e.g. click a customer → drill to a customer detail page)
35. Bookmarks for saved views? Yes / No
36. PDF export button on Page 1? Yes / No

## 10. Anything else

37. Any pages or KPIs from existing reports we should preserve the look of?
38. Any visuals to AVOID (e.g. "we hate pie charts")?
39. Accessibility requirements beyond WCAG AA?
40. Any compliance constraints on what data can appear together (e.g. GDPR PII rules)?

---

After this session, write all answers to `output/branding/design_decisions.yaml`
(see `design_decisions.yaml.example` for the schema), commit, and send the file
back to the client for written sign-off before Phase 1 starts.
