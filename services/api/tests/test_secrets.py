from app.detectors.secrets import scan_text_secrets
from app.engine.policy import decide_from_findings
from app.models import Decision


def test_detects_demo_token():
    text = "CLIENT_TOKEN=demo-not-a-real-secret"
    findings = scan_text_secrets(text)
    assert findings
    assert decide_from_findings(findings) == Decision.require_review


def test_allow_benign_text():
    findings = scan_text_secrets("Hello, this is a normal message.")
    assert decide_from_findings(findings) == Decision.allow