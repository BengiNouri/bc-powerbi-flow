"""Phase 0c — Generate PBI theme.json from brand_assets.json.

Output:  output/branding/theme.json (drag-drop into PBI Desktop View → Themes)

Usage:
    python gen_pbi_theme.py
"""
from __future__ import annotations

import colorsys
import json
from pathlib import Path

ROOT = Path(__file__).parent
BRAND_FILE = ROOT / "output" / "branding" / "brand_assets.json"
SKELETON = ROOT / "templates" / "theme_skeleton.json"
OUT = ROOT / "output" / "branding" / "theme.json"


def lighten(hex_color: str, factor: float) -> str:
    r, g, b = (int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    l = max(0, min(1, l + factor))
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return f"#{int(r * 255):02X}{int(g * 255):02X}{int(b * 255):02X}"


def contrast_ratio(c1: str, c2: str) -> float:
    def lum(c: str) -> float:
        rgb = [int(c[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        rgb = [((v + 0.055) / 1.055) ** 2.4 if v > 0.03928 else v / 12.92 for v in rgb]
        return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]

    l1, l2 = lum(c1), lum(c2)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


def main() -> None:
    if not BRAND_FILE.exists():
        raise SystemExit(f"Missing {BRAND_FILE}. Run extract_brand.py first.")
    brand = json.loads(BRAND_FILE.read_text(encoding="utf-8"))
    skel = SKELETON.read_text(encoding="utf-8")
    c = brand["colors"]
    f = brand["fonts"]

    # WCAG checks — auto-swap text colour on primary backgrounds if low contrast
    warnings = list(brand.get("warnings", []))
    text_on_primary = "#FFFFFF" if contrast_ratio("#FFFFFF", c["primary"]) >= 4.5 else "#000000"
    if contrast_ratio(c["text"], c["background"]) < 4.5:
        warnings.append("Text colour has < 4.5:1 contrast with background — using #1A1A1A fallback")
        c["text"] = "#1A1A1A"

    replacements = {
        "client_name":    brand["client_name"],
        "primary":        c["primary"],
        "secondary":      c["secondary"],
        "accent":         c["accent"],
        "success":        c["success"],
        "warning":        c["warning"],
        "background":     c["background"],
        "text":           c["text"],
        "primary_light":  lighten(c["primary"], 0.30),
        "secondary_dark": lighten(c["secondary"], -0.20),
        "neutral":        "#9CA3AF",
        "heading_font":   f["heading"],
        "body_font":      f["body"],
    }
    rendered = skel
    for k, v in replacements.items():
        rendered = rendered.replace("{{" + k + "}}", v)

    # Validate JSON
    try:
        parsed = json.loads(rendered)
    except json.JSONDecodeError as e:
        raise SystemExit(f"Theme template produced invalid JSON: {e}")

    OUT.write_text(json.dumps(parsed, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"  text-on-primary: {text_on_primary}")
    print(f"  contrast(text, bg): {contrast_ratio(c['text'], c['background']):.2f}:1")
    if warnings:
        print("Warnings:")
        for w in warnings:
            print(f"  ⚠️  {w}")
    # Write warnings back to brand_assets.json so design_brief picks them up
    brand["warnings"] = warnings
    BRAND_FILE.write_text(json.dumps(brand, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
