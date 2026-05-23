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
| `[Green]+0.0%;[Red]-0.0%;0.0%` | `+5.2%` green / `-3.1%` red | **Color-coded deltas** |
| `[Red]+#;[Green]#;0` | `+23` red / `15` green | Inverted-good metric (e.g. tickets — over target is bad) |

### ❌ DON'T

| Format string | Why it fails |
|---|---|
| `[Green]▲ 0.0%;[Red]▼ 0.0%;0.0%` | **Unicode arrows ▲▼ break PBI's format parser** — entire format string renders as literal text (`-[gryy%m...`) |
| `[Color #003F5C]0.0%` | Hex color codes not supported — only named colors |
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

- We shipped `[Green]▲ 0.0%` formats for 5 measures × 1 page × visible to client = **5 broken cards on screenshot**. Root cause: arrogant assumption that PBI parses Unicode in format strings. Cost: 30 min of rework + trust damage. Fix: removed arrows, kept only named colors.
- We used `image` visualType for logos before validating it could bind RegisteredResources. Got "Select image in the format pane under Style" placeholder. Cost: removed image visual entirely. Fix: use textbox with bold client name as logo header.
- We added 10 measures via MCP that were lost when PBI Desktop closed without Save. Cost: had to re-add and write TMDL to disk manually. Fix: this pattern doc + "always export TMDL after measure changes" rule.

**Each lesson cost time. Each could have been avoided by validating one minimal example first.**
