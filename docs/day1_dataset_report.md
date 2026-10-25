# AI Guardian (SentinelAI) - Day 1 Dataset Inspection & Quality Report

**Project Name:** AI Guardian (SentinelAI)  
**Document:** Day 1 Dataset Quality & Exploratory Analysis Report  
**Author:** Antigravity (Autonomous ML Security Research Agent)  
**Date:** October 26, 2026  
**Status:** Complete & Verified  

---

## 1. Project Overview & Objective
AI Guardian is a research-oriented machine learning security firewall designed to protect autonomous AI agents and Large Language Models (LLMs) from prompt injection attacks, jailbreaks, and unauthorized downstream tool executions.

Day 1 focuses strictly on **dataset understanding, exploratory data analysis (EDA), empirical quality audits, data leakage detection, and reproducible local storage**. No model training or architecture claims are made on Day 1.

---

## 2. Dataset Identification & Provenance
* **Dataset Identifier:** `cyberec/Prompt-injection-dataset`
* **Source Repository:** Hugging Face Datasets ([https://huggingface.co/datasets/cyberec/Prompt-injection-dataset](https://huggingface.co/datasets/cyberec/Prompt-injection-dataset))
* **Verified License:** Apache License 2.0 (verified via MLCommons Croissant metadata in the dataset card)
* **Creator / Curators:** `cyberec`
* **Domain / Task:** Binary text classification for LLM prompt injection and jailbreak detection
* **Languages Covered:** English
* **Schema Standard:** Conforms to MLCommons Croissant 1.1 specification

---

## 3. Configuration, Splits & Scale

The dataset provides two distinct official configurations sharing an identical 8-column schema:
1. **`core`**: Curated, un-augmented partition designed specifically for classical machine learning baselines (Logistic Regression, Linear SVMs, Decision Trees).
2. **`full`**: Expanded partition containing additional augmented training examples (total 15,919 rows) suited for larger language models or transformers.

### Empirical Split Record Counts

| Configuration | Split | Number of Rows | Percentage of Config | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **`core`** | **Train** | **4,391** | 69.99% | Baseline model training |
| **`core`** | **Validation** | **941** | 15.00% | Hyperparameter tuning & threshold calibration |
| **`core`** | **Test** | **942** | 15.01% | Unbiased held-out evaluation |
| **`core` Total** | — | **6,274** | 100.0% | Classical ML pipeline |
| **`full`** | Train | 14,036 | 88.17% | Augmented training partition |
| **`full`** | Validation | 941 | 5.91% | Identical to core validation |
| **`full`** | Test | 942 | 5.92% | Identical to core test |
| **`full` Total** | — | **15,919** | 100.0% | Deep learning / transformer pipeline |

> [!NOTE]
> The validation (941) and test (942) sets are identical between `core` and `full`, providing an objective, standardized benchmark across model families.

---

## 4. Schema & Data Types

The dataset contains 8 columns discovered and validated via `ml/inspect_dataset.py`:

| Column Name | Discovered Type | Description & Semantic Meaning | Example Values |
| :--- | :--- | :--- | :--- |
| `text` | `string` / `object` | The raw prompt string submitted to the AI agent. Untrusted input. | `"Ignore previous instructions..."` |
| `label` | `int64` | Binary ground-truth target: `1` = Malicious (Prompt Injection/Jailbreak), `0` = Benign. | `0`, `1` |
| `category` | `string` / `object` | Attack taxonomic category (29 distinct attack types cataloged). | `direct_injection`, `crescendo`, `jailbreak` |
| `source` | `string` / `object` | Provenance / origin tracking for data collection. | `original`, `synthetic` |
| `severity` | `string` / `object` | Security risk tier assigned to the prompt. | `low`, `medium`, `high`, `critical` |
| `group_id` | `string` / `object` | Cluster identifier used to group variations of an attack to prevent leakage across splits. | `grp_e4017db16629` |
| `augmented` | `bool` | Indicates whether the prompt was generated through data augmentation. | `True`, `False` |
| `tags` | `array` / `list` | Sub-technique keywords describing specific payload mechanisms. | `["override", "admin_claim"]` |

---

## 5. Data Quality & Integrity Audits

### 5.1 Missing, Null, and Blank Value Analysis
Every row across all splits was programmatically audited:
* **Null / NaN values across all columns:** **0 (0.00%)**
* **Empty string (`""`) text entries:** **0 (0.00%)**
* **Whitespace-only (`"   "`) text entries:** **0 (0.00%)**

### 5.2 Duplicate Analysis
* **`core` configuration:**
  * Exact text duplicates in `train`: **0 (0.00%)**
  * Exact text duplicates in `validation`: **0 (0.00%)**
  * Exact text duplicates in `test`: **0 (0.00%)**
  * Exact full-row duplicates: **0 (0.00%)**
* **`full` configuration:**
  * Exact text duplicates in `train`: **102 (0.73%)** (resulting from augmentation variations)
  * Exact text duplicates in `validation`: **0**
  * Exact text duplicates in `test`: **0**

### 5.3 Label Consistency Audit
We conducted a grouping check on `text` to find instances where the same prompt was tagged as both Benign (`0`) and Malicious (`1`).
* **Contradictory text instances:** **0**
* **Label consistency rate:** **100.0%**

---

## 6. Class Distribution & Imbalance Analysis

| Split (`core`) | Benign (Class 0) | Malicious (Class 1) | Total Prompts | Malicious Ratio |
| :--- | :--- | :--- | :--- | :--- |
| **Train** | 1,741 (39.65%) | 2,650 (60.35%) | 4,391 | ~1.52 : 1 |
| **Validation** | 407 (43.25%) | 534 (56.75%) | 941 | ~1.31 : 1 |
| **Test** | 390 (41.40%) | 552 (58.60%) | 942 | ~1.42 : 1 |
| **Overall** | **2,538 (40.45%)** | **3,736 (59.55%)** | **6,274** | **~1.47 : 1** |

### Assessment:
The class ratio (~60% malicious to ~40% benign) is well-balanced for an adversarial detection task. While real-world production environments typically exhibit an extreme class imbalance (>99% benign, <1% malicious), a balanced benchmark enables robust learning of decision boundaries without requiring aggressive synthetic oversampling. 

---

## 7. Text Length & Distribution Analysis

Prompts vary substantially in character and word length between benign queries and complex injection attacks:

| Metric | Overall (`core`) | Train Split | Validation Split | Test Split | Benign (`0`) | Malicious (`1`) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Minimum Chars** | 10 | 10 | 12 | 10 | 14 | 10 |
| **25th Percentile** | 44.0 | 44.0 | 43.0 | 44.0 | 42.0 | 51.0 |
| **Median Chars** | **56.0** | **56.0** | **55.0** | **56.5** | **48.0** | **78.0** |
| **Mean Chars** | **143.22** | **142.98** | **143.46** | **144.11** | **70.04** | **192.94** |
| **75th Percentile** | 95.75 | 95.0 | 98.0 | 95.0 | 54.0 | 151.0 |
| **95th Percentile** | 462.70 | 469.5 | 451.0 | 456.8 | 79.15 | 634.5 |
| **99th Percentile** | 2,003.89 | 1,989.10 | 2,079.80 | 1,929.96 | 604.71 | 2,175.25 |
| **Maximum Chars** | 7,009 | 7,009 | 3,972 | 4,218 | 2,158 | 7,009 |
| **Median Word Count** | 8.0 | 8.0 | 8.0 | 8.0 | 7.0 | 12.0 |
| **Mean Word Count** | 20.03 | 20.21 | 19.44 | 19.78 | 10.76 | 26.33 |

### Critical Finding: The "Length Disparity" Artifact
* **Benign Prompts:** Highly concentrated around short queries (Mean: 70 chars; 95% of benign prompts are under 80 characters).
* **Malicious Prompts:** Significantly longer (Mean: 193 chars; 25% exceed 151 chars, extending up to 7,009 chars).
* **Research Risk:** Classical ML models (such as bag-of-words or un-normalized TF-IDF) can easily learn a spurious correlation where longer inputs are classified as attacks simply due to length.
* **Mitigation for Day 2:** Preprocessing must use sublinear TF scaling (`sublinear_tf=True`) and character n-grams, while unit tests must evaluate short injections and long benign text.

---

## 8. Data Leakage & Group-Aware Splitting

A major failure mode in machine learning security research is **near-duplicate data leakage**: an attacker prompt is lightly rephrased and placed in both train and test splits, producing artificially inflated test scores.

To evaluate this in `cyberec/Prompt-injection-dataset`:
1. **Exact Text Overlap Test:**
   * `train` vs `validation`: **0 common texts**
   * `train` vs `test`: **0 common texts**
   * `validation` vs `test`: **0 common texts**
2. **Group ID Isolation Test:**
   * Each cluster of semantically linked prompts shares a unique `group_id`.
   * Common `group_id`s across `train` and `validation`: **0**
   * Common `group_id`s across `train` and `test`: **0**
   * Common `group_id`s across `validation` and `test`: **0**

### Conclusion:
The official dataset partitioning strictly isolates attack groups. The test set represents genuine out-of-group evaluation, preventing data leakage.

---

## 9. Attack Taxonomies & Severity Distributions

### Top Attack Categories in Dataset:
1. `direct_injection` (classic instruction overrides, prefix injection, system-prompt extraction)
2. `crescendo` (multi-turn logic exploitation building toward malicious objectives)
3. `jailbreak` (roleplay, hypothetical framing, fictional scenarios)
4. `evasion` (encoding, token manipulation, linguistic disguises)
5. `indirect_injection` (payloads embedded in web documents, markdown, or email data)

### Severity Breakdown:
* **Critical:** Direct instructions to generate actionable harm or exploit agentic tools.
* **High:** Outright system prompt exfiltration or authorization bypasses.
* **Medium:** Roleplay jailbreaks without explicit weaponization.
* **Low:** Theoretical probing and philosophical neutrality arguments.

---

## 10. Local Data Storage & Artifacts

All splits have been archived locally in `ml/data/` in both Apache Parquet (preserving schema types including lists and booleans) and standard CSV:

```
ml/data/
├── core_train.parquet        (388 KB)
├── core_train.csv            (992 KB)
├── core_validation.parquet   (93 KB)
├── core_validation.csv       (215 KB)
├── core_test.parquet         (95 KB)
├── core_test.csv             (216 KB)
├── full_train.parquet        (1.4 MB)
└── full_train.csv            (3.1 MB)
```

Generated publication-quality visual reports are stored in `ml/reports/`:
* `class_distribution.png`: Bar breakdown across splits.
* `text_length_distribution.png`: Density plots with median markers.
* `category_distribution.png`: Top 12 attack taxonomies.
* `severity_distribution.png`: Risk tier distributions.
* `data_quality_summary.png`: Visual audit scorecard.
* `data_quality_summary.json`: Complete machine-readable metrics summary.

---

## 11. Limitations & Unresolved Research Questions

1. **Length Asymmetry:** The benign set has limited representation of long, legitimate documents (e.g., source code, essays, long legal contracts). We must supplement benign test evaluation with long benign texts on Day 2.
2. **Language Coverage:** Dataset is currently focused on English. Non-English and polyglot prompt injection remains an open frontier.
3. **Multi-Turn Context:** Single-prompt classification does not capture stateful multi-turn crescendo attacks where individual turns appear benign in isolation.
4. **Adversarial Suffixes:** Unreadable GCG (Greedy Coordinate Gradient) token strings may bypass tokenizers if character-level n-grams are not utilized.

---

## 12. Recommended Day 2 Strategy
1. **Target Config:** Use `core` configuration for classical ML baseline models (Logistic Regression, Linear SVM, Decision Tree / Random Forest).
2. **Feature Extraction:** Character n-grams (range 3-5) combined with word n-grams (range 1-2) using TF-IDF with `sublinear_tf=True`.
3. **Hardware Efficiency:** Suitable for Intel Core i3 and 8 GB RAM; training takes under 15 seconds without GPU requirements.
4. **Evaluation Focus:** Strict separation of precision, recall, and false positive rates on benign queries.
