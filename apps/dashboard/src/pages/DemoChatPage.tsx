import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { FileUp, Send, ShieldAlert } from "lucide-react";
import { Link } from "react-router-dom";
import {
  redactImage,
  redactText,
  scanFile,
  scanImage,
  scanText,
  verifyText,
  type ScanDecision,
  ScanError,
} from "../lib/airlock";
import { severityTone } from "../lib/incidents";

function uuid(): string {
  return crypto.randomUUID();
}

type ReceiverLog = { count: number; items: unknown[] };

const ATTACH_ACCEPT =
  "image/*,.pdf,.txt,.md,.json,.csv,.log,.mp3,.wav,.m4a,.ogg,.mp4,.webm,.mov,.py,.js,.ts,.env,.yaml,.yml";

function looksLikeCode(content: string): boolean {
  if (!content.trim()) return false;
  return (
    /^\s*(import |from |def |class |const |let |var |#include |package )/m.test(content) ||
    /PAYMENT_API_KEY|sk_live_|sk_test_|postgresql:\/\//.test(content)
  );
}

function fileModalityLabel(scan: ScanDecision | null, file: File | null): string {
  if (scan?.modality) return scan.modality;
  if (!file) return "text";
  const n = file.name.toLowerCase();
  if (/\.(png|jpe?g|webp|gif)$/.test(n)) return "image";
  if (n.endsWith(".pdf")) return "document";
  if (/\.(mp3|wav|m4a|ogg)$/.test(n)) return "audio";
  if (/\.(mp4|webm|mov)$/.test(n)) return "video";
  if (/\.(py|js|ts|env)$/.test(n)) return "code";
  return "document";
}

export function DemoChatPage() {
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [pending, setPending] = useState(false);
  const [modal, setModal] = useState<ScanDecision | null>(null);
  const [lastActionId, setLastActionId] = useState("");
  const [log, setLog] = useState<ReceiverLog | null>(null);
  const [lastScan, setLastScan] = useState<ScanDecision | null>(null);
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

  async function submitPayload(payload: {
    text: string;
    imageName?: string;
    attachmentName?: string;
    modality?: string;
  }) {
    await fetch("/api/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    setStatus("Sent — receiver confirmed");
    await refreshLog();
  }

  async function finishAllowed(
    scan: ScanDecision,
    payload: { text: string; imageName?: string; attachmentName?: string; modality?: string },
  ) {
    void scan;
    await submitPayload(payload);
  }

  async function guardedSend() {
    const actionId = uuid();
    setLastActionId(actionId);
    setPending(true);
    setStatus("AIRLOCK: scanning…");
    setModal(null);
    try {
      let scan: ScanDecision;

      if (file) {
        scan = await scanFile(actionId, file);
        setLastScan(scan);
        const mod = scan.modality ?? fileModalityLabel(scan, file);
        if (scan.decision === "block") {
          setModal(scan);
          setPending(false);
          setStatus(`AIRLOCK: blocked (${mod}) — not sending`);
          return;
        }
        if (scan.decision === "require_review") {
          setModal(scan);
          setPending(false);
          setStatus(`AIRLOCK: review required (${mod}) — not sending`);
          return;
        }
        if (scan.decision === "allow" || scan.decision === "warn") {
          await finishAllowed(scan, {
            text: text || `[${mod} attachment: ${file.name}]`,
            attachmentName: file.name,
            modality: mod,
            ...(mod === "image" ? { imageName: file.name } : {}),
          });
          setPending(false);
          setStatus(
            scan.findings.length
              ? `Sent (${scan.decision}) with ${scan.findings.length} noted finding(s)`
              : `Sent — scan reported allow (${mod}, 0 findings)`,
          );
          return;
        }
        setModal(scan);
        setPending(false);
        setStatus(`AIRLOCK: ${scan.decision} (${mod})`);
        return;
      }

      if (!text.trim()) {
        setStatus("AIRLOCK: add a message or attachment");
        setPending(false);
        return;
      }

      const modality = looksLikeCode(text) ? "code" : "text";
      scan = await scanText(actionId, text, modality);
      setLastScan(scan);
      if (scan.decision === "allow" || scan.decision === "warn") {
        await finishAllowed(scan, { text, modality });
        setPending(false);
        return;
      }
      if (scan.decision === "block") {
        setModal({ ...scan, modality });
        setStatus("AIRLOCK: blocked");
        setPending(false);
        return;
      }
      setModal({ ...scan, modality });
      setStatus("AIRLOCK: review required");
    } catch (e) {
      if (e instanceof ScanError) {
        if (e.code === "FILE_TOO_LARGE") {
          setStatus("AIRLOCK: file too large (max 25MB) — not sending");
        } else if (e.code === "CLIENT_TIMEOUT") {
          setStatus(`AIRLOCK: scan timed out — not sending (${e.message})`);
        } else if (e.code === "BACKEND_UNAVAILABLE") {
          setStatus(`AIRLOCK: API unreachable — not sending (${e.message})`);
        } else if (e.code === "UNAUTHORIZED") {
          setStatus("AIRLOCK: API auth failed — check AIRLOCK_LOCAL_TOKEN");
        } else {
          setStatus(`AIRLOCK: scan failed (${e.code}) — not sending`);
        }
      } else {
        setStatus("AIRLOCK: scan unavailable — not sending");
      }
      console.error(e);
    }
    setPending(false);
  }

  async function createSafeCopy() {
    if (!modal) return;
    const mod = fileModalityLabel(modal, file);
    try {
      if (file && mod === "image") {
        const blob = await redactImage(lastActionId, file, modal);
        const sanitizedFile = new File([blob], file.name.replace(/\.\w+$/, "") + "-safe.png", {
          type: "image/png",
        });
        const verified = await scanImage(lastActionId, sanitizedFile);
        if (verified.decision === "allow" || verified.decision === "warn") {
          await submitPayload({
            text: text || "[sanitized image]",
            imageName: sanitizedFile.name,
            attachmentName: sanitizedFile.name,
            modality: "image",
          });
          setFile(sanitizedFile);
          setModal(null);
          setStatus("Sanitized image sent");
        } else {
          setStatus("Sanitized image still flagged");
        }
        return;
      }

      const sourceText =
        modal.extracted_text ??
        (file && mod !== "image" ? await file.text().catch(() => text) : text);

      const redactMod =
        mod === "image" ? "text" : (mod as "text" | "code" | "document" | "audio" | "video");

      const sanitized = await redactText(lastActionId, sourceText, modal, redactMod);
      const verified = await verifyText(lastActionId, sanitized);
      if (verified.decision === "allow" || verified.decision === "warn") {
        await submitPayload({
          text: sanitized,
          attachmentName: file?.name,
          modality: mod,
        });
        setText(sanitized);
        setModal(null);
        setStatus(`Sanitized ${mod} sent`);
      } else {
        setStatus("Sanitized copy still flagged");
      }
    } catch (e) {
      setStatus("Redaction failed");
      console.error(e);
    }
  }

  const pendingModality = file ? fileModalityLabel(null, file) : looksLikeCode(text) ? "code" : "text";

  return (
    <motion.div className="page-stack chat-page" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <section className="card">
        <p className="card-sub">
          Multimodal pre-send security gate: scan <strong>text, code, image, document, audio, or
          video</strong> before anything hits the mock receiver. Inspector Q&amp;A is separate; this
          page is the outbound protection story. Incidents log in{" "}
          <Link to="/incidents" className="text-link">
            Incidents
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
            <span className="field-label">Message (text or code)</span>
            <textarea
              id="airlock-compose"
              className="input"
              rows={8}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste message or Python/config…"
            />
          </label>
          <label className="field file-field">
            <span className="field-label">
              Attachment{" "}
              {file ? (
                <span className={`pill pill-low mono`}>{pendingModality}</span>
              ) : (
                <span className="muted small">optional — PDF, image, audio, video, code file</span>
              )}
            </span>
            <div className="file-row">
              <FileUp size={16} aria-hidden />
              <input
                type="file"
                accept={ATTACH_ACCEPT}
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
              {file ? <span className="muted small">{file.name}</span> : null}
            </div>
          </label>
          <button
            type="button"
            className="btn btn-primary"
            data-airlock-guarded-send
            disabled={pending || (!text.trim() && !file)}
            onClick={guardedSend}
          >
            <Send size={16} aria-hidden />
            {pending ? "Scanning…" : "Send"}
          </button>
        </section>

        <section className="card">
          <h2 className="card-title">Scan result</h2>
          <p className="card-sub">
            Latest local scan (stays on this machine). Blocked sends never reach the receiver log
            below.
          </p>
          {lastScan ? (
            <>
              <p className="mono">
                <strong>Decision:</strong> {lastScan.decision}
                {lastScan.modality ? ` · ${lastScan.modality}` : ""}
                {lastScan.filename ? ` · ${lastScan.filename}` : ""}
                {lastScan.scan_id ? (
                  <>
                    {" "}
                    ·{" "}
                    <Link to="/incidents" className="text-link">
                      incident log
                    </Link>
                  </>
                ) : null}
              </p>
              {lastScan.findings.length === 0 ? (
                <p className="muted small">No policy findings (outbound allow).</p>
              ) : (
                <ul className="finding-list">
                  {lastScan.findings.slice(0, 6).map((f) => (
                    <li key={f.id} className="finding-card">
                      <span className={`pill pill-${severityTone(f.severity)}`}>{f.severity}</span>
                      <p className="finding-cat mono">{f.category}</p>
                      <p className="finding-excerpt">{f.excerpt_redacted}</p>
                    </li>
                  ))}
                </ul>
              )}
            </>
          ) : (
            <p className="muted small">Run Send to scan; results appear here.</p>
          )}

          <h2 className="card-title" style={{ marginTop: "1.25rem" }}>
            Receiver log
          </h2>
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
          <p className="mono muted">
            Decision: {modal.decision}
            {modal.modality || file ? ` · modality: ${fileModalityLabel(modal, file)}` : ""}
            {modal.filename ? ` · ${modal.filename}` : file ? ` · ${file.name}` : ""}
          </p>
          {modal.extracted_text ? (
            <details className="muted small">
              <summary>Extracted content preview (local only)</summary>
              <pre className="receiver-pre mono" style={{ maxHeight: "8rem", overflow: "auto" }}>
                {modal.extracted_text.slice(0, 2000)}
              </pre>
            </details>
          ) : null}
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