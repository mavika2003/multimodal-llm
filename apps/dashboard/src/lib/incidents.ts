import type { IncidentRow } from "./types";

export function severityTone(severity: string): "critical" | "warning" | "low" {
  const s = severity?.toLowerCase() ?? "";
  if (s.includes("high") || s.includes("critical")) return "critical";
  if (s.includes("medium") || s.includes("med")) return "warning";
  return "low";
}

export function transmissionLabel(status: string): string {
  switch (status) {
    case "not_sent_confirmed":
      return "Prevented";
    case "sent_confirmed":
      return "Transmitted (flagged)";
    default:
      return "Unknown";
  }
}

export function formatTime(iso: string) {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString(undefined, {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function formatDateTime(iso: string) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export function activityState(row: IncidentRow) {
  if (row.review_status && row.review_status !== "open") return row.review_status;
  if (row.workflow_state) return row.workflow_state;
  return row.decision || "unknown";
}

export function countPotentialRisks(incidents: IncidentRow[]) {
  return incidents.filter((i) => {
    const tone = severityTone(i.severity);
    return tone !== "low" || i.decision === "require_review" || i.decision === "block";
  }).length;
}

export function groupIncidentsByDay(incidents: IncidentRow[]): { label: string; count: number }[] {
  const map = new Map<string, number>();
  for (const i of incidents) {
    if (!i.observed_at) continue;
    const day = i.observed_at.slice(0, 10);
    map.set(day, (map.get(day) ?? 0) + 1);
  }
  return [...map.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([label, count]) => ({ label, count }));
}

export const DEMO_CHAT_PATH = "/chat";