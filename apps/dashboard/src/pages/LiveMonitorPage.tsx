import { useSearchParams, useOutletContext } from "react-router-dom";
import { motion } from "framer-motion";
import { ActivityFeed } from "../components/ActivityFeed";
import { useDashboardPoll } from "../hooks/useDashboardPoll";
import type { OutletContext } from "../layout/AppShell";

export function LiveMonitorPage() {
  const { incidents, loading } = useDashboardPoll(2000);
  const { openIncident } = useOutletContext<OutletContext>();
  const [, setParams] = useSearchParams();

  const open = (id: string) => {
    openIncident(id);
    setParams({ incident: id });
  };

  return (
    <motion.div className="page-stack" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <section className="card">
        <div className="card-head-row">
          <h2 className="card-title">Event stream</h2>
          <span className="live-pill mono">{loading ? "Syncing…" : "Polling 2s"}</span>
        </div>
        <p className="card-sub">
          Timestamps and statuses reflect recorded workflow state, not inferred breach confirmation.
        </p>
        <ActivityFeed items={incidents} onOpen={open} />
      </section>
    </motion.div>
  );
}