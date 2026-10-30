# AI Guardian (SentinelAI)

> **Machine Learning-Powered Security Firewall for AI Agents and LLMs**  
> *Combines statistical machine learning classifiers, sensitive data detection, and deterministic policy enforcement to mitigate prompt injection and unauthorized autonomous actions.*

[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-green.svg)](https://opensource.org/licenses/Apache-2.0)
[![Status](https://img.shields.io/badge/Status-Day%203%20Completed-brightgreen.svg)](#current-implementation-status)

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
│   │   ├── prompt_injection_svm.joblib     # Trained TF-IDF + LinearSVC pipeline
│   │   ├── model_metadata.json             # Day 2 baseline metadata
│   │   └── svm_model_metadata.json         # Day 3 SVM metadata and validation results
│   ├── reports/                # Visual charts, markdown analyses, and JSON summaries
│   │   ├── confusion_matrix.png            # Day 2: Test set confusion matrix heatmap
│   │   ├── roc_curve.png                   # Day 2: Receiver operating characteristic curve
│   │   ├── metrics_summary.png             # Day 2: Default vs. calibrated threshold metrics
│   │   ├── error_analysis.md               # Day 2: In-depth qualitative error audit
│   │   ├── test_evaluation_summary.json    # Day 2: Complete machine-readable test metrics
│   │   ├── class_distribution.png          # Day 1: Class distribution breakdown
│   │   ├── text_length_distribution.png    # Day 1: Text length density plots
│   │   ├── day3_model_comparison.json      # Day 3: Test metrics and threshold results
│   │   ├── model_error_comparison.md       # Day 3: Disagreement and error analysis
│   │   ├── robustness_test_results.md      # Day 3: Synthetic robustness results
│   │   └── ...
│   ├── notebooks/              # Exploratory research notebooks
│   ├── train_svm.py            # Day 3 TF-IDF + LinearSVC training
│   ├── compare_models.py       # Saved-artifact comparison and visualizations
│   ├── compare_errors.py       # Cross-model disagreement analysis
│   ├── robustness_tests.py     # Small, labeled synthetic test suite
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
│   ├── day2_model_report.md    # Day 2 complete baseline model training and evaluation report
│   └── day3_model_comparison.md # Day 3 controlled comparison and limitations
├── requirements.txt            # Pinned, tested dependencies for local environment
├── .gitignore                  # Git exclusion rules
└── README.md                   # Project overview and instructions
```

---

## 4. Current Implementation Status (Day 1–Day 3 Complete)

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
* [x] **Day 3 - Linear SVM:** Trained and saved the TF-IDF + LinearSVC pipeline to `ml/artifacts/prompt_injection_svm.joblib`; validation-only threshold analysis and model metadata are saved alongside it.
* [x] **Day 3 - Controlled Comparison:** Evaluated the saved Logistic Regression and LinearSVC pipelines on the same 942-example `core_test` split; results and charts are in `ml/reports/`.
* [x] **Day 3 - Errors and Robustness:** Generated cross-model error analysis and executed a separate 30-case synthetic suite; see the report and caveats below.
* [x] **Day 3 - Tests and Research Report:** SVM and Logistic Regression artifact tests pass; see `docs/day3_model_comparison.md`.

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

## 6. Day 3 Model Comparison

The saved Day 2 Logistic Regression artifact and the Day 3 LinearSVC artifact were compared on the identical official `core_test` split (942 examples: 390 benign, 552 malicious). Both artifact metadata records 4,391 training rows from `core_train`; exact text and `group_id` overlap across official splits was checked and found to be zero. No baseline model or Day 2 evaluation report was overwritten.

### Default test-set metrics

| Metric | Logistic Regression | Linear SVM |
| :--- | ---: | ---: |
| Accuracy | 95.22% | 95.22% |
| Precision | 94.55% | 94.71% |
| Recall | 97.46% | 97.28% |
| F1 | 0.9599 | 0.9598 |
| False-positive rate | 7.95% (31/390) | 7.69% (30/390) |
| False-negative rate | 2.54% (14/552) | 2.72% (15/552) |
| ROC-AUC | 0.9937 | 0.9943 |
| Training duration (recorded) | 0.1359 s | 0.9247 s |
| Mean single-request latency (this comparison run) | 3.739 ms | 3.886 ms |
| P95 single-request latency (this comparison run) | 6.179 ms | 7.173 ms |
| Saved artifact size | 162.3 KiB | 150.4 KiB |

Validation-selected thresholds maximized F1 on `core_validation` only: Logistic Regression threshold **0.7102** and SVM decision-score threshold **0.0300**. On the untouched test set these yielded, respectively, LR F1 **0.9532** (7 FP, 43 FN) and SVM F1 **0.9606** (29 FP, 15 FN). SVM decision scores are not probabilities. Latency is hardware/load-sensitive; use the same-run values above for comparison rather than the earlier Day 2 profiling result.

| Model at validation-selected threshold | Test accuracy | Precision | Recall | F1 | FP / FN |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Logistic Regression (0.7102 probability) | 94.69% | 98.64% | 92.21% | 0.9532 | 7 / 43 |
| Linear SVM (0.0300 decision score) | 95.33% | 94.88% | 97.28% | 0.9606 | 29 / 15 |

The models tie on accuracy and near-tie on F1. SVM reduces one default-threshold false positive but adds one false negative; measured ROC-AUC is slightly higher, while the Logistic Regression artifact trains faster. There is no evidence here of a decisive winner. Full methods, charts, errors, synthetic test findings, and limitations are in [docs/day3_model_comparison.md](docs/day3_model_comparison.md).

### Day 3 commands

```powershell
python ml\train_svm.py --config core --max-features 20000 --ngram-min 1 --ngram-max 2 --c-reg 1.0 --class-weight balanced --random-state 42
python ml\compare_models.py --config core
python ml\compare_errors.py --config core
python ml\robustness_tests.py
python -m unittest ml/test_svm.py ml/test_model.py
```

Default comparison outputs are saved in `ml/reports/`. The `LinearSVC.decision_function()` score is a signed distance from the learned boundary, not an attack-probability percentage.

---

## 7. Setup & Execution Instructions

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

# Day 3 SVM and baseline regression tests
python -m unittest ml/test_svm.py ml/test_model.py
```

---

## 8. Planned Development Stages

* [x] **Day 1 (Completed):** Dataset inspection, data quality audits, leakage detection, empirical profiling, and documentation.
* [x] **Day 2 (Completed):** Data preprocessing, TF-IDF feature extraction, length-bias mitigation, Logistic Regression baseline training, held-out test evaluation, validation threshold calibration, error analysis, and unit testing.
* [x] **Day 3 (Completed):** TF-IDF + LinearSVC training, saved-artifact comparison, validation-only threshold analysis, error analysis, synthetic robustness tests, and documentation.
* [ ] **Day 4 (Next):** Deterministic security policy engine (least privilege, capability sandboxing, and human authorization for sensitive actions).
* [ ] **Future:** Additional character n-gram robustness experiments, calibrated ensemble evaluation, API gateway, monitoring dashboard, and adaptive red-teaming.

---

## 9. License
This project is licensed under the Apache License 2.0. Dataset sourced from `cyberec/Prompt-injection-dataset` under Apache 2.0.
