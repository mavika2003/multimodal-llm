import base64
import hashlib
import uuid
from datetime import datetime, timezone

from app.db import repository
from app.detectors.ocr import scan_image_bytes
from app.detectors.secrets import scan_text_secrets
from app.engine.policy import decide_from_findings
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

    return ScanResponse(
        scan_id=scan_id,
        action_id=req.action_id,
        state="decision_ready",
        decision=decision,
        findings=findings,
        transmission_status="not_sent_confirmed",
    )


def scan_image_b64(action_id: str, image_b64: str, source: str, dest: str) -> ScanResponse:
    scan_id = f"scan-{uuid.uuid4().hex[:12]}"
    raw = base64.b64decode(image_b64.split(",")[-1])
    _text, findings = scan_image_bytes(raw)
    decision = decide_from_findings(findings)
    severity = "high" if findings else "low"
    if findings:
        severity = max(findings, key=lambda f: ["low", "medium", "high", "critical", "unknown"].index(f.severity)).severity

    title = "Image scan: no findings" if not findings else "Possible credential in screenshot"

    incident_id = repository.create_incident_from_scan(
        action_id=action_id,
        modality="image",
        severity=severity,
        decision=decision.value,
        title=title,
        summary_redacted=findings[0].excerpt_redacted if findings else None,
        destination_origin=dest,
        source_app=source,
        findings=findings,
        payload_sha256=hashlib.sha256(raw).hexdigest(),
    )
    repository.add_event_step(incident_id, "scanning", {"scan_id": scan_id})
    repository.add_event_step(incident_id, "decision_ready", {"decision": decision.value})

    return ScanResponse(
        scan_id=scan_id,
        action_id=action_id,
        state="decision_ready",
        decision=decision,
        findings=findings,
        transmission_status="not_sent_confirmed",
    )