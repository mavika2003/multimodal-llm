from app.engine.upload_scan import infer_upload_modality, scan_uploaded_file


def test_infer_modality():
    assert infer_upload_modality("secret.png") == "image"
    assert infer_upload_modality("brief.pdf") == "document"
    assert infer_upload_modality("clip.mp4") == "video"
    assert infer_upload_modality("note.py") == "code"


def test_scan_code_bytes_finds_api_key():
    body = b'API_KEY = "sk_test_AIRLOCK_FAKE_abc123"\n'
    resp = scan_uploaded_file(
        "act-test-1",
        body,
        "config.py",
        "test",
        "http://127.0.0.1:5173",
        "code",
    )
    assert resp.modality == "code"
    assert resp.findings
    assert resp.decision.value in ("require_review", "block")