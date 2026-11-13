import { useState } from "react";
import { BadgeCheck, LockKeyhole } from "lucide-react";
import { ErrorState, PageTitle, ScorePanel } from "../components/Feedback.jsx";
import { DecisionBadge } from "../components/StatusBadges.jsx";
import { checkAction, getEventDetails } from "../services/api.js";

const ACTIONS = [
  ["search_public_documents", "Search public documents"],
  ["read_customer_record", "Read customer record"],
  ["send_simulated_email", "Send simulated email"],
  ["update_simulated_record", "Update simulated record"],
  ["delete_simulated_resource", "Delete simulated resource"],
];
const ROLES = ["admin", "analyst", "viewer"];

export default function ActionAuthorization() {
  const [role, setRole] = useState("analyst");
  const [action, setAction] = useState(ACTIONS[0][0]);
  const [prompt, setPrompt] = useState("");
  const [resourceId, setResourceId] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [result, setResult] = useState(null);
  const [policyId, setPolicyId] = useState(null);
  const [detailError, setDetailError] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event) {
    event.preventDefault();
    if (!prompt.trim()) { setError("Enter the prompt associated with the proposed action."); return; }
    if (action === "delete_simulated_resource" && !confirmed) { setError("Confirm the simulated deletion check before evaluating this action."); return; }
    setLoading(true);
    setError("");
    setResult(null);
    setPolicyId(null);
    setDetailError("");
    try {
      const response = await checkAction({
        prompt: prompt.trim(),
        proposed_action: action,
        user_context: `mock-${role}`,
        user_role: role,
        resource_context: resourceId.trim() ? { resource_id: resourceId.trim() } : null,
        confirm_delete: action === "delete_simulated_resource" && confirmed,
      });
      setResult(response);
      try {
        const event = await getEventDetails(response.request_id);
        setPolicyId(event.policy_id || null);
      } catch (eventError) {
        setDetailError(`Audit policy metadata could not be loaded: ${eventError.message}`);
      }
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageTitle eyebrow="POLICY TESTING" title="Action authorization" description="Evaluate a proposed action against backend policy and risk controls." />
      <div className="notice notice-amber"><LockKeyhole size={17} /><span><strong>Development demonstration.</strong> The role selector sends a mock identity only; changing a role here does not grant privileges. Backend policy is authoritative. No real action is executed.</span></div>
      <form className="panel form-panel" onSubmit={submit}>
        <div className="form-grid">
          <div className="field"><label htmlFor="mock-role">Development mock identity</label><select id="mock-role" value={role} onChange={(event) => setRole(event.target.value)}>{ROLES.map((value) => <option key={value} value={value}>{value[0].toUpperCase() + value.slice(1)}</option>)}</select><small>Not production authentication</small></div>
          <div className="field"><label htmlFor="action-select">Proposed action</label><select id="action-select" value={action} onChange={(event) => { setAction(event.target.value); setConfirmed(false); setError(""); }}>{ACTIONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><small>Action key: <code>{action}</code></small></div>
          <div className="field full"><label htmlFor="resource-id">Resource identifier <span className="muted">(optional)</span></label><input id="resource-id" value={resourceId} maxLength={128} onChange={(event) => setResourceId(event.target.value)} placeholder="e.g. demo-record-01" /></div>
          <div className="field full"><label htmlFor="action-prompt">Prompt to evaluate</label><textarea id="action-prompt" value={prompt} onChange={(event) => setPrompt(event.target.value.slice(0, 20000))} maxLength={20000} rows={5} placeholder="Describe the request that led to this proposed action..." /></div>
          {action === "delete_simulated_resource" && <label className="confirm-control"><input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} /><span><strong>Explicit confirmation required</strong><small>Confirm evaluation only. The dashboard will never delete resources.</small></span></label>}
        </div>
        {error && <ErrorState message={error} />}
        <div className="form-actions"><span className="muted">Request sent to backend authorization policy</span><button className="button primary" disabled={loading || !prompt.trim()}><BadgeCheck size={16} />{loading ? "Evaluating..." : "Evaluate action"}</button></div>
      </form>
      {result && <div className="result-stack">
        <ScorePanel result={result} />
        <section className="panel detail-panel"><div className="result-heading"><h3>Policy decision</h3><DecisionBadge value={result.decision} /></div><div className="detail-row"><span>Mock role</span><strong>{result.policy_decision?.role || role}</strong></div><div className="detail-row"><span>Action</span><strong>{result.policy_decision?.action || action}</strong></div><div className="detail-row"><span>Policy ID</span><strong>{policyId || "Not returned"}</strong></div><div className="detail-row"><span>Authorization</span><strong>{result.policy_decision?.authorized ? "Permitted by policy" : "Denied by policy"}</strong></div>{result.policy_decision?.reason && <div className="detail-copy">{result.policy_decision.reason}</div>}{detailError && <p className="inline-warning">{detailError}</p>}</section>
        <div className="two-column"><section className="panel detail-panel"><h3>Prompt analysis</h3><div className="detail-row"><span>Injection indicator</span><strong>{result.detection_findings?.ml_detection?.is_suspicious ? "Detected" : "Not detected"}</strong></div><div className="detail-row"><span>Model</span><strong>{result.detection_findings?.ml_detection?.model_name || "Unavailable"}</strong></div><div className="detail-copy">{result.detection_findings?.ml_detection?.detection_reason || "No model explanation was returned."}</div></section><section className="panel detail-panel"><h3>Data-leak check</h3><div className="detail-row"><span>Sensitive data</span><strong>{result.detection_findings?.data_leak_detection?.has_sensitive_data ? "Detected" : "Not detected"}</strong></div><div className="finding-tags">{(result.detection_findings?.data_leak_detection?.findings || []).map((finding) => <span className="finding-tag" key={finding.type}>{finding.type} · {finding.count}</span>)}</div></section></div>
        {result.decision !== "ALLOW" && <div className="notice notice-amber"><LockKeyhole size={16} /><span>This action was not authorized. The result is informational; no action was performed.</span></div>}
      </div>}
    </>
  );
}
