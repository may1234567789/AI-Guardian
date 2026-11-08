# Day 9 Project Audit

## Scope and evidence

This audit examines the checked-in source, reports and saved artifacts, then verifies runtime behavior with tests and a production frontend build. The Day 1, 2, 3, 5, 6, and 8 reports were read. No Day 4 or Day 7 report was present; those components were assessed from source and tests instead. A report's claims are treated as recorded historical results unless independently rerun.

## Component status

| Component | Status | Evidence / remaining work |
|---|---|---|
| Project structure | Implemented and working | Python packages under `backend/` and `ml/`; React/Vite app under `frontend/`; documentation under `docs/`. |
| Backend | Implemented; verified by tests | FastAPI app, request schemas, routers, services, and lifecycle/database setup are present. Full test results are recorded in [release readiness](day9_release_readiness.md). Live-run verification is recorded there once completed. |
| Frontend | Implemented; build verified | React/Vite routes and centralized API client exist. Build output is generated locally and ignored. The UI's role selector is a mock identity, not authentication. |
| ML models and artifacts | Implemented and loadable | Logistic Regression and LinearSVC joblib pipelines and metadata are checked in. Existing API/security tests load the configured model. Historical metrics are documented in Day 2/3 reports; no fresh benchmark is claimed here. |
| Dataset and preprocessing | Implemented | Core/full CSV and Parquet splits and preprocessing/audit scripts are present. The Day 1 report documents dataset provenance and split checks. |
| Security engine | Implemented; invariants tested | Prompt/data detectors, risk engine, policy engine, and permission guard are present. A raw-sensitive-match response issue in `/scan-output` was fixed and regression-tested for Day 9. |
| Simulated agent and tools | Implemented; synthetic-only | Agent and allowlisted mock tools use in-memory/public fixture data. The dashboard action endpoint only evaluates authorization; it does not dispatch these tools. |
| Database and event logging | Implemented and tested | SQLAlchemy creates a SQLite database/table on initialization. Events store summary metadata rather than full prompt/output text. The checked-in database contains synthetic/test event metadata; it is not an authoritative empty production log. |
| API endpoints | Implemented and tested | Root, health, scan, scan-output, scan-document, check-action, events, stats, and evaluation summary routes are present. |
| Tests | Implemented; actual run recorded | Backend and ML tests plus Day 8 invariant tests are included. See release-readiness test results for final counts and warnings. |
| Documentation | Partially present before Day 9; expanded | Day 1–3, Day 5–6, and Day 8 reports existed. Day 4/7 summaries and screenshots were absent. This preparation adds submission-focused documents without overwriting prior reports. |

## Security invariants checked

The existing Day 8 tests cover viewer denial, unknown roles/tools, policy denial independent of a benign model result, REVIEW non-execution, document trust boundaries, server-side role separation, output scanning, destructive confirmation, and fail-closed model errors. They use synthetic inputs and mock tools. The Day 9 API regression test additionally verifies that the output-scan response does not return matched email/token strings and redacts repeated matches.

The invariant suite is not proof of comprehensive security. The API's role is client-provided demo context, not authenticated identity; no dashboard request performs a real agent action.

## Audit findings and fixes

1. **Fixed — output scan included raw matches in API findings.** `/scan-output` now returns finding type/count only and redacts all matches in returned text. Regression test added.
2. **Fixed — SVM decision score was displayed as a risk score and could exceed 1.** The raw signed score is now separately identified; a bounded monotonic normalization is used for risk aggregation and is explicitly not labeled a probability.
3. **Fixed — backend dependencies were missing from root requirements.** FastAPI, Uvicorn, SQLAlchemy, Pydantic, HTTPX, and pytest requirements are included alongside ML dependencies.
4. **Fixed — README described an Apache-licensed project although no project license file was present.** README now says no project license is included and separates dataset provenance from code licensing.
5. **Known limitation — development identity is not authentication.** Do not expose this service as a production authorization boundary.
6. **Known limitation — simulated-agent execution has no dashboard page.** Genuine captures of the other live dashboard views are included; the simulator is demonstrated from a terminal command instead.
7. **Fixed — event creation used deprecated naive `utcnow()`.** It now uses an explicit UTC clock while retaining SQLite-compatible naive timestamps.
8. **Fixed — broad API/health exception handlers did not log failures.** They now log sanitized request path and exception type without returning internal details to clients.

## Prior reports

- Present: `day1_research_notes.md`, `day1_dataset_report.md`, `day2_model_report.md`, `day3_model_comparison.md`, `day5_fastapi_backend.md`, `day6_frontend_dashboard.md`, `day8_security_evaluation.md`.
- Not present: standalone Day 4 and Day 7 reports.
- Historical experiment artifacts remain in `ml/reports/` and `backend/evaluation/results/`. Their values are not represented as a new Day 9 experiment.

## Submission assessment

The project has a demonstrable local prototype, buildable frontend, tests, saved CPU model artifacts, sample data, and a documented synthetic security evaluation. It is suitable for academic demonstration **with limitations disclosed**. Final readiness depends on the live startup/smoke checks and the user's own environment and screenshot verification recorded in [release readiness](day9_release_readiness.md).
