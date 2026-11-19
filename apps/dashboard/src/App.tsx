import { Navigate, Route, Routes, useParams } from "react-router-dom";
import { AppShell } from "./layout/AppShell";
import { OverviewPage } from "./pages/OverviewPage";
import { LiveMonitorPage } from "./pages/LiveMonitorPage";
import { IncidentsPage } from "./pages/IncidentsPage";
import { InspectorPage } from "./pages/InspectorPage";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { DemoChatPage } from "./pages/DemoChatPage";

function LegacyIncidentRedirect() {
  const { id } = useParams();
  return <Navigate to={`/incidents?incident=${encodeURIComponent(id ?? "")}`} replace />;
}

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<OverviewPage />} />
        <Route path="chat" element={<DemoChatPage />} />
        <Route path="live" element={<LiveMonitorPage />} />
        <Route path="incidents" element={<IncidentsPage />} />
        <Route path="incidents/:id" element={<LegacyIncidentRedirect />} />
        <Route path="inspector" element={<InspectorPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}