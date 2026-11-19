# AIRLOCK hackathon quick start

## One-time setup

```bash
cd /Users/malvikasawant/Documents/multimodal-llm
make setup-api
make setup-frontends
cp .env.example .env   # if needed
```

Optional: `brew install tesseract` for screenshot OCR.

Optional: `ollama pull qwen2.5-coder:3b` for inspector code/LLM tasks.

## Run (3 terminals)

```bash
# Terminal 1
cd services/api && source .venv/bin/activate && uvicorn app.main:app --host 127.0.0.1 --port 8765 --reload

# Terminal 2
cd apps/dashboard && npm run dev

# Terminal 3
cd apps/demo-chat && npm run dev
```

Chrome extension (optional): `cd apps/extension && npm run build`, load unpacked from `apps/extension/dist`.

## Demo flows

1. Open http://127.0.0.1:5174 and paste contents of `fixtures/synthetic_only/sample_secret.txt`. Click Send. AIRLOCK pauses and shows review UI. Receiver log should stay empty until you cancel or send sanitized text.
2. Open http://127.0.0.1:5173 for the dashboard (includes Demo Chat at /chat), incidents, and inspector Q&A.
3. Health: http://127.0.0.1:8765/api/v1/health

## Tests

```bash
cd services/api && source .venv/bin/activate && pytest -q
```