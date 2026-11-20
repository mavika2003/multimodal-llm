"""Policy-based confidential business context detection."""

from __future__ import annotations

import re
import uuid
from pathlib import Path

import yaml

from app.models import Finding, SourceAnchor
from app.settings import settings

_cached_policy: dict | None = None


def _load_policy() -> dict:
    global _cached_policy
    if _cached_policy is not None:
        return _cached_policy
    path = settings.policy_path
    if not path.is_file():
        _cached_policy = {"indicators": [], "codenames": []}
        return _cached_policy
    with open(path, encoding="utf-8") as f:
        _cached_policy = yaml.safe_load(f) or {}
    return _cached_policy


def scan_contextual_text(
    text: str,
    detector_prefix: str = "context_policy",
    page_or_frame: int | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    policy = _load_policy()
    for item in policy.get("indicators", []):
        pattern = item.get("pattern")
        if not pattern:
            continue
        cat = item.get("category", "confidential_context")
        sev = item.get("severity", "medium")
        for m in re.finditer(pattern, text):
            start, end = m.span()
            snippet = text[max(0, start - 30) : min(len(text), end + 30)]
            findings.append(
                Finding(
                    id=f"finding-{uuid.uuid4().hex[:12]}",
                    category=cat,
                    severity=sev,  # type: ignore[arg-type]
                    detector=detector_prefix,
                    confidence_label="medium",
                    anchor=SourceAnchor(
                        kind="text_span",
                        start=start,
                        end=end,
                        page_or_frame=page_or_frame,
                    ),
                    excerpt_redacted=re.sub(re.escape(text[start:end]), "[REDACTED]", snippet, count=1),
                    explanation_redacted="Matched local confidentiality policy.",
                    policy_rule_id=cat,
                )
            )
    for code in policy.get("codenames", []):
        for m in re.finditer(re.escape(code), text, re.IGNORECASE):
            start, end = m.span()
            if any(f.anchor.start == start for f in findings):
                continue
            findings.append(
                Finding(
                    id=f"finding-{uuid.uuid4().hex[:12]}",
                    category="confidential_project",
                    severity="medium",
                    detector=detector_prefix,
                    confidence_label="medium",
                    anchor=SourceAnchor(kind="text_span", start=start, end=end, page_or_frame=page_or_frame),
                    excerpt_redacted=f"... Project [REDACTED] ...",
                    explanation_redacted=f"Codename {code} flagged by policy.",
                    policy_rule_id="codename",
                )
            )
    return findings