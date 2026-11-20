import hashlib
import uuid
from datetime import datetime, timezone

from app.db import repository
from app.detectors.secrets import scan_text_secrets
from app.engine.policy import decide_from_findings
from app.engine.upload_scan import scan_image_b64_response
from app.models import Decision, ScanResponse, TextScanRequest


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def scan_text(req: TextScanRequest) -> ScanResponse:
    scan_id = f"scan-{uuid.uuid4().hex[:12]}"
    findings = scan_text_secrets(req.content)
    decision = decide_from_findings(findings)
    severity = "unknown"
    if findings:
        order = ["critical", "high", "medium", "low", "unknown"]
        severity = min(findings, key=lambda f: order.index(f.severity)).severity

    title = "Text scan: no findings"
    if findings:
        title = f"Possible {findings[0].category.replace('_', ' ')} in outgoing text"

    incident_id = repository.create_incident_from_scan(
        action_id=req.action_id,
        modality=req.modality,
        severity=severity,
        decision=decision.value,
        title=title,
        summary_redacted=findings[0].excerpt_redacted if findings else None,
        destination_origin=req.destination_origin,
        source_app=req.source,
        findings=findings,
        payload_sha256=req.payload_sha256
        or hashlib.sha256(req.content.encode()).hexdigest(),
    )

    repository.add_event_step(incident_id, "scanning", {"scan_id": scan_id})
    repository.add_event_step(incident_id, "decision_ready", {"decision": decision.value})

    mod = req.modality
    return ScanResponse(
        scan_id=scan_id,
        action_id=req.action_id,
        state="decision_ready",
        decision=decision,
        findings=findings,
        transmission_status="not_sent_confirmed",
        modality=mod,
        extracted_text=req.content[:120_000] if len(req.content) <= 120_000 else req.content[:120_000] + "\n...[truncated]",
    )


def scan_image_b64(action_id: str, image_b64: str, source: str, dest: str) -> ScanResponse:
    return scan_image_b64_response(action_id, image_b64, source, dest)