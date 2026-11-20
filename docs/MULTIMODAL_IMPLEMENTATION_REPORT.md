# AIRLOCK multimodal implementation report

## 1. Features implemented

- Central Ollama config: `OLLAMA_VLM_MODEL=qwen3.5:9b`, `OLLAMA_TEXT_MODEL=qwen3.5:9b`, `OLLAMA_CODER_MODEL=qwen2.5-coder:3b`
- VLM routing via `resolve_vlm_model()` (prefers configured Qwen 3.5 over llava)
- Image Q&A: real base64 bytes to Ollama `/api/chat`; OCR supplement + uncertainty note
- PDF: PyMuPDF text + OCR for low-text (scanned) pages
- Audio: faster-whisper ASR + librosa acoustic sound events on waveforms
- Video: ffmpeg frames, per-frame OCR + synchronous Qwen VLM, audio ASR + acoustics
- Secrets: DB URLs, JWT, phones, passwords, contextual policy (`config/confidentiality_policy.yaml`)
- Code: markdown fence stripping (`extract_python_code`), sandbox run normalizes input
- Fixtures: `scripts/generate_multimodal_fixtures.py` (PNG, PDF, MP4, WAV, code samples)

## 2. Key files modified/added

- `services/api/app/settings.py`
- `services/api/app/llm/ollama_client.py`, `multimodal.py`, `ollama_runtime.py`, `whisper_local.py`, `code_extract.py`
- `services/api/app/detectors/pdf_pipeline.py`, `video_pipeline.py`, `ingest.py`, `analyze.py`, `contextual.py`, `secrets.py`
- `services/api/app/audio/acoustic_events.py`
- `services/api/app/routes/inspector.py`, `demo.py`
- `services/api/requirements.txt`, `pytest.ini`
- `config/confidentiality_policy.yaml`
- `scripts/generate_multimodal_fixtures.py`, `scripts/prefetch_whisper.py`
- `Makefile`, `.env.example`
- `apps/dashboard/src/api.ts`, `InspectorPage.tsx` (ingest metadata only)

## 3. Dependencies (API `.venv`)

faster-whisper, soundfile, scipy, librosa, pymupdf, opencv-python-headless, onnxruntime, PyYAML (+ existing fastapi stack).

Torch was pulled optionally for PANNs but **not used** (package broken without wget data).

## 4. Models

| Model | Use | Cache location |
|-------|-----|----------------|
| `qwen3.5:9b` (Ollama) | Vision + text Q&A | Ollama |
| `qwen2.5-coder:3b` | Code generation | Ollama |
| Whisper `base` | ASR | `./data/models/whisper` |

Prefetch: `make setup-api` then `services/api/.venv/bin/python ../../scripts/prefetch_whisper.py`

## 5. Test results (executed)

| Suite | Result |
|-------|--------|
| `pytest -q -m "not integration"` | **15 passed** |
| `pytest tests/test_integration_multimodal.py -m integration` | **1 passed**, **1 skipped** (whisper: missing `demo_speech.wav` or download) |
| Video integration | **PASS** (MP4 frames + `t=` OCR) ~300s with VLM |

## 6. Modality matrix

| Modality | Status | Notes |
|----------|--------|-------|
| Image describe/Q&A | **PASS** | Qwen 3.5 + Tesseract |
| Image security scan | **PASS** | Rules on OCR |
| Audio ASR | **PARTIAL** | faster-whisper wired; needs weight prefetch + speech WAV fixture |
| Sound events | **PARTIAL** | Acoustic librosa analysis (not AudioSet CNN; better than transcript-only) |
| Text/PDF doc | **PASS** | pypdf + PyMuPDF OCR pages |
| Scanned PDF | **PASS** | `scanned_document.pdf` fixture |
| Video MP4 + VLM | **PASS** | Sparse frames, max 6 VLM calls |
| Code gen + sandbox | **PASS** | Fence stripping + template fallback |
| Contextual secrets | **PASS** | Policy YAML + NIGHTJAR patterns |
| Cloud APIs | **PASS** | None for inference |

## 7. Limitations

- Acoustic classifier is signal-processing based, not a full AudioSet-trained tagger (PANNs install failed).
- Code sandbox remains AST-limited subprocess isolation (not a container).
- Video VLM is sparse sampling; not frame-exact DLP.
- `say`-generated speech WAV may fail in CI; ffmpeg sine fallback is not real speech for ASR demos.
- Concurrent Ollama calls serialized (`ollama_max_concurrent_requests=1`).

## 8. Start commands

```bash
make setup-api
make demo-fixtures
services/api/.venv/bin/python scripts/prefetch_whisper.py   # once online
make api
make dashboard
```

## 9. Offline demo

1. Run prefetch_whisper while online.
2. `ollama pull` models already present.
3. Disable network; start API + dashboard.
4. Inspector kit + Demo Chat multimodal scans using local caches only.