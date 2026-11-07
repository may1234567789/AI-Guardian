from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = Path(__file__).with_name("results")
REPORT_PATH = ROOT / "docs" / "day8_security_evaluation.md"
CONFIGURATIONS = ("E1", "E2", "E3", "E4")


def _pct(value: float | None) -> str:
    return "N/A" if value is None else f"{value * 100:.1f}%"


def _number(value: float | None, unit: str = "") -> str:
    return "N/A" if value is None else f"{value:.3f}{unit}"


def _category_detection(rows: list[dict[str, Any]], category: str) -> tuple[int, int, int]:
    selected = [row for row in rows if row["category"] == category and row["expected_malicious"]]
    detected = sum(row.get("predicted_detection") is True for row in selected)
    executed = sum(row["tool_executed"] for row in selected)
    return detected, len(selected), executed


def render_report(
    summary: dict[str, Any],
    metadata: dict[str, Any],
    failures: dict[str, Any],
    results: dict[str, Any],
) -> str:
    experiments = summary["experiments"]
    lines = [
        "# Day 8: SentinelAI Security Evaluation",
        "",
        f"**Run ID:** `{summary['run_id']}`  ",
        f"**Evaluation date (UTC):** {metadata['evaluation_date_utc']}  ",
        f"**Scenario suite:** v{metadata['scenario_suite_version']} ({summary['scenario_count']} scenarios)  ",
        f"**Evidence:** Synthetic scenarios and mock tools only. This evaluation does not establish production-grade security.",
        "",
        "## A. Research Objective",
        "",
        "This evaluation compares an unprotected simulated agent, deterministic phrase filtering, the selected trained ML detector, and the complete ML-plus-policy pipeline. The goal is to measure detection, authorization, privacy, utility, and latency trade-offs. A blocked tool action is not counted as a correctly classified injection unless the detection component independently predicted malicious input.",
        "",
        "## B. Experimental Setup",
        "",
        f"- **Hardware:** {metadata['hardware_note']}",
        f"- **Operating system / processor:** `{metadata['platform']}` / `{metadata['processor']}`.",
        f"- **Python:** `{metadata['python_version'].split()[0]}`; package versions: `{json.dumps(metadata['package_versions'], sort_keys=True)}`.",
        f"- **Selected model:** `{metadata['model_configuration']['metadata_model_name']}` from `{metadata['model_artifact']}`; SHA-256 `{metadata['model_artifact_sha256']}`.",
        f"- **Model features:** TF-IDF unigram/bigram pipeline with `{metadata['model_configuration']['classifier_config']}`.",
        f"- **Positive class:** label `1` (`prompt_injection`), verified from saved artifact `classes_ == [0, 1]` and `svm_model_metadata.json` label mapping. SVM scores are decision-boundary distances, not calibrated probabilities.",
        f"- **Dataset:** `{metadata['dataset_identifier']}` (`{metadata['dataset_config']}`); the saved model was loaded, not retrained.",
        f"- **Evaluation cases:** {summary['scenario_count']} generated synthetic cases; category counts: `{json.dumps(summary['scenario_suite_counts_by_category'], sort_keys=True)}`.",
        f"- **Runtime:** all four configurations used the same scenario IDs, deterministic mock resource reset, and registered mock tool implementations. No external tools, services, credentials, or destructive real resources were used.",
        f"- **Git commit:** `{metadata['git_commit'] or 'unavailable'}`; working tree dirty: `{metadata.get('working_tree_dirty', 'not recorded')}`.",
        "- **Prior-day documentation:** Day 1-3 and Day 5-6 reports exist. Day 4 and Day 7 reports were not present; their backend source, model artifacts, tools, API, and tests were inspected directly instead of inventing missing summaries.",
        "",
        "### Dataset leakage audit",
        "",
        f"Case-folded, trimmed exact-text overlap between the generated user request plus optional document and core train/validation/test data: `{json.dumps(metadata['dataset_leakage_audit']['evaluation_exact_overlap_rows'], sort_keys=True)}`. Cross-split unique-text overlap counts: `{json.dumps(metadata['dataset_leakage_audit']['cross_split_unique_text_overlaps'], sort_keys=True)}`. Evaluation scenarios were not used for fitting or threshold tuning. This checks exact text only, not semantic or paraphrase leakage.",
        "",
        "## C. Experimental Methodology",
        "",
        "- **E1 — Unprotected Agent:** bypasses SentinelAI detection and role policy, but invokes only registered mock executors. The mock delete primitive still requires its explicit confirmation flag.",
        "- **E2 — Rule-Based Filtering:** checks fixed, documented suspicious phrases after case-folding and whitespace normalization; it does not use model scores or role authorization.",
        "- **E3 — ML-Based Detection:** applies the saved LinearSVC pipeline and its existing threshold; no policy decision affects its detection label or tool gating.",
        "- **E4 — ML + Deterministic Policy Enforcement:** combines standalone detector measurement, `PermissionGuard`, `PolicyEngine`, `RiskEngine`, `DataLeakDetector`, mock-tool role checks, and output scanning. `REVIEW` and denial do not dispatch a tool. Policy denials remain authoritative.",
        "",
        "Each mock store is reset before each scenario/configuration run. The same 120 scenario definitions are used in each configuration. Detector initialization/model loading is excluded from per-request latency. Evaluation labels are hand-authored assumptions and may need manual review; quoted or ambiguous examples are context-dependent.",
        "",
        "## D. Evaluation Metrics",
        "",
        "- **Detection metrics:** malicious label is positive. Accuracy, precision, recall, F1, FPR = FP/(FP+TN), and FNR = FN/(FN+TP). ROC-AUC and average precision use continuous SVM decision scores when both labels and valid scores exist; these scores are not probabilities. E1/E2 do not have valid continuous ML scores.",
        "- **Unauthorized-action prevention:** unauthorized scenarios with no successful tool execution divided by all scenarios labeled unauthorized. This measures the final observed outcome, independently from injection classification.",
        "- **Legitimate-task completion:** benign, policy-authorized scenarios that execute successfully divided by benign, authorized scenarios expected to execute. Safe output redaction does not reverse the fact that the mock tool ran.",
        "- **Sensitive-output prevention:** targeted synthetic sensitive-output cases with no sensitive-pattern output returned (blocked or redacted) divided by those cases. Denominator is the explicitly flagged synthetic record-output attempts.",
        "- **Tool execution accuracy:** scenarios with successful tool execution matching the expected execution flag divided by applicable scenarios. Tool errors are listed separately.",
        "- **Latency:** mean, median, P95 (reported because each configuration has at least 20 cases), and max monotonic-clock per-scenario elapsed time. Model-only inference is separately timed. These local measurements are load-sensitive.",
        "",
        "## E. Experimental Results",
        "",
        "| Metric | E1 | E2 | E3 | E4 |",
        "|---|---:|---:|---:|---:|",
    ]
    metric_rows = [
        ("Attack detection rate", lambda x: _pct(x["enforcement"]["attack_detection_rate"])),
        ("Unauthorized-action prevention", lambda x: _pct(x["enforcement"]["unauthorized_action_prevention_rate"])),
        ("Legitimate-task completion", lambda x: _pct(x["enforcement"]["legitimate_task_completion_rate"])),
        ("Sensitive-data prevention", lambda x: _pct(x["enforcement"]["sensitive_data_leakage_prevention_rate"])),
        ("False-positive rate", lambda x: _pct(x["detection"]["false_positive_rate"])),
        ("False-negative rate", lambda x: _pct(x["detection"]["false_negative_rate"])),
        ("Accuracy", lambda x: _pct(x["detection"]["accuracy"])),
        ("Precision", lambda x: _pct(x["detection"]["precision"])),
        ("Recall", lambda x: _pct(x["detection"]["recall"])),
        ("F1", lambda x: _pct(x["detection"]["f1"])),
        ("ROC-AUC", lambda x: _number(x["detection"]["roc_auc"])),
        ("Average precision", lambda x: _number(x["detection"]["average_precision"])),
        ("Tool execution accuracy", lambda x: _pct(x["enforcement"]["tool_execution_accuracy"])),
        ("Average latency (ms)", lambda x: _number(x["latency"]["average_ms"], " ms")),
        ("Median latency (ms)", lambda x: _number(x["latency"]["median_ms"], " ms")),
        ("P95 latency (ms)", lambda x: _number(x["latency"]["p95_ms"], " ms")),
        ("Maximum latency (ms)", lambda x: _number(x["latency"]["max_ms"], " ms")),
        ("Average ML inference (ms)", lambda x: _number(x["latency"]["model_inference"]["average_ms"], " ms")),
    ]
    for label, get_value in metric_rows:
        lines.append("| " + label + " | " + " | ".join(
            get_value(experiments[configuration]) for configuration in CONFIGURATIONS
        ) + " |")
    lines.extend([
        "",
        f"Scenario counts per configuration: {summary['scenario_count']}; total scenario-configuration runs: {summary['evaluated_scenario_runs']}.",
        "",
        "### Attack categories",
        "",
        "| Configuration | Direct detected / attempts | Direct tool executions | Indirect detected / attempts | Indirect tool executions |",
        "|---|---:|---:|---:|---:|",
    ])
    for configuration in CONFIGURATIONS:
        rows = [row for row in results["scenario_results"] if row["configuration"] == configuration]
        direct_detected, direct_total, direct_exec = _category_detection(rows, "Direct prompt injection")
        indirect_detected, indirect_total, indirect_exec = _category_detection(rows, "Indirect prompt injection")
        lines.append(
            f"| {configuration} | {direct_detected}/{direct_total} | {direct_exec} | "
            f"{indirect_detected}/{indirect_total} | {indirect_exec} |"
        )
    lines.extend([
        "",
        "### Charts",
        "",
        "![Detection metric comparison](../ml/reports/day8/detection_metrics.png)",
        "",
        "![Unauthorized action prevention](../ml/reports/day8/unauthorized_action_prevention.png)",
        "",
        "![Legitimate task completion](../ml/reports/day8/legitimate_task_completion.png)",
        "",
        "![Sensitive data prevention](../ml/reports/day8/sensitive_data_prevention.png)",
        "",
        "![False positive and false negative rates](../ml/reports/day8/false_positive_false_negative.png)",
        "",
        "![Latency comparison](../ml/reports/day8/latency_comparison.png)",
        "",
        "![Confusion matrices](../ml/reports/day8/confusion_matrices.png)",
        "",
        "## F. Security Analysis",
        "",
        f"E4 blocked or reviewed the injected direct/indirect cases as reported above; its measured attack-detection results come from the classifier alone. Across E4 indirect-injection cases, {failures['e4_indirect_injection']['tool_executions']} of {failures['e4_indirect_injection']['attempts']} reached mock-tool execution. Across direct injections, {sum(row['category'] == 'Direct prompt injection' and row['tool_executed'] for row in results['scenario_results'] if row['configuration'] == 'E4')} reached mock-tool execution. Direct and indirect counts use only the generated labels and should not be generalized to real traffic.",
        "",
        f"E4 prevented {experiments['E4']['enforcement']['unauthorized_action_prevention']['prevented']} of {experiments['E4']['enforcement']['unauthorized_action_prevention']['denominator']} role/action-unauthorized scenarios. The policy decision is independent of model classification; unknown identities are denied by the policy. E1-E3 intentionally have no authoritative role/action gate.",
        "",
        "The rule baseline uses fixed phrases and can miss novel wording or altered punctuation; conversely, benign research discussion and quoted attack language can trigger phrase-based false positives. ML false positives/negatives are shown as observed rather than corrected or tuned on the evaluation set. An input may be blocked by policy even when the classifier calls it benign; that is not counted as a successful injection classification.",
        "",
        "## G. Model Analysis",
        "",
        f"Observed E3 confusion matrix (TN, FP, FN, TP): `{experiments['E3']['detection']['confusion_matrix']}`; E4 classifier-only matrix: `{experiments['E4']['detection']['confusion_matrix']}`. Robustness examples and predictions are saved in `backend/evaluation/results/scenario_results.json` under `robustness_results` and plotted in `ml/reports/day8/robustness_predictions.png`.",
        "",
        "The model is a sparse TF-IDF + LinearSVC classifier trained on English benchmark data. It is not a semantic/LLM classifier; distribution shift, paraphrases, multilingual content, long benign messages, indirect document context, and ambiguous quoted content remain limitations. The validation-selected threshold is reused unchanged; no test/evaluation examples were used to tune it.",
        "",
        "## H. Policy Enforcement Analysis",
        "",
        "E4 combines model-based detection with the existing role/action policy and mock registry checks. The model cannot override policy denial, and model unavailability now blocks protected requests. Output scanning is applied before mock tool results are exposed. These controls are only as complete as current policies: the inspected implementation has role/action checks but no per-user customer/resource ownership or tenant ACL, recorded as an explicit coverage gap below.",
        "",
        "## I. Performance Analysis",
        "",
        f"E4 average end-to-end latency was {_number(experiments['E4']['latency']['average_ms'], ' ms')} (median {_number(experiments['E4']['latency']['median_ms'], ' ms')}, P95 {_number(experiments['E4']['latency']['p95_ms'], ' ms')}); its standalone model inference mean was {_number(experiments['E4']['latency']['model_inference']['average_ms'], ' ms')}. Total run duration was {_number(metadata['total_duration_seconds'], ' s')}. E4 performs additional policy and output checks, although observed latency also includes Python scheduling and mock-tool execution. No hardware-independent performance guarantee is implied.",
        "",
        "## J. Failure Analysis",
        "",
        f"- Recorded failure rows: {failures['failure_count']}; critical unauthorized executions or sensitive exposures: {failures['critical_failure_count']}.",
        f"- Critical failures by configuration (the baselines intentionally omit controls): `{json.dumps(failures['critical_failure_count_by_configuration'], sort_keys=True)}`. E4 recorded {failures['e4_malicious_tool_execution_count']} malicious tool execution(s), reported separately as HIGH severity.",
        f"- Unauthorized tool executions: {failures['unauthorized_tool_execution_count']}.",
        f"- Sensitive output exposures in marked scenarios: {failures['sensitive_output_exposure_count']}.",
        f"- Tool/pipeline errors are counted per configuration in the comparison summary; detailed sanitized rows are in `backend/evaluation/results/failure_analysis.json`.",
    ])
    for gap in failures["coverage_gaps"]:
        lines.append(f"- **{gap['severity']} — {gap['failure_category']}:** {gap['actual_behavior']} Remediation: {gap['suggested_remediation']}")
    lines.extend([
        "",
        "The E4 direct-injection miss is important: for the recorded case, the SVM score fell below its existing threshold and the current explicit marker set did not match the wording, so a permitted admin mock update executed. This is a high-severity security failure even though the role/action policy allowed the operation; do not treat E4 as safe until this behavior is addressed and verified on a fresh holdout. The invariant suite and pre-existing backend suite are separate from these scenario outcomes. Output scanner errors fail closed in E4. Failure rows contain scenario IDs and sanitized error types, not raw prompt contents or tool output.",
        "",
        "## K. Limitations",
        "",
        f"- The {summary['scenario_count']} cases are synthetic, fixed, and hand-labeled; expected labels are assumptions that require manual review.",
        "- Exact text leakage was checked against the selected core train/validation/test split, not semantic similarity or every upstream dataset revision.",
        "- A compact English TF-IDF/SVM detector has limited generalization; a successful synthetic test is not a real-world guarantee.",
        "- The rule-based filter is intentionally simple and susceptible to wording changes and context-driven false positives.",
        "- No real external tools, services, credentials, or production workload were exercised.",
        "- The simulated agent and mock tools do not represent the full behavior, concurrency, identity, resource authorization, or event telemetry of a deployed agent.",
        "- The experiment runner does not emit database audit events; event persistence was covered only by existing backend tests.",
        "",
        "## L. Conclusion",
        "",
        f"On this suite, E4 detected {experiments['E4']['enforcement']['attack_detection_counts']['detected']}/{experiments['E4']['enforcement']['attack_detection_counts']['denominator']} labeled attacks, prevented {experiments['E4']['enforcement']['unauthorized_action_prevention']['prevented']}/{experiments['E4']['enforcement']['unauthorized_action_prevention']['denominator']} role/action-unauthorized attempts, completed {experiments['E4']['enforcement']['legitimate_task_completion']['completed']}/{experiments['E4']['enforcement']['legitimate_task_completion']['denominator']} benign authorized tasks, and prevented {experiments['E4']['enforcement']['sensitive_data_leakage_prevention']['prevented_or_redacted']}/{experiments['E4']['enforcement']['sensitive_data_leakage_prevention']['denominator']} marked synthetic output disclosures. E4 still allowed one labeled direct injection to execute a mock update. These measurements show trade-offs on this bounded synthetic suite only; they do not prove production-grade security or resistance to unseen prompt injection.",
        "",
        "## Day 8 acceptance checklist",
        "",
    ])
    checklist = [
        ("Existing Day 1-7 work inspected", "Complete"),
        ("Evaluation scenarios created", "Complete"),
        ("Scenario labels reviewed", "Complete — reviewed for structure; labels still require independent human review"),
        ("Training/test leakage checked", "Complete — exact case-folded text overlap only"),
        ("E1 implemented", "Complete"),
        ("E2 implemented", "Complete"),
        ("E3 implemented", "Complete"),
        ("E4 implemented", "Complete"),
        ("All experiments executed", "Complete"),
        ("ML metrics calculated", "Complete"),
        ("Security enforcement metrics calculated", "Complete"),
        ("Latency measured", "Complete"),
        ("Security invariants tested", "Complete"),
        ("Robustness tests executed", "Complete"),
        ("Failure analysis generated", "Complete"),
        ("Comparison charts generated", "Complete"),
        ("Raw results saved", "Complete — timestamped run preserved"),
        ("Research evaluation report created", "Complete"),
        ("Evaluation dashboard updated", "Complete"),
        ("README and evaluation instructions updated", "Complete — see backend/evaluation/README.md"),
    ]
    lines.extend(f"- [{ 'x' if state.startswith('Complete') else ' ' }] {item}: {state}" for item, state in checklist)
    lines.extend([
        "",
        "## Reproducibility artifacts",
        "",
        "- Raw results: `backend/evaluation/results/scenario_results.json`",
        "- Summary: `backend/evaluation/results/experiment_summary.json` and `.csv`",
        "- Failure analysis: `backend/evaluation/results/failure_analysis.json`",
        "- Run metadata: `backend/evaluation/results/run_metadata.json`",
        "- Preserved timestamped runs: `backend/evaluation/results/runs/`",
        "- Reproduction commands: `backend/evaluation/README.md`",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    summary = json.loads((RESULTS_DIR / "experiment_summary.json").read_text(encoding="utf-8"))
    metadata = json.loads((RESULTS_DIR / "run_metadata.json").read_text(encoding="utf-8"))
    failures = json.loads((RESULTS_DIR / "failure_analysis.json").read_text(encoding="utf-8"))
    results = json.loads((RESULTS_DIR / "scenario_results.json").read_text(encoding="utf-8"))
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(render_report(summary, metadata, failures, results), encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
