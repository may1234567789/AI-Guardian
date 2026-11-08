import { useState } from "react";
import { Eraser, ScanLine, ShieldAlert } from "lucide-react";
import { ErrorState, PageTitle, ScorePanel } from "../components/Feedback.jsx";
import { DecisionBadge, RiskBadge } from "../components/StatusBadges.jsx";
import { scanOutput } from "../services/api.js";

const EXAMPLES = [
  ["Synthetic email", "For the demo contact demo.user@example.com about the public project update."],
  ["Synthetic key", "api_key: demo_key_for_ui_only_1234567890"],
];

export default function DataLeakScanner() {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event) {
    event.preventDefault();
    if (!text.trim()) { setError("Enter output text before scanning."); return; }
    setLoading(true);
    setError("");
    setResult(null);
    try {
      setResult(await scanOutput({ output_text: text.trim(), source: "sentinelai-dashboard" }));
      setText("");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageTitle eyebrow="DATA PROTECTION" title="Data leak scanner" description="Check generated text for sensitive patterns before delivery. Only the local backend receives the submitted content." />
      <div className="notice notice-amber"><ShieldAlert size={17} /><span><strong>Values are withheld.</strong> The backend returns finding categories and counts and redacts detected values before responding.</span></div>
      <div className="example-row"><span>Synthetic examples</span>{EXAMPLES.map(([label, value]) => <button className="example-chip" key={label} onClick={() => { setText(value); setResult(null); setError(""); }}>{label}</button>)}</div>
      <form className="panel form-panel" onSubmit={submit}>
        <label htmlFor="output-text">Text to inspect</label>
        <textarea id="output-text" value={text} onChange={(event) => { setText(event.target.value.slice(0, 20000)); setError(""); }} maxLength={20000} rows={9} placeholder="Paste AI-generated output here..." />
        <div className="input-meta"><span>Maximum 20,000 characters · Text is not stored in browser storage</span><span>{text.length.toLocaleString()} / 20,000</span></div>
        {error && <ErrorState message={error} />}
        <div className="form-actions"><button type="button" className="button secondary" onClick={() => { setText(""); setResult(null); setError(""); }}><Eraser size={15} /> Clear</button><button className="button primary" disabled={loading || !text.trim()}><ScanLine size={16} />{loading ? "Scanning..." : "Scan output"}</button></div>
      </form>
      {result && <div className="result-stack">
        <ScorePanel result={result} />
        <div className="two-column">        <section className="panel detail-panel"><h3>Sensitive-data findings</h3><div className="detail-row"><span>Detected</span><strong>{result.findings?.length ? "Yes" : "No"}</strong></div><div className="detail-row"><span>Finding categories</span><strong>{result.findings?.length || 0}</strong></div><div className="finding-list">{(result.findings || []).map((finding) => <div className="finding-item" key={finding.type}><div><strong>{finding.type}</strong><span>{finding.count} match{finding.count === 1 ? "" : "es"}</span></div><code>[REDACTED {finding.type}]</code></div>)}{!result.findings?.length && <span className="muted">No sensitive patterns detected.</span>}</div><p className="muted">The API does not include raw matched examples in its response.</p></section>
          <section className="panel detail-panel"><h3>Risk assessment</h3><div className="detail-row"><span>Decision</span><DecisionBadge value={result.decision} /></div><div className="detail-row"><span>Risk level</span><RiskBadge value={result.risk_level} /></div><div className="detail-row"><span>Risk score</span><strong>{Number(result.risk_score).toFixed(2)}</strong></div><ul className="reason-list">{(result.reasons || []).map((reason) => <li key={reason}>{reason}</li>)}</ul></section></div>
      </div>}
    </>
  );
}
