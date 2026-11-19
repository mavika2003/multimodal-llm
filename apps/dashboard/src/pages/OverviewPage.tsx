import { Link, useOutletContext, useSearchParams } from "react-router-dom";
import { Shield, AlertTriangle, ShieldOff, ClipboardList, Server } from "lucide-react";
import { motion } from "framer-motion";
import { KpiCard } from "../components/KpiCard";
import { ActivityFeed } from "../components/ActivityFeed";
import { BarChart } from "../components/BarChart";
import { useDashboardPoll } from "../hooks/useDashboardPoll";
import { countPotentialRisks, groupIncidentsByDay } from "../lib/incidents";
import type { OutletContext } from "../layout/AppShell";

export function OverviewPage() {
  const { health, stats, incidents, error, loading } = useDashboardPoll();
  const { openIncident } = useOutletContext<OutletContext>();
  const [, setParams] = useSearchParams();

  const open = (id: string) => {
    openIncident(id);
    setParams({ incident: id });
  };

  const ollamaUp = Boolean(health?.ollama_reachable);
  const byModality = stats?.by_modality ?? {};
  const modalityData = Object.entries(byModality).map(([label, count]) => ({ label, count }));
  const timeline = groupIncidentsByDay(incidents);

  return (
    <motion.div
      className="page-stack"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
    >
      <div className="status-banner card">
        <div>
          <p className="status-banner-label">Protection status</p>
          <p className="status-banner-value">
            {error ? "API offline" : "Active on this device"}
          </p>
        </div>
        <motion.div>
          <p className="status-banner-label">Local runtime</p>
          <p className={`status-banner-value ${ollamaUp ? "text-emerald" : "text-amber"}`}>
            {loading ? "Checking…" : ollamaUp ? "Ollama reachable" : "Rules-only fallback"}
          </p>
        </motion.div>
      </div>

      {error ? (
        <motion.div className="card card-error" role="alert">
          {error}. Start the API with <code className="mono">./scripts/run_dev.sh</code>.
        </motion.div>
      ) : null}

      <section className="kpi-grid" aria-label="Key metrics">
        <KpiCard
          label="Actions scanned"
          value={stats?.actions_scanned ?? 0}
          description="Total incidents recorded in local SQLite"
          icon={Shield}
          accent="blue"
          delay={0}
        />
        <KpiCard
          label="Potential risks detected"
          value={countPotentialRisks(incidents)}
          description="Events with elevated severity or review decision"
          icon={AlertTriangle}
          accent="amber"
          delay={0.04}
        />
        <KpiCard
          label="Prevented sharing actions"
          value={stats?.prevented ?? 0}
          description="Verified pauses before transmission"
          icon={ShieldOff}
          accent="emerald"
          delay={0.08}
        />
        <KpiCard
          label="Incidents needing review"
          value={stats?.review_required ?? 0}
          description="Open items awaiting triage"
          icon={ClipboardList}
          accent="coral"
          delay={0.12}
        />
      </section>

      <div className="dashboard-grid">
        <section className="card">
          <h2 className="card-title">Threat activity</h2>
          <p className="card-sub">Counts grouped by observed date (local store)</p>
          <BarChart data={timeline} barColor="var(--blue)" emptyLabel="Not enough history for a timeline yet." />
        </section>

        <section className="card">
          <h2 className="card-title">Findings by modality</h2>
          <p className="card-sub">From GET /analytics/summary</p>
          <BarChart data={modalityData} barColor="var(--emerald)" />
        </section>
      </div>

      <div className="dashboard-grid">
        <section className="card">
          <div className="card-head-row">
            <h2 className="card-title">Live activity</h2>
            <Link to="/live" className="text-link">
              Open monitor
            </Link>
          </div>
          <ActivityFeed items={incidents.slice(0, 8)} onOpen={open} compact />
        </section>

        <section className="card">
          <div className="card-head-row">
            <h2 className="card-title">System health</h2>
            <Server size={16} className="muted" aria-hidden />
          </div>
          <pre className="mono health-pre">
            {`status: ${health?.status ?? "—"}
ollama_reachable: ${ollamaUp}
offline_ready: ${String(health?.offline_ready ?? false)}
models: ${health?.ollama_models?.length ? health.ollama_models.join(", ") : "none"}`}
          </pre>
        </section>
      </div>

      <section className="card">
        <h2 className="card-title">Recent incidents</h2>
        <motion.div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Decision</th>
                <th>Transmission</th>
                <th>Review</th>
                <th>Title</th>
              </tr>
            </thead>
            <tbody>
              {incidents.slice(0, 8).map((i) => (
                <tr key={i.id}>
                  <td>
                    <button type="button" className="text-link mono" onClick={() => open(i.id)}>
                      {i.id}
                    </button>
                  </td>
                  <td>{i.decision}</td>
                  <td>{i.transmission_status}</td>
                  <td>{i.review_status}</td>
                  <td>{i.title}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </motion.div>
      </section>
    </motion.div>
  );
}