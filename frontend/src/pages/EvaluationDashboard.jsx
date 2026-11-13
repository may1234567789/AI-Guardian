import { useCallback, useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { EmptyState, ErrorState, LoadingState, PageTitle } from "../components/Feedback.jsx";
import { getEvaluationSummary } from "../services/api.js";

const CONFIGURATIONS = ["E1", "E2", "E3", "E4"];
const percent = (value) => Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : "N/A";
const latency = (value) => Number.isFinite(value) ? `${value.toFixed(3)} ms` : "N/A";

export default function EvaluationDashboard() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadSummary = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setSummary(await getEvaluationSummary());
    } catch (requestError) {
      setError(requestError.message || "The evaluation summary could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSummary();
  }, [loadSummary]);

  if (loading) return <LoadingState label="Loading saved Day 8 evaluation results..." />;
  if (error) return <ErrorState message={error} onRetry={loadSummary} />;
  if (!summary?.available) {
    return (
      <>
        <PageTitle eyebrow="DAY 8 EVALUATION" title="Security evaluation" description="Measured comparison of SentinelAI's synthetic security experiments." />
        <EmptyState title="No evaluation results yet" description={summary?.message || "Run the Day 8 evaluation to populate this dashboard with measured results."} />
      </>
    );
  }

  const rows = CONFIGURATIONS.map((configuration) => {
    const experiment = summary.experiments?.[configuration];
    if (!experiment) return null;
    return {
      configuration,
      name: experiment.name,
      detection: experiment.enforcement.attack_detection_rate,
      unauthorized: experiment.enforcement.unauthorized_action_prevention_rate,
      legitimate: experiment.enforcement.legitimate_task_completion_rate,
      sensitive: experiment.enforcement.sensitive_data_leakage_prevention_rate,
      falsePositive: experiment.detection.false_positive_rate,
      average: experiment.latency.average_ms,
      median: experiment.latency.median_ms,
      p95: experiment.latency.p95_ms,
    };
  }).filter(Boolean);

  const chartData = rows.map((row) => ({
    name: row.configuration,
    "Attack detection": Number.isFinite(row.detection) ? row.detection * 100 : null,
    "Unauthorized prevention": Number.isFinite(row.unauthorized) ? row.unauthorized * 100 : null,
    "Legitimate completion": Number.isFinite(row.legitimate) ? row.legitimate * 100 : null,
    "Sensitive-data prevention": Number.isFinite(row.sensitive) ? row.sensitive * 100 : null,
  }));
  const runAt = summary.run_id || "Not recorded";

  return (
    <>
      <PageTitle
        eyebrow="DAY 8 EVALUATION"
        title="Security evaluation"
        description="Actual results from the saved synthetic E1–E4 experiment run; no demonstration metrics are hardcoded."
        action={<button className="button secondary" onClick={loadSummary}><RefreshCw size={14} /> Refresh</button>}
      />
      <div className="notice">
        <span><strong>{summary.scenario_count} scenarios per configuration · {summary.evaluated_scenario_runs} measured runs.</strong> Synthetic scenarios and mock tools only. Run {runAt}.</span>
      </div>
      <section className="panel chart-panel model-chart">
        <div className="panel-heading"><div><h3>E1–E4 security outcome comparison</h3><span>Rates calculated from saved experiment results · percent</span></div></div>
        <div className="bar-chart"><ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 12, right: 12, bottom: 4, left: 0 }}>
            <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="name" tick={{ fill: "var(--text-secondary)", fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis domain={[0, 100]} tick={{ fill: "var(--text-tertiary)", fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ background: "var(--surface-raised)", border: "1px solid var(--border)", borderRadius: 4 }} formatter={(value) => Number.isFinite(value) ? `${Number(value).toFixed(1)}%` : "N/A"} />
            <Legend wrapperStyle={{ color: "var(--text-secondary)", fontSize: 11 }} />
            <Bar dataKey="Attack detection" fill="var(--accent)" isAnimationActive={false} />
            <Bar dataKey="Unauthorized prevention" fill="var(--danger)" isAnimationActive={false} />
            <Bar dataKey="Legitimate completion" fill="var(--success)" isAnimationActive={false} />
            <Bar dataKey="Sensitive-data prevention" fill="var(--warning)" isAnimationActive={false} />
          </BarChart>
        </ResponsiveContainer></div>
      </section>
      <section className="panel table-panel metrics-table">
        <div className="panel-heading"><div><h3>Configuration results</h3><span>Each row uses the same scenario suite and mock data reset policy.</span></div></div>
        <div className="table-scroll"><table>
          <thead><tr><th>Experiment</th><th>Attack detection</th><th>Unauthorized prevention</th><th>Legitimate completion</th><th>Sensitive-data prevention</th><th>False-positive rate</th><th>Mean latency</th><th>Median</th><th>P95</th></tr></thead>
          <tbody>{rows.map((row) => <tr key={row.configuration}>
            <td><strong>{row.configuration}</strong><span className="table-sub">{row.name}</span></td>
            <td>{percent(row.detection)}</td><td>{percent(row.unauthorized)}</td><td>{percent(row.legitimate)}</td>
            <td>{percent(row.sensitive)}</td><td>{percent(row.falsePositive)}</td>
            <td>{latency(row.average)}</td><td>{latency(row.median)}</td><td>{latency(row.p95)}</td>
          </tr>)}</tbody>
        </table></div>
      </section>
      <div className="detail-grid evaluation-counts">
        {Object.entries(summary.scenario_suite_counts_by_category || {}).map(([category, count]) => (
          <div key={category}><span>{category}</span><strong>{count}</strong></div>
        ))}
      </div>
      <ul className="caveat-list">
        <li>Prompt-injection metrics use the detector prediction alone; a policy denial is not an ML true positive.</li>
        <li>Expected labels are synthetic evaluation assumptions. Results do not demonstrate production-grade security.</li>
      </ul>
    </>
  );
}
