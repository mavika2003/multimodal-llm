type ScanData = {
  decision: string;
  findings: Array<{ category: string; severity: string; excerpt_redacted: string }>;
};

type GuardSettings = {
  proactive: boolean;
  blockOnSend: boolean;
  scanOnPaste: boolean;
  liveDebounce: boolean;
};

const SHIELD_ID = "airlock-proactive-shield";
const MODAL_ID = "airlock-proactive-modal";

let lastScan: ScanData | null = null;
let lastTextHash = "";
let debounceTimer: ReturnType<typeof setTimeout> | null = null;
let settings: GuardSettings = {
  proactive: true,
  blockOnSend: true,
  scanOnPaste: true,
  liveDebounce: true,
};
let allowBypass = false;

function settingsFromStorage(data: Record<string, unknown>): GuardSettings {
  return {
    proactive: Boolean(data.proactive ?? true),
    blockOnSend: Boolean(data.blockOnSend ?? true),
    scanOnPaste: data.scanOnPaste !== false,
    liveDebounce: data.liveDebounce !== false,
  };
}

function loadSettings(cb: () => void) {
  chrome.storage.sync.get(
    { proactive: true, blockOnSend: true, scanOnPaste: true, liveDebounce: true },
    (data) => {
      settings = settingsFromStorage(data);
      cb();
    },
  );
}

function ensureShield() {
  if (document.getElementById(SHIELD_ID)) return;
  const el = document.createElement("div");
  el.id = SHIELD_ID;
  el.setAttribute("role", "status");
  el.style.cssText =
    "position:fixed;bottom:12px;right:12px;z-index:2147483646;background:#15191f;color:#9aa4b2;padding:8px 12px;font:12px system-ui;border-radius:8px;border:1px solid #2a3441;max-width:220px;box-shadow:0 4px 24px rgba(0,0,0,.4);";
  el.textContent = "AIRLOCK proactive · idle";
  document.documentElement.appendChild(el);
}

function updateShield(data: ScanData | null, err?: string) {
  ensureShield();
  const el = document.getElementById(SHIELD_ID)!;
  if (err) {
    el.textContent = `AIRLOCK · ${err}`;
    el.style.borderColor = "#b45309";
    el.style.color = "#fcd34d";
    return;
  }
  if (!data) return;
  const n = data.findings?.length ?? 0;
  el.textContent = `AIRLOCK · ${data.decision}${n ? ` (${n})` : ""}`;
  if (data.decision === "block") {
    el.style.borderColor = "#dc2626";
    el.style.color = "#fca5a5";
  } else if (data.decision === "require_review") {
    el.style.borderColor = "#d97706";
    el.style.color = "#fcd34d";
  } else {
    el.style.borderColor = "#1f6b50";
    el.style.color = "#6ee7b7";
  }
}

function simpleHash(s: string): string {
  let h = 0;
  for (let i = 0; i < s.length; i += 1) h = (h * 31 + s.charCodeAt(i)) | 0;
  return String(h);
}

function textFromTarget(target: EventTarget | null): string {
  if (!target || !(target instanceof HTMLElement)) return "";
  if (target instanceof HTMLTextAreaElement) return target.value;
  if (target instanceof HTMLInputElement && target.type === "text") return target.value;
  if (target.isContentEditable) return target.innerText || "";
  const parent = target.closest(
    "textarea,[contenteditable='true'],[contenteditable='plaintext-only'],[role='textbox'],.ProseMirror",
  );
  if (parent instanceof HTMLTextAreaElement) return parent.value;
  if (parent instanceof HTMLElement && parent.isContentEditable) return parent.innerText || "";
  return "";
}

const COMPOSE_SELECTORS = [
  "textarea",
  "[contenteditable='true']",
  "[contenteditable='plaintext-only']",
  "[role='textbox']",
  ".ProseMirror",
  "[data-testid='chat-input']",
  "#prompt-textarea",
].join(",");

function readComposeEl(el: HTMLElement): string {
  if (el instanceof HTMLTextAreaElement) return el.value;
  return (el.innerText || el.textContent || "").trim();
}

function gatherLargestCompose(): string {
  const nodes = [...document.querySelectorAll<HTMLElement>(COMPOSE_SELECTORS)].filter((e) => {
    if (e.getAttribute("aria-hidden") === "true") return false;
    const t = readComposeEl(e);
    return t.length > 0;
  });
  nodes.sort((a, b) => readComposeEl(b).length - readComposeEl(a).length);
  if (nodes[0]) return readComposeEl(nodes[0]);
  const active = document.activeElement;
  if (active instanceof HTMLElement) {
    const t = textFromTarget(active);
    if (t.trim()) return t;
  }
  return "";
}

function scanContent(text: string, onDone: (data: ScanData | null, err?: string) => void) {
  const trimmed = text.trim();
  if (trimmed.length < 8) return;
  const h = simpleHash(trimmed);
  if (h === lastTextHash && lastScan) {
    onDone(lastScan);
    return;
  }
  chrome.runtime.sendMessage(
    {
      type: "AIRLOCK_SCAN_TEXT",
      payload: {
        action_id: crypto.randomUUID(),
        source: "chrome-extension-proactive",
        destination_origin: location.origin,
        modality: "text",
        content: trimmed.slice(0, 120_000),
      },
    },
    (res) => {
      if (chrome.runtime.lastError || !res?.ok) {
        onDone(null, "API offline");
        return;
      }
      lastTextHash = h;
      lastScan = res.data as ScanData;
      onDone(lastScan);
    },
  );
}

function scheduleLiveScan(text: string) {
  if (!settings.liveDebounce) return;
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    scanContent(text, (data, err) => {
      updateShield(data, err);
      if (data && shouldBlock(data.decision)) showBlockModal(data);
    });
  }, 700);
}

function afterPasteScan(pasted: string) {
  const attempt = () => {
    const merged = [pasted, gatherLargestCompose()].filter(Boolean).join("\n").trim();
    const body = merged.length >= pasted.length ? merged : pasted;
    if (body.length < 8) return;
    scanContent(body, (data, err) => {
      updateShield(data, err);
      if (data && shouldBlock(data.decision)) showBlockModal(data);
      else if (data && data.decision === "warn") {
        showBlockModal({ ...data, decision: "warn" });
      }
    });
  };
  attempt();
  setTimeout(attempt, 80);
  setTimeout(attempt, 250);
}

function isComposeTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  if (target instanceof HTMLTextAreaElement) return true;
  if (target.isContentEditable) return true;
  if (target.closest(".ProseMirror, [role='textbox'], [data-testid*='composer'], [contenteditable]")) {
    return true;
  }
  return false;
}

function findSendButton(): HTMLElement | null {
  const buttons = [...document.querySelectorAll<HTMLElement>("button,[role='button']")];
  for (const btn of buttons) {
    if (isLikelySendButton(btn)) return btn;
  }
  return null;
}

function isLikelySendButton(el: HTMLElement): boolean {
  if (allowBypass) return false;
  const label = (
    el.getAttribute("aria-label") ||
    el.getAttribute("data-testid") ||
    el.getAttribute("title") ||
    el.textContent ||
    ""
  ).toLowerCase();
  if (
    label.includes("send") ||
    label.includes("submit") ||
    label.includes("message") ||
    label === "run"
  ) {
    return true;
  }
  if (el.closest('button[type="submit"], [data-airlock-guarded-send]')) return true;
  const prose = document.querySelector(".ProseMirror");
  if (prose) {
    const shell =
      prose.closest("[class*='composer'], [class*='input'], form, [data-testid*='chat']") ||
      prose.parentElement?.parentElement;
    if (shell?.contains(el) && el.tagName === "BUTTON" && !label.includes("attach") && !label.includes("upload")) {
      return true;
    }
  }
  return false;
}

function guardSend(trigger: "click" | "enter", proceed: () => void) {
  const text = gatherLargestCompose();
  if (text.trim().length < 8) {
    proceed();
    return;
  }
  updateShield(null, "scanning…");
  scanContent(text, (data, err) => {
    if (err || !data) {
      updateShield(null, err || "scan failed");
      proceed();
      return;
    }
    updateShield(data);
    if (shouldBlock(data.decision) || data.decision === "warn") {
      showBlockModal(data);
      return;
    }
    proceed();
  });
}

function shouldBlock(decision: string): boolean {
  if (!settings.blockOnSend) return false;
  return decision === "block" || decision === "require_review";
}

function showBlockModal(data: ScanData) {
  let modal = document.getElementById(MODAL_ID);
  if (!modal) {
    modal = document.createElement("div");
    modal.id = MODAL_ID;
    modal.setAttribute("role", "alertdialog");
    modal.style.cssText =
      "position:fixed;inset:0;z-index:2147483647;background:rgba(0,0,0,.55);display:flex;align-items:center;justify-content:center;font:14px system-ui;";
    document.documentElement.appendChild(modal);
  }
  const findings = (data.findings || [])
    .slice(0, 5)
    .map((f) => `<li><strong>${f.severity}</strong> ${f.category}: ${f.excerpt_redacted}</li>`)
    .join("");
  const title =
    data.decision === "warn"
      ? "AIRLOCK warning"
      : "AIRLOCK paused this send";
  const border =
    data.decision === "warn" ? "#d97706" : data.decision === "block" ? "#dc2626" : "#d97706";
  modal.innerHTML = `<div style="background:#15191f;color:#e8eaed;max-width:420px;padding:20px;border-radius:12px;border:1px solid ${border};">
    <h2 style="margin:0 0 8px;font-size:16px">${title}</h2>
    <p style="margin:0 0 12px;color:#9aa4b2">Decision: <strong>${data.decision}</strong>. Sensitive patterns were detected before content left this page.</p>
    <ul style="margin:0 0 16px;padding-left:18px;font-size:12px">${findings || "<li>Policy match</li>"}</ul>
    <button type="button" id="airlock-modal-dismiss" style="padding:8px 14px;border-radius:6px;border:1px solid #2a3441;background:#1a2332;color:#e8eaed;cursor:pointer">Dismiss</button>
    <button type="button" id="airlock-modal-force" style="margin-left:8px;padding:8px 14px;border-radius:6px;border:1px solid #7f1d1d;background:#450a0a;color:#fecaca;cursor:pointer">Send anyway (unsafe)</button>
  </div>`;
  modal.style.display = "flex";
  document.getElementById("airlock-modal-dismiss")!.addEventListener("click", () => {
    modal!.style.display = "none";
  });
  document.getElementById("airlock-modal-force")!.addEventListener("click", () => {
    modal!.style.display = "none";
    allowBypass = true;
    setTimeout(() => {
      allowBypass = false;
    }, 3000);
  });
}

function initProactive() {
  if (document.documentElement.dataset.airlockProactiveInit === "1") return;
  document.documentElement.dataset.airlockProactiveInit = "1";
  ensureShield();
  updateShield(null, "guard active");

    document.addEventListener(
      "input",
      (e) => {
        const t = textFromTarget(e.target) || gatherLargestCompose();
        if (t.trim().length >= 8) scheduleLiveScan(t);
      },
      true,
    );

    document.addEventListener(
      "paste",
      (e) => {
        if (!settings.scanOnPaste) return;
        const pasted = e.clipboardData?.getData("text/plain") ?? "";
        if (pasted.trim().length >= 8) afterPasteScan(pasted);
      },
      true,
    );

    document.addEventListener(
      "click",
      (e) => {
        if (allowBypass) return;
        const target = e.target;
        if (!(target instanceof HTMLElement)) return;
        const btn = target.closest("button,[role='button']") as HTMLElement | null;
        if (!btn || !isLikelySendButton(btn)) return;

        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();

        guardSend("click", () => {
          allowBypass = true;
          btn.click();
          setTimeout(() => {
            allowBypass = false;
          }, 800);
        });
      },
      true,
    );

    document.addEventListener(
      "keydown",
      (e) => {
        if (allowBypass || !settings.blockOnSend) return;
        if (e.key !== "Enter" || e.shiftKey) return;
        if (!isComposeTarget(e.target)) return;
        const text = gatherLargestCompose();
        if (text.trim().length < 8) return;

        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();

        guardSend("enter", () => {
          allowBypass = true;
          const btn = findSendButton();
          if (btn) btn.click();
          else if (e.target instanceof HTMLElement) {
            e.target.dispatchEvent(
              new KeyboardEvent("keydown", { key: "Enter", bubbles: true, cancelable: true }),
            );
          }
          setTimeout(() => {
            allowBypass = false;
          }, 800);
        });
      },
      true,
    );
}

function boot() {
  chrome.storage.sync.get(
    { proactive: false, blockOnSend: true, scanOnPaste: true, liveDebounce: true },
    (data) => {
      settings = settingsFromStorage(data);
      if (settings.proactive) initProactive();
      else {
        ensureShield();
        updateShield(null, "off — enable in extension popup");
      }
    },
  );
}

boot();

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type === "AIRLOCK_PING_GUARD") {
    sendResponse({
      ready: document.documentElement.dataset.airlockProactiveInit === "1",
      proactive: settings.proactive,
    });
    return true;
  }
  return undefined;
});

chrome.storage.onChanged.addListener((changes) => {
  if (changes.proactive || changes.blockOnSend || changes.scanOnPaste || changes.liveDebounce) {
    chrome.storage.sync.get(
      { proactive: false, blockOnSend: true, scanOnPaste: true, liveDebounce: true },
      (data) => {
        settings = settingsFromStorage(data);
        if (changes.proactive?.newValue && !document.documentElement.dataset.airlockProactiveInit) {
          initProactive();
        }
      },
    );
  }
});