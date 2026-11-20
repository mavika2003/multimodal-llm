#!/usr/bin/env python3
"""Generate synthetic multimodal fixtures (local, fictional secrets)."""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "fixtures" / "multimodal_demo"
OUT.mkdir(parents=True, exist_ok=True)


def gen_png():
    from PIL import Image, ImageDraw, ImageFont

    for name, lines in [
        (
            "screenshot_labels.png",
            [
                "Synthetic deploy log (demo)",
                "export CLIENT_TOKEN=syn_demo_on_screen",
                'config = { "apiKey": "sk-demo-not-real" }',
            ],
        ),
        (
            "safe_image.png",
            ["Public park photo (demo)", "No credentials on this slide."],
        ),
    ]:
        img = Image.new("RGB", (480, 240), color=(248, 250, 252))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
        except OSError:
            font = ImageFont.load_default()
        y = 24
        for line in lines:
            color = (185, 28, 28) if "TOKEN" in line or "apiKey" in line else (30, 41, 59)
            draw.text((20, y), line, fill=color, font=font)
            y += 28
        img.save(OUT / name, format="PNG")
        print("wrote", OUT / name)


def gen_code_files():
    (OUT.parent / "synthetic_only").mkdir(exist_ok=True)
    (OUT / "sample_secret.py").write_text(
        textwrap.dedent(
            """
            # FAKE
            PAYMENT_API_KEY = "sk_test_AIRLOCK_FAKE_only"
            CONFIDENTIAL_CONTEXT = "Project NIGHTJAR private acquisition target $48.5M"
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    (OUT / "sample_secret.ts").write_text(
        'const token = "ghp_syntheticGitHubTokenForDemoOnly123";\n',
        encoding="utf-8",
    )
    (OUT / "sample_secret.env").write_text(
        "API_KEY=sk_live_synthetic_demo_only\nDATABASE_URL=postgresql://demo:FakePass@localhost/db\n",
        encoding="utf-8",
    )


def gen_pdfs():
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Project Phoenix launches in Q2 2026. Contact: demo@example.com.")
    doc.save(OUT / "demo_document.pdf")
    doc.close()

    scan = fitz.open()
    p = scan.new_page()
    # image-only page via pixmap render of screenshot
    from PIL import Image

    img_path = OUT / "screenshot_labels.png"
    if img_path.exists():
        pix = fitz.Pixmap(str(img_path))
        p.insert_image(fitz.Rect(36, 36, 400, 300), pixmap=pix)
    scan.save(OUT / "scanned_document.pdf")
    scan.close()
    print("wrote PDFs")


def gen_audio():
    speech = OUT / "demo_speech.wav"
    ok = subprocess.run(
        ["say", "-o", str(speech), "--file-format=WAVE", "Please send the customer report to the team."],
        check=False,
    ).returncode == 0
    if not ok or not speech.exists() or speech.stat().st_size < 1000:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:duration=2.5",
                "-ar",
                "16000",
                str(speech),
            ],
            check=False,
            capture_output=True,
        )
    tone = OUT / "demo_sound_events.wav"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=1200:duration=0.4",
            "-ar",
            "16000",
            str(tone),
        ],
        check=False,
        capture_output=True,
    )
    print("audio fixtures", speech.exists(), tone.exists())


def gen_video():
    png = OUT / "screenshot_labels.png"
    mp4 = OUT / "demo_video.mp4"
    safe = OUT / "safe_image.png"
    if not png.exists():
        return
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(png),
            "-t",
            "3",
            "-vf",
            "format=yuv420p",
            str(OUT / "segment_secret.mp4"),
        ],
        check=False,
        capture_output=True,
    )
    if safe.exists():
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loop",
                "1",
                "-i",
                str(safe),
                "-t",
                "3",
                "-vf",
                "format=yuv420p",
                str(OUT / "segment_safe.mp4"),
            ],
            check=False,
            capture_output=True,
        )
    list_file = OUT / "concat.txt"
    list_file.write_text(
        f"file '{OUT / 'segment_secret.mp4'}'\nfile '{OUT / 'segment_safe.mp4'}'\n",
        encoding="utf-8",
    )
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(mp4)],
        check=False,
        capture_output=True,
    )
    print("video", mp4.exists())


def main():
    gen_png()
    gen_code_files()
    try:
        gen_pdfs()
    except Exception as e:
        print("pdf skip", e)
    gen_audio()
    gen_video()


if __name__ == "__main__":
    main()