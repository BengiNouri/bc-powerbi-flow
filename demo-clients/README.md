# Demo client artefacts

Each subfolder holds the **branding output** for one demo client — the artefacts that
Phase 0c (`extract_brand.py` → `gen_pbi_theme.py` → `gen_design_brief.py`) produces.

Use these to:
- Show prospects what their report would look like before we build it
- A/B test branding variations
- Regression-test the branding scripts against real-world inputs

## How to load a demo client into PBI Desktop

1. Open `AkseDemoDW_v2.pbip` (or any built `.pbip`) in Power BI Desktop
2. **View → Themes → Browse for themes...**
3. Pick `demo-clients/<client>/theme.json`
4. The report instantly re-skins with the client's colours + fonts

## Current demo clients

| Folder | Source URL | Brand palette | Notes |
|---|---|---|---|
| `vestas/` | https://www.vestas.com | Navy `#0048AD` + sky `#00A0DC` | Wind turbines — fits B2B / pipeline / industry KPIs |
| `toms/` | https://www.toms.com | Red `#C8102E` + burgundy `#7A1A2B` | Chocolate — fits FMCG / retail demos |
| `lego/` | https://www.lego.com | Lego red `#D01012` + yellow `#FFCF00` | Iconic; great for retail / SKU-heavy demos |
| `lakrids-by-bulow/` | https://www.lakridsbybulow.com | Black `#000000` + gold `#B8964D` | Premium / luxury feel; perfect for high-end FMCG |

## How to add a new demo client

```bash
# 1. Update .env with their URL
echo "CLIENT_URL=https://newclient.com" > .env

# 2. Run the three Phase 0c scripts
python extract_brand.py
python gen_pbi_theme.py
python gen_design_brief.py

# 3. Archive the result
mkdir demo-clients/newclient
cp output/branding/brand_assets.json output/branding/theme.json output/branding/design_brief.md \
   demo-clients/newclient/

# 4. Commit
git add demo-clients/newclient && git commit -m "demo: add newclient branding"
```
