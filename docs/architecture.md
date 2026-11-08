# SentinelAI Architecture and Security Workflow

## Implemented architecture

The `/check-action` route evaluates and logs a proposed action; it does not call `SimulatedAgent` or execute a tool. `SimulatedAgent` is exercised by evaluation and security tests. This distinction prevents the diagram from implying a live external-agent integration.

```mermaid
flowchart TD
    U[User / Evaluator] --> D[React Dashboard]
    D -->|HTTP JSON| API[FastAPI]
    API --> S[SecurityService]
    S --> M[Prompt Injection Detector<br/>TF-IDF + LinearSVC]
    S --> L[Sensitive Data Detector]
    S --> R[Risk Engine]
    S --> P[Policy Engine]
    P --> G[Permission Guard]
    G -->|decision| API
    API --> DB[(SQLite Event Metadata)]
    API --> D

    subgraph Evaluation and tests only
      H[Evaluation Harness] --> A[Simulated Agent]
      A --> G
      G -->|ALLOW only| T[Allowlisted Mock Tool Registry]
      T --> O[Output Security Scan]
      O --> H
    end
```

### Main components

- **React/Vite dashboard:** submits scans and action authorization checks, presents event history and recorded model/evaluation data.
- **FastAPI:** validates request models, routes API calls, returns health/scan/authorization/event results.
- **SecurityService:** coordinates prompt/data checks and action evaluation.
- **Prompt detector:** loads a saved scikit-learn pipeline. The selected LinearSVC emits a signed decision score, not a probability.
- **Policy engine and permission guard:** deterministic least-privilege checks; policy denial cannot be overridden by a benign ML score.
- **Simulated agent:** separate in-process test/evaluation path; registered tools only, all local/mock.
- **SQLite:** persists event metadata and summaries; complete prompt/output text is not intended to be stored.

## Data-flow diagram

```mermaid
flowchart LR
    IN[Prompt or document] --> VALIDATE[Request schema and length validation]
    VALIDATE --> DETECT[ML prompt analysis]
    VALIDATE --> SENSITIVE[Sensitive-data analysis]
    DETECT --> RISK[Risk result]
    SENSITIVE --> RISK
    RISK --> POLICY[Role/action policy evaluation]
    POLICY --> DECISION{Final decision}
    DECISION -->|ALLOW| RESP[Return authorization result]
    DECISION -->|BLOCK| RESP
    DECISION -->|REVIEW| RESP
    RESP --> EVENT[Log summary metadata]
    EVENT --> DASH[Dashboard]
```

In the separate simulated-agent harness, an ALLOW result can dispatch a registered mock action; BLOCK and REVIEW do not dispatch. Mock output is scanned before it is returned. The API's `/check-action` endpoint itself is non-executing.

## Security workflow

```mermaid
flowchart TD
    START[Request received] --> SHAPE{Input valid?}
    SHAPE -->|No| REJECT[Reject request]
    SHAPE -->|Yes| POLICY{Known role/action and policy permits?}
    POLICY -->|No| BLOCK[BLOCK: no tool execution]
    POLICY -->|Yes| MODEL{Model available?}
    MODEL -->|No| BLOCK
    MODEL -->|Suspicious sensitive action| BLOCK
    MODEL -->|Suspicious, needs review| REVIEW[REVIEW: no tool execution]
    MODEL -->|Acceptable| CONFIRM{Destructive action?}
    CONFIRM -->|Yes, not confirmed| BLOCK
    CONFIRM -->|No or explicitly confirmed| ALLOW[ALLOW]
    ALLOW --> EXEC[Mock tool only in evaluation harness]
    EXEC --> SCAN[Scan output for sensitive material]
    SCAN --> RETURN[Return safe result and log metadata]
    BLOCK --> RETURN
    REVIEW --> RETURN
```

### Decision meanings

| Decision | Meaning | Tool execution |
|---|---|---|
| **ALLOW** | Policy permits the known action and available checks do not require a deny/review. | Permitted only in the simulated-agent harness; dashboard `/check-action` only reports the decision. |
| **BLOCK** | Invalid or policy-denied request, detector failure, suspicious protected action, or unconfirmed destructive action. | Never. |
| **REVIEW** | Additional human assessment is required for suspicious or sensitive content. | Never automatically. |

These are prototype behaviors; the workflow is not a certification or guarantee that all attacks are detected.

## Use-case diagram

```mermaid
flowchart LR
    Student[Student / Evaluator]
    Admin[Mock admin]
    Viewer[Mock viewer]
    Scan((Scan prompt or output))
    Check((Check proposed action))
    Events((View event history))
    Metrics((View historical metrics))
    Sim((Run synthetic agent evaluation))
    Student --> Scan
    Student --> Check
    Student --> Events
    Student --> Metrics
    Student --> Sim
    Admin --> Check
    Viewer --> Check
```

## Trust boundaries and scope

- HTTP traffic is intended for loopback during the demonstration; CORS allows the two Vite localhost origins.
- `user_role` and user context are mock values provided by a client, not verified credentials.
- Prompt/document text is untrusted. Documents cannot grant permissions or change the separately supplied server-side role in the simulator.
- Tool registry entries are fixed in-process functions; no arbitrary shell/network execution is implemented.
- Evaluation cases and model benchmark labels are synthetic/provided dataset labels and have limitations described in the reports.
