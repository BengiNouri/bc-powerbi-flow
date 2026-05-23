# PBI patterns — tested DO and DON'T

> **Read this before generating any DAX measure formatString or visual.json structure.**
> Every entry below has been **verified in PBI Desktop** to either work or fail.
> Don't add an entry unless you've actually rendered it.

---

## DAX measure formatStrings

### ✅ DO

| Format string | Renders | Use case |
|---|---|---|
| `#,##0` | `73` | Integers |
| `#,##0.0` | `73.4` | 1-decimal numbers |
| `#,##0.00` | `73.42` | 2-decimal numbers |
| `#,##0 kr` | `5,000,000 kr` | DKK currency |
| `#,##0 DKK` | `5,000,000 DKK` | DKK alt notation |
| `0.0%` | `24.5%` | Percentages (input is fraction 0.245) |
| `+0;-0;0` | `+5`, `-3`, `0` | Signed integers with explicit + |
| `+0.0%;-0.0%;0.0%` | `+5.2%` / `-3.1%` | Plain signed percentage (works in **all** visual types) |
| `+#;-#;0` | `+23` / `-3` | Plain signed integer |
| `[Green]+0.0%;[Red]-0.0%;0.0%` (Tables/Matrix only!) | green `+5.2%` / red `-3.1%` | **Color tokens only render in Table & Matrix visuals, NOT in Card visuals** — cards show the format string as raw text |

### ❌ DON'T

| Format string | Why it fails |
|---|---|
| `[Green]+0.0%` **in a Card visual** | **Card visuals don't apply color tokens — they render the format string as literal text** (`-[gryy%m...`). Use plain `+0.0%;-0.0%;0.0%` on cards. Color works only in Table/Matrix. |
| `[Green]▲ 0.0%;[Red]▼ 0.0%;0.0%` | Even in Table/Matrix, Unicode arrows ▲▼ may break PBI's format parser depending on locale. Stick to named colors + plain ASCII. |
| `[Color #003F5C]0.0%` | Hex color codes not supported — only the 8 named colors |
| `"text" 0.0%` | String literals via double-quotes don't render in measure formats |
| `\n` linebreaks | Format strings are single-line only |

**PBI supported color tokens** (these 8 only):
- `[Red]` `[Green]` `[Blue]` `[Yellow]` `[Magenta]` `[Cyan]` `[Black]` `[White]`

For arrows or icons, use a **separate text DAX measure** instead:
```dax
Revenue Trend Icon =
VAR _delta = [Revenue vs Target %]
RETURN IF(_delta >= 0, "▲", IF(_delta < 0, "▼", "●"))
```
Then bind it as a separate visual or stack it next to the % card.

---

## visual queryState roles — match the visual type

Different visual types expect different role names in `query.queryState`:

| visualType | Correct role | Wrong role gives |
|---|---|---|
| `card` | `Values` | (empty card) |
| `slicer` | `Field` (singular!) | "Select or drag fields to populate visual" |
| `lineChart` / `clusteredBarChart` / `clusteredColumnChart` | `Category` + `Y` | empty chart |
| `donutChart` | `Category` + `Y` | empty donut |
| `tableEx` | `Values` | empty table |
| `matrix` | `Rows` + `Columns` + `Values` | empty matrix |
| `image` | (no query) | n/a |
| `textbox` | (no query) | n/a |

❌ Common mistake: using `Values` for slicer (renders as empty visual asking for fields)

---

## visual.json projections

### ✅ DO

Every chart/donut/table/slicer projection needs `queryRef` + `nativeQueryRef`:

```json
{
  "field": {
    "Measure": {
      "Expression": {"SourceRef": {"Entity": "_Measures"}},
      "Property": "Revenue"
    },
    "Name": "_Measures.Revenue",
    "NativeReferenceName": "Revenue"
  },
  "queryRef": "_Measures.Revenue",
  "nativeQueryRef": "Revenue"
}
```

Replace `Measure` → `Column` for column references.

### ❌ DON'T

| Pattern | Why it fails |
|---|---|
| Omit `queryRef` | PBI fails to load: "Required property 'queryRef' was not included" |
| `image` visualType with `imageUrl` binding | Doesn't bind RegisteredResources reliably — use textbox for "logo" |
| `pages.json` missing on first open | PBI regenerates page folders and wipes visuals |
| Title via `visual.objects.title.show: false` | PBI ignores it — auto-title still renders. Use **theme.visualStyles.<type>.\*.title.show: false** instead |
| Visual ends at x>1280 or y>720 | Renders cut off — keep within canvas |

---

## theme.json visualStyles

### ✅ DO disable auto-titles in theme (not per-visual)

```json
"visualStyles": {
  "lineChart": {
    "*": {
      "title": [{"show": false}]
    }
  }
}
```

Same for `clusteredBarChart`, `clusteredColumnChart`, `donutChart`, `tableEx`.

### ✅ DO use dataColors in fixed order

```json
"dataColors": [
  "{{primary}}",        // [0] series 1 colour
  "{{secondary}}",      // [1] series 2 colour
  "{{accent}}",         // [2]
  "{{success}}",        // [3] semantic good
  "{{warning}}",        // [4] semantic warning
  "{{primary_light}}",  // [5] series 3
  "{{secondary_dark}}", // [6] series 4
  "{{neutral}}"         // [7] grey
]
```

`good` / `bad` / `neutral` semantic colours map to dataColors[3] / dataColors[4] / dataColors[2] in PBI conditional formatting.

---

## PBIP semantic model persistence

### ✅ DO export TMDL after every MCP measure change

```bash
# After running measure_operations.Create or .Update via MCP:
# Export TMDL via MCP → write to definition/tables/_Measures.tmdl
```

If you skip this, **measures live only in PBI Desktop's in-memory model**.
Closing PBI Desktop without Ctrl+S = measures lost.

### ❌ DON'T mix model.bim with TMDL `definition/` folder

PBIP format uses ONE of:
- TMDL: `<name>.SemanticModel/definition/tables/*.tmdl` (modern, version-friendly)
- BIM: `<name>.SemanticModel/model.bim` (legacy single-file)

Having both can cause PBI to use the wrong one.

---

## When in doubt: how to verify a new pattern works

1. Build the simplest possible PBIP file by hand in PBI Desktop with the pattern you want to replicate
2. `Ctrl+S` → close → inspect the generated `.tmdl` / `visual.json` on disk
3. Copy that exact structure into the generator
4. Test that the generator output matches PBI's own output
5. Add it to this doc under ✅ DO

**Don't generate 100 visuals using an untested pattern.** One bad pattern × 100 = 100 broken visuals + a screenshot of gibberish you have to apologise for.

---

## Lessons learned (session 2026-05-23)

- **Iteration 1 (wrong):** shipped `[Green]▲ 0.0%` formats. Assumed Unicode arrows were the problem when cards showed gibberish.
- **Iteration 2 (wrong):** removed arrows, kept colors `[Green]+0.0%`. STILL broken — same gibberish.
- **Iteration 3 (correct):** removed colors entirely. Plain `+0.0%;-0.0%;0.0%` finally renders.
- **Root cause:** PBI Card visuals don't apply color tokens in formatStrings — only Table/Matrix do. Cards render the entire format string as literal text when colors are present.
- **Cost:** 3 iterations × 5 measures × rerun-pipeline × user time = ~90 min lost + 2 broken screenshots sent to user.

**The general lesson:** When a pattern fails, don't tweak it twice in the same direction. Step back and ask "what assumption is wrong?" — in this case, "PBI parses color tokens everywhere" was wrong. It only parses them in some visual types.

**The Karpathy lesson:** "Think before coding. State your assumptions explicitly. If uncertain, ask." I assumed Card visuals support colored format strings. I never validated that assumption against PBI docs OR a minimal test. Validating one card by hand in PBI Desktop before generating 5 would have caught this in 2 minutes instead of 90.

**The systems lesson:** Add `verify_one_card_renders.py` to the playbook BEFORE bulk-generating cards. The test should literally open PBI Desktop and screenshot a single card with the new format string, and fail loudly if it doesn't show the expected value.

Other lessons from this session:
- Image visualType for logos: didn't validate RegisteredResources binding first → removed entirely, used textbox
- MCP-added measures lost on PBI close without save → export TMDL to disk after every MCP measure change

**Each lesson cost time. Each could have been avoided by validating one minimal example first.**
