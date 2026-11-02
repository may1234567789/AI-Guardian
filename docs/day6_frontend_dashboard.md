# Day 6: SentinelAI Security Dashboard

## Overview

The Day 6 dashboard is a responsive React single-page application built with Vite. It consumes the existing FastAPI service; it does not replace or duplicate backend authorization, prompt analysis, or event storage.

## Architecture and technology

- React 18 and Vite with JavaScript.
- React Router routes for each dashboard page.
- A centralized Fetch API service in `frontend/src/services/api.js` with JSON error handling and a 12-second request timeout.
- Recharts for aggregate decision, risk, category, and historical model visualizations.
- Lucide React for interface icons and plain CSS for the responsive dark theme.
- Configurable backend URL: `VITE_API_BASE_URL` (defaults to `http://127.0.0.1:8000`) or the Settings page. The Settings page stores only the API base URL in browser local storage; prompt and output text are not persisted.

## Pages

| Route | Purpose |
| --- | --- |
| `/` | Live backend status, `/stats`, latest event aggregates, recent audit events, and quick links. |
| `/scanner` | Sends prompt text to `POST /scan`; shows backend decision, score, detector output, and reasons. |
| `/authorization` | Sends a development mock identity and proposed action to `POST /check-action`; the action is evaluated only and never executed. |
| `/data-leak` | Sends output text to `POST /scan-output`; displays finding types/counts and redaction placeholders, not raw API-returned examples. |
| `/events` | Filters and pages through `GET /events`; fetches selected event metadata from `GET /events/{request_id}`. |
| `/models` | Displays historical measured results from Day 2/Day 3 experiment reports. The SVM score is identified as a decision score, not a probability. |
| `/settings` | Tests the configured API URL and shows fields from `GET /health`, mock roles, and policy limitations. |

Reusable UI includes the navigation shell, connection and decision badges, feedback states, event table, and risk-score summary.

## Backend communication

The API client calls the existing endpoints with their implemented request shapes:

- `GET /health`
- `GET /stats`
- `POST /scan` with `prompt`, `user_context`, and `source`
- `POST /scan-output` with `output_text` and `source`
- `POST /check-action` with `prompt`, `proposed_action`, `user_context`, `user_role`, `resource_context`, and `confirm_delete`
- `GET /events` with `decision`, `event_type`, `limit`, and `offset`
- `GET /events/{request_id}`

The backend CORS allowlist includes both `http://localhost:5173` and `http://127.0.0.1:5173`. API errors are displayed as errors; the UI does not fabricate successful responses. Event type/risk distribution charts use only the latest 200 returned events, while decision totals use the backend aggregate endpoint.

## Security and known limitations

- The role selector submits a mock development identity and is not authentication. Backend policy remains authoritative.
- The dashboard does not execute proposed actions or edit backend policies.
- Output-scan findings can include raw examples in the API response. The UI intentionally omits those fields and displays only category/count information and fixed redaction placeholders.
- The backend event endpoint provides offset pagination but no total matching-record count; the UI therefore shows the current page size rather than a fabricated total.
- The model page is historical experiment reporting, not a live benchmark. It uses `ml/reports/day3_model_comparison.json` measured results represented in `frontend/src/data/modelMetrics.json`.
- No screenshots are versioned; the dashboard was also checked in a local browser at desktop and mobile widths.

## Run locally

Start the backend from the repository root in one PowerShell terminal:

```powershell
$env:PYTHONPATH = "."
.\venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Dashboard: `http://127.0.0.1:5173`
Backend docs: `http://127.0.0.1:8000/docs`

## Validation and execution checklist

- [x] Existing backend endpoints and response schemas inspected.
- [x] Existing frontend checked; only a placeholder was present.
- [x] React/Vite app, routing, shell, and responsive navigation implemented.
- [x] Overview uses backend health, statistics, and events.
- [x] Prompt scanner connected to `POST /scan`, including empty-input and API-error states.
- [x] Action authorization connected to `POST /check-action`, including mock identity and delete confirmation.
- [x] Data-leak scanner connected to `POST /scan-output`; raw finding examples are withheld.
- [x] Security events connected to list and detail endpoints, with filters and offset pagination.
- [x] Model metrics use recorded Day 2/Day 3 experiment values; missing numeric values render as `N/A`.
- [x] Settings page shows health fields and allows the API base URL to be updated.
- [x] Loading, empty, and error states implemented.
- [x] Responsive layouts and keyboard focus styles added.
- [x] Frontend build verified.
- [x] Backend tests and representative API integration checks verified.
- [x] README updated with backend/frontend commands and dashboard URL.
- [x] Browser checks covered overview, benign and suspicious prompt scans, synthetic email/key redaction, denied action and delete confirmation, event filtering/details, backend failure/recovery, and mobile navigation/layout.
