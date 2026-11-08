# Day 9 Release Readiness

## Scope and prototype disclaimer

SentinelAI is an academic prototype using synthetic scenarios and simulated tools. It is not production-certified and cannot guarantee prevention of prompt injection. Dashboard roles are caller-provided mock values, not authentication. No real external action is performed.

## Components verified

- [x] Python project and model/data artifacts are present in the repository.
- [x] FastAPI backend tests pass; live startup and endpoint smoke status is recorded below.
- [x] React/Vite production build passes.
- [x] API output-scan no longer includes raw matched examples; regression test covers repeated email and token matches.
- [x] SVM's raw signed decision score is no longer presented as an unbounded risk score; risk normalization is bounded and documented as non-probabilistic.
- [x] SQLite table is initialized by backend startup code; tests exercise persistence-backed routes.
- [x] Security invariant suite covers authorization, trust boundaries, tool restrictions, confirmation, output scan, and model failure.
- [ ] Faculty machine clean-install has not been independently performed unless verified by the presenter.

## Tests and checks executed

| Check | Command | Result |
|---|---|---|
| Backend + ML tests before the Day 9 regression test | `.\venv\Scripts\python.exe -m pytest backend ml -q` | 75 passed, 11 warnings (41.84 s). |
| Targeted output-scan tests after the fix | `.\venv\Scripts\python.exe -m pytest backend\tests\test_api_scan.py -q` | 7 passed, 3 warnings (4.27 s). |
| Frontend production build | `Set-Location frontend; npm run build` | Passed; Vite 6.4.5, 2,222 modules transformed, build completed in 5.84 s. |
| Initial incorrect frontend command | `npm run build` from repository root | Failed because the root has no `package.json`; rerun from `frontend` succeeded. |
| Final Python test suite | `.\venv\Scripts\python.exe -m pytest backend ml -q` | 76 passed, 1 warning (12.13 s). |
| Dependency consistency | `.\venv\Scripts\python.exe -m pip check` | No broken requirements found. |
| Final frontend production build | `Set-Location frontend; npm run build` | Passed; Vite 6.4.5, 2,222 modules transformed, build completed in 4.04 s. |
| Mock-agent demo | Public FAQ search through `SimulatedAgent` and registered tools | `ALLOW`, `search_public_documents`, `tool_executed=True`; local execution used bundled public mock documents only. |
| Live backend | `python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000`; `GET /health` | `ok`; database connected, security engine initialized, ML model loaded. |
| Live frontend | `npm run dev` from `frontend`; GET `http://127.0.0.1:5173` | HTTP 200; page title `SentinelAI · Security Console`. |
| Live security smoke | POST `/scan`, `/scan-output`, `/check-action` with synthetic prompt/data and mock viewer | Injection BLOCK; risk score 0.8398 (bounded); raw SVM decision 1.656559 labeled non-probability; output response contains no test email/token; viewer record access BLOCK. |
| Whitespace / patch check | `git diff --check` | Passed. |

The final Python run passed 76 tests with one AnyIO/Starlette deprecation warning in the installed test-client dependency. An earlier run before the timestamp cleanup had 11 warnings; event timestamps now use a UTC clock compatible with SQLite's naive `DateTime` column.

## Issues fixed in this preparation

- Removed raw sensitive matches from `/scan-output` finding records, redacted every match in returned text, and added a regression test.
- Added backend and testing dependencies to root `requirements.txt`.
- Added root `.env.example` and ignored local environment files while preserving safe examples.
- Reworked README claims, install instructions, architecture boundary, results, limitations, and references. No project license was added or claimed.
- Added the Day 9 audit, report support, architecture, demo, and release-readiness documents.
- Replaced deprecated event timestamp generation with an explicit UTC clock compatible with the SQLite column.
- Added sanitized server-side logging for health-check and unexpected API errors; internal exception details remain out of client responses and logs.

## Installation verification

- Python dependencies are represented in `requirements.txt`; the currently available local virtual environment is Python 3.12.
- Frontend lockfile exists at `frontend/package-lock.json`; `npm run build` succeeds with the installed dependencies.
- Backend can initialize SQLite tables through `create_db_and_tables()`.
- Live local URLs were checked below. A fresh dependency install (`pip install -r requirements.txt` and `npm ci`) was not run; verify those commands on the submission machine.

## Security invariant verification

| Invariant | Evidence |
|---|---|
| Viewer cannot execute administrator-only actions | Day 8 invariant test |
| Unknown roles and unknown tools are denied | Day 8 invariant tests |
| Low/benign ML risk cannot override policy denial | Day 8 policy-denial invariant test |
| REVIEW does not execute tools | Day 8 simulated-agent invariant test |
| Untrusted documents cannot grant permissions | Day 8 invariant test |
| Prompt cannot change separately supplied trusted role in the simulator | Day 8 invariant test |
| Sensitive tool output is scanned before being returned by the simulator | Day 8 invariant test |
| Destructive mock action requires explicit confirmation | Day 8 invariant test |
| Model failure blocks guarded operations | Day 8 invariant test |
| Output scan response does not echo email/token matches | Day 9 `test_scan_output_never_returns_sensitive_matches` |
| CORS is not unrestricted by origin | FastAPI CORS allowlist is limited to `localhost:5173` and `127.0.0.1:5173`; methods/headers remain wildcard within those origins |
| Mock tools do not call real external services | Source inspection of `backend/agent/mock_tools.py` and tool registry |

These tests establish only the tested cases, not comprehensive security.

## Remaining known issues and limitations

- Mock identity is not production authentication or authorization.
- Model and pattern checks have false positives/negatives; Day 8 synthetic ML+policy evaluation reports 80% false positives and only 52% legitimate-task completion.
- Six genuine dashboard screenshots are included; the terminal-only simulated agent is not pictured.
- No Day 4 or Day 7 standalone reports exist.
- SQLite file is checked in and contains synthetic/test event metadata; it should not be mistaken for a clean production database.
- Existing deprecation warnings remain as listed above.
- Project license is unspecified; no license was added.

## Screenshots and submission assessment

Six genuine local dashboard screenshots are in `docs/screenshots/`. They show the overview, prompt injection result, viewer denial, synthetic sensitive-data scan, event history, and historical model page. Event counts come from synthetic/test records in the checked-in local SQLite file. The simulated agent is terminal-only and is not pictured. See `docs/screenshots/README.md`.

**Readiness:** suitable for an academic local demonstration after confirming a clean setup on the faculty/demo machine and explaining prototype limitations. Not ready for production deployment. Before submission, the student should review every report citation, verify the captured screenshots render on the target machine, confirm institution formatting, and disclose that no real authentication or external tools are present.

## Final verification record

- Full tests: 76 passed, 1 dependency deprecation warning.
- Live backend: healthy; database and model loaded; API security smoke tests behaved as expected.
- Frontend: development URL returned HTTP 200; production build passed.
- Remaining errors: no observed startup/build/test errors. One dependency deprecation warning remains as listed above.
