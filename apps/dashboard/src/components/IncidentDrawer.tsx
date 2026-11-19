import { useCallback, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Copy, CheckCircle2, XCircle } from "lucide-react";
import { fetchIncident, triageIncident } from "../api";
import { formatDateTime, severityTone, transmissionLabel } from "../lib/incidents";
import { useToast } from "../context/ToastContext";
import { usePrefersReducedMotion } from "../hooks/usePrefersReducedMotion";

export function IncidentDrawer({
  incidentId,
  onClose,
}: {
  incidentId: string | null;
  onClose: () => void;
}) {
  const reduced = usePrefersReducedMotion();
  const { push } = useToast();
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const reload = useCallback(() => {
    if (!incidentId) return;
    setLoading(true);
    fetchIncident(incidentId)
      .then(setDetail)
      .catch(() => push("Failed to load incident", "error"))
      .finally(() => setLoading(false));
  }, [incidentId, push]);

  useEffect(() => {
    if (incidentId) reload();
    else setDetail(null);
  }, [incidentId, reload]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && incidentId) onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [incidentId, onClose]);

  const findings = (detail?.findings as Array<Record<string, string>>) ?? [];
  const steps = (detail?.event_steps as Array<Record<string, string>>) ?? [];

  const copyId = async () => {
    if (!incidentId) return;
    try {
      await navigator.clipboard.writeText(incidentId);
      setCopied(true);
      push("Incident ID copied", "success");
      setTimeout(() => setCopied(false), 1500);
    } catch {
      push("Could not copy ID", "error");
    }
  };

  return (
    <AnimatePresence>
      {incidentId ? (
        <>
          <motion.button
            type="button"
            className="drawer-backdrop"
            aria-label="Close incident panel"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          <motion.aside
            className="incident-drawer"
            role="dialog"
            aria-modal="true"
            aria-label="Incident details"
            initial={reduced ? false : { x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
          >
            <header className="drawer-header">
              <div>
                <p className="drawer-eyebrow">Incident</p>
                <h2 className="drawer-title">{String(detail?.title ?? incidentId)}</h2>
              </div>
              <div className="drawer-actions">
                <button type="button" className="icon-btn" onClick={copyId} title="Copy incident ID">
                  {copied ? <CheckCircle2 size={16} /> : <Copy size={16} />}
                </button>
                <button type="button" className="icon-btn" onClick={onClose} title="Close">
                  <X size={18} />
                </button>
              </div>
            </header>

            {loading && !detail ? (
              <div className="drawer-body skeleton-wrap">
                <div className="skeleton skeleton-line" />
                <div className="skeleton skeleton-line short" />
                <div className="skeleton skeleton-block" />
              </div>
            ) : detail ? (
              <div className="drawer-body">
                {detail.summary_redacted ? (
                  <p className="drawer-summary">{String(detail.summary_redacted)}</p>
                ) : null}
                <dl className="meta-dl">
                  <div className="meta-pair">
                    <dt>Transmission</dt>
                    <dd>{transmissionLabel(String(detail.transmission_status))}</dd>
                  </div>
                  <div className="meta-pair">
                    <dt>Decision</dt>
                    <dd>{String(detail.decision)}</dd>
                  </div>
                  <div className="meta-pair">
                    <dt>Review</dt>
                    <dd>{String(detail.review_status)}</dd>
                  </div>
                  <div className="meta-pair">
                    <dt>Observed</dt>
                    <dd className="mono">{formatDateTime(String(detail.observed_at))}</dd>
                  </div>
                </dl>

                <h3 className="drawer-section-title">Findings (redacted)</h3>
                {findings.length === 0 ? (
                  <p className="muted">No findings recorded.</p>
                ) : (
                  <ul className="finding-list">
                    {findings.map((f) => (
                      <li key={f.id} className="card finding-card">
                        <span className={`pill pill-${severityTone(f.severity)}`}>{f.severity}</span>
                        <p className="finding-cat mono">{f.category}</p>
                        <p className="finding-excerpt">{f.excerpt_redacted}</p>
                        {f.explanation_redacted ? (
                          <p className="muted small">{f.explanation_redacted}</p>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                )}

                <h3 className="drawer-section-title">Timeline</h3>
                <ol className="timeline">
                  {steps.map((s, idx) => (
                    <li key={idx}>
                      <span className="mono muted">{s.occurred_at}</span>
                      <span>{s.step}</span>
                    </li>
                  ))}
                </ol>

                <motion.div className="drawer-footer-actions">
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() =>
                      triageIncident(incidentId, "resolved").then(() => {
                        push("Marked resolved", "success");
                        reload();
                      })
                    }
                  >
                    <CheckCircle2 size={16} />
                    Resolve
                  </button>
                  <button
                    type="button"
                    className="btn btn-ghost"
                    onClick={() =>
                      triageIncident(incidentId, "false_positive").then(() => {
                        push("Marked false positive", "success");
                        reload();
                      })
                    }
                  >
                    <XCircle size={16} />
                    False positive
                  </button>
                </motion.div>
              </div>
            ) : null}
          </motion.aside>
        </>
      ) : null}
    </AnimatePresence>
  );
}