import { useMemo, useState } from "react";
import { useSearchParams, useOutletContext } from "react-router-dom";
import { motion } from "framer-motion";
import { Search } from "lucide-react";
import { useDashboardPoll } from "../hooks/useDashboardPoll";
import { formatDateTime, severityTone, transmissionLabel } from "../lib/incidents";
import type { OutletContext } from "../layout/AppShell";

export function IncidentsPage() {
  const { incidents } = useDashboardPoll();
  const { openIncident } = useOutletContext<OutletContext>();
  const [, setParams] = useSearchParams();
  const [q, setQ] = useState("");
  const [severity, setSeverity] = useState("all");
  const [modality, setModality] = useState("all");
  const [review, setReview] = useState("all");

  const modalities = useMemo(
    () => [...new Set(incidents.map((i) => i.modality).filter(Boolean))].sort(),
    [incidents],
  );

  const filtered = useMemo(() => {
    return incidents.filter((i) => {
      if (severity !== "all" && severityTone(i.severity) !== severity) return false;
      if (modality !== "all" && i.modality !== modality) return false;
      if (review !== "all" && i.review_status !== review) return false;
      if (!q.trim()) return true;
      const hay = `${i.id} ${i.title} ${i.decision}`.toLowerCase();
      return hay.includes(q.trim().toLowerCase());
    });
  }, [incidents, q, severity, modality, review]);

  const open = (id: string) => {
    openIncident(id);
    setParams({ incident: id });
  };

  return (
    <motion.div className="page-stack" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <section className="card filters-card">
        <div className="filters-row">
          <label className="search-field">
            <Search size={16} aria-hidden />
            <input
              type="search"
              placeholder="Search ID, title, decision…"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              aria-label="Search incidents"
            />
          </label>
          <select value={severity} onChange={(e) => setSeverity(e.target.value)} aria-label="Severity">
            <option value="all">All severities</option>
            <option value="critical">Critical / high</option>
            <option value="warning">Medium</option>
            <option value="low">Low</option>
          </select>
          <select value={modality} onChange={(e) => setModality(e.target.value)} aria-label="Modality">
            <option value="all">All modalities</option>
            {modalities.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
          <select value={review} onChange={(e) => setReview(e.target.value)} aria-label="Review status">
            <option value="all">All review states</option>
            <option value="open">open</option>
            <option value="resolved">resolved</option>
            <option value="false_positive">false_positive</option>
          </select>
        </div>
      </section>

      <section className="card">
        <p className="card-sub">{filtered.length} incident(s) from local API</p>
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Time</th>
                <th>Modality</th>
                <th>Severity</th>
                <th>Transmission</th>
                <th>Review</th>
                <th>Title</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((i) => (
                <tr
                  key={i.id}
                  className="row-clickable"
                  tabIndex={0}
                  onClick={() => open(i.id)}
                  onKeyDown={(e) => e.key === "Enter" && open(i.id)}
                >
                  <td className="mono text-link">{i.id}</td>
                  <td className="mono muted">{formatDateTime(i.observed_at)}</td>
                  <td>
                    <span className="chip">{i.modality}</span>
                  </td>
                  <td>
                    <span className={`pill pill-${severityTone(i.severity)}`}>{i.severity}</span>
                  </td>
                  <td>{transmissionLabel(i.transmission_status)}</td>
                  <td>{i.review_status}</td>
                  <td>{i.title}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </motion.div>
  );
}