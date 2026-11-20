"""PDF extraction: searchable text + OCR/VLM for image-heavy pages."""

from __future__ import annotations

import base64
import io
from dataclasses import dataclass

from app.detectors.analyze import analyze_extracted_text
from app.detectors.ocr import scan_image_bytes
from app.settings import settings

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


@dataclass
class PdfExtractResult:
    text: str
    page_count: int
    ocr_pages: list[int]
    vlm_notes: list[str]


def extract_pdf_enhanced(data: bytes, filename: str) -> PdfExtractResult:
    if not fitz:
        from app.detectors.ingest import extract_document_text

        t = extract_document_text(data, filename)
        return PdfExtractResult(t, 0, [], [])

    doc = fitz.open(stream=data, filetype="pdf")
    parts: list[str] = []
    ocr_pages: list[int] = []
    vlm_notes: list[str] = []
    page_count = min(doc.page_count, settings.pdf_max_pages)

    for page_num in range(page_count):
        page = doc.load_page(page_num)
        page_text = (page.get_text() or "").strip()
        header = f"--- page {page_num + 1} ---"
        if len(page_text) >= 40:
            parts.append(f"{header}\n{page_text}")
            continue
        # Image-heavy / scanned page
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        img_bytes = pix.tobytes("png")
        ocr_text, _ = scan_image_bytes(img_bytes)
        ocr_pages.append(page_num + 1)
        parts.append(f"{header}\n[scanned_page_ocr]\n{ocr_text}")
        if page_num < settings.pdf_vlm_max_pages:
            vlm_notes.append(f"page_{page_num + 1}_rendered_for_vision")

    doc.close()
    text = "\n\n".join(parts).strip() or "[PDF contained no extractable content]"
    return PdfExtractResult(text, page_count, ocr_pages, vlm_notes)


def extract_document_text(data: bytes, filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return extract_pdf_enhanced(data, filename).text
    if lower.endswith((".txt", ".md", ".json", ".csv", ".log", ".srt", ".vtt")):
        return data.decode("utf-8", errors="replace")
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        parts = []
        for i, page in enumerate(reader.pages[: settings.pdf_max_pages], start=1):
            t = (page.extract_text() or "").strip()
            if t:
                parts.append(f"--- page {i} ---\n{t}")
        if parts:
            return "\n\n".join(parts)
    except Exception:
        pass
    return data.decode("utf-8", errors="replace")