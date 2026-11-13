import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { ChevronLeft, ChevronRight, RefreshCw, Search, X } from "lucide-react";
import SecurityEventTable from "../components/SecurityEventTable.jsx";
import { EmptyState, ErrorState, LoadingState, PageTitle } from "../components/Feedback.jsx";
import { DecisionBadge, RiskBadge } from "../components/StatusBadges.jsx";
import { getEventDetails, getEvents } from "../services/api.js";

const PAGE_SIZE = 20;

export default function SecurityEvents() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [decision, setDecision] = useState("");
  const [eventType, setEventType] = useState("");
  const [riskLevel, setRiskLevel] = useState("");
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [detail, setDetail] = useState(null);
  const [detailError, setDetailError] = useState("");
  const visibleItems = useMemo(() => {
    const term = search.trim().toLowerCase();
    return items.filter((event) => {
      const matchesRisk = !riskLevel || event.risk_level?.toUpperCase() === riskLevel;
      const searchable = [event.request_id, event.event_type, event.user_role, event.action, event.decision, event.risk_level].filter(Boolean).join(" ").toLowerCase();
      return matchesRisk && (!term || searchable.includes(term));
    });
  }, [items, riskLevel, search]);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await getEvents({ decision, event_type: eventType, limit: PAGE_SIZE, offset });
      setItems(response.items || []);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }, [decision, eventType, offset]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    const requestId = searchParams.get("request");
    if (!requestId) {
      setDetail(null);
      setDetailError("");
      return;
    }
    let active = true;
    getEventDetails(requestId).then((event) => {
      if (active) { setDetail(event); setDetailError(""); }
    }).catch((requestError) => {
      if (active) { setDetail(null); setDetailError(requestError.message); }
    });
    return () => { active = false; };
  }, [searchParams]);

  function changeFilter(setter, value) {
    setter(value);
    setOffset(0);
  }
  async function selectEvent(requestId) {
    setSearchParams({ request: requestId });
  }

  return (
    <>
      <PageTitle eyebrow="MONITORING" title="Security events" description="Search and inspect backend audit metadata. Raw prompts and sensitive values are not displayed." action={<button className="button secondary" onClick={load} disabled={loading}><RefreshCw size={15} className={loading ? "spin" : ""} /> Refresh</button>} />
      <section className="panel event-controls">
        <div className="field search-field"><label htmlFor="event-search">Search loaded events</label><div className="search-input"><Search size={15} /><input id="event-search" type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="ID, type, role, or action" /></div></div>
        <div className="field"><label htmlFor="decision-filter">Decision</label><select id="decision-filter" value={decision} onChange={(event) => changeFilter(setDecision, event.target.value)}><option value="">All decisions</option><option value="ALLOW">Allow</option><option value="BLOCK">Block</option><option value="REVIEW">Review</option></select></div>
        <div className="field"><label htmlFor="type-filter">Event type</label><select id="type-filter" value={eventType} onChange={(event) => changeFilter(setEventType, event.target.value)}><option value="">All types</option><option value="prompt_scan">Prompt scan</option><option value="action_check">Action check</option></select></div>
        <div className="field"><label htmlFor="risk-filter">Risk</label><select id="risk-filter" value={riskLevel} onChange={(event) => setRiskLevel(event.target.value)}><option value="">All risk levels</option><option value="LOW">Low</option><option value="MEDIUM">Medium</option><option value="HIGH">High</option><option value="CRITICAL">Critical</option></select></div>
        <span className="muted filter-page">Search and risk filters apply to this {items.length}-event page</span>
      </section>
      <section className="panel table-panel">
        {error ? <ErrorState message={error} onRetry={load} /> : loading && !items.length ? <LoadingState label="Loading security events..." /> : visibleItems.length ? <SecurityEventTable events={visibleItems} onSelect={selectEvent} /> : <EmptyState title={items.length ? "No events match these filters" : "No events recorded"} description={items.length ? "Adjust the search or filters to see matching records." : "Run a security scan to create an event."} />}
        <div className="pagination"><span>{items.length ? `Page ${Math.floor(offset / PAGE_SIZE) + 1} · ${visibleItems.length} shown of ${items.length} loaded` : "No events on this page"}</span><div><button className="button secondary small" onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))} disabled={offset === 0 || loading}><ChevronLeft size={15} /> Previous</button><button className="button secondary small" onClick={() => setOffset(offset + PAGE_SIZE)} disabled={items.length < PAGE_SIZE || loading}>Next <ChevronRight size={15} /></button></div></div>
      </section>
      {detailError && <ErrorState message={detailError} />}
      {detail && <section className="panel detail-panel event-detail"><div className="result-heading"><div><span className="eyebrow">EVENT DETAILS</span><h2>{detail.request_id}</h2></div><button className="icon-button" onClick={() => setSearchParams({})} aria-label="Close event details"><X size={17} /></button></div><div className="detail-grid"><div><span>Timestamp</span><strong>{detail.timestamp ? new Date(detail.timestamp).toLocaleString() : "—"}</strong></div><div><span>Type</span><strong>{detail.event_type || "—"}</strong></div><div><span>Role</span><strong>{detail.user_role || "—"}</strong></div><div><span>Action</span><strong>{detail.action || "—"}</strong></div><div><span>Risk score</span><strong>{Number(detail.risk_score || 0).toFixed(2)}</strong></div><div><span>Risk level</span><RiskBadge value={detail.risk_level} /></div><div><span>Decision</span><DecisionBadge value={detail.decision} /></div><div><span>Policy ID</span><strong>{detail.policy_id || "—"}</strong></div></div><div className="detail-copy">{detail.reason || "No reason recorded."}</div></section>}
    </>
  );
}
