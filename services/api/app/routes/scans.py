import base64

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel

from app.auth import verify_bearer, verify_origin
from app.detectors.secrets import scan_text_secrets
from app.engine.orchestrator import scan_image_b64, scan_text
from app.engine.policy import decide_from_findings
from app.models import RedactRequest, RedactResponse, ScanResponse, TextScanRequest
from app.redaction.image import redact_image_bytes
from app.redaction.text import redact_text

router = APIRouter(dependencies=[Depends(verify_bearer), Depends(verify_origin)])


@router.post("/scans/text", response_model=ScanResponse)
def scans_text(req: TextScanRequest) -> ScanResponse:
    if len(req.content.encode()) > 512_000:
        from fastapi import HTTPException

        raise HTTPException(status_code=413, detail="FILE_TOO_LARGE")
    return scan_text(req)


@router.post("/scans/image", response_model=ScanResponse)
async def scans_image(
    action_id: str = Form(...),
    source: str = Form("local-demo-chat"),
    destination_origin: str = Form("http://127.0.0.1:5174"),
    file: UploadFile = File(...),
) -> ScanResponse:
    data = await file.read()
    if len(data) > 25_000_000:
        from fastapi import HTTPException

        raise HTTPException(status_code=413, detail="FILE_TOO_LARGE")
    b64 = base64.b64encode(data).decode()
    return scan_image_b64(action_id, b64, source, destination_origin)


@router.post("/redactions", response_model=RedactResponse)
def redactions(req: RedactRequest) -> RedactResponse:
    if req.modality in ("text", "code") and req.content_text is not None:
        sanitized = redact_text(req.content_text, req.findings, req.finding_ids)
        return RedactResponse(sanitized_text=sanitized, finding_ids=req.finding_ids)
    if req.modality == "image" and req.image_base64:
        raw = base64.b64decode(req.image_base64.split(",")[-1])
        out = redact_image_bytes(raw, req.findings, req.finding_ids)
        b64 = base64.b64encode(out).decode()
        return RedactResponse(
            sanitized_image_base64=f"data:image/png;base64,{b64}",
            finding_ids=req.finding_ids,
        )
    from fastapi import HTTPException

    raise HTTPException(status_code=400, detail="INVALID_PAYLOAD")


class VerifyTextBody(BaseModel):
    content: str
    action_id: str


@router.post("/scans/verify-text", response_model=ScanResponse)
def verify_text_after_redact(body: VerifyTextBody) -> ScanResponse:
    content = body.content
    action_id = body.action_id
    findings = scan_text_secrets(content)
    decision = decide_from_findings(findings)
    return ScanResponse(
        scan_id="verify",
        action_id=action_id,
        decision=decision,
        findings=findings,
        transmission_status="not_sent_confirmed",
    )