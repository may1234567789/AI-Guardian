import { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { Activity, ArrowUpRight, BarChart3, Bot, ChevronRight, FileSearch, FlaskConical, LayoutDashboard, LockKeyhole, Menu, Settings, Shield, X } from "lucide-react";
import { ConnectionBadge } from "./StatusBadges.jsx";
import { getApiBaseUrl } from "../services/api.js";

const navigation = [
  { to: "/", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/scanner", label: "Prompt scanner", icon: FileSearch },
  { to: "/authorization", label: "Action authorization", icon: LockKeyhole },
  { to: "/data-leak", label: "Data leak scanner", icon: Shield },
  { to: "/events", label: "Security events", icon: Activity },
  { to: "/models", label: "Model performance", icon: BarChart3 },
  { to: "/evaluation", label: "Security evaluation", icon: FlaskConical },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function Shell({ health, checkedAt, refreshHealth }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();
  const active = navigation.find((item) => item.to === location.pathname);
  const closeMenu = () => setMenuOpen(false);

  return (
    <div className="app-shell">
      {menuOpen && <button className="mobile-backdrop" onClick={closeMenu} aria-label="Close navigation" />}
      <aside className={`sidebar ${menuOpen ? "sidebar-open" : ""}`}>
        <div className="brand"><div className="brand-icon"><Shield size={20} /></div><div><strong>SentinelAI</strong><span>SECURITY CONSOLE</span></div><button className="sidebar-close" onClick={closeMenu} aria-label="Close menu"><X size={19} /></button></div>
        <div className="nav-caption">WORKSPACE</div>
        <nav aria-label="Main navigation">
          {navigation.map(({ to, label, icon: Icon, end }) => <NavLink key={to} to={to} end={end} onClick={closeMenu} className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}><Icon size={17} /><span>{label}</span>{label === "Overview" && <ChevronRight className="nav-arrow" size={15} />}</NavLink>)}
        </nav>
        <div className="sidebar-bottom"><div className="env-card"><span className="live-dot" /><div><strong>Development environment</strong><span>Local API · Mock identity</span></div></div><div className="side-foot"><span>SentinelAI</span><span>v1.0.0</span></div></div>
      </aside>
      <main className="main-area">
        <header className="topbar"><button className="mobile-menu" onClick={() => setMenuOpen(true)} aria-label="Open navigation"><Menu size={20} /></button><div className="breadcrumb"><span>Console</span><ChevronRight size={14} /><strong>{active?.label || "Overview"}</strong></div><div className="topbar-right"><button className="status-refresh" onClick={refreshHealth} title="Refresh backend status"><ConnectionBadge status={health?.status} /></button><span className="top-date">{checkedAt ? new Date(checkedAt).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" }) : new Date().toLocaleDateString()}</span></div></header>
        <div className="page-wrap"><Outlet context={{ health, checkedAt, refreshHealth }} /></div>
        <footer className="app-footer"><span><Bot size={14} /> SentinelAI · local security monitoring</span><a href={`${getApiBaseUrl()}/docs`} target="_blank" rel="noreferrer">API docs <ArrowUpRight size={13} /></a></footer>
      </main>
    </div>
  );
}
