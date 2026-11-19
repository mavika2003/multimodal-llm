import { motion } from "framer-motion";
import { BarChart } from "../components/BarChart";
import { useDashboardPoll } from "../hooks/useDashboardPoll";
import { groupIncidentsByDay, countPotentialRisks } from "../lib/incidents";

export function AnalyticsPage() {
  const { stats, incidents } = useDashboardPoll();

  const byDecision = Object.entries(
    incidents.reduce<Record<string, number>>((acc, i) => {
      const k = i.decision || "unknown";
      acc[k] = (acc[k] ?? 0) + 1;
      return acc;
    }, {}),
  ).map(([label, count]) => ({ label, count }));

  const byTransmission = Object.entries(
    incidents.reduce<Record<string, number>>((acc, i) => {
      const k = i.transmission_status || "unknown";
      acc[k] = (acc[k] ?? 0) + 1;
      return acc;
    }, {}),
  ).map(([label, count]) => ({ label, count }));

  const modalityData = Object.entries(stats?.by_modality ?? {}).map(([label, count]) => ({
    label,
    count,
  }));

  return (
    <motion.div className="page-stack" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="kpi-grid kpi-grid-3">
        <article className="card stat-inline">
          <p className="stat-inline-label">Actions scanned</p>
          <p className="stat-inline-value">{stats?.actions_scanned ?? 0}</p>
        </article>
        <article className="card stat-inline">
          <p className="stat-inline-label">Potential risks</p>
          <p className="stat-inline-value">{countPotentialRisks(incidents)}</p>
        </article>
        <article className="card stat-inline">
          <p className="stat-inline-label">Review queue</p>
          <p className="stat-inline-value">{stats?.review_required ?? 0}</p>
        </article>
      </div>

      <motion.div className="dashboard-grid">
        <section className="card">
          <h2 className="card-title">Activity over time</h2>
          <BarChart data={groupIncidentsByDay(incidents)} barColor="var(--blue)" />
        </section>
        <section className="card">
          <h2 className="card-title">By modality</h2>
          <BarChart data={modalityData} barColor="var(--emerald)" />
        </section>
      </motion.div>

      <motion.div className="dashboard-grid">
        <section className="card">
          <h2 className="card-title">Decisions</h2>
          <BarChart data={byDecision} barColor="var(--amber)" />
        </section>
        <section className="card">
          <h2 className="card-title">Transmission status</h2>
          <BarChart data={byTransmission} barColor="var(--coral)" />
        </section>
      </motion.div>
    </motion.div>
  );
}