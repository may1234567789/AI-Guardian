import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Activity, ArrowRight, Ban, Check, Clock3, FileSearch, RefreshCw, ShieldAlert, ShieldCheck, Siren } from "lucide-react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import SecurityEventTable from "../components/SecurityEventTable.jsx";
import { EmptyState, ErrorState, LoadingState, PageTitle } from "../components/Feedback.jsx";
import { getEvents, getStats } from "../services/api.js";

const COLORS = { ALLOW: "#36d399", BLOCK: "#ff637d", REVIEW: "#f6bd60" };
const statCards = [
  { key: "total_events", label: "Total requests", icon: Activity, color: "blue" },
  { key: "allowed_requests", label: "Allowed", icon: Check, color: "green" },
  { key: "blocked_requests", label: "Blocked", icon: Ban, color: "red" },
  { key: "review_requests", label: "Needs review", icon: Clock3, color: "amber" },
  { key: "high_risk_requests", label: "High risk", icon: ShieldAlert, color: "orange" },
  { key: "critical_risk_requests", label: "Critical risk", icon: Siren, color: "purple" },
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

  const riskDistribution = useMemo(() => {
    const counts = events.reduce((result, event) => {
      const level = (event.risk_level || "UNKNOWN").toUpperCase();
      result[level] = (result[level] || 0) + 1;
      return result;
    }, {});
    return Object.entries(counts).map(([name, value]) => ({ name, value }));
  }, [events]);
  const eventDistribution = useMemo(() => {
    const counts = events.reduce((result, event) => {
      const type = event.event_type || "unknown";
      result[type] = (result[type] || 0) + 1;
      return result;
    }, {});
    return Object.entries(counts).map(([name, value]) => ({ name, value }));
  }, [events]);
  const decisions = useMemo(() => Object.entries(stats?.decision_distribution || {}).map(([name, value]) => ({ name, value })), [stats]);
  const recentEvents = events.slice(0, 6);

  return (
    <>
      <PageTitle eyebrow="SECURITY OVERVIEW" title="Good evening." description="Live visibility into the security decisions recorded by your local SentinelAI API." action={<button className="button secondary" onClick={() => { refresh(); refreshHealth(); }} disabled={loading}><RefreshCw size={15} className={loading ? "spin" : ""} /> Refresh</button>} />
      <div className="overview-status">
        <div className={`status-banner ${health?.status === "ok" ? "status-good" : health?.status === "degraded" ? "status-warn" : "status-bad"}`}><span className="live-dot" /><div><strong>{health?.status === "ok" ? "Security engine operational" : health?.status === "degraded" ? "Backend running in degraded mode" : "Backend connection unavailable"}</strong><span>{health ? `Database ${health.database} · ML model ${health.ml_model}` : "Checking backend health..."}</span></div><Link to="/settings">Connection details <ArrowRight size={14} /></Link></div>
        <div className="status-banner model-banner"><div className="status-icon"><ShieldCheck size={18} /></div><div><strong>Model status</strong><span>{health?.ml_model === "loaded" ? "Prompt injection model loaded" : health?.ml_model || "Checking model..."}</span></div><span className="mini-pill">{health?.app_version ? `API v${health.app_version}` : "Local API"}</span></div>
      </div>

      {errors.stats ? <ErrorState message={errors.stats} onRetry={refresh} /> : loading && !stats ? <LoadingState label="Loading backend statistics..." /> : (
        <div className="stat-grid">{statCards.map(({ key, label, icon: Icon, color }) => <article className="stat-card" key={key}><div className={`stat-icon ${color}`}><Icon size={18} /></div><span>{label}</span><strong>{stats?.[key] ?? 0}</strong><small>From recorded security events</small></article>)}</div>
      )}

      <div className="section-heading"><div><span className="eyebrow">EVENT INTELLIGENCE</span><h2>Security activity</h2></div><span className="updated-note">{updatedAt ? `Updated ${new Date(updatedAt).toLocaleTimeString()}` : ""}</span></div>
      <div className="chart-grid">
        <article className="panel chart-panel"><div className="panel-heading"><div><h3>Decision distribution</h3><span>Aggregate counts from /stats</span></div><div className="chart-mark"><Activity size={17} /></div></div>{decisions.length ? <div className="chart-content"><div className="donut"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={decisions} dataKey="value" nameKey="name" innerRadius={54} outerRadius={76} paddingAngle={4} stroke="none">{decisions.map((item) => <Cell key={item.name} fill={COLORS[item.name] || "#56b4f5"} />)}</Pie><Tooltip contentStyle={{ background: "#151d29", border: "1px solid #293648", borderRadius: 10 }} /></PieChart></ResponsiveContainer><div className="donut-center"><strong>{stats?.total_events ?? 0}</strong><span>events</span></div></div><div className="chart-legend">{decisions.map(({ name, value }) => <div key={name}><span className="legend-dot" style={{ background: COLORS[name] || "#56b4f5" }} />{name}<strong>{value}</strong></div>)}</div></div> : <EmptyState title="No decision data yet" description="Run a scan to start collecting decisions." />}</article>
        <DistributionPanel title="Risk levels" subtitle={`Derived from the latest ${events.length} available events`} data={riskDistribution} colors={{ LOW: "#36d399", MEDIUM: "#f6bd60", HIGH: "#ff8b5c", CRITICAL: "#ff637d" }} />
        <DistributionPanel title="Event categories" subtitle={`Derived from the latest ${events.length} available events`} data={eventDistribution} colors={{ prompt_scan: "#59b5ff", action_check: "#a68bfa" }} />
      </div>

      <div className="section-heading"><div><span className="eyebrow">AUDIT LOG</span><h2>Recent security events</h2></div><Link className="text-link" to="/events">View all events <ArrowRight size={14} /></Link></div>
      <section className="panel table-panel">
        {errors.events ? <ErrorState message={errors.events} onRetry={refresh} /> : loading && !events.length ? <LoadingState /> : recentEvents.length ? <SecurityEventTable events={recentEvents} onSelect={(requestId) => window.location.assign(`/events?request=${encodeURIComponent(requestId)}`)} /> : <EmptyState title="No events recorded" description="Events from prompt scans and action checks will appear here." />}
      </section>

      <section className="quick-actions"><div><span className="eyebrow">QUICK ACTIONS</span><h2>Run a security check</h2><p>Submit a prompt, test an action policy, or inspect output for sensitive data.</p></div><div className="quick-links"><Link to="/scanner"><FileSearch size={16} /> Scan prompt <ArrowRight size={14} /></Link><Link to="/authorization"><LockIcon /> Evaluate action <ArrowRight size={14} /></Link><Link to="/data-leak"><ShieldCheck size={16} /> Scan output <ArrowRight size={14} /></Link></div></section>
    </>
  );
}

function DistributionPanel({ title, subtitle, data, colors }) {
  return <article className="panel chart-panel"><div className="panel-heading"><div><h3>{title}</h3><span>{subtitle}</span></div><div className="chart-mark"><Activity size={17} /></div></div>{data.length ? <div className="chart-content"><div className="donut"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={data} dataKey="value" nameKey="name" innerRadius={54} outerRadius={76} paddingAngle={4} stroke="none">{data.map((item, index) => <Cell key={item.name} fill={colors[item.name] || ["#59b5ff", "#a68bfa", "#36d399", "#f6bd60"][index % 4]} />)}</Pie><Tooltip contentStyle={{ background: "#151d29", border: "1px solid #293648", borderRadius: 10 }} /></PieChart></ResponsiveContainer><div className="donut-center"><strong>{data.reduce((sum, item) => sum + item.value, 0)}</strong><span>events</span></div></div><div className="chart-legend">{data.map(({ name, value }) => <div key={name}><span className="legend-dot" style={{ background: colors[name] || "#59b5ff" }} />{name.replaceAll("_", " ")}<strong>{value}</strong></div>)}</div></div> : <EmptyState title={`No ${title.toLowerCase()} yet`} description="Recorded events will provide this aggregate." />}</article>;
}

function LockIcon() {
  return <ShieldCheck size={16} />;
}
