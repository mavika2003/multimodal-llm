const statusEl = document.getElementById("status")!;
const decisionEl = document.getElementById("decision")!;
const detailEl = document.getElementById("detail")!;
const proactiveEl = document.getElementById("proactive") as HTMLInputElement;
const blockEl = document.getElementById("blockOnSend") as HTMLInputElement;
const pasteEl = document.getElementById("scanOnPaste") as HTMLInputElement;
const liveEl = document.getElementById("liveDebounce") as HTMLInputElement;

async function health() {
  try {
    const r = await fetch("http://127.0.0.1:8765/api/v1/health");
    const data = await r.json();
    statusEl.textContent = data.status === "ok" ? "API OK on :8765" : "API reported issues";
  } catch {
    statusEl.textContent = "Start API: make api (port 8765)";
  }
}

function showScan(data: { decision?: string; findings?: unknown[] }) {
  decisionEl.textContent = `Decision: ${data.decision ?? "unknown"}`;
  detailEl.textContent = JSON.stringify(data.findings ?? [], null, 2);
}

function loadSettings() {
  chrome.storage.sync.get(
    {
      proactive: false,
      blockOnSend: true,
      scanOnPaste: true,
      liveDebounce: true,
    },
    (data) => {
      proactiveEl.checked = Boolean(data.proactive);
      blockEl.checked = data.blockOnSend !== false;
      pasteEl.checked = data.scanOnPaste !== false;
      liveEl.checked = data.liveDebounce !== false;
    },
  );
}

document.getElementById("save-settings")!.addEventListener("click", () => {
  const next = {
    proactive: proactiveEl.checked,
    blockOnSend: blockEl.checked,
    scanOnPaste: pasteEl.checked,
    liveDebounce: liveEl.checked,
  };
  if (next.proactive) {
    chrome.runtime.sendMessage({ type: "AIRLOCK_ENABLE_PROACTIVE" }, (res) => {
      if (!res?.ok) {
        statusEl.textContent = res?.error || "Could not enable all-sites access";
        proactiveEl.checked = false;
        return;
      }
      chrome.storage.sync.set(next, () => {
        statusEl.textContent =
          "Proactive guard enabled. Refresh this tab once if the shield does not appear.";
      });
    });
  } else {
    chrome.storage.sync.set(next, () => {
      chrome.runtime.sendMessage({ type: "AIRLOCK_DISABLE_PROACTIVE" }, () => {
        statusEl.textContent = "Proactive guard off (manual scan still works)";
      });
    });
  }
});

async function pingGuard(tabId: number) {
  try {
    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId },
      func: () =>
        new Promise((resolve) => {
          chrome.runtime.sendMessage({ type: "AIRLOCK_PING_GUARD" }, (r) => resolve(r));
        }),
    });
    return result as { ready?: boolean; proactive?: boolean } | undefined;
  } catch {
    return undefined;
  }
}

document.getElementById("scan-compose")!.addEventListener("click", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) return;
  const guard = await pingGuard(tab.id);
  if (!guard?.ready) {
    statusEl.textContent =
      "Guard not active on this tab — Save settings, then refresh the page (Cmd+Shift+R).";
  }
  const [{ result }] = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => {
      const el = document.activeElement;
      if (el instanceof HTMLTextAreaElement) return el.value;
      if (el instanceof HTMLElement && el.isContentEditable) return el.innerText;
      const areas = [...document.querySelectorAll("textarea")];
      areas.sort(
        (a, b) =>
          (b as HTMLTextAreaElement).value.length - (a as HTMLTextAreaElement).value.length,
      );
      return areas[0] ? (areas[0] as HTMLTextAreaElement).value : "";
    },
  });
  const text = String(result ?? "");
  if (!text.trim()) {
    decisionEl.textContent = "No compose field found on this tab.";
    return;
  }
  chrome.runtime.sendMessage(
    {
      type: "AIRLOCK_SCAN_TEXT",
      payload: composePayload(text, tab.url),
    },
    (res) => {
      if (res?.ok) showScan(res.data);
      else decisionEl.textContent = res?.error ?? "Scan failed";
    },
  );
});

document.getElementById("scan-selection")!.addEventListener("click", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) return;
  const [{ result }] = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => window.getSelection()?.toString() ?? "",
  });
  const text = String(result ?? "");
  if (!text.trim()) {
    decisionEl.textContent = "Select text on the page first.";
    return;
  }
  chrome.runtime.sendMessage(
    {
      type: "AIRLOCK_SCAN_TEXT",
      payload: composePayload(text, tab.url),
    },
    (res) => {
      if (res?.ok) showScan(res.data);
      else decisionEl.textContent = res?.error ?? "Scan failed";
    },
  );
});

function composePayload(content: string, tabUrl?: string) {
  let origin = "http://127.0.0.1:5173";
  try {
    if (tabUrl) origin = new URL(tabUrl).origin;
  } catch {
    /* ignore */
  }
  return {
    action_id: crypto.randomUUID(),
    source: "chrome-extension",
    destination_origin: origin,
    modality: "text",
    content,
  };
}

loadSettings();
void health();