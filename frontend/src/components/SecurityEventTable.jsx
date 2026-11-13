import { useState } from "react";
import { ArrowUpRight, Check, Copy } from "lucide-react";
import { DecisionBadge, RiskBadge } from "./StatusBadges.jsx";

export default function SecurityEventTable({ events, onSelect, compact = false }) {
  const [copyMessage, setCopyMessage] = useState("");

  async function copyRequestId(requestId) {
    try {
      await navigator.clipboard.writeText(requestId);
      setCopyMessage(`Copied ${requestId}`);
    } catch (error) {
      setCopyMessage(`Could not copy request ID: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  return (
    <div className={`table-scroll ${compact ? "compact-events" : ""}`}>
      <table>
        <thead><tr><th>Request</th><th>Timestamp</th><th>Type</th>{!compact && <th>Role / Action</th>}<th>Risk</th><th>Decision</th><th aria-label="Actions" /></tr></thead>
        <tbody>
          {events.map((event) => (
            <tr key={event.request_id}>
              <td><code>{event.request_id}</code></td>
              <td className="nowrap">{event.timestamp ? new Date(event.timestamp).toLocaleString() : "—"}</td>
              <td>{event.event_type || "—"}</td>
              {!compact && <td>{event.user_role || "—"}<span className="table-sub">{event.action || "—"}</span></td>}
              <td><RiskBadge value={event.risk_level} /><span className="table-sub">{Number(event.risk_score || 0).toFixed(2)}</span></td>
              <td><DecisionBadge value={event.decision} /></td>
              <td><div className="table-actions"><button className="table-link" onClick={() => copyRequestId(event.request_id)} aria-label={`Copy request ID ${event.request_id}`} title="Copy request ID"><Copy size={14} /></button><button className="table-link" onClick={() => onSelect?.(event.request_id)} aria-label={`View event ${event.request_id}`} title="View event details"><ArrowUpRight size={16} /></button></div></td>
            </tr>
          ))}
        </tbody>
      </table>
      {copyMessage && <div className="copy-status" role="status"><Check size={13} />{copyMessage}</div>}
    </div>
  );
}
