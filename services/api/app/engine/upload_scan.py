import base64
import hashlib
import uuid

from app.models import Finding, SourceAnchor
from app.db import repository
from app.detectors.analyze import analyze_extracted_text, merge_findings
from app.detectors.ingest import extract_audio_text
from app.detectors.pdf_pipeline import extract_document_text
from app.detectors.ocr import scan_image_bytes
from app.engine.policy import decide_from_findings
from app.models import Decision, Finding, ScanResponse
from app.scan.diagnostics import new_scan_diag

_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
_AUDIO_EXT = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".opus"}
_VIDEO_EXT = {".mp4", ".webm", ".mov", ".mkv", ".avi", ".m4v"}
_CODE_EXT = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".java",
    ".go",
    ".rs",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".sh",
    ".bash",
    ".zsh",
    ".yaml",
    ".yml",
    ".env",
    ".sql",
    ".rb",
    ".php",
}


def infer_upload_modality(filename: str) -> str:
    lower = filename.lower()
    for ext in _IMAGE_EXT:
        if lower.endswith(ext):
            return "image"
    if lower.endswith(".pdf"):
        return "document"
    for ext in _AUDIO_EXT:
        if lower.endswith(ext):
            return "audio"
    for ext in _VIDEO_EXT:
        if lower.endswith(ext):
            return "video"
    for ext in _CODE_EXT:
        if lower.endswith(ext):
            return "code"
    if lower.endswith((".txt", ".md", ".json", ".csv", ".log", ".srt", ".vtt")):
        return "text"
    return "document"


def _severity_from_findings(findings: list[Finding]) -> str:
    if not findings:
        return "low"
    order = ["critical", "high", "medium", "low", "unknown"]
    return min(findings, key=lambda f: order.index(f.severity)).severity


def _title_for(modality: str, findings: list[Finding]) -> str:
    if not findings:
        return f"{modality.title()} scan: no findings"
    cat = findings[0].category.replace("_", " ")
    return f"Possible {cat} in outgoing {modality}"


def _persist_scan(
    *,
    action_id: str,
    modality: str,
    findings: list[Finding],
    decision: Decision,
    title: str,
    source: str,
    dest: str,
    payload_sha256: str,
    filename: str | None,
    extracted_text: str | None,
    scan_request_id: str | None = None,
    stages_ms: dict[str, float] | None = None,
) -> ScanResponse:
    scan_id = f"scan-{uuid.uuid4().hex[:12]}"
    severity = _severity_from_findings(findings)
    summary = findings[0].excerpt_redacted if findings else None

    incident_id = repository.create_incident_from_scan(
        action_id=action_id,
        modality=modality,
        severity=severity,
        decision=decision.value,
        title=title,
        summary_redacted=summary,
        destination_origin=dest,
        source_app=source,
        findings=findings,
        payload_sha256=payload_sha256,
    )
    repository.add_event_step(incident_id, "scanning", {"scan_id": scan_id, "filename": filename})
    repository.add_event_step(incident_id, "decision_ready", {"decision": decision.value})

    preview = extracted_text
    if preview and len(preview) > 120_000:
        preview = preview[:120_000] + "\n...[truncated for response]"

    return ScanResponse(
        scan_id=scan_id,
        action_id=action_id,
        state="decision_ready",
        decision=decision,
        findings=findings,
        transmission_status="not_sent_confirmed",
        modality=modality,
        filename=filename,
        extracted_text=preview,
        scan_request_id=scan_request_id,
        stages_ms=stages_ms,
    )


def scan_uploaded_file(
    action_id: str,
    data: bytes,
    filename: str,
    source: str,
    dest: str,
    modality: str | None = None,
) -> ScanResponse:
    mod = modality or infer_upload_modality(filename)
    diag = new_scan_diag(action_id, mod, filename)
    sha = hashlib.sha256(data).hexdigest()

    if mod == "image":
        ocr_text, findings = scan_image_bytes(data)
        decision = decide_from_findings(findings)
        return _persist_scan(
            action_id=action_id,
            modality="image",
            findings=findings,
            decision=decision,
            title=_title_for("image", findings),
            source=source,
            dest=dest,
            payload_sha256=sha,
            filename=filename,
            extracted_text=ocr_text or None,
        )

    if mod == "document":
        extracted = extract_document_text(data, filename)
        findings = analyze_extracted_text(extracted, detector_prefix="document_scan")
    elif mod == "audio":
        extracted, _sounds, _model, asr_err = extract_audio_text(data, filename)
        findings = analyze_extracted_text(extracted, detector_prefix="audio_scan")
        if asr_err and not findings:
            findings.append(
                Finding(
                    id=f"finding-{uuid.uuid4().hex[:12]}",
                    category="asr_failed",
                    severity="unknown",
                    detector="audio_scan",
                    confidence_label="low",
                    anchor=SourceAnchor(kind="text_span", start=0, end=0),
                    excerpt_redacted=f"[ASR failed: {asr_err[:120]}]",
                    explanation_redacted="Speech could not be transcribed; audio may still contain secrets.",
                )
            )
        elif not findings and extracted and "[Transcription failed" in extracted:
            findings.append(
                Finding(
                    id=f"finding-{uuid.uuid4().hex[:12]}",
                    category="asr_failed",
                    severity="unknown",
                    detector="audio_scan",
                    confidence_label="low",
                    anchor=SourceAnchor(kind="text_span", start=0, end=0),
                    excerpt_redacted="[Transcription failed]",
                    explanation_redacted="Speech could not be transcribed; audio may still contain secrets.",
                )
            )
    elif mod == "video":
        from app.detectors.ingest import extract_video_text_firewall

        with diag.stage("video_extract"):
            extracted, _sounds, _models, frame_findings = extract_video_text_firewall(
                data, filename, diag=diag
            )
        with diag.stage("video_rules"):
            text_findings = analyze_extracted_text(extracted, detector_prefix="video_scan")
            findings = merge_findings(frame_findings, text_findings)
            ocr_had_signal = any(
                line.startswith("[t=") and "OCR:" in line and "(none)" not in line
                for line in extracted.splitlines()
            )
            if not findings and "no_video_frames_extracted" in extracted:
                findings.append(
                    Finding(
                        id=f"finding-{uuid.uuid4().hex[:12]}",
                        category="video_extract_failed",
                        severity="unknown",
                        detector="video_scan",
                        confidence_label="low",
                        anchor=SourceAnchor(kind="text_span", start=0, end=0),
                        excerpt_redacted="[Could not read video frames]",
                        explanation_redacted="ffmpeg did not extract frames; scan cannot see on-screen secrets.",
                    )
                )
            elif not findings and not ocr_had_signal and "Video analysis" in extracted:
                findings.append(
                    Finding(
                        id=f"finding-{uuid.uuid4().hex[:12]}",
                        category="video_blind_ocr",
                        severity="medium",
                        detector="video_scan",
                        confidence_label="low",
                        anchor=SourceAnchor(kind="text_span", start=0, end=0),
                        excerpt_redacted="[No readable text from video frames]",
                        explanation_redacted="OCR/VLM found no text; outbound video may still hide on-screen secrets.",
                    )
                )
    elif mod == "code":
        extracted = data.decode("utf-8", errors="replace")
        findings = analyze_extracted_text(extracted, detector_prefix="code_scan")
    else:
        mod = "text"
        extracted = data.decode("utf-8", errors="replace")
        findings = analyze_extracted_text(extracted, detector_prefix="text_scan")

    decision = decide_from_findings(findings)
    return _persist_scan(
        action_id=action_id,
        modality=mod,
        findings=findings,
        decision=decision,
        title=_title_for(mod, findings),
        source=source,
        dest=dest,
        payload_sha256=sha,
        filename=filename,
        extracted_text=extracted,
        scan_request_id=diag.request_id,
        stages_ms=diag.stages_ms,
    )


def scan_image_b64_response(
    action_id: str, image_b64: str, source: str, dest: str, filename: str | None = None
) -> ScanResponse:
    raw = base64.b64decode(image_b64.split(",")[-1])
    return scan_uploaded_file(
        action_id, raw, filename or "upload.png", source, dest, modality="image"
    )