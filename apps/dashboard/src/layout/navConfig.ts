import {
  Activity,
  BarChart3,
  LayoutDashboard,
  MessageSquare,
  Radar,
  ScanSearch,
  Settings,
} from "lucide-react";

export const NAV_ITEMS = [
  { to: "/", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/chat", label: "Demo Chat", icon: MessageSquare },
  { to: "/live", label: "Live Monitor", icon: Radar },
  { to: "/incidents", label: "Incidents", icon: Activity },
  { to: "/inspector", label: "Inspector", icon: ScanSearch },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/settings", label: "Settings", icon: Settings },
] as const;

export const PAGE_TITLES: Record<string, { title: string; subtitle: string }> = {
  "/": {
    title: "Command Center",
    subtitle: "Local AI protection before content leaves your device",
  },
  "/chat": {
    title: "Demo Chat",
    subtitle: "Multimodal pre-send scan: text, code, image, document, audio, video",
  },
  "/live": {
    title: "Live Monitor",
    subtitle: "Real-time lifecycle of scan and triage events from SQLite",
  },
  "/incidents": {
    title: "Incidents",
    subtitle: "Investigate, triage, and review redacted evidence metadata",
  },
  "/inspector": {
    title: "Privacy Inspector",
    subtitle: "Manual multimodal analysis and grounded Q&A",
  },
  "/analytics": {
    title: "Analytics",
    subtitle: "Aggregates computed from your on-device incident store",
  },
  "/settings": {
    title: "Settings",
    subtitle: "Runtime, models, and local-only configuration",
  },
};