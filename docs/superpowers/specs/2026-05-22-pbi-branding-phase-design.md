# Design — Power BI report branding phase

**Status:** Draft for review
**Date:** 2026-05-22
**Owner:** Benjamin (Lodværket)
**Phase:** Inserts as Phase 0c in `PLAYBOOK.md`, between source-scan/modelling (0a/0b) and bronze ingestion (1).

---

## 1. Goal

Make every Power BI client report look branded — using the client's actual colours, fonts, and logo — without manual design work. The phase is **"first draft good enough to show the client"**: auto-extract → apply standard template → present → refine. Iteration after client review uses the brainstorming skill for layout tweaks (not in scope of this spec).

**Success criteria:**
- A new client engagement produces a working `theme.json` + `design_brief.md` in under 20 minutes.
- The PBI report rendered with this theme uses the client's primary/secondary colours in every chart, KPI card, and slicer — no defaults leak through.
- Client can review the design brief and either sign off or return hex-code corrections in a single round trip.
- WCAG AA contrast holds for all text-on-colour combinations.

## 2. Approach

**Picked: Approach A — Auto-extract + standard template + iterate.**

Rejected alternatives:
- **Approach B (auto + live brainstorm session on layout):** overkill for first draft; brainstorm is reserved for post-review tweaks.
- **Approach C (brand-only, no layout design):** skips the client-facing design brief, makes iteration harder.

The phase has four scripts that run in sequence and never touch the PBI Desktop session:

```
.env CLIENT_URL
        │
        ▼
extract_brand.py ───► output/branding/brand_assets.json + logo.png
        │
        ▼
gen_pbi_theme.py ───► output/branding/theme.json
        │
        ▼
gen_design_brief.py ─► output/branding/design_brief.md
        │
        ▼
   (send to client)
        │
        ▼
   client sign-off
        │
        ▼
   Phase 1 (bronze)
```

All four scripts are pure Python with no MCP interaction. They produce file artefacts that downstream phases consume.

## 3. Components

### 3.1 `extract_brand.py`

**Tech:** `requests` + `beautifulsoup4` + `colorthief` + `cssutils`

**Inputs:** `CLIENT_URL` from `.env`
**Outputs:** `output/branding/brand_assets.json`, `output/branding/logo.png`

Scrape order (each step has a fallback):

1. **Logo:** `<img>` with `logo` in class/alt/src → `<link rel="icon">` (favicon) → `og:image` meta
2. **Primary colour:**
   1. `<meta name="theme-color">` content
   2. ColorThief dominant colour on logo (skip if logo is monochrome/transparent)
   3. CSS `body` / `header` background-color
3. **Secondary colour:** ColorThief second-most colour on logo, or first `button`/`a` colour in CSS
4. **Accent / success / warning:** derived from primary via HSL lighten/darken (no scraping needed)
5. **Fonts:**
   1. Google Fonts link: `<link href="fonts.googleapis.com/css?family=Inter:...">`
   2. CSS `body { font-family: ... }`
   3. Fallback: Segoe UI (PBI default)
6. **Client name:** `<meta property="og:site_name">` → `<title>` first word

Each field is tagged with `confidence: high | medium | low` so the design brief can flag uncertain extractions.

**`brand_assets.json` schema:**

```json
{
  "client_url": "https://nordicsteel.dk",
  "client_name": "Nordic Steel",
  "logo_url": "https://nordicsteel.dk/img/logo.svg",
  "logo_local": "output/branding/logo.png",
  "colors": {
    "primary":    "#0E3A5F",
    "secondary":  "#C8A14A",
    "accent":     "#F2F2F2",
    "success":    "#3FA34D",
    "warning":    "#E67E22",
    "background": "#FFFFFF",
    "text":       "#1A1A1A"
  },
  "fonts": {
    "heading":  "Inter",
    "body":     "Inter",
    "fallback": "Segoe UI"
  },
  "language": "da-DK",
  "confidence": {
    "primary_color":   "high",
    "secondary_color": "medium",
    "fonts":           "medium",
    "logo":            "high"
  },
  "warnings": []
}
```

### 3.2 `gen_pbi_theme.py`

**Inputs:** `output/branding/brand_assets.json`, `templates/theme_skeleton.json`
**Outputs:** `output/branding/theme.json`

Reads brand assets, fills the PBI theme skeleton:

- **8-entry `dataColors` array** in fixed order: `[primary, secondary, accent, success, warning, lighten(primary,30%), darken(secondary,20%), neutral-gray]`. Order matters because PBI assigns these to chart series in this exact sequence.
- **Semantic colours:** `good = success`, `neutral = accent`, `bad = warning` (drives KPI conditional formatting).
- **Text classes:** `title`, `header`, `label`, `callout` with brand fonts and sizes 24/16/12/36 respectively.
- **Visual styles:** card (no border, brand primary callout), line chart (2px line), bar/column (rounded corners 2px), slicer (dropdown mode, brand check colour), table (alternating 5% grey rows, header in primary).
- **WCAG AA check:** if `contrast(text_color, background) < 4.5:1`, auto-swap to white/black and log a warning to stdout + append to `brand_assets.json` `warnings[]`.

The resulting `theme.json` validates against PBI theme schema 2.130.0.

### 3.3 `gen_design_brief.py`

**Inputs:** `output/branding/brand_assets.json`, `templates/design_brief_template.md`
**Outputs:** `output/branding/design_brief.md`

Templates an 80–120 line markdown doc with:

1. Brand table (logo thumb, primary/secondary swatches, font) with confidence flags
2. Six-page report structure (taken from `report_spec.yaml` if present, else default 6-page layout)
3. Explicit feedback prompts: "Send hex codes if wrong", "Mark KPIs to swap", "Choose lang"
4. Warnings emitted by `gen_pbi_theme.py` (low-contrast text, unsupported fonts, etc.)

The file uses no images other than the local logo thumb to keep the markdown portable (sendable as email attachment).

### 3.4 `templates/theme_skeleton.json` + `templates/design_brief_template.md`

Static templates shipped in the repo. Skeleton has all the PBI-required keys with placeholder tokens (`{{primary}}`, `{{heading_font}}`, `{{title_size}}`) that `gen_pbi_theme.py` and `gen_design_brief.py` substitute.

## 4. PLAYBOOK integration

Inserts as **Phase 0c** between `0b — Semantic model design` and `1 — Synthetic / Bronze`.

```markdown
### Phase 0c — Branding & design (15-20 min)

Pre-flight: CLIENT_URL set in .env.

Steps:
1. python extract_brand.py        → brand_assets.json + logo.png
2. python gen_pbi_theme.py        → theme.json
3. python gen_design_brief.py     → design_brief.md
4. Send design_brief.md to client. Wait for sign-off OR corrections.
5. If corrected: edit brand_assets.json, re-run steps 2-3.

Verify:
- python -m json.tool output/branding/theme.json > /dev/null
- All "low"/"medium" confidence flags either resolved to "high" or
  explicitly approved by client in writing.
- WCAG contrast check passes (no warnings in brand_assets.json).
```

**Phase 5 picks up `theme.json` indirectly** — measures use `formatString` with locale-aware separators (da-DK vs en-US) based on `brand_assets.language`.

**Phase 6 (`gen_pbi_report.py`) reads `brand_assets.json` directly:**
- `client_name` becomes page title text on Page 1
- `logo_local` is referenced from a Page 1 image visual (StaticResources/logo.png)
- Colour overrides in visuals (rare — most colour comes from theme.json by reference)

**Phase 7 publish:** workspace name suffix `{client_name}_DW` for clarity in Fabric.

## 5. How it fits with the rest of the stack

### 5.1 Power BI Modeling MCP

`theme.json` is **a file-based artefact**, not an MCP entity. PBI Desktop loads it from disk via `View → Themes → Browse for themes`, or PBIP picks it up from `StaticResources/SharedResources/BaseThemes/`. No MCP call needed for theming.

What MCP **does** care about:
- After `theme.json` is loaded in PBI Desktop, MCP-created visuals will inherit the theme's `dataColors` automatically because `visual.json` references colours by role (`good`, `bad`, role-based) not literal hex.
- `_Measures` table `culture` property (set via `model_operations.Update`) must match `brand_assets.language` to keep decimal separators consistent with the theme's text classes.

### 5.2 andrej-karpathy-skills CLAUDE.md guidelines

Each of the four guidelines maps to a concrete check in this phase:

| Karpathy rule | How Phase 0c respects it |
|---|---|
| **Think before coding** | `extract_brand.py` emits a `confidence` field rather than silently picking — Claude surfaces "I'm not sure about the secondary colour" to the user |
| **Simplicity first** | Four small scripts, each <200 LOC. No "colour-palette-as-a-service" abstraction. No CSS pre-processor. No design-token framework. |
| **Surgical changes** | Phase 0c only **adds** files in `output/branding/` and `templates/`. It does not modify `gen_pbi_report.py` — that script just reads `brand_assets.json` if present. |
| **Goal-driven execution** | Verify gate has three concrete checks (JSON validates, no low-confidence unresolved, WCAG passes). "Looks good" alone is not enough to proceed. |

These rules also feed back into the **orchestration prompt** in `PLAYBOOK.md`: Claude is instructed to refuse to silently progress when a confidence flag is "low".

### 5.3 superpowers:brainstorming skill

Used in **two places**:

1. **Spec phase (this document):** brainstorming was used to design Phase 0c itself — produced this spec.
2. **Iteration phase (after client review):** if the client returns substantive layout feedback (not just hex codes), Claude invokes `superpowers:brainstorming` with the client's comments as input. Output is a revised `report_spec.yaml` that re-drives `gen_pbi_report.py`. This iteration loop is **out of scope of this spec** but the contract is documented here so Phase 6 doesn't need to be re-specified later.

### 5.4 superpowers:writing-plans skill (next step)

Per the brainstorming skill's flow, after this spec is approved the next step is `superpowers:writing-plans` to produce an implementation plan (test order, file order, parallel work). Implementation begins from that plan, not from this spec.

### 5.5 Other existing stack components

| Existing | Interaction with Phase 0c |
|---|---|
| `scan_source.py` (Phase 0a) | No interaction — different concern (data vs design). Both share `.env`. |
| `transform_full.py` (Phase 2) | No interaction. |
| `gen_pbi_schemas.py` (Phase 5 prep) | No interaction — column metadata is data-driven, not brand-driven. |
| `gen_pbi_report.py` (Phase 6) | **Reads** `brand_assets.json` for client name + logo path. **Does not modify it.** |
| `fabric_load_supabase.py` (Phase 4) | No interaction. |

## 6. Failure modes

| Symptom | Fix |
|---|---|
| `extract_brand.py` returns 403/404 | Client has bot protection (Cloudflare, WAF). Pass `--ua "Mozilla/5.0 ..."` or manually craft `brand_assets.json` from screenshots. |
| ColorThief returns only greys | Logo is transparent/monochrome. Fall back to `theme-color` meta or ask the client for hex codes. Confidence drops to `low`. |
| Font is not PBI-supported | Auto-fallback to Segoe UI. Add warning to `brand_assets.json` and `design_brief.md`. |
| Low WCAG contrast on `text` over `primary` | `gen_pbi_theme.py` auto-swaps text colour and writes warning. Client confirms swap is acceptable in design brief. |
| Multiple logos detected | Pick the one in `<header>`. If ambiguous, save all candidates to `output/branding/logo-candidates/` and ask the client which to use. |
| `theme.json` fails PBI schema validation | Bug in `gen_pbi_theme.py`. Add the failing key to a fixtures test. |

## 7. Verification

**Unit-level (pytest):**
- `extract_brand.py`: snapshot test against 3 known sites (nordicsteel.dk, akse.dk, microsoft.com) — assert primary colour ±10 RGB tolerance from expected.
- `gen_pbi_theme.py`: input fixture → output `theme.json` matches snapshot byte-for-byte (after json.dumps with sort_keys).
- `gen_design_brief.py`: confidence flags render correctly for each level (high/medium/low).

**Integration:**
- End-to-end test: `extract_brand → gen_pbi_theme → gen_design_brief` produces all three artefacts with no warnings on a known good URL.
- WCAG contrast check has its own test with adversarial inputs (#FFFF00 text on #FFFFFF background should fail).

**Manual:**
- Drop `theme.json` into PBI Desktop, open any existing PBIP. Confirm dataColors update across all visuals.
- Open `design_brief.md` in a markdown viewer. Confirm logo thumbnail renders, swatches visible, confidence flags styled.

## 8. Out of scope (future work)

- **Image mockups in `design_brief.md`:** Pillow-rendered placeholder PNGs of each report page with brand colours. Requires `report_spec.yaml` first.
- **Live brainstorm flow** for layout decisions after client review (Phase 0d? Or part of Phase 6 iteration). Documented contract above but no implementation.
- **Dark mode themes:** brands with dark backgrounds (e.g., gaming companies). Current spec assumes light theme — add `theme.mode = light | dark` to brand_assets.json in a v2.
- **Multi-language report labels:** `brand_assets.language` is captured but not yet used to translate KPI names. Will require `i18n/<lang>.yaml` file.
- **Brand guide PDF parsing:** if a client has a real PDF brand guide, parse it instead of scraping the website. Use `pdfplumber` + LLM-extraction.

## 9. References

- PBI theme schema: https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-report-themes
- WCAG 2.1 contrast: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html
- Karpathy CLAUDE.md: https://github.com/multica-ai/andrej-karpathy-skills
- powerbi-modeling-mcp: https://www.npmjs.com/package/@microsoft/powerbi-modeling-mcp
- superpowers brainstorming/writing-plans skills: project plugin cache
