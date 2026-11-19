import { useCallback, useEffect, useState } from "react";
import {
  redactText,
  scanImage,
  scanText,
  verifyText,
  type ScanDecision,
} from "./airlock";

function uuid(): string {
  return crypto.randomUUID();
}

export default function App() {
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [pending, setPending] = useState(false);
  const [modal, setModal] = useState<ScanDecision | null>(null);
  const [lastActionId, setLastActionId] = useState<string>("");
  const [log, setLog] = useState<{ count: number; items: unknown[] } | null>(
    null,
  );
  const [status, setStatus] = useState<string>("AIRLOCK: ready");

  const refreshLog = useCallback(async () => {
    const r = await fetch("/api/received");
    setLog(await r.json());
  }, []);

  useEffect(() => {
    refreshLog();
    const t = setInterval(refreshLog, 2000);
    return () => clearInterval(t);
  }, [refreshLog]);

  async function submitPayload(payload: {
    text: string;
    imageName?: string;
  }) {
    await fetch("/api/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    setStatus("Sent (receiver confirmed)");
    await refreshLog();
  }

  async function guardedSend() {
    const actionId = uuid();
    setLastActionId(actionId);
    setPending(true);
    setStatus("AIRLOCK: scanning...");
    try {
      let scan: ScanDecision;
      if (file) {
        scan = await scanImage(actionId, file);
        if (scan.decision === "allow" || scan.decision === "warn") {
          await submitPayload({
            text: text || "[image attachment]",
            imageName: file.name,
          });
          setPending(false);
          return;
        }
        setModal(scan);
        setPending(false);
        setStatus("AIRLOCK: review required (image)");
        return;
      }
      scan = await scanText(actionId, text);
      if (scan.decision === "allow" || scan.decision === "warn") {
        await submitPayload({ text });
        setPending(false);
        return;
      }
      if (scan.decision === "block") {
        setModal(scan);
        setStatus("AIRLOCK: blocked");
        setPending(false);
        return;
      }
      setModal(scan);
      setStatus("AIRLOCK: review required");
    } catch (e) {
      setStatus("AIRLOCK: scan unavailable - not sending");
      console.error(e);
    }
    setPending(false);
  }

  async function createSafeCopy() {
    if (!modal) return;
    const sanitized = await redactText(lastActionId, text, modal);
    const verified = await verifyText(lastActionId, sanitized);
    if (verified.decision === "allow" || verified.decision === "warn") {
      await submitPayload({ text: sanitized });
      setText(sanitized);
      setModal(null);
      setStatus("Sanitized copy sent");
    } else {
      setStatus("Sanitized copy still flagged");
    }
  }

  return (
    <div style={{ fontFamily: "system-ui", maxWidth: 720, margin: "2rem auto" }}>
      <h1>Local Demo Chat</h1>
      <p style={{ color: "#555" }}>
        Synthetic target for AIRLOCK. Receiver log proves what actually
        arrived.
      </p>
      <div
        style={{
          padding: "0.5rem 1rem",
          background: "#111",
          color: "#0f0",
          fontFamily: "monospace",
          fontSize: 12,
        }}
      >
        {status}
      </div>
      <textarea
        rows={8}
        style={{ width: "100%", marginTop: 16 }}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Paste synthetic code or message..."
      />
      <div style={{ marginTop: 8 }}>
        <input
          type="file"
          accept="image/*"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
      </div>
      <button
        type="button"
        style={{ marginTop: 12, padding: "8px 16px" }}
        disabled={pending || (!text && !file)}
        onClick={guardedSend}
      >
        {pending ? "Scanning..." : "Send"}
      </button>

      {modal && (
        <div
          style={{
            marginTop: 24,
            border: "1px solid #c00",
            padding: 16,
            background: "#fff5f5",
          }}
        >
          <h3>Review before send</h3>
          <p>Decision: {modal.decision}</p>
          <ul>
            {modal.findings.map((f) => (
              <li key={f.id}>
                <strong>{f.category}</strong> ({f.severity}):{" "}
                {f.excerpt_redacted}
              </li>
            ))}
          </ul>
          <button type="button" onClick={() => setModal(null)}>
            Cancel
          </button>{" "}
          <button type="button" onClick={createSafeCopy}>
            Create safe copy (text)
          </button>
        </div>
      )}

      <section style={{ marginTop: 32 }}>
        <h2>Server received log</h2>
        <p>Count: {log?.count ?? 0} (original blocked payload should not appear)</p>
        <pre style={{ background: "#f4f4f4", padding: 12, fontSize: 11 }}>
          {JSON.stringify(log?.items ?? [], null, 2)}
        </pre>
      </section>
    </div>
  );
}