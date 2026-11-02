import { ArrowUpRight } from "lucide-react";
import { DecisionBadge, RiskBadge } from "./StatusBadges.jsx";

export default function SecurityEventTable({ events, onSelect }) {
  return (
    <div className="table-scroll">
      <table>
        <thead><tr><th>Request</th><th>Timestamp</th><th>Type</th><th>Role / Action</th><th>Risk</th><th>Decision</th><th aria-label="Details" /></tr></thead>
        <tbody>
          {events.map((event) => (
            <tr key={event.request_id}>
              <td><code>{event.request_id}</code></td>
              <td className="nowrap">{event.timestamp ? new Date(event.timestamp).toLocaleString() : "—"}</td>
              <td>{event.event_type || "—"}</td>
              <td>{event.user_role || "—"}<span className="table-sub">{event.action || "—"}</span></td>
              <td><RiskBadge value={event.risk_level} /><span className="table-sub">{Number(event.risk_score || 0).toFixed(2)}</span></td>
              <td><DecisionBadge value={event.decision} /></td>
              <td><button className="table-link" onClick={() => onSelect?.(event.request_id)} aria-label={`View event ${event.request_id}`}><ArrowUpRight size={16} /></button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
