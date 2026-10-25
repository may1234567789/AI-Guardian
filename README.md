# AI Guardian (SentinelAI)

> **Machine Learning-Powered Security Firewall for AI Agents and LLMs**  
> *Combines statistical machine learning classifiers, sensitive data detection, and deterministic policy enforcement to mitigate prompt injection and unauthorized autonomous actions.*

[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-green.svg)](https://opensource.org/licenses/Apache-2.0)
[![Status](https://img.shields.io/badge/Status-Day%201%20Completed-orange.svg)](#current-implementation-status)

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
│   ├── artifacts/              # Serialized models and vectorizers (Day 2+)
│   ├── reports/                # Visual charts and machine-readable JSON summaries
│   │   ├── class_distribution.png
│   │   ├── text_length_distribution.png
│   │   ├── category_distribution.png
│   │   ├── severity_distribution.png
│   │   ├── data_quality_summary.png
│   │   └── data_quality_summary.json
│   ├── notebooks/              # Exploratory research notebooks
│   ├── inspect_dataset.py      # Schema discovery, null/duplicate checks, leakage audits
│   ├── analyze_dataset.py      # In-depth EDA, statistical profiling, and visualizations
│   └── test_data_pipeline.py   # Automated unit tests for inspection & analysis logic
├── backend/                    # Reserved for FastAPI Gateway (Planned)
├── frontend/                   # Reserved for React Firewall Dashboard (Planned)
├── docs/                       # Research documentation and empirical reports
│   ├── day1_dataset_report.md  # Complete empirical audit report
│   └── day1_research_notes.md  # Theoretical foundations and threat taxonomy
├── requirements.txt            # Pinned, tested dependencies for local environment
├── .gitignore                  # Git exclusion rules
└── README.md                   # Project overview and instructions
```

---

## 4. Current Implementation Status (Day 1 Complete)

* [x] **Project Structure & Environment:** Clean modular architecture initialized; local virtual environment (`venv`) established and verified.
* [x] **Dependency Management:** Day 1 dependencies installed and tested on Python 3.14 under Windows Application Control / Smart App Control constraints.
* [x] **Dataset Source Discovery:** Hugging Face dataset `cyberec/Prompt-injection-dataset` verified (Apache 2.0 license, Croissant 1.1 metadata).
* [x] **Schema & Split Inspection:** Evaluated `core` (6,274 samples) and `full` (15,919 samples) partitions. Zero nulls, zero blanks, zero cross-split leakage.
* [x] **Data Quality & Leakage Auditing:** Group-aware isolation confirmed; empirical length distribution disparity cataloged.
* [x] **Local Storage:** Full Parquet and CSV archives generated in `ml/data/`.
* [x] **Reporting & Visualizations:** Five high-resolution visual reports and JSON scorecard created in `ml/reports/`.
* [x] **Unit Testing:** Automated unit tests in `ml/test_data_pipeline.py` executing cleanly (6/6 passing).

---

## 5. Setup & Execution Instructions

### Prerequisites
* Windows 10/11, Linux, or macOS
* Python 3.10+ (tested up to Python 3.14)
* 4 GB+ RAM (optimized for 8 GB RAM / Intel Core i3 systems)

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

### Step 4: Run Dataset Inspection Script
```bash
# Inspect 'core' configuration (classical ML partition)
python ml/inspect_dataset.py --config core

# Optional: Inspect 'full' configuration (expanded transformer partition)
python ml/inspect_dataset.py --config full
```

### Step 5: Run Deep Exploratory Analysis & Visualization
```bash
python ml/analyze_dataset.py --config core
```
*Outputs will be saved in `ml/reports/`.*

### Step 6: Run Automated Unit Tests
```bash
python -m unittest ml/test_data_pipeline.py
```

---

## 6. Planned Development Stages

* **Day 1 (Completed):** Dataset inspection, data quality audits, leakage detection, empirical profiling, and documentation.
* **Day 2 (Next):** Text preprocessing, character and word n-gram feature extraction (TF-IDF), length-bias mitigation, and baseline classical ML model training (Logistic Regression, Linear SVM, Decision Trees).
* **Day 3:** Hyperparameter tuning, threshold calibration for False Positive Rate minimization, and serialization of inference pipelines.
* **Day 4:** Deterministic security policy engine and sensitive data regex/canary token detectors.
* **Day 5:** FastAPI firewall gateway with sub-5ms inference latency.
* **Day 6:** React security monitoring dashboard and threat event telemetry.
* **Day 7:** End-to-end integration testing and red-teaming against adversarial prompt injections.

---

## 7. License
This project is licensed under the Apache License 2.0. Dataset sourced from `cyberec/Prompt-injection-dataset` under Apache 2.0.
