import { AlertTriangle, LoaderCircle, RefreshCw } from "lucide-react";
import { DecisionBadge, RiskBadge } from "./StatusBadges.jsx";

export function LoadingState({ label = "Loading security data..." }) {
  return <div className="feedback loading"><LoaderCircle className="spin" size={20} />{label}</div>;
}

export function EmptyState({ title, description }) {
  return <div className="feedback empty"><div className="empty-mark">—</div><strong>{title}</strong><span>{description}</span></div>;
}

export function ErrorState({ message, onRetry }) {
  return <div className="feedback error"><AlertTriangle size={18} /><div><strong>Unable to load data</strong><span>{message}</span></div>{onRetry && <button className="icon-button" onClick={onRetry} aria-label="Retry"><RefreshCw size={16} /></button>}</div>;
}

export function PageTitle({ eyebrow, title, description, action }) {
  return <div className="page-title"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>{action}</div>;
}

export function ScorePanel({ result }) {
  return (
    <section className="result-panel">
      <div className="result-heading"><div><span className="eyebrow">BACKEND ASSESSMENT</span><h2>Security decision</h2></div><div className="result-badges"><RiskBadge value={result.risk_level} /><DecisionBadge value={result.decision} /></div></div>
      <div className="score-grid">
        <div className="score-number"><span>Aggregated backend risk score · not a probability</span><strong>{Number(result.risk_score).toFixed(2)}</strong><div className="score-track"><i style={{ width: `${Math.min(100, Math.max(0, Number(result.risk_score) * 100))}%` }} /></div></div>
        <div><span className="muted-label">Request ID</span><code>{result.request_id}</code></div>
      </div>
      {result.explanation && <p className="result-explanation">{result.explanation}</p>}
    </section>
  );
}
