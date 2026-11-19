from app.models import Decision, Finding


def decide_from_findings(findings: list[Finding], scan_failed: bool = False) -> Decision:
    if scan_failed:
        return Decision.unknown
    if not findings:
        return Decision.allow
    severities = {f.severity for f in findings}
    categories = {f.category for f in findings}

    if "critical" in severities or categories.intersection(
        {"private_key_block", "aws_key", "github_token"}
    ):
        return Decision.block

    if findings:
        if any(f.category == "ocr_unavailable" for f in findings):
            return Decision.require_review
        return Decision.require_review

    return Decision.allow