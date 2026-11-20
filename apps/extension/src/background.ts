const API = "http://127.0.0.1:8765/api/v1";
const TOKEN = "dev-local-token";
const PROACTIVE_SCRIPT_ID = "airlock-proactive";

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "airlock-scan-selection",
    title: "AIRLOCK: scan selection",
    contexts: ["selection"],
  });
  void syncProactiveRegistration();
});

chrome.storage.onChanged.addListener((changes, area) => {
  if (area === "sync" && changes.proactive) {
    void syncProactiveRegistration();
  }
});

chrome.runtime.onStartup.addListener(() => {
  void syncProactiveRegistration();
});

chrome.tabs.onUpdated.addListener((tabId, info) => {
  if (info.status !== "complete") return;
  void maybeInjectTab(tabId);
});

async function maybeInjectTab(tabId: number) {
  const { proactive } = await chrome.storage.sync.get({ proactive: false });
  if (!proactive) return;
  try {
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ["proactive.js"],
    });
  } catch {
    /* chrome:// etc. */
  }
}

async function injectProactiveIntoOpenTabs() {
  const tabs = await chrome.tabs.query({ url: ["http://*/*", "https://*/*"] });
  for (const tab of tabs) {
    if (!tab.id) continue;
    try {
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ["proactive.js"],
      });
    } catch {
      /* restricted pages */
    }
  }
}

async function syncProactiveRegistration() {
  const { proactive } = await chrome.storage.sync.get({ proactive: false });
  try {
    const registered = await chrome.scripting.getRegisteredContentScripts();
    const has = registered.some((s) => s.id === PROACTIVE_SCRIPT_ID);
    if (proactive && !has) {
      await chrome.scripting.registerContentScripts([
        {
          id: PROACTIVE_SCRIPT_ID,
          js: ["proactive.js"],
          matches: ["<all_urls>"],
          runAt: "document_idle",
          persist: true,
        },
      ]);
    }
    if (!proactive && has) {
      await chrome.scripting.unregisterContentScripts({ ids: [PROACTIVE_SCRIPT_ID] });
    }
  } catch (e) {
    console.warn("AIRLOCK proactive registration", e);
  }
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type === "AIRLOCK_ENABLE_PROACTIVE") {
    (async () => {
      const ok = await chrome.permissions.request({ origins: ["<all_urls>"] });
      if (!ok) {
        sendResponse({ ok: false, error: "Permission denied" });
        return;
      }
      await chrome.storage.sync.set({ proactive: true });
      await syncProactiveRegistration();
      await injectProactiveIntoOpenTabs();
      sendResponse({ ok: true });
    })();
    return true;
  }
  if (msg.type === "AIRLOCK_DISABLE_PROACTIVE") {
    (async () => {
      await chrome.storage.sync.set({ proactive: false });
      await syncProactiveRegistration();
      sendResponse({ ok: true });
    })();
    return true;
  }
  if (msg.type === "AIRLOCK_SCAN_TEXT") {
    (async () => {
      try {
        const r = await fetch(`${API}/scans/text`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${TOKEN}`,
          },
          body: JSON.stringify(msg.payload),
        });
        const data = await r.json();
        if (!r.ok) {
          sendResponse({ ok: false, error: JSON.stringify(data) });
          return;
        }
        const tabId = _sender.tab?.id;
        if (tabId) {
          await chrome.action.setBadgeText({ tabId, text: badgeForDecision(data.decision) });
          await chrome.action.setBadgeBackgroundColor({
            tabId,
            color: data.decision === "block" ? "#7f1d1d" : "#1f6b50",
          });
        }
        sendResponse({ ok: true, data });
      } catch (e) {
        sendResponse({ ok: false, error: String(e) });
      }
    })();
    return true;
  }
  return undefined;
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId !== "airlock-scan-selection" || !info.selectionText?.trim()) return;
  void scanText(info.selectionText, tab?.id, tab?.url);
});

async function scanText(content: string, tabId?: number, pageOrigin?: string) {
  const payload = {
    action_id: crypto.randomUUID(),
    source: "chrome-extension",
    destination_origin: pageOrigin || "http://127.0.0.1:5173",
    modality: "text",
    content,
  };
  try {
    const r = await fetch(`${API}/scans/text`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${TOKEN}`,
      },
      body: JSON.stringify(payload),
    });
    const data = await r.json();
    if (tabId) {
      await chrome.action.setBadgeText({ tabId, text: badgeForDecision(data.decision) });
    }
  } catch {
    if (tabId) await chrome.action.setBadgeText({ tabId, text: "!" });
  }
}

function badgeForDecision(decision: string): string {
  if (decision === "allow") return "OK";
  if (decision === "warn") return "!";
  if (decision === "require_review") return "RV";
  if (decision === "block") return "BL";
  return "?";
}