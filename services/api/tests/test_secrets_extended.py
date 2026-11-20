from app.detectors.analyze import analyze_extracted_text
from app.detectors.secrets import scan_text_secrets


def test_database_url():
    t = 'DATABASE_URL="postgresql://u:SecretPass@db.internal:5432/app"'
    cats = {f.category for f in scan_text_secrets(t)}
    assert "database_url" in cats


def test_confidential_nightjar():
    t = "CONFIDENTIAL_CONTEXT Project NIGHTJAR private acquisition target $48.5M"
    cats = {f.category for f in analyze_extracted_text(t)}
    assert "confidential_project" in cats or "confidential_context" in cats or "confidential_business" in cats