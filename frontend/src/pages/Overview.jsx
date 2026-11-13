import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Activity, ArrowRight, Ban, Check, Clock3, FileSearch, RefreshCw, ShieldCheck } from "lucide-react";
import SecurityEventTable from "../components/SecurityEventTable.jsx";
import { EmptyState, ErrorState, LoadingState, PageTitle } from "../components/Feedback.jsx";
import { getEvents, getStats } from "../services/api.js";

const DECISION_COLORS = { ALLOW: "var(--success)", BLOCK: "var(--danger)", REVIEW: "var(--warning)" };
const statCards = [
  { key: "total_events", label: "Security events", icon: Activity },
  { key: "blocked_requests", label: "Blocked", icon: Ban, tone: "danger" },
  { key: "allowed_requests", label: "Allowed", icon: Check, tone: "success" },
  { key: "review_requests", label: "Needs review", icon: Clock3, tone: "warning" },
];

export default function Overview({ health, refreshHealth }) {
  const [stats, setStats] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState({});
  const [updatedAt, setUpdatedAt] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    const [statsResult, eventsResult] = await Promise.allSettled([
      getStats(),
      getEvents({ limit: 200, offset: 0 }),
    ]);
    setErrors({
      stats: statsResult.status === "rejected" ? statsResult.reason.message : null,
      events: eventsResult.status === "rejected" ? eventsResult.reason.message : null,
    });
    if (statsResult.status === "fulfilled") setStats(statsResult.value);
    if (eventsResult.status === "fulfilled") setEvents(eventsResult.value.items || []);
    setUpdatedAt(new Date().toISOString());
    setLoading(false);
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const decisions = useMemo(() => Object.entries(stats?.decision_distribution || {}), [stats]);
  const recentEvents = events.slice(0, 8);
  const actionEvents = events.filter((event) => event.event_type === "action_check");
  const lastActionEvent = actionEvents[0];

  return (
    <>
      <PageTitle eyebrow="MONITORING" title="Security Overview" description="Monitor prompt threats, policy decisions, and simulated agent activity." action={<button className="button secondary" onClick={() => { refresh(); refreshHealth(); }} disabled={loading}><RefreshCw size={15} className={loading ? "spin" : ""} /> Refresh</button>} />

      <section className={`connection-summary ${health?.status === "ok" ? "connected" : health?.status === "degraded" ? "degraded" : "disconnected"}`} aria-live="polite">
        <span className="connection-indicator" />
        <div><strong>{health?.status === "ok" ? "Backend connected" : health?.status === "degraded" ? "Backend degraded" : health?.status === "offline" ? "Backend unavailable" : "Checking backend connection"}</strong><span>{health ? `Database ${health.database || "unknown"} · Security engine ${health.security_engine || "unknown"} · Model ${health.ml_model || "unknown"}` : "Health check in progress"}</span></div>
      </section>

      {errors.stats ? <ErrorState message={errors.stats} onRetry={refresh} /> : loading && !stats ? <LoadingState label="Loading backend statistics..." /> : (
        <div className="stat-grid">{statCards.map(({ key, label, icon: Icon, tone }) => <article className="stat-card" key={key}><div className={`stat-icon ${tone || ""}`}><Icon size={16} /></div><div><span>{label}</span><strong>{stats?.[key] ?? 0}</strong></div></article>)}</div>
      )}

      <div className="overview-grid">
        <section className="panel table-panel overview-events">
          <div className="panel-heading"><div><h3>Recent security events</h3><span>{updatedAt ? `Latest records · updated ${new Date(updatedAt).toLocaleTimeString()}` : "Latest recorded decisions"}</span></div><Link className="text-link" to="/events">All events <ArrowRight size={14} /></Link></div>
          {errors.events ? <ErrorState message={errors.events} onRetry={refresh} /> : loading && !events.length ? <LoadingState /> : recentEvents.length ? <SecurityEventTable compact events={recentEvents} onSelect={(requestId) => window.location.assign(`/events?request=${encodeURIComponent(requestId)}`)} /> : <EmptyState title="No events recorded" description="Events from prompt scans and action checks will appear here." />}
        </section>

        <aside className="overview-aside">
          <section className="panel compact-panel">
            <div className="panel-heading"><div><h3>Decision distribution</h3><span>Backend aggregate · all recorded events</span></div></div>
            {errors.stats ? <p className="muted">Decision totals unavailable.</p> : decisions.length ? <div className="decision-list">{decisions.map(([name, value]) => {
              const total = Number(stats?.total_events) || 0;
              const percentage = total ? Math.min(100, (Number(value) / total) * 100) : 0;
              return <div className="decision-row" key={name}><div><span className="decision-name"><i style={{ backgroundColor: DECISION_COLORS[name] || "var(--accent)" }} />{name}</span><strong>{value}</strong></div><span className="decision-track"><i style={{ width: `${percentage}%`, backgroundColor: DECISION_COLORS[name] || "var(--accent)" }} /></span></div>;
            })}</div> : <EmptyState title="No decisions yet" description="Run a scan to start collecting results." />}
          </section>

          <section className="panel compact-panel">
            <div className="panel-heading"><div><h3>Detection summary</h3><span>Cumulative backend counters</span></div><ShieldCheck size={17} className="muted" /></div>
            <div className="summary-row"><span>Prompt injection detections</span><strong>{errors.stats ? "—" : stats?.prompt_injection_detections ?? 0}</strong></div>
            <div className="summary-row"><span>Sensitive-data detections</span><strong>{errors.stats ? "—" : stats?.sensitive_data_detections ?? 0}</strong></div>
          </section>

          <section className="panel compact-panel">
            <div className="panel-heading"><div><h3>Action activity</h3><span>Among latest {events.length} available events</span></div><Activity size={17} className="muted" /></div>
            <div className="summary-row"><span>Authorization checks</span><strong>{errors.events ? "—" : actionEvents.length}</strong></div>
            <div className="summary-row"><span>Most recent check</span><strong>{lastActionEvent?.timestamp ? new Date(lastActionEvent.timestamp).toLocaleString() : "—"}</strong></div>
          </section>
        </aside>
      </div>

      <section className="quick-actions"><div><span className="eyebrow">SECURITY TOOLS</span><h2>Run a security check</h2><p>Inspect prompts, evaluate proposed actions, or scan generated output.</p></div><div className="quick-links"><Link to="/scanner"><FileSearch size={16} /> Scan prompt <ArrowRight size={14} /></Link><Link to="/authorization"><ShieldCheck size={16} /> Evaluate action <ArrowRight size={14} /></Link><Link to="/data-leak"><ShieldCheck size={16} /> Scan output <ArrowRight size={14} /></Link></div></section>
    </>
  );
}
