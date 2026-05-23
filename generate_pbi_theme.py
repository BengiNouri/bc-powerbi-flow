"""
Generate a Power BI custom theme JSON that can be imported into any report.
File -> Switch theme -> Custom themes -> Browse -> select the output file.
"""
import json
from pathlib import Path
from config import OUTPUT_DIR

theme = {
    "name": "CRONUS DW Theme",
    "dataColors": [
        "#0078D4",  # Primary blue
        "#00B294",  # Teal
        "#FFB900",  # Amber
        "#D13438",  # Red
        "#881798",  # Purple
        "#107C10",  # Green
        "#005A9E",  # Dark blue
        "#767676",  # Gray
    ],
    "background": "#FFFFFF",
    "foreground": "#252423",
    "tableAccent": "#0078D4",
    "visualStyles": {
        "*": {
            "*": {
                "general": [{
                    "responsive": True,
                    "keepLayerOrder": True,
                }],
                "title": [{
                    "fontFamily": "Segoe UI Semibold",
                    "fontSize": 12,
                    "fontColor": {"solid": {"color": "#252423"}},
                    "alignment": "left",
                    "show": True,
                }],
                "labels": [{
                    "fontFamily": "Segoe UI",
                    "fontSize": 10,
                    "fontColor": {"solid": {"color": "#605E5C"}},
                }],
            },
            "card": {
                "labels": [{
                    "fontSize": 24,
                    "fontFamily": "Segoe UI Bold",
                    "fontColor": {"solid": {"color": "#0078D4"}},
                }],
                "categoryLabels": [{
                    "fontSize": 10,
                    "fontFamily": "Segoe UI",
                    "fontColor": {"solid": {"color": "#605E5C"}},
                }],
            },
        },
    },
    "textClasses": {
        "callout": {"fontSize": 28, "fontFace": "Segoe UI Bold", "color": "#252423"},
        "title": {"fontSize": 14, "fontFace": "Segoe UI Semibold", "color": "#252423"},
        "header": {"fontSize": 12, "fontFace": "Segoe UI Semibold", "color": "#252423"},
        "label": {"fontSize": 10, "fontFace": "Segoe UI", "color": "#605E5C"},
    },
}

output_path = Path(OUTPUT_DIR) / "CRONUS_DW_Theme.json"
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps(theme, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"Theme saved: {output_path}")
print("Import in Power BI: View -> Themes -> Browse for themes -> select CRONUS_DW_Theme.json")
