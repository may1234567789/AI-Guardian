"""
AI Guardian (SentinelAI) - Model Training Script
=================================================
Trains a leakage-safe baseline prompt-injection classifier using TF-IDF feature
extraction and Logistic Regression.

Architecture:
- Pipeline: TfidfVectorizer -> LogisticRegression
- Fit solely on the training partition (Core dataset).
- Validation partition used exclusively for hyperparameter confirmation and threshold calibration.
- Complete fitted pipeline serialized to Joblib with structured metadata.
"""

import argparse
import datetime
import json
import os
import sys
import time
from typing import Any, Dict, Tuple

# Ensure SentinelAI project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline

from ml.preprocess_data import LABEL_MAPPING, get_preprocessed_splits


DATASET_ID = "cyberec/Prompt-injection-dataset"


def build_pipeline(
    max_features: int = 20000,
    ngram_range: Tuple[int, int] = (1, 2),
    min_df: int = 2,
    sublinear_tf: bool = True,
    c_reg: float = 1.0,
    class_weight: str = "balanced",
    max_iter: int = 1000,
    random_state: int = 42,
) -> Pipeline:
    """
    Constructs an end-to-end scikit-learn Pipeline with TF-IDF vectorization
    and Logistic Regression classifier.
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

    classifier = LogisticRegression(
        C=c_reg,
        solver="lbfgs",
        class_weight=class_weight,
        max_iter=max_iter,
        random_state=random_state,
    )

    return Pipeline([
        ("tfidf", vectorizer),
        ("clf", classifier),
    ])


def calibrate_thresholds(
    y_true: np.ndarray,
    y_probs: np.ndarray,
) -> Dict[str, Any]:
    """
    Evaluates decision threshold behavior on validation data to identify
    optimal operating points for enterprise firewall deployments.
    """
    candidate_thresholds = np.linspace(0.1, 0.9, 81)
    best_f1 = 0.0
    best_f1_th = 0.50

    low_fpr_th = 0.50
    low_fpr_val = 1.0
    low_fpr_recall = 0.0

    records = []
    for th in candidate_thresholds:
        preds = (y_probs >= th).astype(int)
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

    return {
        "default_threshold": 0.50,
        "best_f1_threshold": round(float(best_f1_th), 4),
        "best_f1_score": round(float(best_f1), 4),
        "low_fpr_threshold": round(float(low_fpr_th), 4),
        "threshold_sweep_sample": [r for r in records if round(r["threshold"], 2) in [0.30, 0.40, 0.50, 0.60, 0.70, 0.75, 0.80]],
    }


def train_model(
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
    Full training pipeline execution, validation evaluation, and artifact serialization.
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

    # Build Pipeline
    pipeline = build_pipeline(
        max_features=max_features,
        ngram_range=(ngram_min, ngram_max),
        min_df=2,
        sublinear_tf=True,
        c_reg=c_reg,
        class_weight=class_weight,
        random_state=random_state,
    )

    print("[*] Fitting Pipeline (TF-IDF Vectorizer + Logistic Regression)...")
    t0 = time.perf_counter()
    pipeline.fit(X_train, y_train)
    training_duration_sec = time.perf_counter() - t0
    print(f"[+] Model training completed in {training_duration_sec:.3f} seconds.")

    # Validation Set Evaluation
    val_probs = pipeline.predict_proba(X_val)[:, 1]
    val_preds_default = pipeline.predict(X_val)

    val_accuracy = float(accuracy_score(y_val, val_preds_default))
    val_precision = float(precision_score(y_val, val_preds_default, zero_division=0))
    val_recall = float(recall_score(y_val, val_preds_default, zero_division=0))
    val_f1 = float(f1_score(y_val, val_preds_default, zero_division=0))
    val_roc_auc = float(roc_auc_score(y_val, val_probs))
    cm_val = confusion_matrix(y_val, val_preds_default, labels=[0, 1])
    val_tn, val_fp, val_fn, val_tp = cm_val.ravel()
    val_fpr = float(val_fp / (val_fp + val_tn)) if (val_fp + val_tn) > 0 else 0.0

    print("\n--- Validation Performance (Default Threshold = 0.50) ---")
    print(f" Accuracy:  {val_accuracy:.4f}")
    print(f" Precision: {val_precision:.4f}")
    print(f" Recall:    {val_recall:.4f}")
    print(f" F1-Score:  {val_f1:.4f}")
    print(f" ROC-AUC:   {val_roc_auc:.4f}")
    print(f" FPR:       {val_fpr:.4f} (False Positives: {val_fp}, False Negatives: {val_fn})")

    # Threshold calibration on validation set
    threshold_analysis = calibrate_thresholds(y_val.to_numpy(), val_probs)
    print(f"\n--- Validation Threshold Tuning ---")
    print(f" Best F1 Threshold:    {threshold_analysis['best_f1_threshold']} (F1 = {threshold_analysis['best_f1_score']:.4f})")
    print(f" Low-FPR Profile Thresh: {threshold_analysis['low_fpr_threshold']}")

    # Save Pipeline artifact
    model_filename = "prompt_injection_logreg.joblib"
    model_path = os.path.join(artifacts_dir, model_filename)
    joblib.dump(pipeline, model_path, compress=3)
    model_size_bytes = os.path.getsize(model_path)
    print(f"\n[+] Saved complete trained pipeline to: {model_path} ({model_size_bytes / 1024:.1f} KB)")

    # Save Metadata
    import sklearn
    metadata = {
        "model_name": "prompt_injection_logreg",
        "dataset_identifier": DATASET_ID,
        "dataset_config": config,
        "text_column": "text",
        "label_column": "label",
        "label_mapping": LABEL_MAPPING,
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
            "type": "LogisticRegression",
            "C": c_reg,
            "penalty": "l2 (default)",
            "solver": "lbfgs",
            "class_weight": class_weight,
            "max_iter": 1000,
            "random_state": random_state,
        },
        "training_stats": {
            "training_samples": len(X_train),
            "validation_samples": len(X_val),
            "test_samples": len(test_df),
            "training_duration_seconds": round(training_duration_sec, 4),
            "model_size_bytes": model_size_bytes,
            "training_timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
        "validation_metrics": {
            "default_threshold": 0.50,
            "accuracy": round(val_accuracy, 4),
            "precision": round(val_precision, 4),
            "recall": round(val_recall, 4),
            "f1_score": round(val_f1, 4),
            "roc_auc": round(val_roc_auc, 4),
            "false_positive_rate": round(val_fpr, 4),
            "false_positives": int(val_fp),
            "false_negatives": int(val_fn),
        },
        "threshold_calibration": threshold_analysis,
        "environment": {
            "python_version": sys.version,
            "scikit_learn_version": sklearn.__version__,
            "joblib_version": joblib.__version__,
        },
        "security_limitations": [
            "Statistical bag-of-words / n-gram models can miss novel zero-day prompt injection phrasings and out-of-vocabulary evasion suffixes.",
            "Spurious text length correlations can affect classification of extremely long benign inputs.",
            "Prompt injection classification is non-deterministic and must be paired with deterministic security policies and capability constraints.",
            "Model is trained primarily on English prompt injections and does not provide multi-lingual or multi-turn crescendo attack guarantees.",
        ],
    }

    metadata_path = os.path.join(artifacts_dir, "model_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"[+] Saved model metadata to: {metadata_path}")

    return metadata


def main():
    parser = argparse.ArgumentParser(description="Train SentinelAI Prompt Injection Classifier")
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
    print(" SentinelAI - Model Training Engine")
    print(f" Target Config: {args.config} | Max Features: {args.max_features:,} | Seed: {args.random_state}")
    print("=" * 70)

    train_model(
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
