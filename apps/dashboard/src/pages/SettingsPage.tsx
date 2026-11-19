import { motion } from "framer-motion";
import { useDashboardPoll } from "../hooks/useDashboardPoll";
import { Link } from "react-router-dom";
import { DEMO_CHAT_PATH } from "../lib/incidents";

export function SettingsPage() {
  const { health } = useDashboardPoll(10000);

  return (
    <motion.div className="page-stack" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <section className="card">
        <h2 className="card-title">Local runtime</h2>
        <dl className="settings-dl mono">
          <div>
            <dt>API endpoint</dt>
            <dd>http://127.0.0.1:8765/api/v1</dd>
          </div>
          <div>
            <dt>Health status</dt>
            <dd>{health?.status ?? "—"}</dd>
          </div>
          <div>
            <dt>Ollama</dt>
            <dd>{health?.ollama_reachable ? "Reachable" : "Unavailable (rules-only)"}</dd>
          </div>
          <div>
            <dt>Models</dt>
            <dd>{health?.ollama_models?.join(", ") || "None reported"}</dd>
          </div>
          <div>
            <dt>Offline ready</dt>
            <dd>{String(health?.offline_ready ?? false)}</dd>
          </div>
        </dl>
      </section>

      <section className="card">
        <h2 className="card-title">Demo &amp; data</h2>
        <p className="card-sub">
          Synthetic samples are labeled in the UI. Incident counts and charts are read from SQLite
          on this machine only.
        </p>
        <ul className="settings-list">
          <li>
            Demo chat:{" "}
            <Link to={DEMO_CHAT_PATH} className="text-link">
              {DEMO_CHAT_PATH}
            </Link>{" "}
            (same origin as dashboard)
          </li>
          <li>Auth token: configured via local dev environment (AIRLOCK_LOCAL_TOKEN)</li>
        </ul>
      </section>
    </motion.div>
  );
}