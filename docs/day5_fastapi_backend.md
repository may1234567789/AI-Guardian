# Day 5: FastAPI Backend for SentinelAI

## Overview

This document records the FastAPI backend implementation for SentinelAI. The backend reuses the verified Day 4 security engine instead of re-implementing prompt injection, data leak detection, policy evaluation, or permission gating logic.

## Architecture

The backend is organized into these layers:

- API routers in `backend/api/`
- Request/response models in `backend/schemas/`
- Business logic in `backend/services/`
- SQLite persistence in `backend/database/`
- Existing security logic preserved in `backend/security/`

## Components reused from Day 4

- `PromptDetector`: loads the saved SVM model and classifies suspicious prompts.
- `DataLeakDetector`: scans for emails, phone numbers, API keys, and sensitive keywords.
- `PolicyEngine`: authorizes actions based on user role and action permissions.
- `RiskEngine`: combines ML and leak detection with policy checks.
- `PermissionGuard`: enforces high-impact action blocks when suspicious prompts are detected.

## API endpoints

### GET `/`
Returns a basic API banner.

### GET `/health`
Reports database connectivity, engine initialization, and model loading status.

### POST `/scan`
Evaluates a prompt for injection and sensitive-data content.

### POST `/scan-output`
Scans generated AI output for leaked credentials, email addresses, phone numbers, and confidential phrases.

### POST `/scan-document`
Checks untrusted document text for suspicious instructions and sensitive data.

### POST `/check-action`
Checks and logs whether an AI agent action is permitted under policy and risk checks.

### GET `/events`
Lists paginated security events.

### GET `/events/{request_id}`
Retrieves a specific event by request ID.

### GET `/stats`
Returns aggregate event statistics derived from the SQLite database.

## Database design

SQLite is used with SQLAlchemy via `backend/database/database.py` and `backend/database/models.py`.

The `security_events` table stores:

- request_id
- timestamp
- event_type
- pseudonymous_user_id
- user_role
- action
- risk_score
- risk_level
- decision
- reason
- policy_id
- request_summary

The system stores only redacted or summary metadata instead of full prompts or raw secrets.

## Security controls

- Prompt injection detection via the existing ML model
- Sensitive-data redaction and detection
- Role-based action policy enforcement
- Destructive actions require explicit confirmation
- No storage of raw passwords, API keys, or complete prompts
- CORS restricted to `http://localhost:5173`
- Input length limits implemented through Pydantic validation

## Error handling

The API uses HTTP status codes for malformed requests and missing resources. Internal errors produce a safe generic response without exposing internal traces.

## Testing

The backend was validated using pytest with FastAPI TestClient. The test suite covers health, scan, output scan, action evaluation, event listing, and stats endpoints.

## Known limitations

- This is a development prototype, not production authentication.
- No real network calls, email sending, or external database access are performed.
- Uploaded document extraction is intentionally limited to direct text input only.
- Rate limiting is not implemented for this prototype.

## Frontend integration

A frontend can call the backend with JSON payloads and rely on the request IDs returned in the responses for audit tracking.
