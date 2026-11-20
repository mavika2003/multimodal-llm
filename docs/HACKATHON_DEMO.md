# IEEE Multimodal LLM Hackathon — AIRLOCK demo script

## Does this submission fit the brief?

**Yes**, if you demo all **five inputs in one interface** (Inspector) plus **real-world usability** (dashboard + Chrome extension).

| IEEE requirement (30% checklist) | AIRLOCK surface |
|--------------------------------|-----------------|
| **Image** — describe & Q&A | Inspector → `image`: OCR + optional Ollama VLM |
| **Audio** — transcribe, Q&A, identify sounds | Inspector → `audio`: transcript + sound-event rules |
| **Text** — document Q&A + abstain | Inspector → `document` / `text` |
| **Code** — working code from prompt | Inspector → **Code** tab + sandbox run |
| **Video** — short clip Q&A | Inspector → `video`: multi-frame OCR + Q&A |

**Constraints:** Open-weight models via **Ollama** (coder + optional VLM); **Whisper/ffmpeg** optional for raw audio/video. Rules engine is not the “brain” for Q&A — Ollama answers grounded questions.

**Domain / user (15% impact):** Developers & students sharing code/screenshots with **cloud AI** — AIRLOCK blocks leaks locally before send.

**Deliverables:** Public GitHub repo + live demo on your laptop.

---

## 15-minute live demo flow

**Prep:** `make setup-all` · `make demo-fixtures` · `ollama pull qwen2.5-coder:3b` · optional `ollama pull llava` or `qwen2.5vl`

| # | Time | What judges see |
|---|------|-----------------|
| 1 | 2 min | **Chrome:** Claude/ChatGPT paste secret → extension pause (`require_review`) |
| 2 | 2 min | **Dashboard /chat:** safe copy + receiver log empty until sanitized |
| 3 | 8 min | **Inspector → IEEE hackathon kit:** run all five buttons (document, image, audio, video, code) |
| 4 | 2 min | **Incidents + Inspector Q:** “What did AIRLOCK stop me sharing today?” |
| 5 | 1 min | **Architecture slide:** Ollama models, Tesseract, SQLite, limits |

### Inspector kit — sample questions (auto-loaded)

1. **document** — “When does Project Phoenix launch?”
2. **document_missing** — abstain: embargo date (not in doc)
3. **image** — “What credential-like text appears?”
4. **audio** — “Was keyboard typing present?”
5. **video** — “When is a client token visible?”
6. **code** — generate + sandbox run

---

## Models to mention on slides

| Modality | Primary local model | Fallback |
|----------|---------------------|----------|
| Text/doc/video Q&A | `qwen2.5-coder:3b` | Keyword span retrieval |
| Image Q&A | `llava` / `qwen2.5vl` (if pulled) | Tesseract OCR text |
| Code | `qwen2.5-coder:3b` | Template script |
| Audio ASR | Whisper CLI (optional) | Ship `.txt` transcript fixture |
| Video | ffmpeg frame OCR | Transcript fixture |

List your **Mac model / RAM** on the slide (hackathon constraint).

---

## Honest limits (judges appreciate this — 20% architecture)

- Not full Gemma 4 / Qwen3-VL at hackathon scale on every path
- Raw `.mp4` / `.wav` need ffmpeg; practice pack clips work with ingest + fixtures
- Extension is best-effort DOM hooks, not enterprise DLP
- Desktop agent optional; **not required** for multimodal score

---

## Commands

```bash
make api
make dashboard
make demo-fixtures
make test
```

Open http://127.0.0.1:5173/inspector