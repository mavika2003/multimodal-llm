# AIRLOCK hackathon quick start

## One-time setup

```bash
cd multimodal-llm   # repo root — Makefile lives here
make setup-api
make setup-frontends
cp .env.example .env   # optional
```

Use the API virtualenv only: `services/api/.venv` (not a separate `venv/` at repo root).

Optional: `brew install tesseract` for screenshot / image OCR.

Optional: `ollama pull qwen2.5-coder:3b` for inspector code tasks and grounded Q&A.

Optional: `ffmpeg` and `whisper` CLI for audio/video ingest demos; otherwise upload `.txt` transcripts.

## Run (2 terminals)

```bash
# From repo root (/Users/.../multimodal-llm), not services/api:
# Terminal 1 — API
make api

# Terminal 2 — dashboard + demo chat at /chat
make dashboard
```

If you are already in `services/api`, you can still run `make api` (forwards to root). Or use the direct command:

```bash
cd services/api && source .venv/bin/activate && uvicorn app.main:app --host 127.0.0.1 --port 8765 --reload
```

Open **http://127.0.0.1:5173** (if Vite picks 5176 because 5173 is busy, free ports with `lsof -i :5173` or use that URL; API allows 5173-5176).

Standalone legacy chat (optional third terminal): `make demo-chat` → http://127.0.0.1:5174

## Tests

Do **not** paste shell comments on the same line as pytest. Use:

```bash
make test
```

or:

```bash
cd services/api && source .venv/bin/activate && pytest -q
```

## Chrome extension (passive + proactive)

```bash
make extension-build
```

Chrome → Extensions → Load unpacked → `apps/extension/dist`.

- **Passive:** popup → scan active field / selection; right-click → **AIRLOCK: scan selection**.
- **Proactive (ChatGPT, etc.):** popup → enable **Proactive guard (all sites)** → Save. See [`docs/PROACTIVE.md`](PROACTIVE.md).

## Desktop agent (clipboard)

```bash
make agent
```

Requires API running. Scans clipboard text locally (macOS `pbpaste`). Optional: `make agent-watch`.

## Demo flows

1. **Chat:** http://127.0.0.1:5173/chat — paste `fixtures/synthetic_only/sample_secret.txt`, Send. Review modal → Create safe copy → receiver log updates. Attach an image with visible secrets for OCR + image redaction.
2. **Dashboard:** Overview / Incidents / Live monitor poll real SQLite data from the API.
3. **Inspector:** Upload PDF/image/audio/video (or paste text), run ingest, ask questions. Use **Code** tab for Ollama codegen + sandbox run.
4. **Health:** http://127.0.0.1:8765/api/v1/health