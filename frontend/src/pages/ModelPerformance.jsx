import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Info } from "lucide-react";
import metrics from "../data/modelMetrics.json";
import { PageTitle } from "../components/Feedback.jsx";

const metricLabel = (value) => Number.isFinite(value) ? `${(value * 100).toFixed(2)}%` : "N/A";
const latencyLabel = (value) => Number.isFinite(value) ? `${value.toFixed(2)} ms` : "N/A";

export default function ModelPerformance() {
  const chartData = metrics.models.map((model) => ({
    name: model.name,
    Accuracy: model.default.accuracy * 100,
    Precision: model.default.precision * 100,
    Recall: model.default.recall * 100,
    "F1-score": model.default.f1 * 100,
  }));
  return (
    <>
      <PageTitle eyebrow="ANALYTICS" title="Model performance" description="Held-out classification results for the Logistic Regression and Linear SVM detectors." />
      <div className="notice"><Info size={17} /><span><strong>Measured experiment results.</strong> These are recorded test-set metrics, not live API performance. Dataset: core_test · 942 samples.</span></div>
      <section className="panel model-current"><div className="model-current-icon"><span className="live-dot" /></div><div><span className="eyebrow">CURRENT BACKEND MODEL</span><h2>{metrics.currentBackendModel}</h2><p>Configured backend threshold: <code>{metrics.currentBackendThreshold}</code></p></div><span className="mini-pill">Configured default</span></section>
      <section className="panel chart-panel model-chart"><div className="panel-heading"><div><h3>Default-threshold test metrics</h3><span>Held-out experiment results · percent</span></div></div><div className="bar-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={chartData} margin={{ top: 12, right: 12, bottom: 4, left: 0 }}><CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} /><XAxis dataKey="name" tick={{ fill: "var(--text-secondary)", fontSize: 12 }} axisLine={false} tickLine={false} /><YAxis domain={[0, 100]} tick={{ fill: "var(--text-tertiary)", fontSize: 11 }} axisLine={false} tickLine={false} /><Tooltip contentStyle={{ background: "var(--surface-raised)", border: "1px solid var(--border)", borderRadius: 4 }} formatter={(value) => `${Number(value).toFixed(2)}%`} /><Legend wrapperStyle={{ color: "var(--text-secondary)", fontSize: 12 }} /><Bar dataKey="Accuracy" fill="var(--accent)" isAnimationActive={false} /><Bar dataKey="Precision" fill="#7ca9e8" isAnimationActive={false} /><Bar dataKey="Recall" fill="var(--success)" isAnimationActive={false} /><Bar dataKey="F1-score" fill="var(--warning)" isAnimationActive={false} /></BarChart></ResponsiveContainer></div></section>
      <section className="confusion-section">
        <div className="section-heading"><div><span className="eyebrow">PREDICTION COUNTS</span><h2>Confusion matrices</h2></div><span className="muted">core_test · 942 samples · default thresholds</span></div>
        <div className="two-column">{metrics.models.map((model) => <section className="panel detail-panel confusion-panel" key={`${model.name}-matrix`}><h3>{model.name}</h3><div className="table-scroll"><table><caption>Predicted class by actual class</caption><thead><tr><th>Actual \ Predicted</th><th>Benign</th><th>Malicious</th></tr></thead><tbody><tr><th>Benign</th><td className="matrix-tn">TN {model.default.confusionMatrix.tn}</td><td className="matrix-fp">FP {model.default.confusionMatrix.fp}</td></tr><tr><th>Malicious</th><td className="matrix-fn">FN {model.default.confusionMatrix.fn}</td><td className="matrix-tp">TP {model.default.confusionMatrix.tp}</td></tr></tbody></table></div></section>)}</div>
      </section>
      <section className="panel table-panel metrics-table"><div className="panel-heading"><div><h3>Default threshold metrics</h3><span>Measured on the same held-out test split</span></div></div><div className="table-scroll"><table><thead><tr><th>Model</th><th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1</th><th>False-positive rate</th><th>False-negative rate</th><th>ROC-AUC</th></tr></thead><tbody>{metrics.models.map((model) => <tr key={model.name}><td><strong>{model.name}</strong><span className="table-sub">{model.scoreType}</span></td><td>{metricLabel(model.default.accuracy)}</td><td>{metricLabel(model.default.precision)}</td><td>{metricLabel(model.default.recall)}</td><td>{metricLabel(model.default.f1)}</td><td>{metricLabel(model.default.falsePositiveRate)}</td><td>{metricLabel(model.default.falseNegativeRate)}</td><td>{metricLabel(model.default.rocAuc)}</td></tr>)}</tbody></table></div></section>
      <div className="two-column calibration-grid">{metrics.models.map((model) => <section className="panel detail-panel" key={`${model.name}-calibrated`}><span className="eyebrow">VALIDATION-SELECTED THRESHOLD</span><h3>{model.name}</h3><div className="detail-row"><span>Threshold</span><strong>{model.calibrated.threshold.toFixed(4)}{model.scoreType.includes("Decision") ? " (score)" : " (probability)"}</strong></div><div className="detail-row"><span>Test accuracy / precision</span><strong>{metricLabel(model.calibrated.accuracy)} / {metricLabel(model.calibrated.precision)}</strong></div><div className="detail-row"><span>Test recall / F1</span><strong>{metricLabel(model.calibrated.recall)} / {model.calibrated.f1.toFixed(4)}</strong></div><div className="detail-row"><span>False-positive / negative rate</span><strong>{metricLabel(model.calibrated.falsePositiveRate)} / {metricLabel(model.calibrated.falseNegativeRate)}</strong></div></section>)}</div>
      <section className="panel detail-panel"><h3>Latency and artifact measurements</h3><div className="table-scroll"><table><thead><tr><th>Model</th><th>Mean latency</th><th>P95 latency</th><th>Training time</th><th>Artifact size</th></tr></thead><tbody>{metrics.models.map((model) => <tr key={`${model.name}-latency`}><td>{model.name}</td><td>{latencyLabel(model.default.meanLatencyMs)}</td><td>{latencyLabel(model.default.p95LatencyMs)}</td><td>{Number.isFinite(model.default.trainingSeconds) ? `${model.default.trainingSeconds.toFixed(4)} s` : "N/A"}</td><td>{Number.isFinite(model.default.artifactBytes) ? `${(model.default.artifactBytes / 1024).toFixed(1)} KiB` : "N/A"}</td></tr>)}</tbody></table></div></section>
      <ul className="caveat-list">{metrics.caveats.map((caveat) => <li key={caveat}>{caveat}</li>)}</ul>
      <div className="notice"><Info size={17} /><span><strong>Classification is not system-level security effectiveness.</strong> These metrics evaluate detector labels on a held-out dataset. They do not measure policy enforcement, authorization prevention, sensitive-output handling, or end-to-end agent behavior.</span></div>
    </>
  );
}
