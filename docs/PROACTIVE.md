# Proactive AIRLOCK (browser + desktop)

AIRLOCK was originally **passive**: you paste into the demo chat and click Send. This repo now supports **opt-in proactive** modes that match the product direction in the README (protect outgoing actions, not total surveillance).

## Two proactive channels

| Channel | What it watches | What it does *not* do |
|--------|------------------|------------------------|
| **Chrome extension (v0.3)** | Textareas and contenteditable fields on pages you browse after you enable **Proactive guard** | Keystroke logging, hidden screenshots, or network MITM |
| **Desktop agent** | Clipboard changes; optional folder of new `.txt` / `.env` files | Global screen recording, keylogger, or app hooks |

All scans call the same local API (`POST /scans/text`) and create incidents like the dashboard chat.

## Enable proactive browser guard

1. `make api`
2. `make extension-build`
3. Chrome → Extensions → Load unpacked → `apps/extension/dist`
4. Open the AIRLOCK popup → check **Proactive guard (all sites)** → **Save guard settings**
5. Approve Chrome’s **Read and change all your data on all websites** prompt (required for ChatGPT, Claude, Slack, etc.)
6. **Refresh the chat tab once** after saving (or reload Claude). Tabs that were already open before enable may not run the proactive script until refresh.

### Behavior on any site

- **Live scan while typing** (debounced) → shield badge bottom-right shows `allow` / `require_review` / `block`
- **Scan on paste**
- **Pause Send / Submit** when decision is `block` or `require_review` (override with “Send anyway”)

### Test on ChatGPT (or any chat site)

1. Paste contents of `fixtures/synthetic_only/sample_secret.txt` into the prompt box.
2. Watch the AIRLOCK shield turn amber/red.
3. Click Send → modal should pause the action.
4. Check dashboard **Incidents** (source `chrome-extension-proactive`, destination your site origin).

**Limitations:** Sites change DOM often; send-button heuristics are best-effort. Some apps use shadow DOM or custom events AIRLOCK may not hook yet.

## Enable desktop agent (clipboard)

```bash
make api          # terminal 1
make agent        # terminal 2 — clipboard polling
```

Optional watch Downloads for new text-like files:

```bash
make agent-watch
```

Copy synthetic secret text to the clipboard; macOS shows a **dialog + notification** when AIRLOCK flags it.

### Apple Notes (and Mail, VS Code, etc.)

There is **no “Guard active”** overlay in native Mac apps. That badge is **Chrome extension only**.

**On-screen detection (typing / pasting in Notes):**

1. `make api` and `make agent` from repo root.
2. macOS **System Settings → Privacy & Security → Accessibility** → click **+** and add the **Python binary** printed when the agent starts (e.g. `.../services/api/.venv/bin/python3`). Also enable **Terminal** or **iTerm**.
3. Restart the agent after granting permission.
4. Open Notes, click in the note body, paste or type the synthetic secret.
5. Within ~1–2 seconds you should get an **AIRLOCK on-screen alert** and a log line `[screen:Notes] decision=require_review`.

**TextEdit (easiest native demo):** same steps — grant Automation for **TextEdit**. Run `make agent-debug`, focus TextEdit, paste secrets. Expect `[screen:TextEdit]`. **Cmd+V does not scan the clipboard**; the agent reads the **document text on screen**.

If the document already had secrets when the agent **started**, that text is baselined (no popup). Clear the doc, restart the agent, then paste again — or add new secret lines after start.

**Clipboard (Cmd+C)** still works separately with source `desktop-agent-clipboard`.

**Startup glitch fix:** The agent **baselines** current clipboard/screen on start so you do not get a popup from old copied text. Only **changes** after start alert you.

Set `AIRLOCK_AGENT_SCREEN=0` to disable Accessibility monitoring (clipboard only).

Env vars:

- `AIRLOCK_API` (default `http://127.0.0.1:8765/api/v1`)
- `AIRLOCK_LOCAL_TOKEN` (default `dev-local-token`)
- `AIRLOCK_WATCH_DIR` for folder watch
- `AIRLOCK_AGENT_POLL_SEC` (default `1`)

## What “see all activity on my laptop” would require

Full-device monitoring is **out of scope** for this hackathon build and conflicts with the README privacy principle. A production path would add explicit modules, each opt-in:

- App-specific helpers (IDE plugin, Slack desktop URL handler)
- Enterprise MDM / DLP connector
- Screen-share detection with user consent and OS permissions

The extension + clipboard agent demonstrate the **same decision engine** on real outbound surfaces without pretending to be omniscient.

## Architecture reminder

There is no neural “router model.” **FastAPI routes** pick the pipeline (text rules, OCR, ingest). **Ollama** remains optional for Inspector Q&A, not for every keystroke.