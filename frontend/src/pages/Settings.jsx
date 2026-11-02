import { useEffect, useState } from "react";
import { Check, RefreshCw, Save, Server, Shield } from "lucide-react";
import { ErrorState, PageTitle } from "../components/Feedback.jsx";
import { ConnectionBadge } from "../components/StatusBadges.jsx";
import { getApiBaseUrl, healthCheck, setApiBaseUrl } from "../services/api.js";

export default function Settings({ health, refreshHealth }) {
  const [apiUrl, setApiUrl] = useState(getApiBaseUrl());
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [checking, setChecking] = useState(false);

  useEffect(() => { setApiUrl(getApiBaseUrl()); }, []);

  async function saveAndCheck(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      const normalized = setApiBaseUrl(apiUrl);
      setApiUrl(normalized);
      setChecking(true);
      await healthCheck();
      await refreshHealth();
      setMessage("API base URL saved and the health check succeeded.");
    } catch (requestError) {
      await refreshHealth();
      setError(requestError.message);
    } finally {
      setChecking(false);
    }
  }

  return (
    <>
      <PageTitle eyebrow="CONFIGURATION" title="Settings" description="Configure the local backend connection and review the current development environment." />
      <div className="settings-grid">
        <form className="panel form-panel" onSubmit={saveAndCheck}><div className="panel-heading"><div><h3>Backend connection</h3><span>Only the API base URL is stored in this browser.</span></div><Server size={18} className="muted" /></div><label htmlFor="api-url">Backend API URL</label><input id="api-url" type="url" required value={apiUrl} onChange={(event) => setApiUrl(event.target.value)} placeholder="http://127.0.0.1:8000" /><small>Use the backend origin without credentials or URL parameters.</small>{error && <ErrorState message={error} />}{message && <div className="success-message"><Check size={16} />{message}</div>}<div className="form-actions"><span className="muted">Connection status: <ConnectionBadge status={health?.status} /></span><button className="button primary" disabled={checking}><Save size={15} />{checking ? "Checking..." : "Save and test"}</button></div></form>
        <section className="panel detail-panel"><div className="panel-heading"><div><h3>API health</h3><span>Information returned by GET /health</span></div><button className="icon-button" onClick={refreshHealth} aria-label="Refresh health"><RefreshCw size={16} /></button></div><div className="detail-row"><span>Overall status</span><strong>{health?.status || "Checking..."}</strong></div><div className="detail-row"><span>Database</span><strong>{health?.database || "—"}</strong></div><div className="detail-row"><span>Security engine</span><strong>{health?.security_engine || "—"}</strong></div><div className="detail-row"><span>ML model</span><strong>{health?.ml_model || "—"}</strong></div><div className="detail-row"><span>Application version</span><strong>{health?.app_version || "—"}</strong></div>{health?.error && <p className="inline-warning">{health.error}</p>}</section>
      </div>
      <section className="panel detail-panel settings-policy"><h3><Shield size={17} /> Development policy reference</h3><p>This dashboard does not edit backend policies or authenticate users. Policy evaluation remains authoritative in the backend.</p><div className="role-cards"><div><strong>Admin</strong><span>Policy supports all five listed simulated actions.</span></div><div><strong>Analyst</strong><span>Policy supports public-document search and customer-record read.</span></div><div><strong>Viewer</strong><span>Policy supports public-document search only.</span></div></div><div className="detail-row"><span>Destructive action</span><strong>Delete simulation requires explicit confirmation</strong></div><div className="detail-row"><span>Configured model</span><strong>Linear SVM when the saved SVM artifact is present</strong></div></section>
    </>
  );
}
