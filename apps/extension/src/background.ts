const API = "http://127.0.0.1:8765/api/v1";
const TOKEN = "dev-local-token";

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type !== "AIRLOCK_SCAN_TEXT") return;
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
      sendResponse({ ok: true, data: await r.json() });
    } catch (e) {
      sendResponse({ ok: false, error: String(e) });
    }
  })();
  return true;
});