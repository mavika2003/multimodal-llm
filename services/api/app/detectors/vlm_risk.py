"""Heuristic credential findings from VLM / transcript prose (not only exact OCR)."""

from __future__ import annotations

import re
import uuid

from app.models import Finding, SourceAnchor

_CREDENTIAL_NARRATIVE: list[tuple[str, str, re.Pattern[str]]] = [
    (
        "aws_key",
        "high",
        re.compile(
            r"(?i)(aws.{0,24}(access|secret)\s*key|export\s+aws_|akia[0-9a-z]{8,})",
        ),
    ),
    (
        "api_key",
        "high",
        re.compile(
            r"(?i)(api\s*key|access\s*token|client\s*token|bearer\s+token).{0,40}(visible|shown|displayed|leak)",
        ),
    ),
    (
        "private_key_block",
        "critical",
        re.compile(r"(?i)(private\s+key|-----BEGIN).{0,30}(visible|shown|displayed)"),
    ),
]


def scan_vlm_credential_narrative(
    text: str,
    detector_prefix: str = "vlm_narrative",
    page_or_frame: int | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    for category, severity, pattern in _CREDENTIAL_NARRATIVE:
        for m in pattern.finditer(text):
            start, end = m.span()
            snippet = text[max(0, start - 24) : min(len(text), end + 24)]
            findings.append(
                Finding(
                    id=f"finding-{uuid.uuid4().hex[:12]}",
                    category=category,
                    severity=severity,  # type: ignore[arg-type]
                    detector=detector_prefix,
                    confidence_label="medium",
                    anchor=SourceAnchor(
                        kind="text_span",
                        start=start,
                        end=end,
                        page_or_frame=page_or_frame,
                    ),
                    excerpt_redacted=snippet,
                    explanation_redacted="VLM or transcript described exposed credentials.",
                )
            )
    return findings