import io
import uuid
from dataclasses import dataclass

from PIL import Image

from app.detectors.secrets import scan_text_secrets
from app.models import Finding, SourceAnchor

try:
    import pytesseract
    from pytesseract import Output

    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


@dataclass
class OcrToken:
    text: str
    left: int
    top: int
    width: int
    height: int
    conf: float


def _run_tesseract(image: Image.Image) -> list[OcrToken]:
    if not TESSERACT_AVAILABLE:
        return []
    try:
        data = pytesseract.image_to_data(image, output_type=Output.DICT)
    except Exception:
        return []
    tokens: list[OcrToken] = []
    n = len(data["text"])
    for i in range(n):
        txt = (data["text"][i] or "").strip()
        if not txt:
            continue
        conf = float(data["conf"][i])
        if conf < 0:
            continue
        tokens.append(
            OcrToken(
                text=txt,
                left=int(data["left"][i]),
                top=int(data["top"][i]),
                width=int(data["width"][i]),
                height=int(data["height"][i]),
                conf=conf,
            )
        )
    return tokens


def scan_image_bytes(data: bytes) -> tuple[str, list[Finding]]:
    image = Image.open(io.BytesIO(data)).convert("RGB")
    tokens = _run_tesseract(image)
    full_text = " ".join(t.text for t in tokens)
    findings = scan_text_secrets(full_text, detector_prefix="ocr_plus_rules")

    for f in findings:
        anchor = f.anchor
        if anchor.start is None or anchor.end is None:
            continue
        # Map character span in concatenated text back to rough box via token scan
        cursor = 0
        matched_box: list[int] | None = None
        for tok in tokens:
            tok_start = cursor
            tok_end = cursor + len(tok.text)
            cursor = tok_end + 1
            if tok_start <= anchor.start < tok_end or tok_start < anchor.end <= tok_end:
                x1, y1 = tok.left, tok.top
                x2, y2 = tok.left + tok.width, tok.top + tok.height
                if matched_box is None:
                    matched_box = [x1, y1, x2, y2]
                else:
                    matched_box = [
                        min(matched_box[0], x1),
                        min(matched_box[1], y1),
                        max(matched_box[2], x2),
                        max(matched_box[3], y2),
                    ]
        if matched_box:
            f.anchor = SourceAnchor(
                kind="image_box",
                page_or_frame=0,
                bbox_xyxy=matched_box,
            )
            f.detector = "ocr_plus_rules"

    if not TESSERACT_AVAILABLE and not findings:
        findings.append(
            Finding(
                id=f"finding-{uuid.uuid4().hex[:12]}",
                category="ocr_unavailable",
                severity="unknown",
                detector="ocr",
                confidence_label="low",
                anchor=SourceAnchor(kind="image_box", page_or_frame=0, bbox_xyxy=[0, 0, 0, 0]),
                excerpt_redacted="[OCR engine not installed]",
                explanation_redacted="Install Tesseract for screenshot scanning.",
            )
        )

    return full_text, findings