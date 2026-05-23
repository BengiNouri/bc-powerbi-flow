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

| Folder | Source URL | Notes |
|---|---|---|
| `vestas/` | https://www.vestas.com | Wind turbine manufacturer — fits B2B / pipeline / employees / industry KPIs perfectly. Strong navy + sky-blue brand. |

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
