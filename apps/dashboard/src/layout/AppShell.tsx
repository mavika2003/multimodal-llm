import { useState } from "react";
import { Link, NavLink, Outlet, useLocation, useSearchParams } from "react-router-dom";
import { Lock, PanelLeftClose, PanelLeft, MessageSquare, Circle } from "lucide-react";
import { NAV_ITEMS, PAGE_TITLES } from "./navConfig";
import { IncidentDrawer } from "../components/IncidentDrawer";
import { useDashboardPoll } from "../hooks/useDashboardPoll";

function titleForPath(pathname: string) {
  const base = pathname.split("?")[0];
  if (PAGE_TITLES[base]) return PAGE_TITLES[base];
  if (base.startsWith("/incidents")) return PAGE_TITLES["/incidents"];
  return { title: "AIRLOCK", subtitle: "Local privacy command center" };
}

export function AppShell() {
  const [collapsed, setCollapsed] = useState(false);
  const { pathname } = useLocation();
  const [params, setParams] = useSearchParams();
  const incidentId = params.get("incident");
  const { health } = useDashboardPoll();
  const meta = titleForPath(pathname);
  const ollamaUp = Boolean(health?.ollama_reachable);

  const closeDrawer = () => {
    const next = new URLSearchParams(params);
    next.delete("incident");
    setParams(next);
  };

  return (
    <div className={`app-shell ${collapsed ? "sidebar-collapsed" : ""}`}>
      <aside className="sidebar" aria-label="Main navigation">
        <div className="sidebar-brand">
          <Lock size={20} className="brand-icon" aria-hidden />
          {!collapsed && <span>AIRLOCK</span>}
        </div>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
              title={label}
            >
              <Icon size={18} aria-hidden />
              {!collapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-status card">
          {!collapsed && <p className="status-label">Protection</p>}
          <p className="status-line">
            <Circle size={8} className={ollamaUp ? "dot-emerald" : "dot-amber"} />
            {!collapsed && (ollamaUp ? "Local models ready" : "Rules-only runtime")}
          </p>
        </div>

        <button
          type="button"
          className="sidebar-toggle icon-btn"
          onClick={() => setCollapsed((v) => !v)}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <PanelLeft size={18} /> : <PanelLeftClose size={18} />}
        </button>
      </aside>

      <div className="main-column">
        <header className="topbar">
          <div>
            <p className="breadcrumb mono">AIRLOCK / {meta.title}</p>
            <h1 className="topbar-title">{meta.title}</h1>
            <p className="topbar-subtitle">{meta.subtitle}</p>
          </div>
          <Link className="btn btn-primary" to="/chat">
            Demo chat
            <MessageSquare size={14} aria-hidden />
          </Link>
        </header>

        <main className="page-content">
          <Outlet context={{ openIncident: (id: string) => setParams({ incident: id }) }} />
        </main>
      </div>

      <IncidentDrawer incidentId={incidentId} onClose={closeDrawer} />
    </div>
  );
}

export type OutletContext = { openIncident: (id: string) => void };