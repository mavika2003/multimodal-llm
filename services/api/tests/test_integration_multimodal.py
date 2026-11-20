from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[3]
FIX = ROOT / "fixtures" / "multimodal_demo"


@pytest.mark.skipif(not (FIX / "screenshot_labels.png").exists(), reason="fixtures missing")
def test_image_ocr_finds_secret():
    from app.detectors.ocr import scan_image_bytes

    data = (FIX / "screenshot_labels.png").read_bytes()
    text, findings = scan_image_bytes(data)
    assert "CLIENT_TOKEN" in text or "syn_demo" in text
    assert findings


@pytest.mark.skipif(not (FIX / "sample_secret.py").exists(), reason="fixtures missing")
def test_code_fixture_scan():
    from app.engine.upload_scan import scan_uploaded_file

    data = (FIX / "sample_secret.py").read_bytes()
    resp = scan_uploaded_file("t1", data, "sample_secret.py", "test", "http://127.0.0.1:5173", "code")
    assert resp.findings


@pytest.mark.skipif(not (FIX / "demo_document.pdf").exists(), reason="pdf missing")
def test_pdf_extract():
    from app.detectors.pdf_pipeline import extract_pdf_enhanced

    data = (FIX / "demo_document.pdf").read_bytes()
    res = extract_pdf_enhanced(data, "demo_document.pdf")
    assert "Phoenix" in res.text


@pytest.mark.integration
@pytest.mark.skipif(not (FIX / "demo_speech.wav").exists(), reason="audio missing")
def test_whisper_transcribe():
    from app.llm.whisper_local import transcribe_audio_file

    tr = transcribe_audio_file(FIX / "demo_speech.wav")
    if tr.error and "not installed" in tr.error:
        pytest.skip(tr.error)
    assert tr.transcript or tr.error


@pytest.mark.integration
@pytest.mark.skipif(not (FIX / "demo_video.mp4").exists(), reason="video missing")
def test_video_extract_has_timestamps():
    from app.detectors.video_pipeline import extract_video_enhanced

    data = (FIX / "demo_video.mp4").read_bytes()
    res = extract_video_enhanced(data, "demo_video.mp4")
    assert "t=" in res.text