"""
AI Guardian (SentinelAI) - Day 3: Linear SVM Model Training Script
====================================================================
Trains a TF-IDF + LinearSVC prompt-injection classifier for comparison
against the Day 2 Logistic Regression baseline.

Architecture:
- Pipeline: TfidfVectorizer -> LinearSVC
- Fit solely on the training partition (core_train).
- Validation partition used for threshold analysis on decision scores.
- Complete fitted pipeline serialized to Joblib with structured metadata.

Key Design Notes:
- LinearSVC uses decision_function() to produce decision scores.
- These scores are NOT calibrated probabilities. They represent the signed
  distance from the model's learned decision boundary.
- A positive score means the model leans toward class 1 (malicious);
  a negative score means class 0 (benign), given the default class ordering.
- Score magnitudes should NOT be interpreted as percentages of attack probability.
- Threshold adjustments on decision scores must be selected using validation data.
"""

import argparse
import datetime
import json
import os
import sys
import time
import warnings
from typing import Any, Dict, Tuple

# Ensure SentinelAI project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer
from sklearn.svm import LinearSVC

from ml.preprocess_data import LABEL_MAPPING, get_preprocessed_splits, validate_text_inputs


DATASET_ID = "cyberec/Prompt-injection-dataset"


def build_svm_pipeline(
    max_features: int = 20000,
    ngram_range: Tuple[int, int] = (1, 2),
    min_df: int = 2,
    sublinear_tf: bool = True,
    c_reg: float = 1.0,
    class_weight: str = "balanced",
    max_iter: int = 10000,
    random_state: int = 42,
) -> Pipeline:
    """
    Constructs an end-to-end scikit-learn Pipeline with TF-IDF vectorization
    and Linear Support Vector Classification.

    LinearSVC is chosen over SVC(kernel='linear') for:
    - O(n) scaling with liblinear vs O(n^2-n^3) with libsvm.
    - Memory efficiency suitable for 8 GB RAM systems.
    - Equivalent decision boundary to SVC(kernel='linear') for linearly separable text.

    Note: LinearSVC does not support predict_proba() natively.
    Use decision_function() for decision scores (not probabilities).
    """
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=ngram_range,
        min_df=min_df,
        sublinear_tf=sublinear_tf,
        lowercase=True,
        # Preserve all security tokens by omitting aggressive standard stop words
        stop_words=None,
    )

    classifier = LinearSVC(
        C=c_reg,
        class_weight=class_weight,
        max_iter=max_iter,
        random_state=random_state,
        loss="squared_hinge",  # Default, smooth loss for convergence
        dual="auto",  # Let sklearn choose based on n_samples vs n_features
    )

    return Pipeline([
        ("validate_text", FunctionTransformer(validate_text_inputs, validate=False)),
        ("tfidf", vectorizer),
        ("clf", classifier),
    ])


def calibrate_svm_thresholds(
    y_true: np.ndarray,
    decision_scores: np.ndarray,
) -> Dict[str, Any]:
    """
    Evaluates alternative decision thresholds on LinearSVC decision scores
    using validation data.

    IMPORTANT: decision_scores are NOT probabilities.
    - The default decision boundary for LinearSVC is at score = 0.0.
    - Scores > 0 predict class 1 (malicious); scores < 0 predict class 0 (benign).
    - Score magnitude indicates distance from the boundary, not attack probability.
    - Threshold adjustments shift the effective decision boundary.

    This analysis sweeps thresholds across the observed score range to find
    operating points that balance false positives vs. false negatives.
    """
    # Sweep thresholds across the score range centered on 0
    min_score = float(np.min(decision_scores))
    max_score = float(np.max(decision_scores))
    # Focus sweep on the region around the default boundary (0.0)
    sweep_min = max(min_score, -3.0)
    sweep_max = min(max_score, 3.0)
    candidate_thresholds = np.linspace(sweep_min, sweep_max, 201)

    best_f1 = 0.0
    best_f1_th = 0.0

    low_fpr_th = 0.0
    low_fpr_val = 1.0
    low_fpr_recall = 0.0

    records = []
    for th in candidate_thresholds:
        preds = (decision_scores >= th).astype(int)
        if len(np.unique(preds)) < 2 and len(np.unique(y_true)) > 1:
            # Skip degenerate thresholds that predict all one class
            continue
        cm = confusion_matrix(y_true, preds, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        p = precision_score(y_true, preds, zero_division=0)
        r = recall_score(y_true, preds, zero_division=0)
        f = f1_score(y_true, preds, zero_division=0)

        records.append({
            "threshold": round(float(th), 4),
            "precision": round(float(p), 4),
            "recall": round(float(r), 4),
            "f1": round(float(f), 4),
            "fpr": round(float(fpr), 4),
            "fp": int(fp),
            "fn": int(fn),
        })

        if f > best_f1:
            best_f1 = f
            best_f1_th = th

        # Low-FPR threshold: Target FPR <= 2.0% while keeping recall >= 90%
        if fpr <= 0.02 and r >= 0.90:
            if r > low_fpr_recall or low_fpr_val > fpr:
                low_fpr_th = th
                low_fpr_val = fpr
                low_fpr_recall = r

    # Sample key thresholds for the report
    sampled = []
    target_ths = [-1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0]
    for rec in records:
        if any(abs(rec["threshold"] - t) < 0.04 for t in target_ths):
            sampled.append(rec)

    return {
        "default_threshold": 0.0,
        "score_type": "decision_function (NOT calibrated probability)",
        "best_f1_threshold": round(float(best_f1_th), 4),
        "best_f1_score": round(float(best_f1), 4),
        "low_fpr_threshold": round(float(low_fpr_th), 4),
        "score_range": {"min": round(min_score, 4), "max": round(max_score, 4)},
        "threshold_sweep_sample": sampled,
    }


def train_svm_model(
    config: str = "core",
    data_dir: str = "ml/data",
    artifacts_dir: str = "ml/artifacts",
    max_features: int = 20000,
    ngram_min: int = 1,
    ngram_max: int = 2,
    c_reg: float = 1.0,
    class_weight: str = "balanced",
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Full SVM training pipeline execution, validation evaluation, and artifact serialization.
    """
    os.makedirs(artifacts_dir, exist_ok=True)

    print(f"[*] Loading preprocessed data ({config} configuration)...")
    train_df, val_df, test_df = get_preprocessed_splits(
        config=config,
        data_dir=data_dir,
        drop_duplicates=True,
    )

    X_train, y_train = train_df["text"], train_df["label"]
    X_val, y_val = val_df["text"], val_df["label"]

    print(f"[*] Training partition: {len(X_train):,} samples | Val partition: {len(X_val):,} samples | Test partition: {len(test_df):,} samples")
    print(f"[*] Target labels: {LABEL_MAPPING}")
    print(f"[*] Train class distribution: {dict(y_train.value_counts().sort_index())}")

    # Build Pipeline
    pipeline = build_svm_pipeline(
        max_features=max_features,
        ngram_range=(ngram_min, ngram_max),
        min_df=2,
        sublinear_tf=True,
        c_reg=c_reg,
        class_weight=class_weight,
        random_state=random_state,
    )

    print("[*] Fitting Pipeline (TF-IDF Vectorizer + LinearSVC)...")
    # Capture convergence warnings
    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter("always")
        t0 = time.perf_counter()
        pipeline.fit(X_train, y_train)
        training_duration_sec = time.perf_counter() - t0

    convergence_warning = None
    for w in caught_warnings:
        if "ConvergenceWarning" in str(w.category):
            convergence_warning = str(w.message)
            print(f"[!] Convergence Warning: {convergence_warning}")

    print(f"[+] Model training completed in {training_duration_sec:.4f} seconds.")

    # Validation Set Evaluation using decision_function
    val_scores = pipeline.decision_function(X_val)
    val_preds_default = pipeline.predict(X_val)

    val_accuracy = float(accuracy_score(y_val, val_preds_default))
    val_precision = float(precision_score(y_val, val_preds_default, zero_division=0))
    val_recall = float(recall_score(y_val, val_preds_default, zero_division=0))
    val_f1 = float(f1_score(y_val, val_preds_default, zero_division=0))
    cm_val = confusion_matrix(y_val, val_preds_default, labels=[0, 1])
    val_tn, val_fp, val_fn, val_tp = cm_val.ravel()
    val_fpr = float(val_fp / (val_fp + val_tn)) if (val_fp + val_tn) > 0 else 0.0

    print("\n--- Validation Performance (Default Threshold = 0.0 on decision scores) ---")
    print(f" Accuracy:  {val_accuracy:.4f}")
    print(f" Precision: {val_precision:.4f}")
    print(f" Recall:    {val_recall:.4f}")
    print(f" F1-Score:  {val_f1:.4f}")
    print(f" FPR:       {val_fpr:.4f} (False Positives: {val_fp}, False Negatives: {val_fn})")
    print(f" Decision score range: [{val_scores.min():.4f}, {val_scores.max():.4f}]")

    # Threshold calibration on validation set using decision scores
    threshold_analysis = calibrate_svm_thresholds(y_val.to_numpy(), val_scores)
    print(f"\n--- Validation Threshold Tuning (on decision scores) ---")
    print(f" Best F1 Threshold:     {threshold_analysis['best_f1_threshold']} (F1 = {threshold_analysis['best_f1_score']:.4f})")
    print(f" Low-FPR Profile Thresh: {threshold_analysis['low_fpr_threshold']}")
    print(f" NOTE: These thresholds are on decision_function scores, NOT probabilities.")

    # Save Pipeline artifact
    model_filename = "prompt_injection_svm.joblib"
    model_path = os.path.join(artifacts_dir, model_filename)
    joblib.dump(pipeline, model_path, compress=3)
    model_size_bytes = os.path.getsize(model_path)
    print(f"\n[+] Saved complete trained pipeline to: {model_path} ({model_size_bytes / 1024:.1f} KB)")

    # Save Metadata
    import sklearn
    metadata = {
        "model_name": "prompt_injection_svm",
        "dataset_identifier": DATASET_ID,
        "dataset_config": config,
        "text_column": "text",
        "label_column": "label",
        "label_mapping": {str(k): v for k, v in LABEL_MAPPING.items()},
        "split_strategy": "Official group-aware splits (core_train, core_validation, core_test) with zero cross-split text/group leakage.",
        "random_seed": random_state,
        "vectorizer_config": {
            "type": "TfidfVectorizer",
            "max_features": max_features,
            "ngram_range": [ngram_min, ngram_max],
            "min_df": 2,
            "sublinear_tf": True,
            "lowercase": True,
            "stop_words": None,
            "actual_vocabulary_size": len(pipeline.named_steps["tfidf"].vocabulary_),
        },
        "classifier_config": {
            "type": "LinearSVC",
            "C": c_reg,
            "loss": "squared_hinge",
            "class_weight": class_weight,
            "max_iter": 10000,
            "random_state": random_state,
            "dual": "auto",
            "scoring_method": "decision_function (NOT predict_proba)",
            "score_interpretation": (
                "decision_function() returns the signed distance from the learned "
                "decision boundary. Positive scores indicate class 1 (malicious), "
                "negative scores indicate class 0 (benign). Magnitudes are NOT "
                "calibrated probabilities and should not be treated as percentages."
            ),
        },
        "training_stats": {
            "training_samples": len(X_train),
            "validation_samples": len(X_val),
            "test_samples": len(test_df),
            "training_duration_seconds": round(training_duration_sec, 4),
            "model_size_bytes": model_size_bytes,
            "training_timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "convergence_warning": convergence_warning,
        },
        "validation_metrics": {
            "default_threshold": 0.0,
            "accuracy": round(val_accuracy, 4),
            "precision": round(val_precision, 4),
            "recall": round(val_recall, 4),
            "f1_score": round(val_f1, 4),
            "false_positive_rate": round(val_fpr, 4),
            "false_positives": int(val_fp),
            "false_negatives": int(val_fn),
            "decision_score_range": {
                "min": round(float(val_scores.min()), 4),
                "max": round(float(val_scores.max()), 4),
            },
        },
        "threshold_calibration": threshold_analysis,
        "environment": {
            "python_version": sys.version,
            "scikit_learn_version": sklearn.__version__,
            "joblib_version": joblib.__version__,
            "numpy_version": np.__version__,
            "pandas_version": pd.__version__,
        },
        "security_limitations": [
            "Statistical bag-of-words / n-gram models can miss novel zero-day prompt injection phrasings and out-of-vocabulary evasion suffixes.",
            "Spurious text length correlations can affect classification of extremely long benign inputs.",
            "Prompt injection classification is non-deterministic and must be paired with deterministic security policies and capability constraints.",
            "Model is trained primarily on English prompt injections and does not provide multi-lingual or multi-turn crescendo attack guarantees.",
            "LinearSVC decision scores are NOT calibrated probabilities. They represent geometric distance from the hyperplane.",
        ],
    }

    metadata_path = os.path.join(artifacts_dir, "svm_model_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"[+] Saved model metadata to: {metadata_path}")

    return metadata


def main():
    parser = argparse.ArgumentParser(description="Train SentinelAI Linear SVM Prompt Injection Classifier")
    parser.add_argument("--config", type=str, default="core", choices=["core", "full"])
    parser.add_argument("--data-dir", type=str, default="ml/data")
    parser.add_argument("--artifacts-dir", type=str, default="ml/artifacts")
    parser.add_argument("--max-features", type=int, default=20000)
    parser.add_argument("--ngram-min", type=int, default=1)
    parser.add_argument("--ngram-max", type=int, default=2)
    parser.add_argument("--c-reg", type=float, default=1.0)
    parser.add_argument("--class-weight", type=str, default="balanced")
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()

    print("=" * 70)
    print(" SentinelAI - Day 3: Linear SVM Model Training Engine")
    print(f" Target Config: {args.config} | Max Features: {args.max_features:,} | Seed: {args.random_state}")
    print("=" * 70)

    train_svm_model(
        config=args.config,
        data_dir=args.data_dir,
        artifacts_dir=args.artifacts_dir,
        max_features=args.max_features,
        ngram_min=args.ngram_min,
        ngram_max=args.ngram_max,
        c_reg=args.c_reg,
        class_weight=args.class_weight,
        random_state=args.random_state,
    )


if __name__ == "__main__":
    main()
