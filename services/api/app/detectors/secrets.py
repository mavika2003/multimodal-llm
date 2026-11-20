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
        "aws_key",
        "high",
        re.compile(r"(?i)AWS_(?:ACCESS_KEY_ID|SECRET_ACCESS_KEY)\s*=\s*\S+"),
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
    (
        "database_url",
        "high",
        re.compile(
            r"(?i)(postgresql|postgres|mysql|mongodb)(\+[^:]+)?://[^\s'\"]+",
        ),
    ),
    (
        "jwt_token",
        "high",
        re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    ),
    (
        "sk_live_key",
        "critical",
        re.compile(r"sk_live_[A-Za-z0-9]{12,}"),
    ),
]

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"\+\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}")
PASSWORD_ASSIGN_RE = re.compile(
    r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"]?([^\s'\"#]{6,})",
)
SPOKEN_PASSWORD_RE = re.compile(
    r"(?i)(wifi\s+)?(password|passcode|passphrase|bypass\s+word).{0,36}"
    r"(?:is|was|it's|are|'s)\s+([^\n.!?]{4,48})",
)
SPOKEN_EMAIL_RE = re.compile(
    r"(?i)\b([a-z0-9._%+-]{1,64})\s+at\s+([a-z0-9.-]+\.[a-z]{2,})\b",
)
SPOKEN_IT_IS_RE = re.compile(r"(?i)\bit\s+is\s+([^\n.!?]{4,48})")
CREDENTIAL_DIALOGUE_CTX = re.compile(
    r"(?i)(bypass\s+word|wifi\s+password|guest\s+wifi|what\s+is\s+the\s+.*password)",
)


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

    for m in PHONE_RE.finditer(text):
        add(
            "phone",
            "medium",
            m.start(),
            m.end(),
            "phone",
            "Phone number detected; may be PII.",
        )

    for m in PASSWORD_ASSIGN_RE.finditer(text):
        add(
            "hardcoded_password",
            "high",
            m.start(2),
            m.end(2),
            "password",
            "Hardcoded password assignment detected.",
        )

    for m in SPOKEN_PASSWORD_RE.finditer(text):
        start, end = m.span(3)
        add(
            "spoken_password",
            "high",
            start,
            end,
            "password",
            "Spoken password or passphrase detected in transcript.",
        )

    for m in SPOKEN_EMAIL_RE.finditer(text):
        add(
            "email",
            "medium",
            m.start(),
            m.end(),
            "email",
            "Spoken email address detected (at-sign may be missing in ASR).",
        )

    if CREDENTIAL_DIALOGUE_CTX.search(text):
        for m in SPOKEN_IT_IS_RE.finditer(text):
            start, end = m.span(1)
            add(
                "spoken_password",
                "high",
                start,
                end,
                "password",
                "Spoken password shared in conversational audio.",
            )

    return findings