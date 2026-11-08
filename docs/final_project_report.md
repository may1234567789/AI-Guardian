# SentinelAI — Final Project Report Support

This document provides structured, evidence-bounded report material. It is not a claim of production effectiveness. Replace institution-specific title-page details, supervisor details, and student information yourself; none are invented here.

## Chapter 1: Introduction

### Background of AI-agent security

AI agents combine language-model inputs with tools such as search, record access, or messaging. The tool boundary makes authorization, untrusted-input handling, and output inspection important: model-generated or user-supplied language must not itself grant authority.

### Prompt injection

Prompt injection is an attempt to influence an AI system by placing instructions in user input or content the system processes. In indirect prompt injection, instructions may be embedded in retrieved or supplied content. Detection is context-sensitive, so text classification is an indicator rather than a complete defense.

### Importance of access control and motivation

A prompt classifier answers whether text resembles patterns in its training data; it does not decide whether a user is allowed to perform an action. SentinelAI explores layered defenses in which a deterministic role/action policy remains authoritative while ML and sensitive-data scans supply additional risk signals.

## Chapter 2: Problem Statement and Objectives

### Existing challenges

- Prompt classifiers can have false positives and false negatives and may not generalize to unseen attacks.
- Broad keyword rules can block benign discussion or miss paraphrased requests.
- Model confidence cannot replace identity verification and explicit authorization.
- Sensitive information can occur in model/tool output even when input is acceptable.

### Problem definition

Develop and evaluate a lightweight academic prototype that analyzes prompts, checks sensitive-data patterns, evaluates named actions using role policy, and demonstrates safe handling using only synthetic tools and local event logging.

### Objectives

1. Build CPU-friendly text-classification baselines.
2. Apply deterministic role/action policy checks.
3. Detect common sensitive text patterns in inputs and outputs.
4. Demonstrate ALLOW, BLOCK, and REVIEW behaviors using an API and dashboard.
5. Evaluate behavior with held-out dataset examples, automated tests, and explicitly synthetic scenarios.

### Scope

Local prototype only. No production authentication, real AI model/agent connection, real email delivery, external document fetch, or real destructive operation is included.

## Chapter 3: Literature Review

### Prompt injection

Prompt injection research describes how attacker-controlled instructions can influence LLM-integrated applications, including through indirect content. Greshake et al. provide a threat analysis of indirect prompt injection in real-world LLM-integrated applications [3]. OWASP tracks prompt injection as a major LLM application risk [2]. Neither source implies that a classifier alone provides a complete mitigation.

### ML text classification, TF-IDF, Logistic Regression, and Linear SVM

TF-IDF weights terms by their occurrence in a document relative to a collection; term weighting is a long-standing information retrieval technique [4]. SentinelAI converts text into unigram/bigram TF-IDF vectors and compares Logistic Regression with LinearSVC using scikit-learn implementations [5]. LinearSVC returns a decision score, not a calibrated probability. The model results in this project are benchmark-specific and do not establish real-world robustness.

### Role-based access control and policy enforcement

Role-based access control assigns permissions to roles rather than accepting authority from free-form text. Sandhu et al. describe foundational RBAC models [6]. SentinelAI uses a small deterministic role/action mapping, unknown role/action denial, and explicit confirmation for simulated deletion. This does not provide production identity management.

### Literature review boundary

The above references provide foundational context, not a systematic literature review. A formal academic survey, citation-style requirements, and institution-specific formatting remain for the student to complete.

## Chapter 4: System Analysis and Design

### Existing system

An unprotected language agent can treat untrusted instructions as actionable; a standalone classifier or keyword filter does not provide complete authorization, data protection, or auditability.

### Proposed system

SentinelAI combines an ML detector, sensitive-data checks, risk aggregation, deterministic policy, a permission guard, mock agent tools, output scanning, SQLite event metadata, and a React dashboard. The dashboard's action API reports authorization only; the simulated agent is invoked in evaluation/tests.

### Functional requirements

- Accept bounded prompt, output, document, and action-check inputs.
- Return detector/policy decisions with reasons and risk metadata.
- Deny unknown/disallowed actions and require explicit destructive-action confirmation.
- Scan mock output before returning it from the simulated agent.
- Persist security event summaries and provide event/statistics APIs.
- Present scans, authorization, event, and historical model/evaluation views.

### Non-functional requirements

- Run locally on a CPU-only Windows machine with modest memory.
- Keep tool implementations local and non-external.
- Validate API inputs and avoid logging full prompt/output content.
- Expose explicit API errors and dashboard loading/error states.
- Keep experimental results traceable to reports and saved artifacts.

### Architecture, DFD, use cases, and security workflow

See the Mermaid diagrams in [architecture.md](architecture.md). That document explicitly distinguishes the action-check API from the separate simulated-agent evaluation harness.

## Chapter 5: Implementation

### Dataset preprocessing and model training

The project uses the `core` configuration of the `cyberec/Prompt-injection-dataset`, stored as CSV/Parquet. The provided preprocessing scripts inspect split integrity and preserve punctuation/security tokens. TF-IDF uses unigrams and bigrams. Logistic Regression and LinearSVC pipelines use class balancing; the saved SVM uses a validation-selected signed decision threshold. See [Day 1 dataset report](day1_dataset_report.md), [Day 2 model report](day2_model_report.md), and [Day 3 comparison](day3_model_comparison.md).

### Prompt injection and sensitive-data detection

`PromptDetector` loads a saved scikit-learn pipeline. `DataLeakDetector` checks common email, phone, token/key, financial identifier, and confidentiality patterns. These are pattern/model indicators and do not prove all sensitive data or attacks will be recognized.

### Risk, policy, and permission guard

The risk and permission components keep deterministic role/action denials authoritative. Unknown roles/actions are denied; model-load errors fail closed for guarded actions; destructive mock operations require explicit confirmation. REVIEW is not an execution authorization.

### FastAPI, React, simulated agent, mock tools, and SQLite

FastAPI validates and routes requests. React/Vite displays backend results. The simulated agent uses a controlled registry of mock in-memory tools; no real external actions are performed. SQLite stores event metadata and short request summaries rather than full prompts or output. The API role is mock context, not authenticated identity.

## Chapter 6: Testing and Results

### Test categories

The repository includes unit tests for model/data/security functions, API tests using FastAPI TestClient, and security-invariant tests covering role/action denial, REVIEW non-execution, document trust, output scanning, destructive confirmation, and model failure. The exact test commands and Day 9 results appear in [release readiness](day9_release_readiness.md).

### Held-out model comparison (historical recorded result)

The Day 3 report compares both models on 942 held-out examples:

| Model / threshold | Accuracy | Precision | Recall | F1 | ROC-AUC | TN, FP, FN, TP |
|---|---:|---:|---:|---:|---:|---|
| Logistic Regression default | 95.22% | 94.55% | 97.46% | 0.9599 | 0.9937 | 359, 31, 14, 538 |
| LinearSVC default | 95.22% | 94.71% | 97.28% | 0.9598 | 0.9943 | 360, 30, 15, 537 |
| Logistic Regression, validation-selected | 94.69% | 98.64% | 92.21% | 0.9532 | — | 359, 7, 43, 509 |
| LinearSVC, validation-selected decision score | 95.33% | 94.88% | 97.28% | 0.9606 | — | 361, 29, 15, 537 |

These are values from the existing Day 3 report, not measurements rerun for this report. For selected thresholds, precision/recall/F1/accuracy are documented; the table uses the report's confusion matrices. The SVM threshold is not a probability threshold.

### Synthetic Day 8 evaluation

The existing Day 8 report describes 130 synthetic cases per configuration and reports for ML plus deterministic policy: 98.3% attack detection, 100% unauthorized-action prevention, 52.0% legitimate-task completion, 80.0% false-positive rate, and 1.7% false-negative rate. This evaluation uses hand-authored labels and mock tools, and is not representative evidence for production traffic. The report notes an internal 120-vs-130 wording inconsistency in its methodology; run metadata and saved results state 130 scenarios. Interpret accordingly.

### False positives, false negatives, and limitations

The Day 3 error analysis records false alarms on benign security discussion and misses on semantic/roleplay framing. The Day 8 false-positive rate further demonstrates why detector output must be balanced with human review and least-privilege policy. Do not present aggregate accuracy as proof of prevention.

### Results availability

No new confusion matrix, benchmark, screenshot, or scenario result is claimed here. Day 9 verification is limited to the commands and observations listed in the release-readiness document.

## Chapter 7: Conclusion and Future Scope

SentinelAI demonstrates a small end-to-end security prototype using CPU-friendly classical ML, deterministic authorization, sensitive-output checks, API logging, and a dashboard. The project makes the security boundary explicit: text classification does not grant permission, unknown roles/actions are denied, and only mock tools are used.

Current limitations include non-authenticated demo identities, benchmark and synthetic-label limitations, pattern-based sensitive detection, local SQLite, no production deployment controls, and no guarantee of prompt-injection prevention. Future work could add independent scenario review, stronger authentication and retention, broader multilingual/context-aware testing, monitored deployments, and carefully isolated real-agent integration with human approval and revocation.

## References

1. Dataset, [cyberec/Prompt-injection-dataset](https://huggingface.co/datasets/cyberec/Prompt-injection-dataset).
2. OWASP, [Top 10 for Large Language Model Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/).
3. K. Greshake et al., [“Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection”](https://arxiv.org/abs/2302.12173), arXiv:2302.12173, 2023.
4. G. Salton and C. Buckley, “Term-weighting approaches in automatic text retrieval,” *Information Processing & Management*, 24(5), 513–523, 1988, [doi:10.1016/0306-4573(88)90021-0](https://doi.org/10.1016/0306-4573(88)90021-0).
5. Scikit-learn, [text feature extraction](https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction), [LogisticRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html), [LinearSVC](https://scikit-learn.org/stable/modules/generated/sklearn.svm.LinearSVC.html).
6. R. Sandhu et al., “Role-Based Access Control Models,” *Computer*, 29(2), 38–47, 1996, [doi:10.1109/2.485845](https://doi.org/10.1109/2.485845).
7. Official documentation: [FastAPI](https://fastapi.tiangolo.com/), [React](https://react.dev/), [Vite](https://vite.dev/), [SQLite](https://www.sqlite.org/).
