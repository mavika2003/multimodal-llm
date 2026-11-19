import math
import re
import uuid
from collections.abc import Iterable

from app.models import Finding, SourceAnchor

SECRET_PATTERNS: list[tuple[str, str, re.Pattern[str]]] = [
    (
        "api_key",
        "high",
        re.compile(
            r"(?i)(api[_-]?key|apikey|access[_-]?token|client[_-]?token|secret[_-]?key)"
            r"\s*[=:]\s*['\"]?([A-Za-z0-9_\-./+=]{8,})",
        ),
    ),
    (
        "private_key_block",
        "critical",
        re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
    ),
    (
        "aws_key",
        "high",
        re.compile(r"AKIA[0-9A-Z]{16}"),
    ),
    (
        "github_token",
        "high",
        re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    ),
    (
        "bearer_token",
        "medium",
        re.compile(r"(?i)bearer\s+[A-Za-z0-9_\-.]{12,}"),
    ),
]

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


def _entropy(s: str) -> float:
    if not s:
        return 0.0
    freq: dict[str, int] = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    ent = 0.0
    n = len(s)
    for count in freq.values():
        p = count / n
        ent -= p * math.log2(p)
    return ent


def _high_entropy_assignments(text: str) -> Iterable[tuple[int, int, str]]:
    for m in re.finditer(r"=\s*['\"]?([A-Za-z0-9+/=_\-]{20,})['\"]?", text):
        val = m.group(1)
        if _entropy(val) >= 3.8:
            start = m.start(1)
            end = m.end(1)
            yield start, end, val


def scan_text_secrets(text: str, detector_prefix: str = "deterministic_rules") -> list[Finding]:
    findings: list[Finding] = []
    seen_spans: set[tuple[int, int]] = set()

    def add(
        category: str,
        severity: str,
        start: int,
        end: int,
        label: str,
        explanation: str,
    ) -> None:
        if (start, end) in seen_spans:
            return
        seen_spans.add((start, end))
        snippet = text[max(0, start - 20) : min(len(text), end + 20)]
        redacted = re.sub(
            re.escape(text[start:end]),
            "[REDACTED]",
            snippet,
            count=1,
        )
        findings.append(
            Finding(
                id=f"finding-{uuid.uuid4().hex[:12]}",
                category=category,
                severity=severity,  # type: ignore[arg-type]
                detector=detector_prefix,
                confidence_label="high" if severity in ("high", "critical") else "medium",
                anchor=SourceAnchor(kind="text_span", start=start, end=end),
                excerpt_redacted=redacted,
                explanation_redacted=explanation,
                policy_rule_id="hardcoded-secret" if "key" in category or "token" in category else None,
            )
        )

    for category, severity, pattern in SECRET_PATTERNS:
        for m in pattern.finditer(text):
            if m.lastindex and m.lastindex >= 1:
                g = m.group(1)
                if g and pattern.groups >= 2:
                    secret_group = m.group(2) if m.lastindex >= 2 else g
                    if secret_group:
                        start, end = m.span(2) if m.lastindex >= 2 else m.span(1)
                    else:
                        start, end = m.span()
                else:
                    start, end = m.span()
            else:
                start, end = m.span()
            add(
                category,
                severity,
                start,
                end,
                category,
                f"Pattern matched for {category.replace('_', ' ')}.",
            )

    for start, end, _ in _high_entropy_assignments(text):
        add(
            "high_entropy_assignment",
            "medium",
            start,
            end,
            "entropy",
            "High-entropy value resembles a secret assignment.",
        )

    for m in EMAIL_RE.finditer(text):
        add(
            "email",
            "medium",
            m.start(),
            m.end(),
            "email",
            "Email address detected; may be PII depending on context.",
        )

    return findings