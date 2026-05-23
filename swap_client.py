"""swap_client.py — Activate a different demo client's branding on AkseDemoDW_v2.pbip.

Usage:
    python swap_client.py <slug>

    e.g.  python swap_client.py vestas
          python swap_client.py coloplast
          python swap_client.py lakrids-by-bulow

What it does:
    1. Copies demo-clients/<slug>/theme.json  → PBIP RegisteredResources/<ClientName>.json
    2. Copies demo-clients/<slug>/logo.png    → PBIP RegisteredResources/Logo.png
    3. Copies brand_assets.json + theme.json  → output/branding/
       (so gen_pbi_report.py picks up this client on next run)
    4. Copies design_decisions.yaml if present (else removes the existing one
       so gen_pbi_report.py falls back to defaults)
    5. Rewrites report.json customTheme + resourcePackages

After running, CLOSE PBI Desktop and reopen the .pbip to see the new brand.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent
DEMOS = ROOT / "demo-clients"
PBIP_REPORT = ROOT / "output" / "AkseDemoDW" / "AkseDemoDW_v2.Report"
REGISTERED_DIR = PBIP_REPORT / "StaticResources" / "RegisteredResources"
REPORT_JSON = PBIP_REPORT / "definition" / "report.json"
BRANDING_DIR = ROOT / "output" / "branding"


def safe_filename(name: str) -> str:
    """Turn 'Lakrids by Bülow' into 'Lakrids_by_Bulow' for PBI resource names."""
    table = str.maketrans({"ü": "u", "å": "aa", "ø": "o", "æ": "ae", "Æ": "Ae", "Ø": "O", "Å": "Aa", "Ü": "U"})
    cleaned = name.translate(table)
    return re.sub(r"[^A-Za-z0-9_]", "_", cleaned)


def list_demos() -> list[str]:
    return sorted(
        p.name for p in DEMOS.iterdir()
        if p.is_dir() and (p / "brand_assets.json").exists()
    )


def main(slug: str) -> None:
    src = DEMOS / slug
    if not src.exists() or not (src / "brand_assets.json").exists():
        raise SystemExit(f"No demo client '{slug}'. Available: {', '.join(list_demos())}")

    brand = json.loads((src / "brand_assets.json").read_text(encoding="utf-8"))
    client_name = brand["client_name"]
    safe_name = safe_filename(client_name)

    REGISTERED_DIR.mkdir(parents=True, exist_ok=True)
    BRANDING_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Theme into PBIP
    theme_dst = REGISTERED_DIR / f"{safe_name}.json"
    shutil.copy(src / "theme.json", theme_dst)

    # 2. Logo (if present)
    logo_src = src / "logo.png"
    has_logo = logo_src.exists()
    if has_logo:
        shutil.copy(logo_src, REGISTERED_DIR / "Logo.png")

    # 3. Make this the active client for gen_pbi_report.py
    shutil.copy(src / "brand_assets.json", BRANDING_DIR / "brand_assets.json")
    shutil.copy(src / "theme.json",        BRANDING_DIR / "theme.json")

    # 4. Sync design_decisions.yaml — copy if client has one, else REMOVE existing
    decisions_src = src / "design_decisions.yaml"
    decisions_dst = BRANDING_DIR / "design_decisions.yaml"
    if decisions_src.exists():
        shutil.copy(decisions_src, decisions_dst)
        decisions_status = "copied"
    elif decisions_dst.exists():
        decisions_dst.unlink()
        decisions_status = "removed (no client yaml — falls back to defaults)"
    else:
        decisions_status = "none"

    # 5. Update report.json
    report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    report["themeCollection"]["customTheme"] = {
        "name": safe_name,
        "reportVersionAtImport": {"visual": "2.9.0", "report": "3.3.0", "page": "2.3.1"},
        "type": "RegisteredResources",
    }

    # Ensure RegisteredResources package has this theme + logo entries
    reg_pkg = next((p for p in report.get("resourcePackages", []) if p["name"] == "RegisteredResources"), None)
    if reg_pkg is None:
        reg_pkg = {"name": "RegisteredResources", "type": "RegisteredResources", "items": []}
        report.setdefault("resourcePackages", []).append(reg_pkg)
    # Drop old themes, keep non-theme items (e.g. images)
    reg_pkg["items"] = [i for i in reg_pkg["items"] if i.get("type") != "CustomTheme"]
    reg_pkg["items"].insert(0, {"name": safe_name, "path": f"{safe_name}.json", "type": "CustomTheme"})
    if has_logo and not any(i.get("name") == "Logo" for i in reg_pkg["items"]):
        reg_pkg["items"].append({"name": "Logo", "path": "Logo.png", "type": "Image"})

    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Swapped active client to: {client_name}")
    print(f"  Theme:      {theme_dst.relative_to(ROOT)}")
    print(f"  Logo:       {'Logo.png (copied)' if has_logo else 'none'}")
    print(f"  Decisions:  {decisions_status}")
    print(f"  report.json customTheme.name = '{safe_name}'")
    print()
    print("Next: close PBI Desktop and reopen AkseDemoDW_v2.pbip.")
    print(f"Optionally run `python gen_pbi_report.py` to regenerate visuals for {client_name}.")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage: python swap_client.py <slug>\n")
        print("Available demo clients:")
        for d in list_demos():
            print(f"  {d}")
        sys.exit(0 if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help") else 1)
    main(sys.argv[1])
