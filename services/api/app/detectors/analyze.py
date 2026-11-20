from app.detectors.contextual import scan_contextual_text
from app.detectors.secrets import scan_text_secrets
from app.detectors.vlm_risk import scan_vlm_credential_narrative
from app.models import Finding


def merge_findings(*groups: list[Finding]) -> list[Finding]:
    out: list[Finding] = []
    seen: set[tuple] = set()
    for group in groups:
        for f in group:
            key = (
                f.category,
                f.anchor.kind,
                f.anchor.page_or_frame,
                f.anchor.start,
                f.anchor.end,
            )
            if key in seen:
                continue
            seen.add(key)
            out.append(f)
    return out


def analyze_extracted_text(text: str, detector_prefix: str = "ingest_rules") -> list[Finding]:
    findings = scan_text_secrets(text, detector_prefix=detector_prefix)
    contextual = scan_contextual_text(text, detector_prefix="context_policy")
    narrative = scan_vlm_credential_narrative(text, detector_prefix="narrative_rules")
    seen = {(f.anchor.start, f.anchor.end, f.category) for f in findings if f.anchor.start is not None}
    for f in contextual + narrative:
        key = (f.anchor.start, f.anchor.end, f.category)
        if key not in seen:
            findings.append(f)
    return findings