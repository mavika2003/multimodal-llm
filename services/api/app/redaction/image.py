import io

from PIL import Image, ImageDraw

from app.models import Finding


def redact_image_bytes(data: bytes, findings: list[Finding], finding_ids: list[str]) -> bytes:
    image = Image.open(io.BytesIO(data)).convert("RGB")
    draw = ImageDraw.Draw(image)
    pad = 4
    w, h = image.size
    for f in findings:
        if f.id not in finding_ids:
            continue
        if f.anchor.bbox_xyxy and len(f.anchor.bbox_xyxy) == 4:
            x1, y1, x2, y2 = f.anchor.bbox_xyxy
            x1 = max(0, x1 - pad)
            y1 = max(0, y1 - pad)
            x2 = min(w, x2 + pad)
            y2 = min(h, y2 + pad)
            draw.rectangle([x1, y1, x2, y2], fill=(0, 0, 0))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()