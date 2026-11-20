import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ImagePlus, Send, ShieldAlert } from "lucide-react";
import { Link } from "react-router-dom";
import {
  redactImage,
  redactText,
  scanImage,
  scanText,
  verifyText,
  type ScanDecision,
} from "../lib/airlock";
import { severityTone } from "../lib/incidents";

function uuid(): string {
  return crypto.randomUUID();
}

type ReceiverLog = { count: number; items: unknown[] };

export function DemoChatPage() {
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [pending, setPending] = useState(false);
  const [modal, setModal] = useState<ScanDecision | null>(null);
  const [lastActionId, setLastActionId] = useState("");
  const [log, setLog] = useState<ReceiverLog | null>(null);
  const [status, setStatus] = useState("AIRLOCK: ready");

  const refreshLog = useCallback(async () => {
    const r = await fetch("/api/received");
    setLog(await r.json());
  }, []);

  useEffect(() => {
    refreshLog();
    const t = setInterval(refreshLog, 2000);
    return () => clearInterval(t);
  }, [refreshLog]);

  async function submitPayload(payload: { text: string; imageName?: string }) {
    await fetch("/api/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    setStatus("Sent — receiver confirmed");
    await refreshLog();
  }

  async function guardedSend() {
    const actionId = uuid();
    setLastActionId(actionId);
    setPending(true);
    setStatus("AIRLOCK: scanning…");
    try {
      let scan: ScanDecision;
      if (file) {
        scan = await scanImage(actionId, file);
        if (scan.decision === "allow" || scan.decision === "warn") {
          await submitPayload({ text: text || "[image attachment]", imageName: file.name });
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
      setStatus("AIRLOCK: scan unavailable — not sending");
      console.error(e);
    }
    setPending(false);
  }

  async function createSafeCopy() {
    if (!modal) return;
    try {
    if (file) {
      const blob = await redactImage(lastActionId, file, modal);
      const sanitizedFile = new File([blob], file.name.replace(/\.\w+$/, "") + "-safe.png", {
        type: "image/png",
      });
      const verified = await scanImage(lastActionId, sanitizedFile);
      if (verified.decision === "allow" || verified.decision === "warn") {
        await submitPayload({
          text: text || "[sanitized image]",
          imageName: sanitizedFile.name,
        });
        setFile(sanitizedFile);
        setModal(null);
        setStatus("Sanitized image sent");
      } else {
        setStatus("Sanitized image still flagged");
      }
      return;
    }
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
    } catch (e) {
      setStatus("Redaction failed");
      console.error(e);
    }
  }

  return (
    <motion.div className="page-stack chat-page" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <section className="card">
        <p className="card-sub">
          Controlled mock chat with pre-submit AIRLOCK scans. The receiver log below shows only
          what actually reached the fake endpoint. New incidents appear in{" "}
          <Link to="/incidents" className="text-link">
            Incidents
          </Link>{" "}
          and{" "}
          <Link to="/" className="text-link">
            Overview
          </Link>
          .
        </p>
        <div className="chat-status mono" role="status">
          {status}
        </div>
      </section>

      <motion.div className="chat-layout">
        <section className="card">
          <h2 className="card-title">Compose</h2>
          <label className="field">
            <span className="field-label">Message</span>
            <textarea
              id="airlock-compose"
              className="input"
              rows={8}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste synthetic code or message…"
            />
          </label>
          <label className="field file-field">
            <span className="field-label">Attachment</span>
            <div className="file-row">
              <ImagePlus size={16} aria-hidden />
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
              {file ? <span className="muted small">{file.name}</span> : null}
            </div>
          </label>
          <button
            type="button"
            className="btn btn-primary"
            data-airlock-guarded-send
            disabled={pending || (!text && !file)}
            onClick={guardedSend}
          >
            <Send size={16} aria-hidden />
            {pending ? "Scanning…" : "Send"}
          </button>
        </section>

        <section className="card">
          <h2 className="card-title">Receiver log</h2>
          <p className="card-sub">
            Count: {log?.count ?? 0} — blocked originals should not appear here.
          </p>
          <pre className="receiver-pre mono">{JSON.stringify(log?.items ?? [], null, 2)}</pre>
        </section>
      </motion.div>

      {modal ? (
        <section className="card review-card" role="dialog" aria-label="Review before send">
          <div className="review-head">
            <ShieldAlert size={18} className="text-amber" />
            <h2 className="card-title">Review before send</h2>
          </div>
          <p className="mono muted">Decision: {modal.decision}</p>
          <ul className="finding-list">
            {modal.findings.map((f) => (
              <li key={f.id} className="card finding-card">
                <span className={`pill pill-${severityTone(f.severity)}`}>{f.severity}</span>
                <p className="finding-cat mono">{f.category}</p>
                <p className="finding-excerpt">{f.excerpt_redacted}</p>
              </li>
            ))}
          </ul>
          <div className="drawer-footer-actions">
            <button type="button" className="btn btn-ghost" onClick={() => setModal(null)}>
              Cancel
            </button>
            <button type="button" className="btn btn-primary" onClick={createSafeCopy}>
              Create safe copy
            </button>
          </div>
        </section>
      ) : null}
    </motion.div>
  );
}