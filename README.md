# SentinelAI

**An ML-powered security framework for detecting prompt injection and enforcing access control in AI agents**

SentinelAI is an academic prototype that combines a lightweight text classifier, sensitive-data checks, deterministic role-based policies, a FastAPI service, and a React dashboard. Its agent tools operate on synthetic in-memory records only. It is not production-certified and does not guarantee prevention of prompt injection.

## Abstract

AI agents can process user prompts and untrusted documents before proposing actions through tools. A malicious or misleading instruction can therefore influence model behavior or expose sensitive output. SentinelAI explores a layered defense: a TF-IDF text classifier provides a prompt-injection signal, sensitive-data detectors identify common patterns, and deterministic policy checks decide whether a role may request a named action. A simulated agent and mock tool registry support controlled evaluation without real external actions. The dashboard exposes scans, action authorization checks, event history, and recorded model/evaluation results.

## Problem, objectives, and proposed solution

**Problem.** A classifier alone cannot enforce authorization, while a role policy alone does not identify suspicious instructions or sensitive text. A false positive or false negative is possible in either detector.

**Objectives.**

- Evaluate a small, CPU-friendly prompt-injection classifier.
- Enforce role/action rules independently of model risk.
- Require explicit confirmation for destructive mock operations.
- Scan detected output for sensitive material before returning it from the simulated agent.
- Record security event metadata and provide a demonstrable dashboard.

**Proposed solution.** Use ML as a signal, not as the authorization authority. The policy engine denies unknown roles, unknown actions, and disallowed role/action pairs. The permission guard and output scanner add separate checks. All mock tools are local and synthetic.

## Features

- TF-IDF + Logistic Regression and Linear SVM experiment pipelines and saved artifacts.
- Prompt and document scanning, plus sensitive-data detection for prompts and output.
- Role-based action policy and explicit confirmation for simulated deletion.
- A simulated agent and allowlisted mock tools; no real email, network, shell, or external database action.
- FastAPI endpoints, SQLite event metadata, and a React/Vite dashboard.
- Synthetic Day 8 evaluation results and automated security-invariant tests.

## Architecture

The implemented service evaluates action requests but does **not** dispatch a tool from the dashboard. The separate simulated agent is exercised by the evaluation/tests. See the [architecture and workflow diagrams](docs/architecture.md) for this boundary and the ALLOW/BLOCK/REVIEW semantics.

```text
Browser / React Dashboard
        │ HTTP (localhost)
        ▼
FastAPI API ─────► SecurityService
                       ├── Prompt-injection model
                       ├── Sensitive-data detector
                       ├── Risk engine
                       └── Deterministic policy / permission guard
                              │
                              ├── Authorization result → API response
                              └── SimulatedAgent (evaluation harness only)
                                      ├── Registered mock tools
                                      └── Output security scan
        │
        └── SQLite event metadata
```

## Technologies

| Area | Technologies |
|---|---|
| API | Python 3.12, FastAPI, Pydantic, SQLAlchemy |
| ML/data | scikit-learn, TF-IDF, Logistic Regression, LinearSVC, pandas, NumPy, joblib |
| Persistence | SQLite |
| Dashboard | React, Vite, React Router, Recharts |
| Validation | pytest, FastAPI TestClient, Vite production build |

## ML methodology, dataset, and recorded results

The experiments use the `core` configuration of the [cyberec Prompt-injection-dataset](https://huggingface.co/datasets/cyberec/Prompt-injection-dataset), with the provided train/validation/test splits. The checked-in `ml/data/` directory contains CSV and Parquet partitions; preprocessing preserves punctuation and security-related words. TF-IDF uses unigrams and bigrams, `min_df=2`, up to 20,000 features, and sublinear term frequency. The Logistic Regression and LinearSVC pipelines use class-balanced weights. Threshold selection is based on validation data; test results are reported separately.

The existing Day 3 comparison reports 942 held-out test rows. At the default boundaries, Logistic Regression achieved 95.22% accuracy, 94.55% precision, 97.46% recall, 0.9599 F1, and 0.9937 ROC-AUC; LinearSVC achieved 95.22%, 94.71%, 97.28%, 0.9598, and 0.9943 respectively. The validation-selected SVM boundary is a **decision score**, not a probability. The API exposes the raw SVM decision score separately and uses a bounded monotonic normalization for risk aggregation; that normalized score is not a calibrated probability. These are historical experiment results, not a fresh benchmark from this Day 9 preparation. See [Day 3 model comparison](docs/day3_model_comparison.md) and [Day 8 evaluation](docs/day8_security_evaluation.md) for methods, confusion matrices, and caveats.

Day 8's synthetic 130-scenario evaluation reports 98.3% attack detection and 100% unauthorized-action prevention for its ML-plus-policy configuration, alongside an 80% false-positive rate and 52% legitimate-task completion. These synthetic scenario results are not production effectiveness estimates; labels are hand-authored and require human review. Full denominators and definitions are in the report.

## Security workflow

1. Validate request shape and length at the API boundary.
2. Analyze prompt/document content with the ML detector and sensitive-data detector.
3. Evaluate the named role/action against deterministic policy.
4. Deny a policy failure regardless of ML score; do not execute on REVIEW.
5. For simulated-agent tests, invoke only a registered mock tool after authorization.
6. Scan mock output before returning it; replace detected output matches.
7. Persist event metadata, not the complete prompt or output.

The API's role is caller-supplied mock context, **not authenticated identity**. See [known limitations](#limitations).

## API overview

Run the API locally and open `http://127.0.0.1:8000/docs` for the generated OpenAPI page.

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | API status banner |
| GET | `/health` | Database, engine, and model status |
| POST | `/scan` | Prompt and sensitive-input analysis |
| POST | `/scan-output` | Sensitive output scan and redaction |
| POST | `/scan-document` | Untrusted document analysis |
| POST | `/check-action` | Authorization evaluation and event record; does not execute tools |
| GET | `/events` | Filtered/paginated security event metadata |
| GET | `/events/{request_id}` | Event lookup |
| GET | `/stats` | Aggregate event counts |
| GET | `/evaluation/summary` | Existing synthetic evaluation summary |

## Windows installation and run

Use Python 3.12 (the repository's recorded FastAPI environment) and Node.js/npm. The checked-in ML artifacts are loaded at runtime; training is optional.

From the repository root in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example frontend\.env.local
```

In the first PowerShell terminal, start the backend from the repository root:

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
Set-Location frontend
npm ci
npm run dev
```

Open the dashboard at `http://127.0.0.1:5173`, API health at `http://127.0.0.1:8000/health`, and API docs at `http://127.0.0.1:8000/docs`. The API binds to loopback for local demonstration. For an existing `venv`, activate that environment instead of creating `.venv`.

## Testing and model commands

From the repository root:

```powershell
python -m pytest backend ml -q
```

Build the dashboard:

```powershell
Set-Location frontend
npm ci
npm run build
```

Optional model workflow (uses checked-in data; training overwrites the corresponding model artifact and metadata):

```powershell
Set-Location ..
python ml\preprocess_data.py --config core
python ml\train.py --config core --max-features 20000 --random-state 42
python ml\evaluate.py --config core
```

## Screenshots

Genuine local dashboard captures are in [docs/screenshots/](docs/screenshots/): overview, prompt-injection result, viewer action denial, sensitive-data scan, security events, and historical model performance. The overview/event counts reflect synthetic/test records in the local SQLite database. The simulated agent has no dashboard execution page, so its terminal demonstration is not represented by a screenshot. See the [capture notes](docs/screenshots/README.md).

## Results and observations

- The existing held-out model comparison is documented in `docs/day3_model_comparison.md`; Day 8 synthetic evaluation is documented in `docs/day8_security_evaluation.md`.
- The current source test suite and dashboard build are rerun as part of this preparation; see [release readiness](docs/day9_release_readiness.md) for actual run results.
- Synthetic results show a trade-off between attack detection and legitimate-task completion. The classifier is not a standalone security boundary.

## Limitations

- Academic prototype only; no production authentication, user/session authorization, deployment hardening, or production monitoring.
- Prompt-injection detection is statistical and can miss novel or context-dependent attacks; no guarantee of comprehensive prevention.
- Mock identities and tools are demonstrative only. The `/check-action` API evaluates and logs; it does not run the simulated tools.
- Sensitive-data matching is pattern-based and cannot identify every secret or every context.
- SQLite is suitable for the local demo, not a production audit service. Event records use mock identity text provided by the caller.
- Day 8 scenario labels are synthetic assumptions, not an independently adjudicated real-world test set.
- The dashboard's model-performance view is historical reporting, not a live benchmark.
- The project repository does not include a project license. Do not assume the dataset's license applies to this code.

## Future scope

Independent review of scenario labels, broader and context-aware evaluation, authenticated identity and server-side authorization, configurable retention, stronger output handling, deployment controls, and safe integration tests for a real agent in an isolated environment.

## References

1. Dataset: [cyberec/Prompt-injection-dataset](https://huggingface.co/datasets/cyberec/Prompt-injection-dataset); local provenance and split audit: [Day 1 dataset report](docs/day1_dataset_report.md).
2. OWASP, [Top 10 for Large Language Model Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/).
3. Greshake et al., [“Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection”](https://arxiv.org/abs/2302.12173), arXiv:2302.12173, 2023.
4. Salton and Buckley, “Term-weighting approaches in automatic text retrieval,” *Information Processing & Management*, 24(5), 513–523, 1988, [doi:10.1016/0306-4573(88)90021-0](https://doi.org/10.1016/0306-4573(88)90021-0).
5. Scikit-learn documentation: [text feature extraction](https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction), [LogisticRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html), and [LinearSVC](https://scikit-learn.org/stable/modules/generated/sklearn.svm.LinearSVC.html).
6. Sandhu et al., “Role-Based Access Control Models,” *Computer*, 29(2), 38–47, 1996, [doi:10.1109/2.485845](https://doi.org/10.1109/2.485845).
7. Official documentation: [FastAPI](https://fastapi.tiangolo.com/), [React](https://react.dev/), [Vite](https://vite.dev/), and [SQLite](https://www.sqlite.org/).

## Additional submission documents

- [Project audit](docs/day9_project_audit.md)
- [Final report support](docs/final_project_report.md)
- [Architecture diagrams](docs/architecture.md)
- [5–7 minute demo script](docs/day9_demo_script.md)
- [Release readiness and verification](docs/day9_release_readiness.md)
