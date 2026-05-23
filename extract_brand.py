"""Phase 0c — Extract brand assets from a client URL.

Output:  output/branding/brand_assets.json + logo.png

Usage:
    CLIENT_URL=https://akse.dk python extract_brand.py
    python extract_brand.py --url https://nordicsteel.dk --ua "Mozilla/5.0 ..."
"""
from __future__ import annotations

import argparse
import colorsys
import io
import json
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from PIL import Image

ROOT = Path(__file__).parent
OUT_DIR = ROOT / "output" / "branding"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

PBI_SAFE_FONTS = {
    "Segoe UI", "Arial", "Calibri", "Cambria", "Candara", "Comic Sans MS",
    "Consolas", "Constantia", "Corbel", "Courier New", "Georgia", "Lucida Sans Unicode",
    "Symbol", "Tahoma", "Times New Roman", "Trebuchet MS", "Verdana", "Wingdings",
    # Common web-safe fonts that map nicely
    "Inter", "Roboto", "Open Sans", "Lato", "Montserrat", "Poppins", "Source Sans Pro",
}


@dataclass
class BrandAssets:
    client_url: str
    client_name: str = ""
    logo_url: str = ""
    logo_local: str = ""
    colors: dict[str, str] = field(default_factory=dict)
    fonts: dict[str, str] = field(default_factory=dict)
    language: str = "da-DK"
    confidence: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


# ─── HELPERS ───────────────────────────────────────────────────────────────

def hex_clean(value: str) -> str | None:
    """Normalise hex / rgb() / rgba() → '#RRGGBB' or None."""
    if not value:
        return None
    v = value.strip()
    m = re.fullmatch(r"#([0-9a-fA-F]{3,8})", v)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return "#" + h[:6].upper()
    m = re.match(r"rgba?\(([^)]+)\)", v)
    if m:
        parts = [p.strip() for p in m.group(1).split(",")[:3]]
        try:
            r, g, b = (int(float(p)) for p in parts)
            return f"#{r:02X}{g:02X}{b:02X}"
        except ValueError:
            return None
    return None


def lighten(hex_color: str, factor: float) -> str:
    """factor in [-1, 1]; positive lightens, negative darkens."""
    r, g, b = (int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    l = max(0, min(1, l + factor))
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return f"#{int(r * 255):02X}{int(g * 255):02X}{int(b * 255):02X}"


def contrast_ratio(c1: str, c2: str) -> float:
    """WCAG relative-luminance contrast ratio."""

    def lum(c: str) -> float:
        rgb = [int(c[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        rgb = [
            ((v + 0.055) / 1.055) ** 2.4 if v > 0.03928 else v / 12.92 for v in rgb
        ]
        return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]

    l1, l2 = lum(c1), lum(c2)
    light, dark = max(l1, l2), min(l1, l2)
    return (light + 0.05) / (dark + 0.05)


# ─── SCRAPE STEPS ──────────────────────────────────────────────────────────

def fetch(url: str, ua: str) -> tuple[BeautifulSoup, str]:
    r = requests.get(url, headers={"User-Agent": ua}, timeout=15)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser"), r.text


def find_logo(soup: BeautifulSoup, base_url: str) -> str | None:
    """Logo discovery — `<img>` with 'logo' hint → favicon → og:image."""
    # 1. <img> with logo in attrs
    for img in soup.find_all("img"):
        attrs = " ".join(filter(None, [img.get("class", "") and " ".join(img.get("class")), img.get("alt", ""), img.get("src", ""), img.get("id", "")]))
        if "logo" in attrs.lower() and img.get("src"):
            return urljoin(base_url, img["src"])
    # 2. link rel=icon (apple-touch-icon preferred — higher resolution)
    icons = soup.find_all("link", rel=re.compile(r"(apple-touch-icon|icon)", re.I))
    icons.sort(key=lambda x: 0 if "apple-touch-icon" in (x.get("rel") or [""])[0] else 1)
    for link in icons:
        if link.get("href"):
            return urljoin(base_url, link["href"])
    # 3. og:image
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        return urljoin(base_url, og["content"])
    return None


def download_logo(url: str, dest: Path) -> bool:
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        # Convert SVG/ico to PNG if needed (skip SVG for now — store as is)
        ext = Path(urlparse(url).path).suffix.lower()
        if ext == ".svg":
            dest.with_suffix(".svg").write_bytes(r.content)
            # Don't attempt SVG → PNG without extra deps
            return True
        img = Image.open(io.BytesIO(r.content))
        # Composite onto white background if RGBA so ColorThief works on actual visible colours
        if img.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            try:
                img = img.convert("RGBA")
                bg.paste(img, mask=img.split()[-1])
            except Exception:
                bg.paste(img.convert("RGB"))
            img = bg
        img.save(dest)
        return True
    except Exception as e:
        return False


def colorthief_colors(logo_path: Path) -> list[str]:
    """Returns dominant + palette as hex list, or [] if logo not analysable."""
    if not logo_path.exists() or logo_path.suffix.lower() == ".svg":
        return []
    try:
        from colorthief import ColorThief
        ct = ColorThief(str(logo_path))
        palette = ct.get_palette(color_count=5, quality=5)
        return [f"#{r:02X}{g:02X}{b:02X}" for (r, g, b) in palette]
    except Exception:
        return []


def is_grayscale(hex_color: str, tolerance: int = 12) -> bool:
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return max(abs(r - g), abs(r - b), abs(g - b)) < tolerance


def extract_theme_color_meta(soup: BeautifulSoup) -> str | None:
    m = soup.find("meta", attrs={"name": "theme-color"})
    return hex_clean(m["content"]) if m and m.get("content") else None


def extract_font(soup: BeautifulSoup, html: str) -> tuple[str, str]:
    """Returns (font_family, confidence)."""
    # 1. Google Fonts link
    for link in soup.find_all("link", href=re.compile(r"fonts\.(googleapis|gstatic)\.com")):
        m = re.search(r"family=([A-Za-z0-9 +]+)", link.get("href", ""))
        if m:
            fam = m.group(1).replace("+", " ").split(":")[0].strip()
            return fam, "high"
    # 2. CSS body font-family — search the raw HTML for inline / linked CSS
    m = re.search(r"body\s*\{[^}]*font-family\s*:\s*([^;]+);", html, re.I)
    if m:
        fam = m.group(1).split(",")[0].strip().strip("\"'")
        return fam, "medium"
    # 3. Fallback
    return "Segoe UI", "low"


def extract_client_name(soup: BeautifulSoup, url: str) -> str:
    og = soup.find("meta", property="og:site_name")
    if og and og.get("content"):
        return og["content"].strip()
    if soup.title and soup.title.string:
        # Use the first segment before separator
        t = re.split(r"\s*[\-|·–—]\s*", soup.title.string.strip())[0]
        if t:
            return t
    host = urlparse(url).hostname or url
    return host.replace("www.", "").split(".")[0].title()


def extract_language(soup: BeautifulSoup) -> str:
    html = soup.find("html")
    if html and html.get("lang"):
        lang = html["lang"].strip()
        # Normalise: "da" → "da-DK", "en" → "en-US"
        if lang.lower() == "da":
            return "da-DK"
        if lang.lower() == "en":
            return "en-US"
        return lang
    return "da-DK"


# ─── MAIN ──────────────────────────────────────────────────────────────────

def extract(url: str, ua: str = DEFAULT_UA) -> BrandAssets:
    ba = BrandAssets(client_url=url)
    soup, html = fetch(url, ua)
    ba.client_name = extract_client_name(soup, url)
    ba.language = extract_language(soup)

    # Logo
    logo_url = find_logo(soup, url)
    ba.confidence["logo"] = "high" if logo_url else "low"
    if logo_url:
        ba.logo_url = logo_url
        ext = Path(urlparse(logo_url).path).suffix.lower() or ".png"
        if ext not in (".png", ".jpg", ".jpeg", ".svg", ".ico", ".webp"):
            ext = ".png"
        if ext == ".webp":
            ext = ".png"
        local = OUT_DIR / f"logo{ext}"
        if download_logo(logo_url, local):
            ba.logo_local = str(local.relative_to(ROOT)).replace("\\", "/")
        else:
            ba.warnings.append(f"Logo download failed from {logo_url}")
            ba.confidence["logo"] = "low"

    # Colours
    primary, primary_conf = None, "low"
    meta_color = extract_theme_color_meta(soup)
    if meta_color:
        primary = meta_color
        primary_conf = "high"
    palette = colorthief_colors(OUT_DIR / Path(ba.logo_local).name) if ba.logo_local else []
    palette = [p for p in palette if not is_grayscale(p)]  # skip greys
    if not primary and palette:
        primary = palette[0]
        primary_conf = "medium"
    if not primary:
        primary = "#0E3A5F"  # safe default
        primary_conf = "low"
        ba.warnings.append("Primary colour unresolved — used safe default")

    secondary = next((p for p in palette[1:] if p != primary), None)
    if not secondary:
        secondary = lighten(primary, -0.20)  # 20% darker
        secondary_conf = "low"
    else:
        secondary_conf = "medium"

    background = "#FFFFFF"
    text = "#1A1A1A"
    # Auto-flip text if low contrast with primary on KPI cards
    if contrast_ratio(text, primary) < 4.5 and contrast_ratio("#FFFFFF", primary) >= 4.5:
        # Text on white still fine, but primary as card background needs white text — handled in theme later
        pass

    ba.colors = {
        "primary":    primary,
        "secondary":  secondary,
        "accent":     "#F2F2F2",
        "success":    "#3FA34D",
        "warning":    "#E67E22",
        "background": background,
        "text":       text,
    }
    ba.confidence["primary_color"] = primary_conf
    ba.confidence["secondary_color"] = secondary_conf

    # Fonts
    font, font_conf = extract_font(soup, html)
    if font not in PBI_SAFE_FONTS:
        ba.warnings.append(f"Font '{font}' not in PBI safe-list — falling back to Segoe UI")
        font = "Segoe UI"
        font_conf = "low"
    ba.fonts = {"heading": font, "body": font, "fallback": "Segoe UI"}
    ba.confidence["fonts"] = font_conf

    return ba


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=os.environ.get("CLIENT_URL"))
    ap.add_argument("--ua", default=DEFAULT_UA)
    args = ap.parse_args()
    if not args.url:
        raise SystemExit("Set CLIENT_URL via .env or pass --url")

    # Load .env if present
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))
        if not args.url:
            args.url = os.environ.get("CLIENT_URL")

    ba = extract(args.url, args.ua)
    out = OUT_DIR / "brand_assets.json"
    out.write_text(json.dumps(asdict(ba), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)}")
    print(f"  Client:   {ba.client_name}")
    print(f"  Primary:  {ba.colors['primary']} ({ba.confidence['primary_color']})")
    print(f"  Secondary:{ba.colors['secondary']} ({ba.confidence['secondary_color']})")
    print(f"  Font:     {ba.fonts['heading']} ({ba.confidence['fonts']})")
    if ba.warnings:
        print("Warnings:")
        for w in ba.warnings:
            print(f"  ⚠️  {w}")


if __name__ == "__main__":
    main()
