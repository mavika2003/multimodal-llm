# AIRLOCK

**A local-first, multimodal privacy firewall and incident investigation command center.**

> **AIRLOCK detects risky sharing actions before information leaves supported applications, helps users sanitize content, and gives them a private, searchable history of what was detected, blocked, reviewed, or potentially exposed.** All model inference and incident storage run on the user's machine.

**Project status:** Implementation blueprint / hackathon MVP. No detection, interception, or security guarantee is implied until the components and acceptance tests below are implemented.  
**Target:** IEEE AI Hackathon 2026 — Multimodal LLM Challenge, November 18–20, 2026.  
**Primary user:** Developers, students, researchers, and knowledge workers who share code, screenshots, documents, recordings, and videos with web-based AI products and collaboration tools.  
**Product principle:** *Protect the outgoing action, not every moment of the user's life.*

---

## Table of contents

1. [The problem and the promise](#1-the-problem-and-the-promise)
2. [What AIRLOCK does—and does not do](#2-what-airlock-doesand-does-not-do)
3. [Demonstration walkthrough](#3-demonstration-walkthrough)
4. [MVP scope and roadmap](#4-mvp-scope-and-roadmap)
5. [System architecture](#5-system-architecture)
6. [Repository structure](#6-repository-structure)
7. [Technology choices and local models](#7-technology-choices-and-local-models)
8. [Browser extension and interception design](#8-browser-extension-and-interception-design)
9. [Event lifecycle and decision engine](#9-event-lifecycle-and-decision-engine)
10. [Multimodal analysis pipelines](#10-multimodal-analysis-pipelines)
11. [Policies, risk scoring, and decisions](#11-policies-risk-scoring-and-decisions)
12. [Sanitization and safe sharing](#12-sanitization-and-safe-sharing)
13. [Incident database and evidence model](#13-incident-database-and-evidence-model)
14. [Local API contracts](#14-local-api-contracts)
15. [Dashboard and UX specification](#15-dashboard-and-ux-specification)
16. [Local incident investigation and code generation](#16-local-incident-investigation-and-code-generation)
17. [Privacy, security, and threat model](#17-privacy-security-and-threat-model)
18. [Development setup](#18-development-setup)
19. [Implementation milestones](#19-implementation-milestones)
20. [Tests, evaluation, and acceptance criteria](#20-tests-evaluation-and-acceptance-criteria)
21. [Hackathon demo script](#21-hackathon-demo-script)
22. [Known limitations and non-goals](#22-known-limitations-and-non-goals)
23. [Future work](#23-future-work)
24. [References](#24-references)

---

## 1. The problem and the promise

Every day, people paste code into AI chats, attach screenshots to support tickets, upload spreadsheets, submit documents, and share recordings. The information they intentionally want to share may contain **other information they did not intend to disclose**:

- a secret embedded in a code block;
- a customer email in the corner of a screenshot;
- an internal project name spoken in an otherwise harmless recording;
- a screen-recording frame that briefly reveals a token;
- a confidential number in a document that looks public;
- a combination of innocuous fragments which, under a user-supplied policy, reveals a restricted project.

Traditional antivirus does not solve this problem. A conventional firewall knows about network destinations and traffic; it usually does not understand the meaning of content visible in pixels, speech, and documents. Traditional data loss prevention (DLP) tools address parts of this space, so AIRLOCK does **not** claim to invent DLP. The focus is an accessible, transparent, local-first implementation combining multimodal pre-sharing checks and personal incident triage.

### The critical product decision

AIRLOCK has **two complementary workflows**:

1. **Automatic protection:** While the user works in a *supported browser workflow*, the extension notices an outgoing action, obtains the relevant content with permission, asks a local analyzer to assess it, and **pauses that particular action where technically supported** until a policy decision is available.
2. **Investigation:** The dashboard records minimal event metadata, displays evidence and reasoning, lets a user triage historical events, and supports natural-language questions grounded in the local incident database.

The user should **not** have to visit AIRLOCK and manually paste every item to be protected. A manual **Privacy Inspector** remains available for detailed analysis and to satisfy the hackathon's five-modality requirements.

### Why AI must be local

Sending material to a cloud classifier to decide whether that material is safe to upload would itself introduce a disclosure path. AIRLOCK keeps its classification pipeline, local model runtime, original media (when the user explicitly permits retention), incident database, and remediation code on-device. Model weights may be downloaded during setup; an actual offline demo must run with the network disabled afterward.

### Outcome to optimize

Do not optimize primarily for the number of alerts. Optimize for **correctly prevented disclosures, low false-positive friction, transparent decisions, and genuinely useful incident resolution**.

---

## 2. What AIRLOCK does—and does not do

### Supported behaviors (MVP target)

| Capability | Behavior | Status target |
|---|---|---|
| Text pre-submit scan | Pause a supported outgoing message and scan pasted/typed text | **P0** |
| Code and secret detection | Flag likely tokens, credentials, hard-coded secrets, and sensitive paths | **P0** |
| Screenshot scan | OCR + local vision understanding; show precise regions where possible | **P0** |
| User intervention | Allow, cancel, review, or replace/redact content before sending | **P0** |
| Incident logging | Persist metadata without storing full secrets by default | **P0** |
| Dashboard | Overview, live feed, incident details, filtering, triage | **P0** |
| Document inspection | Analyze a PDF/TXT/MD file and answer grounded questions | **P1** |
| Audio inspection | Transcribe, answer questions, and identify selected sound events | **P1** |
| Video inspection | Describe clips, locate risky frames, answer timestamped questions | **P1** |
| Working code generation | Locally generate and test a restricted Python redaction/analysis script | **P1** |
| Natural-language history queries | Grounded queries over authorized, read-only local incident data | **P1** |
| Browser integration across arbitrary sites | Site-specific adapters, explicit permissions, testing | **P2** |
| OS-wide universal interception | Requires platform-specific agent and deep integration | **Not MVP** |

**P0 = must work for live demo. P1 = required to fully satisfy hackathon modality checklist. P2 = future integration.**

### Explicit non-claims

- A detection is **not** proof of a data breach.
- A successful client-side pause is **not** evidence that every possible network transmission was blocked.
- AIRLOCK is **not** a universal operating-system firewall, antivirus, packet-inspection appliance, or enterprise DLP replacement.
- A result of `no_findings` is **not** a guarantee that content is safe.
- It does **not** silently capture the microphone, camera, entire desktop, keystrokes, or browser history.
- It does **not** send users' content to an external LLM.

---

## 3. Demonstration walkthrough

Use a **locally hosted, purpose-built mock AI chat page**, not an actual remote AI provider, for the deterministic interception demo. The mock page must log whether its `/submit` endpoint received the payload, so a judge can verify that blocking happened **before transmission**.

**Scenario A: credential in an outgoing screenshot**

1. Open the local demo chat page beside the AIRLOCK dashboard.
2. Attach a synthetic screenshot showing ordinary code with a planted fake API credential in a small corner.
3. Click **Send**; the application does not submit while AIRLOCK checks the attachment.
4. The local pipeline performs OCR, secret detection, and optional VLM contextual validation.
5. AIRLOCK displays **Potential credential found**, the bounding box, and **Cancel / Review / Create safe copy**.
6. Choose **Create safe copy**. AIRLOCK redacts the exact pixel region, then rescans it.
7. The demo page receives only the sanitized file; its server-side request log shows that the original was never sent.
8. Open the AIRLOCK dashboard. A new event appears in the live feed and can be triaged.
9. Ask the incident assistant: **“What kinds of information did AIRLOCK stop me from sharing today?”** It returns event-linked results.

**Scenario B: text/code paste**

- Type or paste a snippet with a synthetic token into the demo page.
- Try to send it. The protected action pauses.
- Replace the detected value with a stable placeholder, allowing the text to retain its structure.
- Verify that the submitted payload contains the placeholder and not the synthetic secret.

**Scenario C: five-modality inspector**

From AIRLOCK's Inspector page, examine one image, one audio clip, one document, one short video, and one natural-language code prompt. The user can ask questions; the model must cite the actual source where supported and abstain when it cannot answer. Generate and execute one safe analysis/redaction script to demonstrate working code.

**Demo reveal:** The system should show both a **prevented outgoing request** and the **visual incident history** it created. Avoid simulated charts presented as real measured results.

---

## 4. MVP scope and roadmap

### Hackathon scope freeze

**Supported destination:** One controlled local mock chat page, plus an optional extension adapter for a single explicitly tested external browser site.  
**Supported OS:** The development laptop's OS only; document its exact version and CPU/GPU/RAM in the slides.  
**Supported scan types:** Text, code, screenshots (P0); document, audio, and short video (P1).  
**Supported response:** Cancel, review, redact, then explicitly resume the original action where the integration supports it.  
**Dashboard:** Events list, analytics, detail/replay view, triage status, filters, and one local Q&A entry point.

Keep two different notions separate:

- **Real-time interception latency** should be bounded. Fast secret detection should run first; expensive scans should be asynchronous **while the outgoing action stays paused** in the controlled workflow.
- **Deep investigation latency** can take longer. The dashboard can display processing state and partial findings; no event is labeled fully scanned prematurely.

### Potential later releases

- v0.2: Adapter for a specific real web application, with integration tests for its actual DOM and upload flow.
- v0.3: Downloadable sanitized versions of PDF/audio/video and automatic rescan.
- v0.4: Cross-event correlation and personalized policies.
- v1.0: Signed installer, strict privilege separation, encrypted evidence store, updater, reproducible benchmarks, external security audit.

---

## 5. System architecture

```text
+--------------------------- USER'S DEVICE ------------------------------+
|                                                                        |
|  +-----------------------+       +-------------------------------+      |
|  | Supported browser     |       | AIRLOCK dashboard             |      |
|  | - Local demo chat     |       | React / TypeScript            |      |
|  | - Extension adapters  |       | - Overview / live activity    |      |
|  | - Paste / submit      |       | - Triage / privacy insights   |      |
|  | - Attachments         |       | - Inspector / local Q&A       |      |
|  +-----------+-----------+       +---------------+---------------+      |
|              |                                   |                      |
|     extension messages                     localhost API               |
|              v                                   v                      |
|  +------------------------------------------------------------------+  |
|  | FastAPI orchestrator (127.0.0.1 only)                            |  |
|  | - typed payload validation / source authorization                |  |
|  | - scan jobs and decision state machine                           |  |
|  | - local-only inference orchestration                              |  |
|  | - event persistence / SSE / triage                                |  |
|  +----------+----------------+------------------+-------------------+  |
|             |                |                  |                      |
|             v                v                  v                      |
|    +----------------+ +---------------+ +-------------------------+  |
|    | Fast detectors | | Local models  | | Safe transformations    |  |
|    | regex/entropy  | | OCR + VLM     | | text substitution       |  |
|    | Presidio       | | Whisper STT   | | image pixel redaction   |  |
|    | secrets rules  | | local LLM     | | FFmpeg / PDF utilities  |  |
|    +----------------+ | coder LLM     | | sandbox code runner     |  |
|                       +---------------+ +-------------------------+  |
|             +----------------+------------------+                      |
|             v                                   v                      |
|     +--------------------+               +------------------------+   |
|     | SQLite incident DB |               | Encrypted / ephemeral  |   |
|     | minimal metadata   |               | evidence files         |   |
|     +--------------------+               +------------------------+   |
|                                                                        |
|  NO CLOUD MODEL CALLS; NO TELEMETRY BY DEFAULT                         |
+------------------------------------------------------------------------+
```

### Request flow

```text
Outgoing user action
  -> supported adapter synchronously pauses that action
  -> extension validates context and sends the specific content to local backend
  -> cheap deterministic detectors run
  -> applicable OCR/STT/VLM pipeline runs if needed
  -> policy engine returns allow | warn | block | require_review | unknown
  -> user makes an explicit choice when review is required
  -> sanitized payload is produced and rescanned when requested
  -> adapter resumes with the selected payload, if still valid
  -> minimal incident metadata is recorded
  -> dashboard updates through local SSE or polling
```

A background extension worker does **not** by itself suspend arbitrary outgoing network requests. Control the actual submission pathway in the mock application; treat any real-site adapter as separately validated and potentially bypassable.

### Core boundaries

1. **Browser content is untrusted.** Never allow a web page to choose backend filesystem paths or privileged commands.
2. **LLM output is untrusted.** Only typed, validated JSON findings may reach the decision engine.
3. **Generated code is untrusted.** Execute in a sandbox without network or access to arbitrary user files.
4. **Evidence is sensitive.** Keep raw media out of event logs and avoid console logging request payloads.
5. **Detection is not transmission evidence.** Keep observed action, network-confirmation status, and investigation outcome as separate fields.

---

## 6. Repository structure

Suggested monorepo:

```text
airlock/
├── README.md
├── .gitignore
├── .env.example
├── Makefile
├── apps/
│   ├── dashboard/                   # Vite + React + TypeScript
│   │   ├── src/
│   │   │   ├── app/
│   │   │   ├── pages/
│   │   │   │   ├── Overview.tsx
│   │   │   │   ├── LiveActivity.tsx
│   │   │   │   ├── Incidents.tsx
│   │   │   │   ├── IncidentDetail.tsx
│   │   │   │   ├── Inspector.tsx
│   │   │   │   ├── Analytics.tsx
│   │   │   │   └── Settings.tsx
│   │   │   ├── components/
│   │   │   ├── api/
│   │   │   └── types/
│   │   └── package.json
│   ├── extension/                   # MV3 Chrome extension
│   │   ├── manifest.json
│   │   ├── src/
│   │   │   ├── background.ts
│   │   │   ├── content.ts
│   │   │   ├── adapters/
│   │   │   │   └── mock-chat.ts
│   │   │   ├── overlay.ts
│   │   │   └── types.ts
│   │   └── package.json
│   └── demo-chat/                   # Controlled local test target
│       ├── src/
│       └── package.json
├── services/
│   └── api/
│       ├── app/
│       │   ├── main.py
│       │   ├── settings.py
│       │   ├── auth.py
│       │   ├── models.py            # Pydantic schemas
│       │   ├── routes/
│       │   │   ├── scans.py
│       │   │   ├── incidents.py
│       │   │   ├── analytics.py
│       │   │   ├── inspector.py
│       │   │   └── health.py
│       │   ├── detectors/
│       │   │   ├── secrets.py
│       │   │   ├── pii.py
│       │   │   ├── ocr.py
│       │   │   ├── vision.py
│       │   │   ├── audio.py
│       │   │   ├── video.py
│       │   │   └── documents.py
│       │   ├── engine/
│       │   │   ├── orchestrator.py
│       │   │   ├── policy.py
│       │   │   ├── confidence.py
│       │   │   └── decisions.py
│       │   ├── redaction/
│       │   │   ├── text.py
│       │   │   ├── image.py
│       │   │   ├── video.py
│       │   │   └── audio.py
│       │   ├── llm/
│       │   │   ├── ollama_client.py
│       │   │   ├── prompts.py
│       │   │   └── validators.py
│       │   ├── db/
│       │   │   ├── schema.sql
│       │   │   ├── repository.py
│       │   │   └── migrations/
│       │   └── jobs/
│       ├── tests/
│       ├── pyproject.toml
│       └── requirements.txt
├── scripts/
│   ├── setup_models.sh
│   ├── run_dev.sh
│   └── run_benchmark.py
├── fixtures/
│   ├── synthetic_only/             # Never commit real secrets
│   └── expected_results.json
├── docs/
│   ├── architecture.md
│   ├── threat-model.md
│   ├── api.md
│   ├── metrics.md
│   └── demo.md
└── tests/
    ├── extension-e2e/
    ├── fixtures/
    └── acceptance/
```

Do not store downloaded model weights or actual private evidence in Git. Add `data/`, `models/`, `.env`, `*.db`, `*.sqlite`, and `evidence/` to `.gitignore`.

---

## 7. Technology choices and local models

| Layer | Recommendation | Notes |
|---|---|---|
| Dashboard | React + TypeScript + Vite + Tailwind | Fast local UI; optionally shadcn/ui and Recharts |
| Extension | Chrome Manifest V3 + TypeScript | Site adapters; minimal permissions |
| Backend | FastAPI + Pydantic | Typed APIs and job states |
| Local runtime | Ollama | All LLM/VLM requests go to loopback |
| General image/video reasoning | Quantized Qwen3-VL family, if supported by device/runtime | Test specific checkpoint and image behavior before freezing model choice |
| Local code model | Qwen2.5-Coder 3B/7B | Load on demand; code execution separate from inference |
| Transcription | `whisper.cpp` or `faster-whisper` | Local transcription; not a general environmental sound classifier |
| Sound events | Local small audio classifier or supported labels pipeline | Essential for the explicit “identify sounds” requirement |
| OCR | Tesseract or PaddleOCR | Coordinates for precise redaction; local-only |
| Text PII | Presidio + custom recognizers | Entity detection; requires contextual tuning |
| Secret scanning | Regex + entropy + optional Gitleaks-like rules | Deterministic baseline |
| Video | FFmpeg + timestamped frame extraction | Analyze audio separately; sampling can miss brief exposures |
| Document retrieval | PyMuPDF / text extraction + local search | Citations tied to page and snippet; avoid unsupported answers |
| Persistence | SQLite + SQLAlchemy/SQLModel | Offline event store |
| Streaming updates | Server-Sent Events (SSE) or polling | Read-only event feed |
| Testing | Pytest, Playwright, Vitest | Browser and backend behavior |

### Hardware profile / realistic defaults

- **16GB Apple Silicon laptop:** Prefer one small quantized multimodal model resident at a time, smaller coder model, and sequential processing. Measure real memory usage and throughput.
- **32GB+ Apple Silicon:** More room for model context and occasional concurrent processing.
- **NVIDIA GPU machine:** Configure Ollama/Whisper based on available VRAM and driver stack.
- **CPU only:** First demonstrate deterministic text, OCR, and short media; model inference may be noticeably slower.

Never promise precise latency without measurements on the actual hackathon machine. Ship model versions and quantizations in `docs/architecture.md`, along with checksums, licenses, memory use, and benchmark results. Check that *each selected model's weight license* fits the contest's open-weight requirement.

### Model orchestration policy

1. Run fast rules on text or OCR output.
2. Use semantic local LLM/VLM review for uncertain or context-dependent cases.
3. Validate every model response against a schema and actual source coordinates/spans.
4. If inference fails or times out, mark `unknown` or `requires_review`; do not silently relabel unscanned content as safe.
5. Keep local decision logic deterministic and explainable. **A language model never gets final authority to transmit content.**

Example structured finding:

```json
{
  "category": "possible_api_credential",
  "modality": "image",
  "severity": "high",
  "source_anchor": {
    "kind": "image_box",
    "page_or_frame": 0,
    "bbox_xyxy": [218, 81, 412, 101]
  },
  "evidence_excerpt_redacted": "API_KEY = [REDACTED]",
  "explanation": "Credential-like text is shown near a configuration assignment.",
  "detector": "ocr_plus_rules",
  "confidence_label": "high"
}
```

`bbox_xyxy` must come from an actual OCR/image-region system, not invented by an LLM. Validate it against image dimensions. `confidence_label` should be a qualitative, calibrated-by-testing label, not a fabricated probability.

---

## 8. Browser extension and interception design

### Why this is not a network firewall

Chrome MV3 content scripts can observe and modify DOM interactions on permitted pages. The `declarativeNetRequest` API is rule-based and is **not** a general way to introspect arbitrary request bodies and conditionally suspend them for a local LLM scan. Many sites send content through custom JavaScript, background uploads, service workers, shadow DOM, or streaming connections. `webRequestBlocking` is not generally available to ordinary MV3 extensions.

Therefore the architecture relies on a **supported, site-specific pre-submit pathway** rather than promising universal network-level interception.

### Recommended implementation order

**Phase 1 — Controlled mock chat:** Integrate AIRLOCK directly with a first-party local chat page, giving deterministic access to outgoing text and attachments and complete submit control. Verify that blocked content never reaches its receiving endpoint.

**Phase 2 — Extension adapter:** Add a content script for that same mock page and move the interception UX into the extension. Demonstrate user experience without manually visiting the dashboard.

**Phase 3 — Real website adapter (optional):** Scope to one tested site and measure bypass cases. Be clear that coverage is limited and can break as the site's UI changes.

### Example minimal MV3 manifest (illustrative)

```json
{
  "manifest_version": 3,
  "name": "AIRLOCK Privacy Guardian",
  "version": "0.1.0",
  "description": "Local, consent-based pre-sharing privacy checks.",
  "permissions": ["storage"],
  "host_permissions": ["http://127.0.0.1:8765/*"],
  "background": {
    "service_worker": "background.js",
    "type": "module"
  },
  "content_scripts": [
    {
      "matches": ["http://127.0.0.1:5174/*"],
      "js": ["content.js"],
      "run_at": "document_start"
    }
  ],
  "action": {"default_title": "AIRLOCK"}
}
```

Use actual built JS filenames after bundling. For production, request host access as narrowly and transparently as possible. Do not add `<all_urls>` merely to make a hackathon prototype convenient.

### Critical interception sequence

**Never rely on a `paste` event alone.** Users can type, drag, autofill, attach files, or send via keyboard shortcuts. Monitor the submit action for your supported integration and analyze the **final payload**. Paste scanning can be a fast, proactive hint, but the send boundary is authoritative.

Pseudo-code for a *controlled* submit adapter:

```ts
async function guardedSend(payload: OutgoingPayload): Promise<void> {
  // This function replaces the supported demo app's normal send path.
  // It must run BEFORE any fetch(), websocket send(), or upload begins.
  const pending = createPendingAction(payload);
  showPendingUI(pending.id);

  let decision: ScanDecision;
  try {
    decision = await airlock.scanBeforeSend(pending.payload);
  } catch {
    decision = { action: "require_review", reason: "scan_unavailable" };
  }

  if (decision.action === "allow") {
    await sendThroughOriginalApp(pending.payload);
  } else if (decision.action === "block") {
    showBlockedUI(decision);
  } else {
    const choice = await showReviewDialog(decision);
    if (choice.kind === "send_sanitized") {
      const sanitized = await airlock.redact(pending.payload, choice.findingIds);
      const verified = await airlock.scanBeforeSend(sanitized);
      if (verified.action === "allow" || verified.action === "warn") {
        await sendThroughOriginalApp(sanitized);
      } else {
        showBlockedUI(verified);
      }
    } else if (choice.kind === "cancel") {
      cancelPendingAction(pending.id);
    } else {
      // No silent resume. Require deliberate review/override policy.
      showReviewDialog(decision);
    }
  }
}
```

**Production implementation details:**

- Capture immutable payload metadata at the moment of attempted submission; check again if page content changes during scanning.
- Avoid recursive scanning when a programmatic submit re-enters the event handler; use one-time action IDs.
- Handle navigation, tab closure, changed attachments, cancellations, retries, and multiple simultaneous actions.
- The browser may not allow an extension to reconstruct arbitrary `File` objects or replace uploads in every site; validate per adapter.
- A custom SPA may bypass a normal `<form>` submit event. Prefer first-party guarded integration for the reliable MVP.
- Do not proxy secrets through remote telemetry, analytics, or error monitoring.

### Extension-to-backend communication

The service worker performs a local, authenticated fetch to `http://127.0.0.1:8765` with only the specific data being scanned. Content scripts relay messages through `chrome.runtime.sendMessage` and do not hold long-lived privileged secrets. Validate `sender.tab`, URL/origin, message type, size, and allowed adapter before forwarding; do not trust page-provided origin labels.

The API must bind to **127.0.0.1 only**, require a per-install secret or equivalent local authorization, enforce an origin allowlist for browser requests, reject arbitrary web pages, and avoid permissive CORS. A remote website may attempt localhost requests; binding to loopback **alone is not authentication**. Consider Chrome Native Messaging in a later version, with its own trusted-host validation and transport threat model.

---

## 9. Event lifecycle and decision engine

### Event states

```text
observed -> paused -> scanning -> decision_ready
                                  |           |
                                  v           v
                               allowed    review_required
                                              |
                          +-------------------+-------------------+
                          v                   v                   v
                       canceled           sanitized           overridden
                                              |                   |
                                              v                   v
                                           rescanned        user_confirmed
                                              |                   |
                                              +---------+---------+
                                                        v
                                                 action_completed
```

Separately store **network transmission knowledge**:

- `not_sent_confirmed`: The controlled application verified that no send function was called.
- `sent_confirmed`: An instrumented first-party endpoint recorded receipt (avoid recording raw secrets).
- `unknown`: The extension could not verify the network result.

Use different **risk outcome** labels:

- `prevented`: A known outgoing action was stopped before the controlled send boundary.
- `sanitized_and_sent`: A verified sanitized artifact was sent.
- `potential_exposure`: Content may have reached a destination; actual transmission unconfirmed.
- `confirmed_exposure`: A trusted endpoint log or other reliable evidence confirms receipt of the relevant content.
- `false_positive`: User review or a verified test shows the detection was inaccurate.
- `dismissed`: User closed the alert; do not equate this with a false positive.

### Decision types

`allow | warn | require_review | block | unknown`

- `allow`: Scan completed, and policy finds no reason to intervene (not a guarantee of safety).
- `warn`: A finding exists but the configured policy permits continuation with a visible warning.
- `require_review`: Human decision required before the guarded application sends anything.
- `block`: Known high-risk content or mandatory policy prohibits the action.
- `unknown`: Scan incomplete, unsupported, timed out, or failed; controlled flow defaults to pause and review.

### Idempotency

Generate a random `action_id` at the send boundary; reuse it for scans, redaction, resume, and event logging. Keep a bounded set of completed action IDs so duplicate browser events cannot cause repeated transmissions. Reject stale authorization decisions if payload hash changes.

---

## 10. Multimodal analysis pipelines

AIRLOCK must meet the hackathon checklist **as explicitly stated**, not merely accept five extensions. The Inspector page provides accessible Q&A for each input, while the firewall uses the same underlying analysis to detect disclosures.

### 10.1 Image

**Required:** Describe a photo and answer questions about it.

Pipeline:

1. Decode file, enforce size/dimension limits, strip unsafe metadata for derived copies.
2. Run OCR with text **and bounding boxes**.
3. Run secret/PII scanners over the OCR output.
4. Ask local VLM to describe relevant visual context, based on actual pixels.
5. Merge overlapping findings; link to source bounding boxes and OCR text.
6. Display the original image with non-destructive annotations.
7. For redaction, apply solid pixel masks to a **new file**, including padding around sensitive boxes.
8. Rescan the redacted image; optionally manually inspect before sharing.

Example Q&A: “What application is this screenshot showing?” “Where is the credential-like field?” “What is the visible error message?” The system must decline questions not supported by the image.

**Risk:** Screenshots contain small text; OCR may miss it. Include screenshot scaling and rotated/low-resolution test cases. Never claim all visual secrets were detected.

### 10.2 Audio

**Required:** Transcribe speech, answer questions, and identify sounds.

Pipeline:

1. Convert to a safe standard audio format locally using FFmpeg.
2. Transcribe with Whisper and align approximate timestamps.
3. Run a **separate local sound-event classifier** for a limited set such as keyboard typing, speech, alarms, and notification chimes; log supported labels and evaluation quality.
4. Run entity/secret detection over the transcript with evidence timestamps.
5. Answer source-grounded questions about the recording, including uncertainty.
6. For remediation, mute or beep reviewed timestamp ranges in a derived copy; avoid claiming complete removal of speech without manual review.

Question examples: “What project name did the speaker mention?” “Was a notification sound present?” “What was decided at the end?”

**Risk:** Speech transcription can hallucinate in silence, get names wrong, and miss overlapping speakers. Do not treat transcribed PII as confirmed without review.

### 10.3 Text and documents

**Required:** Answer questions about a document and say when the answer is absent.

Pipeline:

1. Accept PDF, TXT, MD and optionally DOCX; parse locally with file-type-specific tools.
2. Preserve source page/section/chunk IDs.
3. Add OCR for scanned PDFs where possible.
4. Run deterministic rules plus Presidio-style entity recognition.
5. Retrieve relevant spans locally (SQLite FTS5 for MVP; vector embeddings optional).
6. Instruct the local model to answer **only** from retrieved passages; return explicit citations.
7. If evidence does not support the answer, return `not_found_in_document`, not a plausible guess.
8. Apply per-document policy categories (internal, confidential, public, user-defined).

Test at least one question whose answer is intentionally missing.

### 10.4 Code

**Required:** Write working code from a prompt.

Two distinct workflows:

- **Detect risky code:** Identify synthetic credentials, tokens, private endpoints, comments containing sensitive information, and suspicious configurations.
- **Generate working code:** Ask the local coder model to produce a narrow Python script such as “Count incident categories from this JSON export” or “Replace these spans in a text file,” then validate and execute it on **synthetic fixtures only**.

Never run generated code directly on the user's actual filesystem or incident database. Prefer a prebuilt, audited redaction library for all real remediation. The generated script is for hackathon evaluation and transparent analytics, not a privileged production execution path.

For execution, use an isolated, no-network worker with restricted filesystem, fixed input files, low privileges, CPU/RAM/time limits, and a subprocess API allowlist. A container without networking may help but does not by itself guarantee security; on platforms without reliable sandboxing, run code generation tests only against a trusted preapproved command set or do not execute user-derived code.

### 10.5 Video

**Required:** Describe a short clip and answer questions about it.

Pipeline:

1. Probe duration, codecs, resolution, and audio tracks.
2. Extract timestamped frames (e.g., every 0.5–2 seconds) plus scene-change frames.
3. For screen recordings, use change detection and OCR; actively consider single-frame exposures that sparse sampling might miss.
4. Transcribe the video audio separately.
5. Aggregate visual findings with time spans and transcript findings.
6. Answer questions with timestamps and visual/audio evidence.
7. For reviewed exposures, apply timed blur rectangles or full-frame masking to a **derived** video, optionally mute selected audio ranges, and rescan relevant intervals.

**Risk:** Sparse frames can miss brief secrets; a 30-second video does not equal a reliable full-frame scan. Offer a “fast scan” vs “thorough scan” choice and report the sampling coverage.

### 10.6 Cross-modal correlation

Correlate findings when the local policy needs multiple facts: for example, a video frame exposes a project codename while the audio mentions an embargo date. The system can flag a **possible combined disclosure** and link both observations. It must **not** infer hidden private facts without evidence or automatically declare a breach.

A structured finding must always contain:

```text
finding_id
category / severity
source modality
source anchor: text span, page, image box, audio interval, or video interval
redacted excerpt or hash
confidence label + detector provenance
policy rationale
review status
```

---

## 11. Policies, risk scoring, and decisions

### Policy types

- `secret`: API keys, access tokens, password strings, private keys, credential patterns.
- `personal`: names, emails, phone numbers, addresses, account identifiers, user-configured identifiers.
- `confidential_business`: project codenames, unreleased dates, internal customer names, proprietary paths, or contract terms **only when supplied in a local user policy**.
- `regulated`: user-configured healthcare/payment identifiers; do not assert regulatory compliance from classifier output.
- `custom`: user-defined keywords, regexes, destinations, and context rules.

### Example policy configuration

```yaml
version: 1
protected_destinations:
  - origin: "http://127.0.0.1:5174"
    mode: require_review
rules:
  - id: hardcoded-secret
    categories: [api_key, private_key, credential]
    severity: critical
    action: block
  - id: customer-pii
    categories: [email, phone, customer_id]
    severity: medium
    action: require_review
  - id: private-project
    categories: [project_codename]
    severity: high
    action: require_review
unknown_scan: require_review
retention_days: 7
retain_raw_media_by_default: false
```

These are **proposed project defaults**, not standards-derived severity classifications. A user must be able to inspect and edit policy logic.

### Decision policy

1. Deterministic exact-match secrets can trigger an immediate block under policy.
2. Context-sensitive PII is usually a review recommendation unless a user policy mandates blocking.
3. Combine detector outputs by evidence quality and policy, **not by averaging uncalibrated LLM probabilities**.
4. Prevent duplicates from different detectors referring to the same span.
5. An unresolved scan leads to review in a guarded workflow; never treat timeout as clean.
6. A conscious user override is logged as an override, not as proof of safety. Optional admin-locked policies can disallow override in future enterprise deployments.

### Severity versus status

Severity expresses potential impact; status expresses what actually happened. A high-severity potential secret can be **prevented**, while a low-severity information disclosure may be **confirmed sent**. Do not merge these fields into a single red/yellow/green label.

---

## 12. Sanitization and safe sharing

### Text and code

Use exact character offsets after detection. Replace secrets with stable placeholders like `[REDACTED_API_KEY_1]` while preserving line breaks, formatting, and surrounding context. Normalize line endings carefully; consider Unicode and overlapping spans. Show a diff before approval.

### Images

Use OCR bounding boxes or user-selected regions. Solid-fill the underlying pixels; do not simply draw a translucent overlay or rely on CSS blur. Regenerate a clean image without original metadata. Offer a preview and rescan the output.

### PDFs

PDF annotation overlays do **not** reliably remove underlying text. For the hackathon, either use a library supporting real redaction/removal of content and inspect the resulting extraction, or export a flattened rasterized version with explicit quality tradeoffs. Never claim a PDF is sanitized merely because black boxes appear on top.

### Audio

Create a new file with approved time ranges muted or replaced. Re-transcribe the result when possible. Keep in mind that incomplete timestamp alignment can leave adjacent private speech audible.

### Video

Create a new file with rendered pixel transformations and audio changes; do not rely on player overlays. Run a second extraction and review the affected intervals. Control file size and transcode time.

### Non-destructive workflow

Original data remains unchanged. Before any export, show **original preview → findings → safe-copy preview → rescan result**. Do not log unredacted content in the dashboard by default.

---

## 13. Incident database and evidence model

Use a local SQLite database (WAL mode optional), backed up only by explicit user choice. Store minimal findings and event provenance. Evidence assets live separately and should be encrypted at rest for any production-like release.

### Suggested SQL schema

```sql
CREATE TABLE incidents (
  id TEXT PRIMARY KEY,
  action_id TEXT NOT NULL UNIQUE,
  observed_at TEXT NOT NULL,
  source_type TEXT NOT NULL,
  source_app TEXT,
  destination_origin TEXT,
  modality TEXT NOT NULL,
  severity TEXT NOT NULL CHECK(severity IN ('low','medium','high','critical','unknown')),
  decision TEXT NOT NULL,
  workflow_state TEXT NOT NULL,
  outcome TEXT NOT NULL,
  transmission_status TEXT NOT NULL DEFAULT 'unknown',
  review_status TEXT NOT NULL DEFAULT 'pending',
  title TEXT NOT NULL,
  summary_redacted TEXT,
  payload_sha256 TEXT,
  scan_duration_ms INTEGER,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE findings (
  id TEXT PRIMARY KEY,
  incident_id TEXT NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  category TEXT NOT NULL,
  severity TEXT NOT NULL,
  detector TEXT NOT NULL,
  confidence_label TEXT,
  anchor_json TEXT NOT NULL,
  excerpt_redacted TEXT,
  policy_rule_id TEXT,
  explanation_redacted TEXT,
  is_confirmed INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE event_steps (
  id TEXT PRIMARY KEY,
  incident_id TEXT NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  occurred_at TEXT NOT NULL,
  step TEXT NOT NULL,
  details_json TEXT
);

CREATE TABLE evidence (
  id TEXT PRIMARY KEY,
  incident_id TEXT NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  media_type TEXT NOT NULL,
  encrypted_local_path TEXT,
  preview_local_path TEXT,
  sha256 TEXT,
  created_at TEXT NOT NULL,
  expires_at TEXT,
  consent_basis TEXT NOT NULL
);

CREATE TABLE triage_notes (
  id TEXT PRIMARY KEY,
  incident_id TEXT NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL,
  resolution TEXT,
  note_redacted TEXT
);

CREATE INDEX idx_incidents_observed_at ON incidents(observed_at);
CREATE INDEX idx_incidents_status ON incidents(review_status, severity);
CREATE INDEX idx_findings_incident ON findings(incident_id);
```

### Privacy-conscious persistence defaults

- Save category, modality, timestamp, action, and redacted contextual evidence.
- Avoid storing full input text, pasted code, image originals, full audio, or video unless the user explicitly opts in.
- Consider HMAC fingerprints instead of plain hashes for low-entropy secrets if correlation is needed; a simple hash is not anonymization.
- Provide retention controls (e.g., 7 days for demo), manual deletion, and one-click delete-all local evidence.
- Store timestamps with timezone/UTC; show the user's local time in the UI.
- Secure local paths against traversal and symlink attacks.
- Maintain a separate immutable event step history if auditable lifecycle reconstruction is required.

### Example redacted event record

```json
{
  "id": "AL-0042",
  "action_id": "demo-action-42",
  "observed_at": "2026-11-18T15:42:13Z",
  "source_type": "browser_extension",
  "source_app": "local-demo-chat",
  "destination_origin": "http://127.0.0.1:5174",
  "modality": "image",
  "severity": "high",
  "decision": "require_review",
  "workflow_state": "review_required",
  "outcome": "pending_review",
  "transmission_status": "not_sent_confirmed",
  "review_status": "pending",
  "title": "Possible API credential in screenshot",
  "summary_redacted": "Credential-like text detected in a code region"
}
```

Demo events must be visibly labeled **synthetic** in the UI.

---

## 14. Local API contracts

Base URL for development: `http://127.0.0.1:8765/api/v1`. Require local authorization for all protected endpoints, enforce payload size and MIME restrictions, and return error types with no raw-content leakage.

### Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Health, loaded models, offline status |
| `POST` | `/scans/text` | Synchronous small text/code scan |
| `POST` | `/scans/media` | Multipart upload and asynchronous media scan job |
| `GET` | `/scans/{job_id}` | Job state, findings, error state |
| `POST` | `/actions/{action_id}/decision` | Record review / cancel / override choice |
| `POST` | `/redactions` | Create safe copy for approved findings |
| `GET` | `/incidents` | Paginated list with filters |
| `GET` | `/incidents/{id}` | Redacted detail and timeline |
| `PATCH` | `/incidents/{id}/triage` | Change review status, notes |
| `GET` | `/analytics/summary` | Totals and trends |
| `GET` | `/events/stream` | SSE feed (or polling fallback) |
| `POST` | `/inspector/ask` | Grounded Q&A over uploaded media or evidence |
| `POST` | `/inspector/code-task` | Restricted code-generation demo task |
| `POST` | `/inspector/code-task/{id}/run` | Sandboxed fixture-only execution |
| `DELETE` | `/evidence/{id}` | Delete a retained evidence object |

### Example request: text scan

```http
POST /api/v1/scans/text
Content-Type: application/json
Authorization: Bearer <LOCAL_INSTALL_TOKEN>
```

```json
{
  "action_id": "1e620bee-f13e-4d2d-8ad6-718286078b62",
  "source": "local-demo-chat",
  "destination_origin": "http://127.0.0.1:5174",
  "modality": "text",
  "content": "CLIENT_TOKEN=demo-not-a-real-secret",
  "payload_sha256": "<sha256-of-original-content>"
}
```

### Example response

```json
{
  "scan_id": "scan-demo-0001",
  "action_id": "1e620bee-f13e-4d2d-8ad6-718286078b62",
  "state": "decision_ready",
  "decision": "require_review",
  "findings": [
    {
      "id": "finding-demo-0001",
      "category": "credential_like_assignment",
      "severity": "medium",
      "detector": "deterministic_rules",
      "anchor": {"kind": "text_span", "start": 13, "end": 35},
      "excerpt_redacted": "CLIENT_TOKEN=[REDACTED]",
      "explanation_redacted": "A token-like value is assigned to a variable; validity not verified."
    }
  ],
  "transmission_status": "not_sent_confirmed"
}
```

The spans and detector outcomes in an actual response must be computed by the implementation. This example is conceptual, not a promise that the illustrative string is truly secret.

### Error handling

Use typed errors: `SCAN_UNAVAILABLE`, `TIMEOUT`, `UNSUPPORTED_MEDIA`, `FILE_TOO_LARGE`, `MODEL_NOT_INSTALLED`, `UNAUTHORIZED_ORIGIN`, `INVALID_PAYLOAD`, `SANITIZATION_FAILED`. In the guarded demo app, all of these trigger a visible **pause/review** rather than silent send.

### Job processing

Audio, video, and large document scans return a job ID and progress state. The guarded action remains paused until a review/decision. Do not conflate an HTTP `202 Accepted` scan job response with an `allow` decision.

---

## 15. Dashboard and UX specification

### Navigation

```text
AIRLOCK
├── Overview
├── Live Activity
├── Incidents
│   └── Incident Detail / Evidence Replay / Triage
├── Privacy Insights
├── Inspector
│   ├── Image
│   ├── Audio
│   ├── Documents
│   ├── Code
│   └── Video
└── Policies & Settings
```

### 15.1 Overview

Top cards:

- Actions scanned (count).
- Findings requiring review (count).
- Prevented submissions (count, **only when interception was verified**).
- Confirmed transmissions involving flagged content (count, only with supporting evidence).

Charts:

- Event counts over time by modality.
- Findings by category and destination (based on observed monitored destinations only).
- Outcome breakdown: prevented, sanitized, dismissed, overridden, unresolved.
- Median/p95 scan duration by media type.

Every number should come from SQLite, not hardcoded UI placeholders. Synthetic demo-mode data must be clearly labeled.

### 15.2 Live Activity

Real-time stream of action lifecycle events:

```text
21:10:14  screenshot selected     image       scanning
21:10:16  possible credential     image       review_required
21:10:19  redaction approved      image       sanitizing
21:10:22  derived image verified  image       sanitized_and_sent
```

A live event should show its actual processing state; do not render an alert as “blocked” until confirmation exists.

### 15.3 Incident Explorer

Filters: date range, source/destination, media type, detector, severity, review status, transmission status, outcome. Support search in **redacted titles and metadata**, not a hidden index of raw personal data by default.

Each row shows: ID, time, category, risk, modality, destination, decision, actual outcome, triage state. Clicking opens detail.

### 15.4 Incident detail / evidence replay

Two-column desktop layout:

**Left:** evidence media preview (redacted by default), exact text span or bounding box, video/audio timeline with highlighted intervals, optional side-by-side original/sanitized view after explicit unlock.  
**Right:** plain-language summary, cited detection mechanism, policy rule, decision, transmission certainty, source and destination, user actions, event steps, triage actions.

Actions: mark `true_positive`, mark `false_positive`, dismiss, add redacted note, create safe copy (if permitted), delete evidence, export sanitized report.

**No invented evidence.** If AIRLOCK did not record a screen capture, don't fabricate a playback visualization. Show metadata and any user-retained evidence only.

### 15.5 Privacy Insights

Questions users should be able to answer:

- What categories do I almost share most often?
- Which destinations are most frequently associated with warnings, adjusting for how often I share there?
- How many findings were corrected or determined to be false positives?
- How long do scans take on my laptop?
- Which data types remain unsupported by the current version?

Do not label a site “untrustworthy” just because it receives frequent alerts.

### 15.6 Privacy Inspector

A deliberate manual analysis workspace for detailed questioning of a user's selected item, *not the primary firewall workflow*. Each modality has:

- input preview;
- descriptive summary;
- Q&A, with grounded citations/timestamps or explicit abstention;
- potential privacy findings;
- processing explanation and confidence limitations;
- safe-copy generation when supported.

### 15.7 Policies & Settings

Controls:

- Protection enabled/paused with clear status.
- Supported destinations and coverage indicator.
- Private categories and user-defined keywords (stored locally).
- Raw evidence retention: off by default; opt in per event.
- Retention period, delete/export controls.
- Model and hardware information, latency, local connectivity status.
- Demo mode with synthetic sample records.

### Accessibility

Keyboard navigation, semantic labels, sufficient contrast, clear focus states, no color-only severity coding, captions/transcripts for audio/video, and clear warning language.

---

## 16. Local incident investigation and code generation

### “Ask AIRLOCK” examples

- “What did AIRLOCK prevent me from submitting today?”
- “Show screenshots where a possible credential was detected.”
- “Which findings are still awaiting review?”
- “How many video events were scanned last week, and how many remain uncertain?”
- “Why did incident AL-0042 receive a high severity?”

### Retrieval and answer generation

1. Parse user question into an allowlisted query intent (`count_by_type`, `list_by_filter`, `describe_incident`, etc.).
2. Validate values and date range against the database schema; **do not execute arbitrary model-generated SQL**.
3. Execute read-only parameterized queries.
4. Provide the model only the minimal authorized result rows, redacted explanations, and incident IDs.
5. Answer with citations to incident IDs and link back to the detail page.
6. When data is absent or outside monitored coverage, say so explicitly.

For example, “I have no monitored events matching that filter” is more accurate than “You never shared anything sensitive.”

### Code generation demo

A judge asks: “Write a Python script that summarizes synthetic incident counts by modality, and show it works.”

Workflow:

- Qwen2.5-Coder creates a script against `fixtures/synthetic_only/incidents.json`.
- AST/basic static validation rejects risky imports and privileged commands, but does not substitute for sandboxing.
- A restricted runner executes with a separate minimal permission set, no network, fixed working directory, no access to real user data, and resource limits.
- Compare output against expected fixture results and show code plus pass/fail output.

Keep code generation separate from any privileged real-data remediation. Use audited deterministic libraries for real redaction.

---

## 17. Privacy, security, and threat model

### Assets to protect

- Outgoing text, source code, attachments, screenshots, documents, and recordings.
- The original secrets that AIRLOCK detects.
- Incident history, private keywords, evidence references, and optional raw media.
- The extension-to-local-server authorization mechanism.

### Threats and mitigations

| Threat | Mitigation / design principle |
|---|---|
| Website tries to access local inference server | Loopback binding **plus** request authentication, strict origins, body limits, no permissive CORS, CSRF/drive-by protections |
| Malicious page sends forged extension events | Sender origin/URL validation, narrow adapter allowlist, schema validation; never trust claimed origin in payload |
| Prompt injection inside documents/images/audio | Treat all source media as untrusted data; model cannot change permissions or invoke send actions |
| LLM hallucinates detection | Source-span/box validation and verified deterministic evidence; review ambiguous cases |
| LLM misses a secret | Honest coverage indication, tests, optional stricter policies, no “100% safe” claim |
| Raw sensitive content persists in logs | Redaction-first log format, explicit retention, no payload console logging |
| Local evidence stolen by malware | OS permissions and encrypted storage for mature version; do not claim protection against fully compromised host |
| Generated code escapes | Restrict execution to sandbox + synthetic fixtures; never mount real secret-bearing files |
| Unsafe redaction overlays | Re-encode media or apply actual redaction, rescan and inspect |
| Extension silently fails on a site | Show coverage state and adapter health; do not claim universal protection |
| User believes an alert proves exfiltration | Separate *finding*, *intervention*, and *transmission evidence* statuses |
| Fake/unsupported file types or decompression bombs | MIME validation, file-size/decode limits, processing timeouts, isolated parsers |
| Resource starvation | Queue limits, bounded inference, cancel option, status visibility, explicit unknown-on-timeout |

### Security defaults

- No remote telemetry, error reporting, or cloud model access.
- No passive camera/microphone activation.
- No storing of full page content in event logs.
- User-visible enable/disable status and site coverage.
- Only user-approved protected sites; narrowly scoped browser permissions.
- Read-only incident queries; explicit triage mutations.
- Sanitize filenames and never use untrusted relative paths directly.
- Redact secrets in application exceptions and debug traces.
- Test loopback endpoint access from an unrelated web page and require rejection.

### Ethical disclosure and user consent

Use synthetic data in public demos. Do not secretly record people's voices, screens, or files. Do not identify third parties from media or speculate about intent. If a real user opts into retained incident evidence, explain local retention and deletion in plain language. If using actual cloud AI sites for integration tests, never send actual credentials or confidential records.

---

## 18. Development setup

The steps below are a **target developer workflow**, not evidence that the repository already contains these files. Commands will work after their referenced packages, scripts, and configuration have been implemented.

### Prerequisites

- Python 3.11+ (pin a tested version).
- Node.js 20+ and npm/pnpm.
- Chrome/Chromium desktop browser.
- Ollama, installed locally.
- FFmpeg and a local OCR engine.
- Git and appropriate model disk space.

### Example installation (macOS with Homebrew)

```bash
brew install python node ffmpeg tesseract ollama
```

Ensure the Ollama service is running. The actual model tag depends on available runtime and hardware:

```bash
ollama list
# Example only; pick and validate specific models from the local registry:
ollama pull qwen3-vl:4b
ollama pull qwen2.5-coder:3b
```

Before using any model tag in a script, verify that it exists in the installed Ollama version and can process the required inputs. Download all weights before the offline demo.

### Backend setup

```bash
cd services/api
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
# Set AIRLOCK_LOCAL_TOKEN in the environment / secure local config.
uvicorn app.main:app --host 127.0.0.1 --port 8765 --reload
```

Suggested Python dependencies (adjust/pin after integration tests):

```text
fastapi
uvicorn[standard]
pydantic
sqlalchemy
python-multipart
httpx
pillow
pymupdf
pytesseract
presidio-analyzer
presidio-anonymizer
faster-whisper
pytest
```

Install OCR language packs and an audio classifier as required. On macOS, support may vary by device and by `faster-whisper` backend; `whisper.cpp` may be a simpler option for local inference.

### Dashboard and local demo page

```bash
cd apps/dashboard && npm install && npm run dev
# in another terminal
cd apps/demo-chat && npm install && npm run dev -- --port 5174
```

Configure the dashboard dev server on a different local port (for example `5173`), and the demo chat on `5174`.

### Chrome extension

1. Build `apps/extension` into a folder with `manifest.json`, `content.js`, and `background.js`.
2. Open `chrome://extensions`.
3. Enable **Developer mode**.
4. Choose **Load unpacked**, select the built extension folder.
5. Open the controlled demo chat page and confirm the AIRLOCK protection indicator is visible.
6. Open the extension's service-worker inspector and check for errors **without logging raw user content**.

### Offline verification

1. Pre-download and verify all model files.
2. Disable Wi-Fi and disconnect networking.
3. Launch local backend, dashboard, demo chat, and extension.
4. Submit the synthetic test scenario and verify detection, intervention, logging, and local Q&A.
5. Confirm the system works without any calls to external APIs; use browser/network tooling to check the relevant local app processes.

---

## 19. Implementation milestones

**Contest window: November 18–20, 2026.** Prioritize a correct small system over broad, unreliable coverage.

### Milestone 0 — Scope freeze and fixtures (first)

- [ ] Decide demo hardware and capture RAM/CPU/GPU specifications.
- [ ] Implement local demo chat with a server-side received-request counter.
- [ ] Create a synthetic fixture corpus for text, code, screenshots, PDF, audio, video.
- [ ] Label known finding spans, bounding boxes, and timestamps.
- [ ] Choose one supported source-to-destination flow and write its acceptance test.

**Exit criterion:** One outgoing action can be paused and its network receipt verified independently.

### Milestone 1 — Backend and deterministic scanning

- [ ] Build FastAPI health and `/scans/text` route.
- [ ] Add regex/secret scanning, PII recognition, and typed findings.
- [ ] Implement policy decisions and SQLite persistence.
- [ ] Record events with no raw secrets in logs.
- [ ] Test invalid input, empty input, and detector timeouts.

**Exit criterion:** Synthetic secrets are found and serialized without exposing the original values in logs.

### Milestone 2 — Automatic intervention

- [ ] Implement guarded local demo submission.
- [ ] Add extension content script and background messaging.
- [ ] Pause, cancel, review, sanitize, and resume a controlled action.
- [ ] Verify that original blocked payload never reaches the demo server.
- [ ] Test keyboard submit, button click, double-click, and payload changes during scan.

**Exit criterion:** End-to-end interception works repeatably with Wi-Fi off.

### Milestone 3 — Image detection and safe copy

- [ ] OCR screenshot + bounding boxes.
- [ ] Local VLM description and image Q&A.
- [ ] Annotated evidence view and true pixel redaction.
- [ ] Rescan sanitized copy before submission.
- [ ] Compare OCR+rules versus OCR+rules+VLM on held-out screenshots.

**Exit criterion:** A previously unseen synthetic screenshot is detected, redacted, and safely submitted.

### Milestone 4 — Dashboard and triage

- [ ] Overview cards and simple charts populated from SQLite.
- [ ] Live activity feed.
- [ ] Incident list with filters.
- [ ] Incident details, detection anchors, and event steps.
- [ ] Triage actions and basic local question answering.

**Exit criterion:** A judge can explain what happened by inspecting the saved event without developer assistance.

### Milestone 5 — Mandatory modality completeness

- [ ] Document Q&A plus an abstention test.
- [ ] Audio transcription, audio Q&A, and separate sound classification.
- [ ] Video summary and timestamped Q&A.
- [ ] Code generation + sandboxed execution on fixtures.
- [ ] One benchmark/test result table per modality.

**Exit criterion:** All five challenge requirements can be demonstrated without cloud inference.

### Milestone 6 — Presentation hardening

- [ ] Airplane-mode smoke test.
- [ ] Demo recovery plan if the VLM is slow or an optional classifier is unavailable.
- [ ] Record true benchmark results, limitations, and model licenses.
- [ ] Verify clean installation/run instructions in GitHub repo.
- [ ] Do not include real customer records, API keys, or private recordings in repository/demo.

---

## 20. Tests, evaluation, and acceptance criteria

### 20.1 Dataset construction

Create **synthetic, fully labeled** fixtures with planted secrets, ordinary nonsecret lookalikes, and realistic formatting:

- Text/code: fake tokens, multiline snippets, benign random IDs, emails, names, and negative examples.
- Images: secrets in terminal windows, sidebars, tabs, small text, poor contrast, and nonsecret screenshots.
- Documents: a few answerable questions plus at least one unanswerable question.
- Audio: clear speech, noise, silence, overlapping speech, and selected labeled sound events.
- Video: visible tokens lasting multiple seconds and brief exposures, plus no-exposure clips.

Use explicit training/tuning/test separation if thresholds are tuned. Never use real credentials in public fixtures.

### 20.2 Core metrics

| Metric | Definition |
|---|---|
| Detection recall | True sensitive instances detected / all labeled sensitive instances |
| Precision | True sensitive instances detected / all instances flagged |
| False-positive rate | False alarms / labeled benign instances (state denominator precisely) |
| Intervention success | Blocked actions that never reached controlled receiving endpoint / blocked trials |
| Sanitization success | Derived files with no remaining labeled target secret / attempted sanitizations |
| Preservation quality | Non-sensitive content still usable after sanitation, with explicit human/rule-based criteria |
| Scan latency | p50/p95 time from guarded submit to decision, per modality |
| Grounded QA accuracy | Correct answers supported by source evidence / labeled questions |
| Abstention accuracy | Correct abstentions / unanswerable questions |
| Sound classification | Accuracy or F1 on supported labeled sound events |
| Generated code validity | Scripts that execute and pass fixture tests / generated scripts |
| Video localization | Fraction of labeled exposure intervals detected, plus timestamp error |
| Locality | No required external network calls during actual inference and demo |

Report results by modality and content type. **Do not invent benchmark values for slides.**

### 20.3 Crucial test cases

1. **Before-send:** Under a controlled adapter, an intercepted original payload is absent from receiver logs.
2. **Safe re-submit:** Sanitized payload reaches receiver, original does not.
3. **Scan timeout:** Submission remains paused; UI shows uncertain status.
4. **Double submit:** Two clicks cause no duplicate transfer.
5. **Payload mutation:** If the content changes during scanning, the old decision cannot authorize the new payload.
6. **False positive:** A benign demo token can be labeled not sensitive and resolved.
7. **Unknown origin:** An unauthorized webpage cannot invoke privileged backend actions.
8. **Prompt injection:** A hostile instruction in a document cannot instruct AIRLOCK to bypass the policy engine.
9. **Missing document answer:** Document Q&A abstains.
10. **Video brief exposure:** Full/fast scan limitations are surfaced; report actual recall.
11. **Audio silence:** Avoid hallucinated transcript being presented as confirmed.
12. **Code runner:** Network and arbitrary file access are denied.
13. **Retention:** Old evidence is deleted according to configured policy.
14. **Offline:** All required flows run after network is disabled.
15. **Evidence integrity:** Annotations point to actual source spans or frames.

### 20.4 Baseline ablation

For image disclosure detection, compare:

- **A:** OCR + regex/PII rules.
- **B:** OCR + regex/PII rules + local VLM contextual review.

Evaluate on the *same held-out corpus*. If B does not materially improve detection, precision, or explanation quality, be transparent. A simple reliable baseline can be superior to a slower model; model use should be justified with actual evidence.

### 20.5 Acceptance criteria for MVP release

- [ ] One working automatic pre-submission intervention in controlled app.
- [ ] No original blocked payload arrives at instrumented demo receiver.
- [ ] One working text/code rule and one screenshot OCR finding.
- [ ] Real pixel redaction followed by rescan and explicit user approval.
- [ ] Incident event appears in dashboard and can be triaged.
- [ ] All five required modalities demonstrated and documented with measured tests.
- [ ] At least one missing-information abstention.
- [ ] A generated code script executes successfully in the restricted fixture runner.
- [ ] Offline demo works on named laptop and local model weights.
- [ ] README accurately describes supported sites, limitations, and known failures.

---

## 21. Hackathon demo script

**Goal: a 3–4-minute, genuinely interactive demo.**

**0:00–0:20 — User problem**  
“People share screenshots, code, recordings, and documents every day. The thing they intended to share is not always the only information inside. AIRLOCK protects supported sharing actions before they leave the device—and explains the results locally.”

**0:20–0:40 — Offline proof**  
Turn off Wi-Fi. Show Ollama/local health indicator and extension status. No cloud inference is used.

**0:40–1:40 — Automatic protection**  
Ask a judge to choose a synthetic screenshot or code snippet. Attach it to the normal-looking local chat. Click Send. AIRLOCK pauses, marks an actual finding, creates a sanitized version, and only the sanitized version reaches the demo receiver.

**1:40–2:30 — Triage**  
Open the dashboard. The event appears. Click it: original/safe preview, evidence region, category, policy, action timestamps, and actual network-receipt status. Mark resolved.

**2:30–3:20 — Multimodal demonstration**  
Show quick preloaded local inspector cases: document Q&A with an abstention, audio transcript plus sound classification, short-video timestamped finding, and a locally generated working code script. Show one source-linked Q&A answer.

**3:20–4:00 — Results and limitations**  
Display measured baseline vs multimodal performance, offline latency, and supported browser scope. End with: **“Your data stays yours. Your mistakes don't have to leave your device.”**

### Backup plan

Have a local demo recording of a successful run for explanation only, **but do not portray a replay as a live success**. Keep a deterministic text-interception demo runnable even if a large model has not loaded. Surface timeout states honestly.

---

## 22. Known limitations and non-goals

- Automatic interception currently applies only to **explicitly supported and tested flows**.
- Rich web apps may bypass form/paste events; site-specific integrations can break.
- Browser extension permissions cannot provide reliable OS-wide monitoring of arbitrary app sharing.
- Large VLM/audio/video scans may be too slow for a normal interactive send unless the action can remain paused.
- OCR and sampling can miss briefly visible or low-quality secrets.
- PII classification is context-sensitive; false positives and false negatives are unavoidable.
- Unredacted originals may remain in browser memory, browser caches, the source application, or OS storage even if AIRLOCK does not retain them.
- A hostile/malicious OS or browser extension can bypass AIRLOCK; the tool is not designed to protect a compromised endpoint.
- A blocked browser action does not prove that no other prior or parallel data transmission occurred.
- Network-disconnected operation does not mean an air-gapped or formally verified application.
- No automated legal conclusion, compliance certification, or guarantee of complete sanitization.
- Never use AIRLOCK as the sole safety boundary for highly consequential data.

---

## 23. Future work

1. **Real browser adapters:** One adapter at a time with continuous integration tests and visible per-site protection health.
2. **OS-native sharing integrations:** macOS share sheet and filesystem hooks; Windows share/clipboard integrations; opt-in permissions, with platform-specific security review.
3. **Local multimodal exposure graph:** Correlate evidence across audio, video, image, text, and code while grounding every conclusion in identifiable observations.
4. **Per-user private policies:** Define business codenames, confidential fields, allowed destinations, and retention exceptions without cloud synchronization.
5. **Private benchmarking toolkit:** Share only synthetic tests and aggregate performance metrics; never upload private data.
6. **Secure local encrypted store:** OS keychain integration, encryption key rotation, tamper-aware incident metadata.
7. **Model switching:** Cost/latency/accuracy-based local selection with device capability profiling.
8. **Proactive but consent-based privacy nudges:** Notify users before supported outgoing actions, without continuous surveillance.
9. **Privacy budget:** Let users inspect patterns of disclosed categories across destinations and time, without claiming unknowable external storage or vendor usage.
10. **Independent security review:** Threat modeling and reproducible testing of its own extension, local API, redaction pipeline, and code runner.

---

## 24. References

These resources informed the implementation choices. They are **not** claims that AIRLOCK has already implemented the behavior. Verify exact API versions and dependency compatibility during development.

- Chrome extensions: [Content scripts](https://developer.chrome.com/docs/extensions/reference/manifest/content-scripts), [Message passing](https://developer.chrome.com/docs/extensions/develop/concepts/messaging), [Permissions](https://developer.chrome.com/docs/extensions/develop/concepts/declare-permissions).
- Chrome network restrictions: [declarativeNetRequest](https://developer.chrome.com/docs/extensions/reference/api/declarativeNetRequest), [webRequest](https://developer.chrome.com/docs/extensions/reference/api/webRequest).
- Chrome [Native Messaging](https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging) for possible future privileged local app integration.
- [Ollama API](https://docs.ollama.com/api), [Ollama vision capabilities](https://docs.ollama.com/capabilities/vision), [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs).
- [Presidio PII detection and anonymization](https://microsoft.github.io/presidio/).
- [whisper.cpp](https://github.com/ggml-org/whisper.cpp) and [faster-whisper](https://github.com/SYSTRAN/faster-whisper).
- [FFmpeg](https://ffmpeg.org/documentation.html), [PyMuPDF](https://pymupdf.readthedocs.io/), and [Tesseract OCR](https://github.com/tesseract-ocr/tesseract).
- [FastAPI](https://fastapi.tiangolo.com/), [Playwright](https://playwright.dev/), [SQLite](https://www.sqlite.org/docs.html).

### License and responsible use

Choose and document a project license before public release. List the **individual model-weight licenses** and data-source permissions in `docs/architecture.md`. Do not include real private data, actual API keys, credentials, or non-consensual recordings in test fixtures.

---

## One-sentence product definition

**AIRLOCK is a privacy-preserving, local multimodal security layer that intervenes at supported sharing boundaries, explains sensitive-data findings, helps users create safer copies, and turns every observed incident into actionable, on-device privacy intelligence.**
