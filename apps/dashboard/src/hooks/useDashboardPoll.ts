import { useEffect, useState } from "react";
import { fetchAnalytics, fetchHealth, fetchIncidents } from "../api";
import type { AnalyticsSummary, HealthInfo, IncidentRow } from "../lib/types";

export function useDashboardPoll(intervalMs = 3000) {
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [stats, setStats] = useState<AnalyticsSummary | null>(null);
  const [incidents, setIncidents] = useState<IncidentRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const refresh = async () => {
      try {
        const [h, s, list] = await Promise.all([
          fetchHealth(),
          fetchAnalytics(),
          fetchIncidents(),
        ]);
        setHealth(h as HealthInfo);
        setStats(s as AnalyticsSummary);
        setIncidents(list as IncidentRow[]);
        setError(null);
      } catch {
        setError("Cannot reach local API at 127.0.0.1:8765");
      } finally {
        setLoading(false);
      }
    };
    refresh();
    const t = setInterval(refresh, intervalMs);
    return () => clearInterval(t);
  }, [intervalMs]);

  return { health, stats, incidents, error, loading };
}