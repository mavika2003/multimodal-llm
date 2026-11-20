#!/usr/bin/env python3
"""
Local AIRLOCK desktop agent (opt-in).

- Clipboard: alerts when clipboard content changes (incl. paste / Cmd+C).
- Screen compose (macOS): Notes / Mail / TextEdit via AppleScript + Accessibility.

Accessibility: enable the Python binary printed at startup (not only Terminal).
System Settings → Privacy & Security → Accessibility → + → select that python3 path.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx

API = os.environ.get("AIRLOCK_API", "http://127.0.0.1:8765/api/v1")
TOKEN = os.environ.get("AIRLOCK_LOCAL_TOKEN", "dev-local-token")
POLL_SEC = float(os.environ.get("AIRLOCK_AGENT_POLL_SEC", "0.8"))
AX_POLL_SEC = float(os.environ.get("AIRLOCK_AGENT_AX_POLL_SEC", "1.5"))
WATCH_DIR = os.environ.get("AIRLOCK_WATCH_DIR", "")
MIN_LEN = int(os.environ.get("AIRLOCK_AGENT_MIN_CHARS", "8"))
SCREEN_WATCH = os.environ.get("AIRLOCK_AGENT_SCREEN", "1").lower() in (
    "1",
    "true",
    "yes",
)
DEBUG = os.environ.get("AIRLOCK_AGENT_DEBUG", "0").lower() in ("1", "true", "yes")
DIALOG_ON_REVIEW = os.environ.get("AIRLOCK_AGENT_DIALOG", "1").lower() in (
    "1",
    "true",
    "yes",
)
NOTIFY_ON_WARN = os.environ.get("AIRLOCK_AGENT_NOTIFY_WARN", "1").lower() in (
    "1",
    "true",
    "yes",
)
ALERT_COOLDOWN_SEC = float(os.environ.get("AIRLOCK_AGENT_ALERT_COOLDOWN", "45"))
OSASCRIPT_TIMEOUT = float(os.environ.get("AIRLOCK_AGENT_OSASCRIPT_TIMEOUT", "4.0"))

WATCH_APPS = {
    "Notes",
    "Mail",
    "TextEdit",
    "Code",
    "Cursor",
    "Terminal",
    "iTerm2",
    "Slack",
    "Microsoft Word",
    "Pages",
}

_last_alert_at: dict[str, float] = {}
_ax_denied_logged = False
_debug_tick = 0

NOTES_APP_SCRIPT = r'''
tell application "Notes"
  try
    set sel to selection
    if (count of sel) > 0 then
      return plaintext of item 1 of sel as text
    end if
  end try
  try
    set acct to default account
    set nlist to notes of acct
    if (count of nlist) > 0 then
      return plaintext of item 1 of nlist as text
    end if
  end try
  return ""
end tell
'''

NOTES_AX_SCRIPT = r'''
tell application "System Events"
  if not (exists process "Notes") then return ""
  tell process "Notes"
    if (count of windows) is 0 then return ""
    set candidates to {}
    try
      set end of candidates to value of text area 1 of front window
    end try
    try
      set end of candidates to value of text area 1 of scroll area 1 of front window
    end try
    try
      set end of candidates to value of text area 1 of scroll area 1 of group 1 of splitter group 1 of front window
    end try
    try
      set end of candidates to value of text area 1 of scroll area 1 of group 1 of front window
    end try
    set best to ""
    repeat with c in candidates
      if c is not missing value then
        set t to c as text
        if (length of t) > (length of best) then set best to t
      end if
    end repeat
    return best
  end tell
end tell
'''

TEXTEDIT_SCRIPT = r'''
tell application "TextEdit"
  try
    if (count of documents) > 0 then
      return text of front document as text
    end if
  end try
  return ""
end tell
'''

FOCUS_AX_SCRIPT = r'''
tell application "System Events"
  set frontProc to first application process whose frontmost is true
  set appName to name of frontProc
  set collected to ""
  try
    set w to front window of frontProc
    set focused to value of attribute "AXFocusedUIElement" of w
    try
      set collected to value of attribute "AXValue" of focused
    end try
    if collected is "" then
      try
        set collected to value of attribute "AXSelectedText" of focused
      end try
    end if
  end try
  return appName & "|||" & collected
end tell
'''


def run_applescript(source: str) -> str:
    try:
        out = subprocess.check_output(
            ["osascript", "-e", source],
            text=True,
            errors="replace",
            timeout=OSASCRIPT_TIMEOUT,
        )
        return (out or "").strip()
    except subprocess.TimeoutExpired:
        return ""
    except subprocess.CalledProcessError as err:
        global _ax_denied_logged
        if not _ax_denied_logged:
            _ax_denied_logged = True
            print(
                "[screen] AppleScript failed — check macOS permissions:\n"
                f"  Accessibility: {sys.executable}\n"
                "  Automation: allow Terminal/Python to control TextEdit & Notes\n"
                f"  ({err})"
            )
        return ""


def read_clipboard() -> str:
    if sys.platform != "darwin":
        return ""
    try:
        return subprocess.check_output(["pbpaste"], text=True, errors="replace", timeout=2) or ""
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return ""


def read_notes_compose() -> str:
    text = run_applescript(NOTES_APP_SCRIPT)
    if len(text.strip()) >= MIN_LEN:
        return text.strip()
    text = run_applescript(NOTES_AX_SCRIPT)
    return text.strip()


def read_textedit_compose() -> str:
    return run_applescript(TEXTEDIT_SCRIPT).strip()


def read_focused_app_text() -> tuple[str, str]:
    if sys.platform != "darwin" or not SCREEN_WATCH:
        return "", ""
    front = frontmost_app_name()

    if front == "TextEdit":
        return "TextEdit", read_textedit_compose()
    if front == "Notes":
        return "Notes", read_notes_compose()

    raw = run_applescript(FOCUS_AX_SCRIPT)
    if "|||" in raw:
        app_name, text = raw.split("|||", 1)
        app_name = app_name.strip()
        text = text.strip()
        if app_name == "TextEdit" or front == "TextEdit":
            te = read_textedit_compose()
            if len(te) > len(text):
                return "TextEdit", te
        if app_name == "Notes" or front == "Notes":
            notes = read_notes_compose()
            if len(notes) > len(text):
                return "Notes", notes
        if app_name in WATCH_APPS:
            return app_name, text
    if front in WATCH_APPS:
        return front, ""
    return "", ""


def frontmost_app_name() -> str:
    return run_applescript(
        'tell application "System Events" to return name of first application process whose frontmost is true'
    )


def _escape_applescript(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")[:400]


def notify_mac(title: str, message: str) -> None:
    if sys.platform != "darwin":
        return
    safe = _escape_applescript(message)
    title_s = _escape_applescript(title)
    subprocess.run(
        ["osascript", "-e", f'display notification "{safe}" with title "{title_s}"'],
        check=False,
        timeout=5,
    )


def alert_mac(title: str, message: str) -> None:
    if sys.platform != "darwin" or not DIALOG_ON_REVIEW:
        return
    safe = _escape_applescript(message)
    title_s = _escape_applescript(title)
    subprocess.run(
        [
            "osascript",
            "-e",
            (
                f'display dialog "{safe}" with title "{title_s}" '
                'buttons {"OK"} default button "OK" with icon caution giving up after 120'
            ),
        ],
        check=False,
        timeout=130,
    )


def format_findings(data: dict) -> str:
    findings = data.get("findings") or []
    if not findings:
        return "Policy match"
    parts = [f"{f.get('severity')}: {f.get('category')}" for f in findings[:3]]
    return ", ".join(parts)


def scan_text(content: str, source: str, destination: str) -> dict | None:
    try:
        r = httpx.post(
            f"{API}/scans/text",
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "action_id": hashlib.sha256((content + str(time.time())).encode()).hexdigest()[:16],
                "source": source,
                "destination_origin": destination,
                "modality": "text",
                "content": content[:120_000],
            },
            timeout=30.0,
        )
        if r.is_success:
            return r.json()
        print("scan failed", r.status_code, r.text[:200])
    except httpx.HTTPError as e:
        print("API unreachable:", e)
    return None


def should_alert(content_hash: str) -> bool:
    now = time.time()
    last = _last_alert_at.get(content_hash, 0.0)
    if now - last < ALERT_COOLDOWN_SEC:
        return False
    _last_alert_at[content_hash] = now
    return True


def surface_decision(data: dict, channel: str, content_hash: str) -> None:
    decision = data.get("decision", "unknown")
    n = len(data.get("findings") or [])
    summary = format_findings(data)
    print(f"[{channel}] decision={decision} findings={n} ({summary})")
    if decision not in ("block", "require_review") and not (
        decision == "warn" and n > 0 and NOTIFY_ON_WARN
    ):
        return
    if decision in ("block", "require_review") and not should_alert(content_hash):
        print(f"[{channel}] alert suppressed (cooldown)")
        return
    title = "AIRLOCK on-screen alert" if channel.startswith("screen") else "AIRLOCK clipboard alert"
    alert_mac(
        title,
        f"{channel}: {decision}. {n} finding(s). {summary}.",
    )
    notify_mac("AIRLOCK", f"{decision}: {summary}")


def process_text_change(
    text: str,
    last_hash: str,
    channel: str,
    destination: str,
    source: str,
    *,
    silent: bool = False,
) -> str:
    t = text.strip()
    if len(t) < MIN_LEN:
        return last_hash
    h = hashlib.sha256(t.encode()).hexdigest()
    if h == last_hash:
        return last_hash
    data = scan_text(t, source, destination)
    if not data:
        return h
    if not silent:
        surface_decision(data, channel, h)
    return h


def seed_baseline(text: str, label: str) -> str:
    t = text.strip()
    if len(t) < MIN_LEN:
        return ""
    h = hashlib.sha256(t.encode()).hexdigest()
    print(f"[{label}] baseline seeded ({len(t)} chars) — no popup on agent start")
    return h


def handle_clipboard(last_hash: str, *, alert: bool = True) -> str:
    return process_text_change(
        read_clipboard(),
        last_hash,
        "clipboard",
        "clipboard://local",
        "desktop-agent-clipboard",
        silent=not alert,
    )


def handle_screen(
    last_hash: str,
    pending_text: str,
    pending_since: float,
) -> tuple[str, str, float]:
    app, text = read_focused_app_text()
    front = frontmost_app_name()
    if DEBUG or (_debug_tick % 6 == 0 and front in ("Notes", "TextEdit")):
        print(f"[debug] front={front!r} watch_app={app!r} text_len={len(text)}")
    if not app and front == "Notes":
        text = read_notes_compose()
        app = "Notes"
    if not app and front == "TextEdit":
        text = read_textedit_compose()
        app = "TextEdit"
    if not app or app not in WATCH_APPS:
        return last_hash, "", 0.0
    if len(text.strip()) < MIN_LEN:
        return last_hash, "", 0.0
    now = time.time()
    if text != pending_text:
        return last_hash, text, now
    if now - pending_since < 0.45:
        return last_hash, pending_text, pending_since
    channel = f"screen:{app}"
    dest = f"app://{app.lower().replace(' ', '-')}"
    new_hash = process_text_change(
        text,
        last_hash,
        channel,
        dest,
        "desktop-agent-screen",
    )
    return new_hash, pending_text, pending_since if new_hash == last_hash else now


def scan_file(path: Path, seen: set[str]) -> None:
    key = str(path.resolve())
    if key in seen:
        return
    try:
        if path.stat().st_size > 512_000:
            return
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    if len(text.strip()) < MIN_LEN:
        return
    seen.add(key)
    process_text_change(
        text,
        "",
        f"file:{path.name}",
        f"file://{path.name}",
        "desktop-agent-file",
    )


def watch_folder(root: Path, seen: set[str]) -> None:
    if not root.is_dir():
        return
    for path in root.iterdir():
        if path.suffix.lower() in {".txt", ".md", ".env", ".json", ".log", ".csv"}:
            scan_file(path, seen)


def print_banner() -> None:
    print("=" * 60)
    print("AIRLOCK desktop agent")
    print(f"API={API}")
    print(f"Python (add to Accessibility): {sys.executable}")
    print()
    print("Enable Debug: AIRLOCK_AGENT_DEBUG=1 make agent")
    print()
    print("Screen: TextEdit + Notes (Automation). Clipboard: Cmd+C changes only.")
    print("Cmd+V does NOT re-scan clipboard — screen polling detects paste in the app.")
    print("Ctrl+C to stop.")
    print("=" * 60)


def main() -> None:
    global _debug_tick
    print_banner()
    clip_hash = seed_baseline(read_clipboard(), "clipboard")
    screen_hash = ""
    app, txt = read_focused_app_text()
    front = frontmost_app_name()
    if not txt and front == "Notes":
        txt = read_notes_compose()
        app = "Notes"
    if not txt and front == "TextEdit":
        txt = read_textedit_compose()
        app = "TextEdit"
    if txt:
        screen_hash = seed_baseline(txt, f"screen:{app or 'app'}")
    file_seen: set[str] = set()
    watch = Path(WATCH_DIR).expanduser() if WATCH_DIR else None
    if watch:
        print(f"Also watching folder: {watch}")
    pending_text = ""
    pending_since = 0.0
    last_ax = 0.0
    while True:
        _debug_tick += 1
        clip_hash = handle_clipboard(clip_hash, alert=True)
        if watch:
            watch_folder(watch, file_seen)
        now = time.time()
        if SCREEN_WATCH and sys.platform == "darwin" and now - last_ax >= AX_POLL_SEC:
            last_ax = now
            screen_hash, pending_text, pending_since = handle_screen(
                screen_hash,
                pending_text,
                pending_since,
            )
        time.sleep(POLL_SEC)


if __name__ == "__main__":
    main()