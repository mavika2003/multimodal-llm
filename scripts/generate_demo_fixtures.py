#!/usr/bin/env python3
"""Generate synthetic multimodal demo image (OCR + optional VLM)."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "fixtures" / "multimodal_demo" / "screenshot_labels.png"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (520, 280), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
        font_sm = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
    except OSError:
        font = ImageFont.load_default()
        font_sm = font
    draw.rectangle((8, 8, 512, 272), outline=(30, 41, 59), width=2)
    draw.text((24, 24), "Synthetic deploy log (demo)", fill=(15, 23, 42), font=font)
    draw.text((24, 60), "export CLIENT_TOKEN=syn_demo_on_screen", fill=(185, 28, 28), font=font_sm)
    draw.text((24, 90), 'config = { "apiKey": "sk-demo-not-real" }', fill=(185, 28, 28), font=font_sm)
    draw.text((24, 130), "Build #1042 — internal only", fill=(71, 85, 105), font=font_sm)
    draw.text((24, 170), "Error: auth failed at gateway", fill=(180, 83, 9), font=font_sm)
    img.save(OUT, format="PNG")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()