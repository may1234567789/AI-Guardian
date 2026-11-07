# SentinelAI Day 8 Evaluation

The evaluation is synthetic-only. It uses the checked-in mock tool registry and the existing saved SVM artifact. It does not retrain or modify a model, call external services, or use real credentials.

Run commands from the repository root in PowerShell:

```powershell
$env:PYTHONPATH = "."
```

## Reproduce the evaluation

Generate the fixed-seed synthetic scenario suite:

```powershell
.\venv\Scripts\python.exe -m backend.evaluation.generate_scenarios --write
```

Run the critical security invariants:

```powershell
.\venv\Scripts\python.exe -m pytest backend\evaluation\test_security_invariants.py backend\evaluation\test_metrics.py -q
```

Execute all four configurations. The runner verifies the saved model, selected dataset split, same scenario IDs per configuration, and exact case-folded text overlap against core train/validation/test data. It resets synthetic tool state before every scenario/configuration pair:

```powershell
.\venv\Scripts\python.exe -m backend.evaluation.run_experiments
```

Calculate detection, enforcement, and latency metrics and write the comparison CSV/JSON:

```powershell
.\venv\Scripts\python.exe -m backend.evaluation.compare_experiments
```

Generate the sanitized failure analysis:

```powershell
.\venv\Scripts\python.exe -m backend.evaluation.failure_analysis
```

Generate charts from the saved measurements:

```powershell
.\venv\Scripts\python.exe -m backend.evaluation.generate_charts
```

Generate the Day 8 research report:

```powershell
.\venv\Scripts\python.exe -m backend.evaluation.generate_report
```

Run the full backend test suite, including pre-existing API/security tests and Day 8 checks:

```powershell
.\venv\Scripts\python.exe -m pytest backend -q
```

Build the dashboard from `frontend\`:

```powershell
npm run build
```

## Outputs

- `scenarios.json`: generated scenario IDs, inputs, assumed labels, roles, actions, and expected outcomes.
- `results\scenario_results.json`: sanitized scenario/configuration measurements and observed robustness predictions. Prompt contents and tool outputs are not copied into result rows.
- `results\experiment_summary.json` and `experiment_summary.csv`: actual results and metric denominators.
- `results\failure_analysis.json`: per-failure scenario IDs, observed behavior, cause, and remediation; includes explicit coverage gaps.
- `results\run_metadata.json`: model/artifact hash, dataset leakage check, seed, versions, environment, timings, and configuration.
- `results\runs\<run-id>\`: preserved copies of raw results and metadata for each execution. Root-level files are the latest-run convenience copies.
- `..\..\ml\reports\day8\`: charts generated from the same raw results.
- `..\..\docs\day8_security_evaluation.md`: generated research-oriented report.

## Metric interpretation

- Malicious prompt injection is positive class `1`; the saved SVM uses a signed decision score, not a probability.
- Injection detection is reported independently from authorization. A policy denial does not count as a detector true positive.
- Unauthorized-action prevention uses unauthorized scenario labels as its denominator and counts successful non-execution.
- Legitimate completion uses benign, authorized scenarios expected to execute as its denominator.
- Sensitive-output prevention uses only scenarios explicitly marked as synthetic sensitive-output attempts; a scanner block/redaction qualifies as prevention.
- P95 latency is reported only when a configuration has at least 20 measurements. Model inference latency is measured separately; model loading is excluded.
- Scenario labels are reproducible assumptions for a controlled evaluation, not ground truth for real-world traffic. They should receive independent manual review.

Evaluation scenarios are not used to fit, tune, or calibrate the saved classifier. The leakage audit checks stripped, case-folded exact text only; it does not prove semantic independence.
