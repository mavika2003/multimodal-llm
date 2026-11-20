import io
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.detectors.ocr import scan_image_bytes
from app.detectors.secrets import scan_text_secrets

try:
    from pypdf import PdfReader

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


def extract_document_text(data: bytes, filename: str) -> str:
    lower = filename.lower()
    if lower.endswith((".txt", ".md", ".json", ".csv", ".log", ".srt", ".vtt")):
        return data.decode("utf-8", errors="replace")
    if lower.endswith(".pdf"):
        if not PDF_AVAILABLE:
            return "[PDF support requires pypdf on the API server]"
        reader = PdfReader(io.BytesIO(data))
        parts: list[str] = []
        for i, page in enumerate(reader.pages[:50], start=1):
            page_text = (page.extract_text() or "").strip()
            if page_text:
                parts.append(f"--- page {i} ---\n{page_text}")
        return "\n\n".join(parts).strip() or "[PDF contained no extractable text]"
    return data.decode("utf-8", errors="replace")


def extract_image_text(data: bytes) -> tuple[str, list]:
    text, findings = scan_image_bytes(data)
    return text, findings


def extract_audio_text(data: bytes, filename: str) -> str:
    lower = filename.lower()
    if lower.endswith((".txt", ".srt", ".vtt", ".md")):
        return data.decode("utf-8", errors="replace")
    if shutil.which("ffmpeg"):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "in"
            wav = Path(td) / "out.wav"
            src.write_bytes(data)
            try:
                subprocess.run(
                    ["ffmpeg", "-y", "-i", str(src), "-ar", "16000", "-ac", "1", str(wav)],
                    check=True,
                    capture_output=True,
                    timeout=120,
                )
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                return (
                    f"[Could not decode audio {filename}. Upload a .txt transcript for offline demo.]"
                )
            if shutil.which("whisper"):
                try:
                    out = subprocess.run(
                        ["whisper", str(wav), "--model", "tiny", "--language", "en", "--output_format", "txt", "--output_dir", td],
                        capture_output=True,
                        text=True,
                        timeout=300,
                    )
                    if out.returncode == 0:
                        txt_files = list(Path(td).glob("*.txt"))
                        if txt_files:
                            return txt_files[0].read_text(encoding="utf-8", errors="replace")
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
    return (
        f"[Audio {filename}: no local transcript extracted. "
        "For demo, attach a .txt transcript or install whisper CLI with ffmpeg.]"
    )


def extract_video_text(data: bytes, filename: str) -> str:
    if shutil.which("ffmpeg"):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "in"
            src.write_bytes(data)
            offsets = [1, 3, 8]
            chunks: list[str] = []
            total_findings = 0
            for sec in offsets:
                frame = Path(td) / f"frame_{sec}.jpg"
                try:
                    subprocess.run(
                        [
                            "ffmpeg",
                            "-y",
                            "-i",
                            str(src),
                            "-ss",
                            str(sec),
                            "-vframes",
                            "1",
                            str(frame),
                        ],
                        check=True,
                        capture_output=True,
                        timeout=120,
                    )
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                    continue
                if not frame.exists():
                    continue
                img_data = frame.read_bytes()
                ocr_text, findings = scan_image_bytes(img_data)
                total_findings += len(findings)
                chunks.append(f"[t={sec}s] {ocr_text.strip() or '(no ocr text)'}")
            if chunks:
                note = f"Multi-frame OCR from {filename}:\n" + "\n".join(chunks)
                if total_findings:
                    note += f"\n(findings: {total_findings} rule hit(s) across frames)"
                return note
    return (
        f"[Video {filename}: frame OCR unavailable without ffmpeg. "
        "Upload a short clip or paste a description in Inspector Q&A.]"
    )


def analyze_extracted_text(text: str, detector_prefix: str = "ingest_rules") -> list:
    return scan_text_secrets(text, detector_prefix=detector_prefix)