import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { ChevronLeft, ChevronRight, RefreshCw, X } from "lucide-react";
import SecurityEventTable from "../components/SecurityEventTable.jsx";
import { EmptyState, ErrorState, LoadingState, PageTitle } from "../components/Feedback.jsx";
import { DecisionBadge, RiskBadge } from "../components/StatusBadges.jsx";
import { getEventDetails, getEvents } from "../services/api.js";

const PAGE_SIZE = 20;

export default function SecurityEvents() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [decision, setDecision] = useState("");
  const [eventType, setEventType] = useState("");
  const [offset, setOffset] = useState(0);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [detail, setDetail] = useState(null);
  const [detailError, setDetailError] = useState("");

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
      <PageTitle eyebrow="AUDIT LOG" title="Security events" description="Browse backend audit metadata. Raw prompts and sensitive values are not displayed." action={<button className="button secondary" onClick={load} disabled={loading}><RefreshCw size={15} className={loading ? "spin" : ""} /> Refresh</button>} />
      <section className="panel event-controls">
        <div className="field"><label htmlFor="decision-filter">Decision</label><select id="decision-filter" value={decision} onChange={(event) => changeFilter(setDecision, event.target.value)}><option value="">All decisions</option><option value="ALLOW">Allow</option><option value="BLOCK">Block</option><option value="REVIEW">Review</option></select></div>
        <div className="field"><label htmlFor="type-filter">Event type</label><select id="type-filter" value={eventType} onChange={(event) => changeFilter(setEventType, event.target.value)}><option value="">All types</option><option value="prompt_scan">Prompt scan</option><option value="action_check">Action check</option></select></div>
        <span className="muted filter-page">Showing up to {PAGE_SIZE} per page</span>
      </section>
      <section className="panel table-panel">
        {error ? <ErrorState message={error} onRetry={load} /> : loading && !items.length ? <LoadingState label="Loading security events..." /> : items.length ? <SecurityEventTable events={items} onSelect={selectEvent} /> : <EmptyState title="No matching events" description="Try changing the filters or run a security scan to create an event." />}
        <div className="pagination"><span>{items.length ? `Page ${Math.floor(offset / PAGE_SIZE) + 1} · ${items.length} event${items.length === 1 ? "" : "s"}` : "No events on this page"}</span><div><button className="button secondary small" onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))} disabled={offset === 0 || loading}><ChevronLeft size={15} /> Previous</button><button className="button secondary small" onClick={() => setOffset(offset + PAGE_SIZE)} disabled={items.length < PAGE_SIZE || loading}>Next <ChevronRight size={15} /></button></div></div>
      </section>
      {detailError && <ErrorState message={detailError} />}
      {detail && <section className="panel detail-panel event-detail"><div className="result-heading"><div><span className="eyebrow">EVENT DETAILS</span><h2>{detail.request_id}</h2></div><button className="icon-button" onClick={() => setSearchParams({})} aria-label="Close event details"><X size={17} /></button></div><div className="detail-grid"><div><span>Timestamp</span><strong>{detail.timestamp ? new Date(detail.timestamp).toLocaleString() : "—"}</strong></div><div><span>Type</span><strong>{detail.event_type || "—"}</strong></div><div><span>Role</span><strong>{detail.user_role || "—"}</strong></div><div><span>Action</span><strong>{detail.action || "—"}</strong></div><div><span>Risk score</span><strong>{Number(detail.risk_score || 0).toFixed(2)}</strong></div><div><span>Risk level</span><RiskBadge value={detail.risk_level} /></div><div><span>Decision</span><DecisionBadge value={detail.decision} /></div><div><span>Policy ID</span><strong>{detail.policy_id || "—"}</strong></div></div><div className="detail-copy">{detail.reason || "No reason recorded."}</div></section>}
    </>
  );
}
