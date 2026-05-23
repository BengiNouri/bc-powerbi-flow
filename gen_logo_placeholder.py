"""Generate a placeholder logo PNG when client hasn't provided one.

Uses Pillow to draw the client name in primary brand colour on transparent bg.
Output: demo-clients/<slug>/logo.png (and copied to PBIP RegisteredResources).
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
BRAND_FILE = ROOT / "output" / "branding" / "brand_assets.json"


def main() -> None:
    if not BRAND_FILE.exists():
        raise SystemExit(f"Missing {BRAND_FILE}. Run extract_brand.py first.")
    brand = json.loads(BRAND_FILE.read_text(encoding="utf-8"))
    name = brand["client_name"]
    primary = brand["colors"]["primary"]

    # Render
    width, height = 280, 80
    img = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # Try a clean sans-serif; fall back to default
    font = None
    for f in ("arial.ttf", "DejaVuSans-Bold.ttf", "calibri.ttf"):
        try:
            font = ImageFont.truetype(f, 36)
            break
        except (OSError, IOError):
            continue
    if font is None:
        font = ImageFont.load_default()

    text = name.upper()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((width - tw) / 2, (height - th) / 2 - bbox[1]), text, fill=primary, font=font)

    # Always write to demo-clients/<slug>/logo.png (per-client, not shared)
    slug = name.lower().replace(" ", "-").replace("ü", "u").replace("ø", "o").replace("æ", "ae").replace("å", "aa")
    out_path = ROOT / "demo-clients" / slug / "logo.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG")
    print(f"Wrote {out_path.relative_to(ROOT)}")

    # Update brand_assets.json to point at the new PNG (relative to repo root)
    brand["logo_local"] = str(out_path.relative_to(ROOT)).replace("\\", "/")
    BRAND_FILE.write_text(json.dumps(brand, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
