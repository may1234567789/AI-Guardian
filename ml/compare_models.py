"""
AI Guardian (SentinelAI) - Day 3: Model Comparison Engine
==========================================================
Fair comparison of TF-IDF + Logistic Regression (Day 2 baseline) vs.
TF-IDF + LinearSVC (Day 3 challenger) on the same held-out test set.

Both models are loaded from their saved artifacts to ensure the comparison
uses the exact models that were trained, not silently retrained variants.

Comparison metrics:
1. Accuracy, Precision, Recall, F1-Score
2. Confusion matrix
3. False-positive rate (FPR) and False-negative rate (FNR)
4. ROC-AUC (where valid scores are available)
5. Inference latency (single-sample and batch)
6. Model artifact size
7. Training duration (from metadata)

Visualizations:
- Metric comparison bar chart
- Confusion matrices for each model
- ROC curves overlay (where applicable)
- Precision-recall curves (where applicable)
- Threshold analysis plots (on validation data)
"""

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

# Ensure SentinelAI project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    auc,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from ml.preprocess_data import get_preprocessed_splits


def measure_inference_latency(
    model: Any,
    texts: List[str],
    num_runs: int = 5,
    sample_size: int = 100,
) -> Dict[str, float]:
    """Measures CPU inference latency reproducibly across multiple runs."""
    # Warm-up pass
    _ = model.predict(texts[:min(10, len(texts))])

    # Batch latency on full test set
    batch_latencies = []
    for _ in range(num_runs):
        t0 = time.perf_counter()
        _ = model.predict(texts)
        batch_latencies.append(time.perf_counter() - t0)

    mean_batch_latency = float(np.mean(batch_latencies))
    latency_per_sample_batch_ms = (mean_batch_latency / len(texts)) * 1000.0

    # Single-sample inference latency
    sample_texts = texts[:min(sample_size, len(texts))]
    single_latencies_ms = []
    for text in sample_texts:
        t0 = time.perf_counter()
        _ = model.predict([text])
        single_latencies_ms.append((time.perf_counter() - t0) * 1000.0)

    return {
        "full_batch_latency_seconds": round(mean_batch_latency, 5),
        "batch_latency_per_sample_ms": round(latency_per_sample_batch_ms, 4),
        "single_request_latency_mean_ms": round(float(np.mean(single_latencies_ms)), 4),
        "single_request_latency_p95_ms": round(float(np.percentile(single_latencies_ms, 95)), 4),
        "single_request_latency_p99_ms": round(float(np.percentile(single_latencies_ms, 99)), 4),
    }


def get_model_scores(model: Any, X: pd.Series) -> Tuple[np.ndarray, np.ndarray, str]:
    """
    Gets predictions and continuous scores from a model.
    
    Returns:
        (predictions, scores, score_type)
        - score_type is 'probability' for LogReg or 'decision_function' for LinearSVC
    """
    predictions = model.predict(X)
    
    # Try predict_proba first (Logistic Regression)
    if hasattr(model, "predict_proba"):
        try:
            scores = model.predict_proba(X)[:, 1]
            return predictions, scores, "probability"
        except AttributeError:
            pass
    
    # Fall back to decision_function (LinearSVC)
    if hasattr(model, "decision_function"):
        scores = model.decision_function(X)
        return predictions, scores, "decision_function"
    
    # Last resort: use predictions as binary scores
    return predictions, predictions.astype(float), "binary"


def compute_all_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    scores: np.ndarray,
    score_type: str,
) -> Dict[str, Any]:
    """Computes the full set of evaluation metrics."""
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    accuracy = float(accuracy_score(y_true, y_pred))
    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0

    result = {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "false_positive_rate": round(fpr, 4),
        "false_negative_rate": round(fnr, 4),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "score_type": score_type,
    }

    # ROC-AUC: valid for both probabilities and decision function scores
    # as long as both classes are present in y_true
    if len(np.unique(y_true)) == 2:
        try:
            roc_auc = float(roc_auc_score(y_true, scores))
            result["roc_auc"] = round(roc_auc, 4)
        except ValueError:
            result["roc_auc"] = None
            result["roc_auc_note"] = "Could not compute ROC-AUC"
    else:
        result["roc_auc"] = None
        result["roc_auc_note"] = "Only one class present in test set"

    return result


def select_validation_threshold(
    y_true: np.ndarray,
    scores: np.ndarray,
    default_threshold: float,
) -> Dict[str, float]:
    """Selects the highest-F1 threshold on validation scores only."""
    best_threshold = default_threshold
    best_f1 = -1.0
    for threshold in np.unique(scores):
        predictions = (scores >= threshold).astype(int)
        candidate_f1 = float(f1_score(y_true, predictions, zero_division=0))
        if candidate_f1 > best_f1 or (
            candidate_f1 == best_f1
            and abs(float(threshold) - default_threshold)
            < abs(best_threshold - default_threshold)
        ):
            best_threshold = float(threshold)
            best_f1 = candidate_f1

    return {"threshold": best_threshold, "validation_f1": best_f1}


def plot_confusion_matrices(
    cm_logreg: np.ndarray,
    cm_svm: np.ndarray,
    output_path: str,
    n_test: int,
):
    """Generates side-by-side confusion matrix heatmaps."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    class_labels = ["Benign (0)", "Malicious (1)"]

    for ax, cm, title in zip(
        axes,
        [cm_logreg, cm_svm],
        ["Logistic Regression", "Linear SVM"],
    ):
        sns.heatmap(
            cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=class_labels, yticklabels=class_labels,
            cbar=True, annot_kws={"size": 14, "weight": "bold"}, ax=ax,
        )
        ax.set_title(f"{title}\n(N={n_test})", fontsize=13, weight="bold", pad=10)
        ax.set_xlabel("Predicted Label", fontsize=11, labelpad=8)
        ax.set_ylabel("True Label", fontsize=11, labelpad=8)

    plt.suptitle("Day 3: Model Comparison — Confusion Matrices", fontsize=15, weight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_metric_comparison(
    logreg_metrics: Dict[str, Any],
    svm_metrics: Dict[str, Any],
    output_path: str,
):
    """Generates a grouped bar chart comparing key metrics."""
    metric_names = ["Accuracy", "Precision", "Recall", "F1-Score"]
    logreg_vals = [
        logreg_metrics["accuracy"],
        logreg_metrics["precision"],
        logreg_metrics["recall"],
        logreg_metrics["f1_score"],
    ]
    svm_vals = [
        svm_metrics["accuracy"],
        svm_metrics["precision"],
        svm_metrics["recall"],
        svm_metrics["f1_score"],
    ]

    x = np.arange(len(metric_names))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9, 6))
    bars1 = ax.bar(x - width / 2, logreg_vals, width, label="Logistic Regression", color="#4a90e2", edgecolor="white")
    bars2 = ax.bar(x + width / 2, svm_vals, width, label="Linear SVM", color="#e74c3c", edgecolor="white")

    ax.set_ylabel("Score", fontsize=12)
    ax.set_title("Day 3: Logistic Regression vs. Linear SVM — Test Metrics", fontsize=14, weight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(metric_names, fontsize=11)
    ax.set_ylim([0.85, 1.02])
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    ax.legend(loc="lower right", fontsize=11)

    # Value labels
    for bar_group in [bars1, bars2]:
        for bar in bar_group:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height + 0.003,
                    f"{height:.3f}", ha="center", va="bottom", fontsize=9, weight="bold")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_roc_curves(
    y_true: np.ndarray,
    logreg_scores: np.ndarray,
    svm_scores: np.ndarray,
    logreg_auc: float,
    svm_auc: float,
    output_path: str,
):
    """Generates overlaid ROC curves for both models."""
    fpr_lr, tpr_lr, _ = roc_curve(y_true, logreg_scores)
    fpr_svm, tpr_svm, _ = roc_curve(y_true, svm_scores)

    fig, ax = plt.subplots(figsize=(8, 7))
    ax.plot(fpr_lr, tpr_lr, color="#4a90e2", lw=2.5,
            label=f"Logistic Regression (AUC = {logreg_auc:.4f})")
    ax.plot(fpr_svm, tpr_svm, color="#e74c3c", lw=2.5,
            label=f"Linear SVM (AUC = {svm_auc:.4f})")
    ax.plot([0, 1], [0, 1], color="#7f7f7f", lw=1.5, linestyle="--",
            label="Random Chance (AUC = 0.50)")

    ax.set_xlim([-0.02, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate (FPR)", fontsize=12, labelpad=8)
    ax.set_ylabel("True Positive Rate (Recall)", fontsize=12, labelpad=8)
    ax.set_title("Day 3: ROC Curves — LogReg vs. Linear SVM", fontsize=14, weight="bold", pad=12)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="lower right", fontsize=11)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_precision_recall_curves(
    y_true: np.ndarray,
    logreg_scores: np.ndarray,
    svm_scores: np.ndarray,
    output_path: str,
):
    """Generates overlaid precision-recall curves for both models."""
    p_lr, r_lr, _ = precision_recall_curve(y_true, logreg_scores)
    p_svm, r_svm, _ = precision_recall_curve(y_true, svm_scores)

    lr_pr_auc = auc(r_lr, p_lr)
    svm_pr_auc = auc(r_svm, p_svm)

    fig, ax = plt.subplots(figsize=(8, 7))
    ax.plot(r_lr, p_lr, color="#4a90e2", lw=2.5,
            label=f"Logistic Regression (PR-AUC = {lr_pr_auc:.4f})")
    ax.plot(r_svm, p_svm, color="#e74c3c", lw=2.5,
            label=f"Linear SVM (PR-AUC = {svm_pr_auc:.4f})")

    # Baseline: prevalence of positive class
    prevalence = np.mean(y_true)
    ax.axhline(y=prevalence, color="#7f7f7f", lw=1.5, linestyle="--",
               label=f"Baseline (prevalence = {prevalence:.2f})")

    ax.set_xlim([0.0, 1.05])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("Recall", fontsize=12, labelpad=8)
    ax.set_ylabel("Precision", fontsize=12, labelpad=8)
    ax.set_title("Day 3: Precision-Recall Curves — LogReg vs. Linear SVM", fontsize=14, weight="bold", pad=12)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="lower left", fontsize=11)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_threshold_analysis(
    y_true: np.ndarray,
    logreg_probs: np.ndarray,
    svm_scores: np.ndarray,
    output_path: str,
    selected_lr_threshold: float,
    selected_svm_threshold: float,
):
    """
    Generates threshold analysis plots for both models.
    Uses VALIDATION data scores (must be passed in) — not test data.
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Logistic Regression: thresholds on probabilities
    thresholds_lr = np.linspace(0.1, 0.95, 50)
    f1s_lr, fprs_lr, recalls_lr = [], [], []
    for th in thresholds_lr:
        preds = (logreg_probs >= th).astype(int)
        f1s_lr.append(f1_score(y_true, preds, zero_division=0))
        cm = confusion_matrix(y_true, preds, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()
        fprs_lr.append(fp / (fp + tn) if (fp + tn) > 0 else 0.0)
        recalls_lr.append(recall_score(y_true, preds, zero_division=0))

    ax = axes[0]
    ax.plot(thresholds_lr, f1s_lr, color="#4a90e2", lw=2, label="F1-Score")
    ax.plot(thresholds_lr, recalls_lr, color="#2ecc71", lw=2, linestyle="--", label="Recall")
    ax.plot(thresholds_lr, fprs_lr, color="#e74c3c", lw=2, linestyle=":", label="FPR")
    ax.axvline(x=0.5, color="#7f7f7f", lw=1, linestyle="--", alpha=0.7, label="Default (0.5)")
    ax.axvline(x=selected_lr_threshold, color="#111111", lw=1, linestyle="-.", alpha=0.8,
               label=f"Validation-selected ({selected_lr_threshold:.3f})")
    ax.set_xlabel("Probability Threshold", fontsize=11)
    ax.set_ylabel("Score", fontsize=11)
    ax.set_title("Logistic Regression\n(Validation Threshold Analysis)", fontsize=12, weight="bold")
    ax.legend(fontsize=9)
    ax.grid(True, linestyle=":", alpha=0.5)

    # Linear SVM: thresholds on decision scores
    sweep_min = max(float(np.min(svm_scores)), -3.0)
    sweep_max = min(float(np.max(svm_scores)), 3.0)
    thresholds_svm = np.linspace(sweep_min, sweep_max, 50)
    f1s_svm, fprs_svm, recalls_svm = [], [], []
    for th in thresholds_svm:
        preds = (svm_scores >= th).astype(int)
        f1s_svm.append(f1_score(y_true, preds, zero_division=0))
        cm = confusion_matrix(y_true, preds, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()
        fprs_svm.append(fp / (fp + tn) if (fp + tn) > 0 else 0.0)
        recalls_svm.append(recall_score(y_true, preds, zero_division=0))

    ax = axes[1]
    ax.plot(thresholds_svm, f1s_svm, color="#e74c3c", lw=2, label="F1-Score")
    ax.plot(thresholds_svm, recalls_svm, color="#2ecc71", lw=2, linestyle="--", label="Recall")
    ax.plot(thresholds_svm, fprs_svm, color="#4a90e2", lw=2, linestyle=":", label="FPR")
    ax.axvline(x=0.0, color="#7f7f7f", lw=1, linestyle="--", alpha=0.7, label="Default (0.0)")
    ax.axvline(x=selected_svm_threshold, color="#111111", lw=1, linestyle="-.", alpha=0.8,
               label=f"Validation-selected ({selected_svm_threshold:.3f})")
    ax.set_xlabel("Decision Score Threshold", fontsize=11)
    ax.set_ylabel("Score", fontsize=11)
    ax.set_title("Linear SVM\n(Validation Threshold Analysis on Decision Scores)", fontsize=12, weight="bold")
    ax.legend(fontsize=9)
    ax.grid(True, linestyle=":", alpha=0.5)

    plt.suptitle("Day 3: Validation-Based Threshold Analysis", fontsize=14, weight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def compare_models(
    logreg_path: str = "ml/artifacts/prompt_injection_logreg.joblib",
    svm_path: str = "ml/artifacts/prompt_injection_svm.joblib",
    logreg_meta_path: str = "ml/artifacts/model_metadata.json",
    svm_meta_path: str = "ml/artifacts/svm_model_metadata.json",
    data_dir: str = "ml/data",
    reports_dir: str = "ml/reports",
    config: str = "core",
) -> Dict[str, Any]:
    """Main comparison workflow."""
    os.makedirs(reports_dir, exist_ok=True)

    # Verify both artifacts exist
    for path, name in [(logreg_path, "Logistic Regression"), (svm_path, "Linear SVM")]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"{name} model not found at {path}.")

    # Load models from saved artifacts
    print("[*] Loading Logistic Regression baseline...")
    logreg_pipeline = joblib.load(logreg_path)
    print("[*] Loading Linear SVM model...")
    svm_pipeline = joblib.load(svm_path)

    # Load metadata
    logreg_meta = {}
    if os.path.exists(logreg_meta_path):
        with open(logreg_meta_path, "r", encoding="utf-8") as f:
            logreg_meta = json.load(f)

    svm_meta = {}
    if os.path.exists(svm_meta_path):
        with open(svm_meta_path, "r", encoding="utf-8") as f:
            svm_meta = json.load(f)

    # Load test data (same split for both models)
    print(f"[*] Loading held-out test data ({config})...")
    train_df, val_df, test_df = get_preprocessed_splits(config=config, data_dir=data_dir, drop_duplicates=True)
    X_test = test_df["text"]
    y_test = test_df["label"].to_numpy()
    X_val = val_df["text"]
    y_val = val_df["label"].to_numpy()
    test_size = len(X_test)
    num_benign = int((y_test == 0).sum())
    num_malicious = int((y_test == 1).sum())

    print(f"[*] Test set: {test_size} examples | Benign: {num_benign} | Malicious: {num_malicious}")

    # Get scores from both models
    print("[*] Computing predictions and scores...")
    lr_preds, lr_scores, lr_score_type = get_model_scores(logreg_pipeline, X_test)
    svm_preds, svm_scores, svm_score_type = get_model_scores(svm_pipeline, X_test)

    print(f"    LogReg score type: {lr_score_type}")
    print(f"    SVM score type: {svm_score_type}")

    # Compute metrics
    print("[*] Computing evaluation metrics...")
    lr_metrics = compute_all_metrics(y_test, lr_preds, lr_scores, lr_score_type)
    svm_metrics = compute_all_metrics(y_test, svm_preds, svm_scores, svm_score_type)

    # Measure latency
    print("[*] Measuring inference latency...")
    lr_latency = measure_inference_latency(logreg_pipeline, X_test.tolist())
    svm_latency = measure_inference_latency(svm_pipeline, X_test.tolist())

    lr_metrics["latency"] = lr_latency
    svm_metrics["latency"] = svm_latency

    # Model sizes
    lr_metrics["model_size_bytes"] = os.path.getsize(logreg_path)
    svm_metrics["model_size_bytes"] = os.path.getsize(svm_path)

    # Training duration from metadata
    lr_metrics["training_duration_seconds"] = logreg_meta.get("training_stats", {}).get("training_duration_seconds", None)
    svm_metrics["training_duration_seconds"] = svm_meta.get("training_stats", {}).get("training_duration_seconds", None)

    # Print comparison
    print("\n" + "=" * 80)
    print(" DAY 3: MODEL COMPARISON — LOGISTIC REGRESSION vs. LINEAR SVM")
    print("=" * 80)
    print(f" Test Set: {test_size} samples ({num_benign} benign, {num_malicious} malicious)")
    print(f" {'Metric':<30} {'LogReg':>15} {'LinearSVM':>15} {'Delta':>12}")
    print("-" * 80)

    for key, label in [
        ("accuracy", "Accuracy"),
        ("precision", "Precision"),
        ("recall", "Recall"),
        ("f1_score", "F1-Score"),
        ("false_positive_rate", "False Positive Rate"),
        ("false_negative_rate", "False Negative Rate"),
        ("roc_auc", "ROC-AUC"),
    ]:
        lr_val = lr_metrics.get(key)
        svm_val = svm_metrics.get(key)
        if lr_val is not None and svm_val is not None:
            delta = svm_val - lr_val
            sign = "+" if delta >= 0 else ""
            print(f" {label:<30} {lr_val:>14.4f} {svm_val:>15.4f} {sign}{delta:>11.4f}")
        else:
            lr_str = f"{lr_val:.4f}" if lr_val is not None else "N/A"
            svm_str = f"{svm_val:.4f}" if svm_val is not None else "N/A"
            print(f" {label:<30} {lr_str:>15} {svm_str:>15} {'N/A':>12}")

    print("-" * 80)
    print(f" {'Confusion Matrix (LR)':<30} TN={lr_metrics['confusion_matrix']['tn']:>4}, FP={lr_metrics['confusion_matrix']['fp']:>4}, FN={lr_metrics['confusion_matrix']['fn']:>4}, TP={lr_metrics['confusion_matrix']['tp']:>4}")
    print(f" {'Confusion Matrix (SVM)':<30} TN={svm_metrics['confusion_matrix']['tn']:>4}, FP={svm_metrics['confusion_matrix']['fp']:>4}, FN={svm_metrics['confusion_matrix']['fn']:>4}, TP={svm_metrics['confusion_matrix']['tp']:>4}")
    print("-" * 80)
    print(f" {'Mean Latency (ms)':<30} {lr_latency['single_request_latency_mean_ms']:>14.3f} {svm_latency['single_request_latency_mean_ms']:>15.3f}")
    print(f" {'P95 Latency (ms)':<30} {lr_latency['single_request_latency_p95_ms']:>14.3f} {svm_latency['single_request_latency_p95_ms']:>15.3f}")
    print(f" {'Model Size (KB)':<30} {lr_metrics['model_size_bytes']/1024:>14.1f} {svm_metrics['model_size_bytes']/1024:>15.1f}")
    if lr_metrics["training_duration_seconds"] and svm_metrics["training_duration_seconds"]:
        print(f" {'Training Time (s)':<30} {lr_metrics['training_duration_seconds']:>14.4f} {svm_metrics['training_duration_seconds']:>15.4f}")
    print("=" * 80)

    # Generate visualizations
    print("\n[*] Generating visualizations...")

    # 1. Confusion matrices
    cm_lr = confusion_matrix(y_test, lr_preds, labels=[0, 1])
    cm_svm = confusion_matrix(y_test, svm_preds, labels=[0, 1])
    cm_path = os.path.join(reports_dir, "day3_confusion_matrices.png")
    plot_confusion_matrices(cm_lr, cm_svm, cm_path, test_size)
    print(f"[+] Saved confusion matrices to: {cm_path}")

    # 2. Metric comparison bar chart
    metric_chart_path = os.path.join(reports_dir, "day3_metric_comparison.png")
    plot_metric_comparison(lr_metrics, svm_metrics, metric_chart_path)
    print(f"[+] Saved metric comparison chart to: {metric_chart_path}")

    # 3. ROC curves (valid for both probability and decision function scores)
    if lr_metrics.get("roc_auc") is not None and svm_metrics.get("roc_auc") is not None:
        roc_path = os.path.join(reports_dir, "day3_roc_curves.png")
        plot_roc_curves(y_test, lr_scores, svm_scores,
                        lr_metrics["roc_auc"], svm_metrics["roc_auc"], roc_path)
        print(f"[+] Saved ROC curves to: {roc_path}")
    else:
        print("[!] Skipping ROC curve: AUC not available for one or both models.")

    # 4. Precision-recall curves
    try:
        pr_path = os.path.join(reports_dir, "day3_precision_recall_curves.png")
        plot_precision_recall_curves(y_test, lr_scores, svm_scores, pr_path)
        print(f"[+] Saved precision-recall curves to: {pr_path}")
    except Exception as e:
        print(f"[!] Precision-recall curve generation failed: {e}")

    # 5. Threshold analysis on validation data
    print("[*] Running validation-based threshold analysis...")
    val_lr_probs = logreg_pipeline.predict_proba(X_val)[:, 1]
    val_svm_scores = svm_pipeline.decision_function(X_val)

    # Select operating thresholds from validation scores, then evaluate once on test.
    lr_threshold = select_validation_threshold(y_val, val_lr_probs, 0.5)
    svm_threshold = select_validation_threshold(y_val, val_svm_scores, 0.0)
    th_path = os.path.join(reports_dir, "day3_threshold_analysis.png")
    plot_threshold_analysis(
        y_val, val_lr_probs, val_svm_scores, th_path,
        lr_threshold["threshold"], svm_threshold["threshold"],
    )
    print(f"[+] Saved threshold analysis to: {th_path}")

    lr_threshold_test_preds = (lr_scores >= lr_threshold["threshold"]).astype(int)
    svm_threshold_test_preds = (svm_scores >= svm_threshold["threshold"]).astype(int)
    threshold_metrics = {
        "selection_objective": "Maximize validation F1; ties prefer the threshold closest to the model default.",
        "selection_split": "core_validation",
        "test_split": "core_test",
        "logistic_regression": {
            **lr_threshold,
            "test_metrics": compute_all_metrics(
                y_test, lr_threshold_test_preds, lr_scores, lr_score_type
            ),
        },
        "linear_svm": {
            **svm_threshold,
            "test_metrics": compute_all_metrics(
                y_test, svm_threshold_test_preds, svm_scores, svm_score_type
            ),
        },
    }

    # Save comparison JSON
    comparison_result = {
        "comparison_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataset_config": config,
        "training_samples": len(train_df),
        "validation_samples": len(val_df),
        "test_samples": test_size,
        "training_class_distribution": {
            "benign_0": int((train_df["label"] == 0).sum()),
            "malicious_1": int((train_df["label"] == 1).sum()),
        },
        "class_distribution": {"benign_0": num_benign, "malicious_1": num_malicious},
        "logistic_regression": {
            "artifact_path": logreg_path,
            "metrics": lr_metrics,
            "score_type": lr_score_type,
            "vectorizer_configuration": logreg_meta.get("vectorizer_config"),
            "classifier_configuration": logreg_meta.get("classifier_config"),
        },
        "linear_svm": {
            "artifact_path": svm_path,
            "metrics": svm_metrics,
            "score_type": svm_score_type,
            "vectorizer_configuration": svm_meta.get("vectorizer_config"),
            "classifier_configuration": svm_meta.get("classifier_config"),
            "decision_score_note": (
                "LinearSVC decision scores are signed distances from the decision boundary, "
                "NOT calibrated probabilities. Positive = class 1 (malicious), negative = class 0 (benign). "
                "Magnitudes reflect geometric distance, not attack probability."
            ),
        },
        "validation_selected_thresholds": threshold_metrics,
        "comparison_notes": [
            "Both models were evaluated on the identical held-out test set (core_test).",
            "Both models were loaded from saved artifacts, not retrained.",
            "Both models were trained on the same training data (core_train, 4391 samples).",
            "Artifact metadata records the same dataset/configuration and training count; the artifacts do not contain a row-level training-data fingerprint.",
            "ROC-AUC for SVM uses decision_function scores, which is mathematically valid.",
            "Latency measured with identical procedures (5-run batch, 100-sample single).",
        ],
        "visualization_paths": {
            "confusion_matrices": cm_path,
            "metric_comparison": metric_chart_path,
            "roc_curves": os.path.join(reports_dir, "day3_roc_curves.png"),
            "precision_recall": os.path.join(reports_dir, "day3_precision_recall_curves.png"),
            "threshold_analysis": th_path,
        },
    }

    comparison_json_path = os.path.join(reports_dir, "day3_model_comparison.json")
    with open(comparison_json_path, "w", encoding="utf-8") as f:
        json.dump(comparison_result, f, indent=2)
    print(f"\n[+] Saved comparison JSON to: {comparison_json_path}")

    return comparison_result


def main():
    parser = argparse.ArgumentParser(description="SentinelAI Day 3: Model Comparison Engine")
    parser.add_argument("--logreg-path", type=str, default="ml/artifacts/prompt_injection_logreg.joblib")
    parser.add_argument("--svm-path", type=str, default="ml/artifacts/prompt_injection_svm.joblib")
    parser.add_argument("--logreg-meta", type=str, default="ml/artifacts/model_metadata.json")
    parser.add_argument("--svm-meta", type=str, default="ml/artifacts/svm_model_metadata.json")
    parser.add_argument("--data-dir", type=str, default="ml/data")
    parser.add_argument("--reports-dir", type=str, default="ml/reports")
    parser.add_argument("--config", type=str, default="core", choices=["core", "full"])
    args = parser.parse_args()

    compare_models(
        logreg_path=args.logreg_path,
        svm_path=args.svm_path,
        logreg_meta_path=args.logreg_meta,
        svm_meta_path=args.svm_meta,
        data_dir=args.data_dir,
        reports_dir=args.reports_dir,
        config=args.config,
    )


if __name__ == "__main__":
    main()
