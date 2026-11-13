# Day 9: SentinelAI UI Redesign

## Previous design observations

- The dark UI relied on gradients, tinted surfaces, rounded cards, and accent colors in too many places.
- The overview used six individual statistic cards and several charts, splitting attention between data with different scopes.
- Navigation was a flat list, and the top bar did not clearly identify the local/development environment.
- Table-heavy pages were difficult to scan at narrower widths, and the dashboard table carried more columns than its compact context needed.
- Risk scores and model decisions needed clearer separation from calibrated probabilities and end-to-end security outcomes.

## Design direction

The redesign uses a restrained Apple Minimal treatment: a luminous white canvas, flat white surfaces, subtle gray borders, and Apple blue for navigation and primary actions. Green, amber, and red are reserved for operational states and security decisions. Typography and alignment provide hierarchy instead of glow, gradients, or oversized panels.

Shared CSS variables define the palette in `frontend/src/styles.css`. SF Pro system fonts, a 33 px page-title scale, spacious section headings, capsule primary actions, and quiet 8 px cards carry the visual hierarchy; IDs and technical values use monospace. Tables remain horizontally scrollable when necessary; the overview uses a compact table variant. The mobile sidebar is hidden when closed, and reduced-motion preferences are respected.

## Pages redesigned

- **Security Overview:** real aggregate event counts, backend connection state, recent events, decision distribution, detector counters, and the number of action checks in the latest loaded events.
- **Prompt Scanner:** existing scan flow and examples retained; risk score is identified as an aggregated backend score, and the SVM decision score remains explicitly non-probabilistic.
- **Data Leak Scanner:** existing scan flow retained; the response’s redacted text is shown without echoing the original input.
- **Action Authorization:** existing role/action/resource inputs and backend policy evaluation retained; action labels are more readable.
- **Security Events:** backend decision/type filters retained, with search and risk filters scoped to the currently loaded page; event details and request-ID copy are available.
- **Model Performance:** existing historical metrics retained; confusion matrices use recorded Day 3 held-out counts, and a note distinguishes classifier metrics from system-level security effectiveness.
- **Security Evaluation:** saved Day 8 evaluation results remain sourced from the backend and use the shared chart palette.
- **Settings:** backend URL and health behavior retained; project/environment/model provenance is shown without adding fictitious controls.

The requested Agent Simulator was not added: the repository has no frontend route or HTTP endpoint for running the internal simulator. Adding a local imitation would imply execution that the existing API does not provide, so this redesign leaves the API contract unchanged. The existing evaluation page continues to show saved simulated-agent experiment results.

## Components and files

- `frontend/src/components/Shell.jsx`: grouped navigation, active-page breadcrumb, environment and connection indicators.
- `frontend/src/components/Feedback.jsx`: clearer assessment hierarchy and explicit risk-score semantics.
- `frontend/src/components/SecurityEventTable.jsx`: compact table variant, copy-ID feedback, and event-detail action.
- `frontend/src/pages/Overview.jsx`, `SecurityEvents.jsx`, `DataLeakScanner.jsx`, `ActionAuthorization.jsx`, `ModelPerformance.jsx`, `EvaluationDashboard.jsx`, and `Settings.jsx`: page-specific layout and data presentation.
- `frontend/src/styles.css`: centralized tokens, compact surfaces, responsive layout, focus visibility, and reduced-motion behavior.
- `frontend/src/data/modelMetrics.json`: confusion-matrix counts from the saved Day 3 comparison report.

No dependencies, backend endpoints, response schemas, or routes were changed.

## Screenshots

Captured local browser screenshots at 1440 × 1000:

- [Overview](./screenshots/day9-overview.png)
- [Prompt scanner](./screenshots/day9-prompt-scanner.png)
- [Data leak scanner](./screenshots/day9-data-leak-scanner.png)
- [Action authorization](./screenshots/day9-action-authorization.png)
- [Security events](./screenshots/day9-security-events.png)
- [Model performance](./screenshots/day9-model-performance.png)
- [Security evaluation](./screenshots/day9-evaluation.png)
- [Settings](./screenshots/day9-settings.png)

The screenshots show the current local database contents; they are development/demo data, not production traffic.

## Validation performed

- `npm run build` in `frontend/` — passed.
- `git diff --check` — passed.
- Started the existing local API and Vite frontend. `GET /health`, `GET /stats`, and `GET /events` returned successfully.
- Opened all eight implemented routes at desktop and 390 × 844 mobile sizes. All returned HTTP 200, rendered the expected page heading, had no page-level JavaScript errors, and had no document-level horizontal overflow.
- Tested the benign example prompt scan and verified the backend assessment/model details rendered.
- Tested the synthetic-email output scan and verified the returned text contained `[REDACTED]` rather than the original email.
- Evaluated a permitted analyst action and verified the policy explanation and backend decision rendered.
- Tested event search, event detail expansion, request-ID copy feedback, and Settings “Save and test.”
- Captured screenshots for all eight routes and visually reviewed the overview, scanners, events, model, evaluation, and settings captures.

## Remaining issues

- Search and risk filters on Security Events apply to the currently loaded page; the backend does not expose a risk-filter parameter or free-text search.
- There is no dashboard Agent Simulator route/API. A genuine interactive simulator requires a separately scoped backend integration.
- During the benign prompt smoke test, the backend returned a suspicious SVM classification while its overall reason stated no suspicious indicators. The UI preserves the detector fields and backend reason separately rather than rewriting the API result; this response inconsistency should be addressed in backend behavior.
- No automated frontend test suite is configured; validation above is a build and local browser smoke test.
