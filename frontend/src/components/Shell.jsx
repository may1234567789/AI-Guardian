import { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { Activity, ArrowUpRight, Bot, ChevronRight, FileSearch, LayoutDashboard, LockKeyhole, Menu, Shield, X } from "lucide-react";
import { ConnectionBadge } from "./StatusBadges.jsx";
import { getApiBaseUrl } from "../services/api.js";

const navigationGroups = [
  {
    label: "MONITORING",
    items: [
      { to: "/", label: "Overview", icon: LayoutDashboard, end: true },
      { to: "/events", label: "Security events", icon: Activity },
    ],
  },
  {
    label: "SECURITY TOOLS",
    items: [
      { to: "/scanner", label: "Prompt scanner", icon: FileSearch },
      { to: "/data-leak", label: "Data leak scanner", icon: Shield },
      { to: "/authorization", label: "Action authorization", icon: LockKeyhole },
    ],
  },
];

export default function Shell({ health, checkedAt, refreshHealth }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();
  const active = navigationGroups.flatMap((group) => group.items).find((item) => item.to === location.pathname);
  const closeMenu = () => setMenuOpen(false);
  const environment = `${["localhost", "127.0.0.1"].includes(window.location.hostname) ? "LOCAL" : "REMOTE"} · ${import.meta.env.MODE.toUpperCase()}`;

  return (
    <div className="app-shell">
      {menuOpen && <button className="mobile-backdrop" onClick={closeMenu} aria-label="Close navigation" />}
      <aside className={`sidebar ${menuOpen ? "sidebar-open" : ""}`}>
        <div className="brand"><div className="brand-icon"><Shield size={20} /></div><div><strong>SentinelAI</strong><span>SECURITY CONSOLE</span></div><button className="sidebar-close" onClick={closeMenu} aria-label="Close menu"><X size={19} /></button></div>
        <nav aria-label="Main navigation">
          {navigationGroups.map((group) => <div className="nav-group" key={group.label}>
            <div className="nav-caption">{group.label}</div>
            {group.items.map(({ to, label, icon: Icon, end }) => <NavLink key={to} to={to} end={end} onClick={closeMenu} className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}><Icon size={16} /><span>{label}</span></NavLink>)}
          </div>)}
        </nav>
      </aside>
      <main className="main-area">
        <header className="topbar"><button className="mobile-menu" onClick={() => setMenuOpen(true)} aria-label="Open navigation" aria-expanded={menuOpen}><Menu size={20} /></button><div className="breadcrumb"><span>Security console</span><ChevronRight size={14} /><strong>{active?.label || "Overview"}</strong></div><div className="topbar-right"><span className="environment-badge">{environment}</span><button className="status-refresh" onClick={refreshHealth} title="Refresh backend status" aria-label="Refresh backend status"><ConnectionBadge status={health?.status} /></button></div></header>
        <div className="page-wrap"><Outlet context={{ health, checkedAt, refreshHealth }} /></div>
        <footer className="app-footer"><span><Bot size={14} /> SentinelAI · local security monitoring</span><a href={`${getApiBaseUrl()}/docs`} target="_blank" rel="noreferrer">API docs <ArrowUpRight size={13} /></a></footer>
      </main>
    </div>
  );
}
