# SentinelAI — Day 3 Model Comparison

**Status:** Complete  
**Dataset:** `cyberec/Prompt-injection-dataset`, `core` configuration  
**Evaluation split:** `core_test` (942 examples)  
**Date:** October 31, 2026

## A. Objective

This experiment compares the Day 2 TF-IDF + Logistic Regression baseline with a resource-conscious TF-IDF + Linear Support Vector Machine. LinearSVC is a common sparse-text classifier and offers a useful comparison of a margin-based objective against logistic loss without requiring a GPU or a large model. The purpose is to measure whether its error trade-offs justify using it in a later security-policy integration—not to assume it is better.

## B. Dataset and Experimental Setup

- **Dataset:** `cyberec/Prompt-injection-dataset`, `core` partition, locally stored under `ml/data/`.
- **Text:** `text`; **label:** `label`, where `0 = benign` and `1 = prompt_injection`.
- **Official group-aware splits:** `core_train` 4,391 rows (1,741 benign / 2,650 malicious), `core_validation` 941 (407 / 534), and `core_test` 942 (390 / 552).
- Preprocessing reuses `ml/preprocess_data.py`, strips only leading/trailing whitespace, removes no security tokens, and checks for exact duplicate text across splits. This run found zero cross-split text overlap. A separate check found zero overlapping `group_id` values between every pair of splits.
- The Logistic Regression and SVM were loaded from their saved artifacts; the baseline was not retrained. Their metadata identifies the same dataset/configuration, official split strategy, and 4,391 training rows. The artifacts do not contain a row-level training-data fingerprint, so the exact training-row provenance is supported by their metadata and shared training/preprocessing code path, not by an embedded checksum.
- Both models use class-balanced weights and compatible TF-IDF settings. Test labels were not used for fitting or threshold selection.

## C. Methods

**TF-IDF:** Both pipelines convert text to sparse TF-IDF vectors using unigrams and bigrams (`ngram_range=(1, 2)`), `min_df=2`, `max_features=20,000`, sublinear term frequency, lowercase normalization, and no stop-word removal. The fitted vocabulary contains 9,908 terms. The vectorizer is fitted only on `core_train` as part of the saved pipeline.

**Logistic Regression:** The existing Day 2 pipeline uses L2 regularization, `C=1.0`, `lbfgs`, class-balanced weights, and up to 1,000 iterations. It provides probabilities through `predict_proba()`.

**Linear SVM:** The new pipeline uses `LinearSVC(C=1.0, loss="squared_hinge", class_weight="balanced", max_iter=10,000, dual="auto", random_state=42)`. A text-input validation step rejects non-string inputs with a clear `ValueError`; the TF-IDF vectorizer and classifier remain in the same serialized scikit-learn Pipeline.

`LinearSVC` does not provide calibrated probabilities. `decision_function()` returns a signed score relative to the learned boundary: positive scores map to class 1 and negative scores to class 0 for this model. Score magnitudes are not attack-probability percentages. ROC-AUC can validly use these continuous scores because both test classes are present; it does not require calibrated probabilities.

## D. Results

### Default decision boundary on the held-out test set

| Metric | Logistic Regression | Linear SVM |
| :--- | ---: | ---: |
| Accuracy | 0.9522 | 0.9522 |
| Precision | 0.9455 | 0.9471 |
| Recall | 0.9746 | 0.9728 |
| F1 | 0.9599 | 0.9598 |
| False-positive rate | 0.0795 (31 / 390) | 0.0769 (30 / 390) |
| False-negative rate | 0.0254 (14 / 552) | 0.0272 (15 / 552) |
| ROC-AUC | 0.9937 | 0.9943 |
| Confusion matrix (TN, FP, FN, TP) | (359, 31, 14, 538) | (360, 30, 15, 537) |
| Training duration (from artifact metadata) | 0.1359 s | 0.9247 s |
| Mean single-request latency (this comparison run) | 3.739 ms | 3.886 ms |
| P95 single-request latency (this comparison run) | 6.179 ms | 7.173 ms |
| Artifact size | 166,187 bytes | 154,047 bytes |

Latency was measured using the same procedure for each model: one warm-up, five full-test batch runs, and individual single-text predictions over up to 100 test examples. Latency is hardware/load-sensitive. The Day 2 evaluation reported a different single-request result (0.452 ms); these timing figures should not be treated as directly interchangeable because they were measured in different runs and conditions.

### Validation-selected F1 thresholds

Thresholds were selected by maximizing F1 across distinct scores on `core_validation`; ties prefer the threshold closest to the default boundary. Only after selecting the thresholds were they applied to `core_test`.

| Model | Validation-selected threshold | Validation F1 | Test accuracy | Test precision | Test recall | Test F1 | Test FPR | Test FNR | Test FP / FN |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Logistic Regression | 0.7102 probability | 0.9574 | 0.9469 | 0.9864 | 0.9221 | 0.9532 | 0.0179 | 0.0779 | 7 / 43 |
| Linear SVM | 0.0300 decision score | 0.9667 | 0.9533 | 0.9488 | 0.9728 | 0.9606 | 0.0744 | 0.0272 | 29 / 15 |

The SVM threshold is a decision-score boundary shift, **not** a probability threshold. Threshold selection and test-set reporting are recorded in `ml/reports/day3_model_comparison.json`.

### Charts and machine-readable outputs

- `ml/reports/day3_metric_comparison.png`
- `ml/reports/day3_confusion_matrices.png`
- `ml/reports/day3_roc_curves.png`
- `ml/reports/day3_precision_recall_curves.png`
- `ml/reports/day3_threshold_analysis.png`
- `ml/reports/day3_model_comparison.json`

The metric bars and confusion matrices use actual default test predictions; ROC and precision-recall curves use continuous test scores. Threshold analysis is based on validation scores and marks the selected validation thresholds.

## E. Error Analysis

The models agreed on 926/942 test rows (98.3%): both were correct on 889, and both were wrong on 37. Each model alone classified 8 examples correctly that the other missed. At default thresholds, Logistic Regression had 31 false positives and 14 false negatives; SVM had 30 and 15, respectively. Neither model had fewer total errors.

Among 19 benign rows containing heuristic security-related terms, Logistic Regression flagged 6 and SVM flagged 5. Direct-override keyword matching found 116 malicious examples; detection was 116/116 for Logistic Regression and 115/116 for SVM. A broad “not containing direct override tokens” bucket included 436 malicious rows and is only a rough heuristic—not a reliable indirect/obfuscated attack taxonomy.

Observed failure themes included benign quoted discussion being flagged as malicious, and roleplay/persona or otherwise semantically framed harmful requests being missed by both models. Some benchmark labels also conflate prompt injection with harmful-content requests, so false positives and negatives can partly reflect task/label ambiguity. The generated examples and detailed counts are in `ml/reports/model_error_comparison.md`; displayed text is truncated. These qualitative samples are diagnostic, not evidence that one model is superior.

## F. Robustness Results

The separate synthetic suite contains 30 hand-written cases, five each for ordinary benign requests, benign security discussion, direct override attempts, confidential-information extraction, indirect/quoted text, and modified attack wording.

| Category | Logistic Regression | Linear SVM |
| :--- | ---: | ---: |
| Ordinary benign | 3/5 | 4/5 |
| Benign security discussion | 4/5 | 3/5 |
| Direct override | 5/5 | 5/5 |
| Confidential extraction | 5/5 | 5/5 |
| Indirect/quoted | 2/5 | 2/5 |
| Modified attack wording | 4/5 | 4/5 |
| **Overall** | **23/30 (76.7%)** | **23/30 (76.7%)** |

Expected labels are assumptions for a qualitative smoke suite and may need human review. In particular, quoting an attack can be benign in one context and malicious in another; suite labels do not establish comprehensive robustness. Full case-level outcomes and failures are in `ml/reports/robustness_test_results.md` and `.json`.

## G. Model Selection

For Day 4, keep Logistic Regression as the comparison/reference candidate while carrying SVM into integration tests. On default test decisions the two models tie on accuracy and F1 to rounding; SVM has one fewer false positive but one more false negative, and a 0.0006 higher ROC-AUC. The SVM trains more slowly in the recorded run (0.9247 s vs. 0.1359 s), although both artifacts are small and inference is in the same measured latency range. The validation-selected SVM boundary modestly raises test F1, but there is no statistical-significance analysis and no decisive overall winner.

For a security workflow, threshold decisions must be made against an explicitly chosen operational cost, then validated on more representative data. Do not make the classifier an authorization authority: pair detection with deterministic capabilities, least privilege, and explicit approval for sensitive actions. Reassess precision and false-positive load under realistic benign-to-attack prevalence before any deployment.

## H. Limitations

- **Dataset bias and label ambiguity:** This is a curated English benchmark, with some content categories potentially conflating injection and harmfulness.
- **Distribution shift and unseen attacks:** Historical training examples cannot guarantee detection of new phrasings, languages, or adaptive attacks.
- **Text-only detection:** A bag-of-words model lacks the agent/tool context and multi-turn state needed to reason about authority or intent.
- **Statistical uncertainty:** A single held-out split and a handful of disagreements do not establish statistically significant model differences.
- **Synthetic suite:** Small, authored for this task, with assumed labels; it is not a robust benchmark.
- **Detection is not prevention:** A model can miss attacks or incorrectly flag benign content. It cannot replace authorization, isolation, output controls, or capability restrictions.
- **Threshold portability:** Logistic probabilities and SVM decision scores have different meanings. Their raw thresholds are not interchangeable; the SVM scores are not calibrated.

## I. Reproducibility

Use the project environment and existing local data. No new packages, external datasets, GPU frameworks, or network downloads are required.

```powershell
.\venv\Scripts\Activate.ps1
python ml\preprocess_data.py --config core
python ml\train_svm.py --config core --max-features 20000 --ngram-min 1 --ngram-max 2 --c-reg 1.0 --class-weight balanced --random-state 42
python ml\compare_models.py --config core
python ml\compare_errors.py --config core
python ml\robustness_tests.py
python -m unittest ml/test_svm.py ml/test_model.py
```

The baseline can be re-trained only when intentionally refreshing Day 2; it was not re-trained for this comparison. The Day 3 workflow loads `ml/artifacts/prompt_injection_logreg.joblib` and `ml/artifacts/prompt_injection_svm.joblib`, with metadata in the corresponding JSON files under `ml/artifacts/`. Python 3.14.8, scikit-learn 1.9.1, joblib 1.6.0, NumPy 2.5.4, and pandas 3.0.6 were used for this run.

### Day 3 acceptance checklist

- **Complete** — Existing Day 1 and Day 2 outputs inspected.
- **Complete** — Logistic Regression baseline artifact verified.
- **Complete** — Existing official splits reused; train/validation/test sizes and group isolation checked.
- **Complete** — Linear SVM pipeline implemented.
- **Complete** — Linear SVM trained without a convergence warning.
- **Complete** — SVM artifact saved to `ml/artifacts/prompt_injection_svm.joblib`.
- **Complete** — SVM metadata saved.
- **Complete** — Both models evaluated on the same held-out test rows.
- **Complete** — Metrics calculated from actual predictions.
- **Complete** — Confusion matrices generated.
- **Complete** — ROC-AUC calculated with both test classes present.
- **Complete** — Thresholds selected using validation data only and evaluated on test afterward.
- **Complete** — Model disagreements and errors analyzed.
- **Complete** — Synthetic robustness suite executed.
- **Complete** — SVM and Logistic Regression artifact tests passed.
- **Complete** — Research report generated.
- **Complete** — README updated.
- **Complete** — Commands, configuration, and measured results documented.
