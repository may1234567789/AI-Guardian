# AI Guardian (SentinelAI)

> **Machine Learning-Powered Security Firewall for AI Agents and LLMs**  
> *Combines statistical machine learning classifiers, sensitive data detection, and deterministic policy enforcement to mitigate prompt injection and unauthorized autonomous actions.*

[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-green.svg)](https://opensource.org/licenses/Apache-2.0)
[![Status](https://img.shields.io/badge/Status-Day%202%20Completed-brightgreen.svg)](#current-implementation-status)

---

## 1. Project Background & Objective

Autonomous AI agents equipped with tool-use capabilities (browsing, shell commands, file system manipulation, API integration) represent a critical paradigm shift in software. However, they introduce profound security risks when untrusted inputs subvert the agent's control flow via **Prompt Injection** (OWASP LLM01:2025).

**AI Guardian (SentinelAI)** is designed to act as an inline, low-latency security gateway. Rather than relying solely on probabilistic models or static blocklists, AI Guardian combines:
1. **Empirically Audited Machine Learning Classifiers:** Fast CPU-friendly baseline models to detect injection and jailbreak payloads in milliseconds.
2. **Deterministic Security Policies:** Strict capability controls and execution sandboxes that prevent destructive actions even in the event of an ML false negative.
3. **Sensitive Data Redaction:** Automated detection of credentials, PII, and API keys before prompt submission.

> [!WARNING]
> **Research & Development Notice:** AI Guardian is currently under active development and is **not production-ready**. No claims of total injection prevention or production certification are made at this stage.

---

## 2. Technology Stack

* **Language:** Python (tested on Python 3.14 on Windows 64-bit)
* **Core Data Processing:** `pandas==3.0.6`, `numpy>=1.26.0`, `pyarrow==25.0.1`
* **Machine Learning Baselines:** `scikit-learn>=1.3.0`, `joblib>=1.3.0`
* **Data Sources & Provenance:** Hugging Face `datasets>=2.16.0` (`cyberec/Prompt-injection-dataset`)
* **Visualization & Reporting:** `matplotlib>=3.8.0`, `seaborn>=0.13.0`
* **Future Components:** FastAPI (Backend API), React (Security Dashboard), SQLite (Event Audit Logging)

---

## 3. Project Directory Structure

```
SentinelAI/
├── ml/
│   ├── data/                   # Verified local Parquet and CSV dataset partitions
│   │   ├── core_train.parquet
│   │   ├── core_validation.parquet
│   │   ├── core_test.parquet
│   │   └── ...
│   ├── artifacts/              # Serialized models and vectorizers
│   │   ├── prompt_injection_logreg.joblib  # Trained TF-IDF + Logistic Regression pipeline
│   │   └── model_metadata.json             # Hyperparameters, metrics, and limitations
│   ├── reports/                # Visual charts, markdown analyses, and JSON summaries
│   │   ├── confusion_matrix.png            # Day 2: Test set confusion matrix heatmap
│   │   ├── roc_curve.png                   # Day 2: Receiver operating characteristic curve
│   │   ├── metrics_summary.png             # Day 2: Default vs. calibrated threshold metrics
│   │   ├── error_analysis.md               # Day 2: In-depth qualitative error audit
│   │   ├── test_evaluation_summary.json    # Day 2: Complete machine-readable test metrics
│   │   ├── class_distribution.png          # Day 1: Class distribution breakdown
│   │   ├── text_length_distribution.png    # Day 1: Text length density plots
│   │   └── ...
│   ├── notebooks/              # Exploratory research notebooks
│   ├── preprocess_data.py      # Leakage-safe preprocessing & cross-split isolation
│   ├── train.py                # Pipeline construction, training, threshold tuning & serialization
│   ├── evaluate.py             # Held-out test set evaluation & chart generation
│   ├── error_analysis.py       # Empirical false positive / false negative diagnostic
│   ├── test_model.py           # Automated model unit & smoke tests (7/7 passing)
│   ├── inspect_dataset.py      # Schema discovery, null/duplicate checks, leakage audits
│   ├── analyze_dataset.py      # In-depth EDA, statistical profiling, and visualizations
│   └── test_data_pipeline.py   # Automated unit tests for inspection & analysis logic
├── backend/                    # Reserved for FastAPI Gateway (Planned)
├── frontend/                   # Reserved for React Firewall Dashboard (Planned)
├── docs/                       # Research documentation and empirical reports
│   ├── day1_dataset_report.md  # Day 1 empirical dataset quality audit
│   ├── day1_research_notes.md  # Day 1 theoretical foundations and threat taxonomy
│   └── day2_model_report.md    # Day 2 complete baseline model training and evaluation report
├── requirements.txt            # Pinned, tested dependencies for local environment
├── .gitignore                  # Git exclusion rules
└── README.md                   # Project overview and instructions
```

---

## 4. Current Implementation Status (Day 1 & Day 2 Complete)

* [x] **Day 1 - Dataset Understanding & Audits:** Schema discovery, data quality inspection (zero nulls, zero empty strings), cross-split leakage audit, length disparity discovery, local Parquet/CSV storage, and 5 visual reports.
* [x] **Day 2 - Preprocessing Pipeline:** Leakage-safe, security-preserving preprocessing in `ml/preprocess_data.py`. Verified zero cross-split overlap across train, validation, and test partitions.
* [x] **Day 2 - Baseline ML Model Training:** Built and trained an end-to-end scikit-learn `Pipeline` (TF-IDF Vectorizer with unigrams/bigrams and sublinear TF + Logistic Regression with class balancing) in `ml/train.py`. Fits in 0.136s.
* [x] **Day 2 - Model Artifact Serialization:** Complete pipeline saved with Joblib to `ml/artifacts/prompt_injection_logreg.joblib` (162.3 KB). Full hyperparameters, split provenance, environment details, and security limitations recorded in `ml/artifacts/model_metadata.json`.
* [x] **Day 2 - Held-Out Test Set Evaluation:** Evaluated on 942 test examples in `ml/evaluate.py`. Default threshold (0.50) achieved **95.22% accuracy, 97.46% recall, 94.55% precision, 0.9599 F1, and 0.9937 ROC-AUC**.
* [x] **Day 2 - Validation Threshold Calibration:** Calibrated operating threshold to 0.71, slashing False Positives from 31 down to 7 (FPR = 1.79%, precision = 98.64%, recall = 92.21%).
* [x] **Day 2 - Latency Profiling:** Verified sub-millisecond CPU inference: **0.452 ms** mean single-request latency, 0.636 ms P95 latency.
* [x] **Day 2 - Visual Reporting:** Publication-ready charts generated in `ml/reports/`: `confusion_matrix.png`, `roc_curve.png`, and `metrics_summary.png`.
* [x] **Day 2 - Error Analysis:** In-depth qualitative audit in `ml/reports/error_analysis.md` analyzing false alarms on long benign prompts and bypasses on social-engineering roleplay ("grandma exploit").
* [x] **Day 2 - Automated Unit Testing:** 7 automated test suites passing in `ml/test_model.py` (model loading, step integrity, predict_proba calibration, batch/single inference, empty input edge cases, and smoke tests).

---

## 5. Measured Baseline Performance (Day 2 Empirical Results)

Evaluated strictly on the held-out test split (`core_test.parquet`, $N = 942$: 390 Benign, 552 Malicious):

| Metric | Default Threshold (0.50) | Validation-Calibrated Threshold (0.71) | Security Impact |
| :--- | :--- | :--- | :--- |
| **Accuracy** | **95.22%** | **94.69%** | Robust baseline accuracy across both splits |
| **Precision** | **94.55%** | **98.64%** | Calibrated threshold minimizes user friction |
| **Recall (Detection Rate)** | **97.46%** (538 / 552) | **92.21%** (509 / 552) | Default captures 97.5% of attack attempts |
| **F1-Score** | **0.9599** | **0.9532** | Strong harmonic performance |
| **ROC-AUC** | **0.9937** | **0.9937** | Excellent class separability |
| **False Positive Rate (FPR)** | **7.95%** (31 / 390) | **1.79%** (7 / 390) | **77.4% reduction in false alarms** |
| **False Negative Rate (FNR)** | **2.54%** (14 / 552) | **7.79%** (43 / 552) | Trade-off for enterprise low-friction profile |
| **Single-Request Mean Latency** | **0.452 ms** | **0.452 ms** | Sub-millisecond CPU inline inspection |
| **Single-Request P95 Latency** | **0.636 ms** | **0.636 ms** | Deterministic tail latency on commodity CPU |

---

## 6. Setup & Execution Instructions

### Prerequisites
* Windows 10/11, Linux, or macOS
* Python 3.10+ (tested on Python 3.14.8 64-bit)
* 4 GB+ RAM (optimized for Intel Core i3 / 8 GB RAM systems; no GPU required)

### Step 1: Clone or Navigate to the Repository
```bash
cd SentinelAI
```

### Step 2: Create and Activate Virtual Environment
```powershell
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run Data Preprocessing & Leakage Verification
```bash
python ml/preprocess_data.py --config core
```

### Step 5: Train Baseline Model & Save Artifacts
```bash
python ml/train.py --config core --max-features 20000 --random-state 42
```
*Artifacts saved to `ml/artifacts/prompt_injection_logreg.joblib` and `ml/artifacts/model_metadata.json`.*

### Step 6: Evaluate Model on Held-Out Test Set
```bash
python ml/evaluate.py --config core
```
*Visual charts and metrics saved to `ml/reports/`.*

### Step 7: Run Qualitative Error Analysis
```bash
python ml/error_analysis.py --config core
```
*Report saved to `ml/reports/error_analysis.md`.*

### Step 8: Run Automated Unit Tests
```bash
# Day 1 Data pipeline tests
python -m unittest ml/test_data_pipeline.py

# Day 2 Model unit and smoke tests
python -m unittest ml/test_model.py
```

---

## 7. Planned Development Stages

* [x] **Day 1 (Completed):** Dataset inspection, data quality audits, leakage detection, empirical profiling, and documentation.
* [x] **Day 2 (Completed):** Data preprocessing, TF-IDF feature extraction, length-bias mitigation, Logistic Regression baseline training, held-out test evaluation, validation threshold calibration, error analysis, and unit testing.
* [ ] **Day 3 (Next):** Model comparison (Linear SVM, Random Forest, Naive Bayes), character n-gram modeling to resist obfuscation/evasion, and calibrated ensemble export.
* [ ] **Day 4:** Deterministic security policy engine (read-only enforcement, capability sandboxing, canary token leaks).
* [ ] **Day 5:** FastAPI high-throughput firewall gateway with inline sub-5ms inspection.
* [ ] **Day 6:** React security monitoring dashboard and real-time threat telemetry.
* [ ] **Day 7:** End-to-end integration red-teaming against adaptive jailbreaks.

---

## 8. License
This project is licensed under the Apache License 2.0. Dataset sourced from `cyberec/Prompt-injection-dataset` under Apache 2.0.
