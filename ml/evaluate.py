"""
AI Guardian (SentinelAI) - Model Evaluation & Reporting Engine
===============================================================
Evaluates the trained prompt-injection classifier on the strictly held-out
test partition (`core_test`).

Key Features:
- Evaluates at default threshold (0.50) and validation-calibrated operating thresholds.
- Calculates Accuracy, Precision, Recall, F1, ROC-AUC, FPR, FNR, and Confusion Matrix.
- Measures inference latency (batch and single-sample average) reproducibly.
- Produces publication-grade visualizations in `ml/reports/`:
  1. Confusion Matrix Heatmap (`confusion_matrix.png`)
  2. ROC Curve with AUC marker (`roc_curve.png`)
  3. Metrics Summary comparison chart (`metrics_summary.png`)
- Dumps comprehensive JSON evaluation metrics to `ml/reports/test_evaluation_summary.json`.
"""

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Tuple

# Ensure SentinelAI project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    auc,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from ml.preprocess_data import LABEL_MAPPING, get_preprocessed_splits


def measure_inference_latency(
    model: Any,
    texts: List[str],
    num_runs: int = 5,
    sample_size: int = 100,
) -> Dict[str, float]:
    """
    Measures CPU inference latency reproducibly across multiple runs.
    """
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

    # Single-sample inference latency (simulates live API request)
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


def compute_metrics_at_threshold(
    y_true: np.ndarray,
    y_probs: np.ndarray,
    threshold: float,
) -> Dict[str, Any]:
    """
    Computes standard classification metrics at a given decision threshold.
    """
    y_pred = (y_probs >= threshold).astype(int)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    accuracy = float(accuracy_score(y_true, y_pred))
    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0

    return {
        "threshold": round(threshold, 4),
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "false_positive_rate": round(fpr, 4),
        "false_negative_rate": round(fnr, 4),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
    }


def plot_confusion_matrix(
    cm: np.ndarray,
    output_path: str,
    title: str = "Prompt Injection Confusion Matrix",
):
    """
    Generates a publication-quality confusion matrix heatmap.
    """
    plt.figure(figsize=(7, 6))
    class_labels = ["Benign (0)", "Malicious (1)"]
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=class_labels,
        yticklabels=class_labels,
        cbar=True,
        annot_kws={"size": 14, "weight": "bold"},
    )
    plt.title(title, fontsize=14, weight="bold", pad=12)
    plt.xlabel("Predicted Security Label", fontsize=12, labelpad=8)
    plt.ylabel("Ground-Truth Label", fontsize=12, labelpad=8)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def plot_roc_curve(
    y_true: np.ndarray,
    y_probs: np.ndarray,
    roc_auc: float,
    output_path: str,
):
    """
    Generates a high-resolution ROC curve with AUC metric.
    """
    fpr_arr, tpr_arr, _ = roc_curve(y_true, y_probs)
    plt.figure(figsize=(7, 6))
    plt.plot(fpr_arr, tpr_arr, color="#1f77b4", lw=2.5, label=f"ROC Curve (AUC = {roc_auc:.4f})")
    plt.plot([0, 1], [0, 1], color="#7f7f7f", lw=1.5, linestyle="--", label="Random Chance (AUC = 0.50)")
    plt.xlim([-0.02, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("False Positive Rate (FPR)", fontsize=12, labelpad=8)
    plt.ylabel("True Positive Rate (Recall)", fontsize=12, labelpad=8)
    plt.title("Receiver Operating Characteristic (ROC) - Test Set", fontsize=14, weight="bold", pad=12)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="lower right", fontsize=11)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def plot_metrics_summary(
    default_metrics: Dict[str, Any],
    calibrated_metrics: Dict[str, Any],
    output_path: str,
):
    """
    Generates a comparative bar chart between default and calibrated operating points.
    """
    metric_names = ["Accuracy", "Precision", "Recall", "F1-Score"]
    def_vals = [
        default_metrics["accuracy"],
        default_metrics["precision"],
        default_metrics["recall"],
        default_metrics["f1_score"],
    ]
    cal_vals = [
        calibrated_metrics["accuracy"],
        calibrated_metrics["precision"],
        calibrated_metrics["recall"],
        calibrated_metrics["f1_score"],
    ]

    x = np.arange(len(metric_names))
    width = 0.35

    plt.figure(figsize=(8, 5.5))
    plt.bar(x - width / 2, def_vals, width, label=f"Default Threshold ({default_metrics['threshold']})", color="#4a90e2")
    plt.bar(x + width / 2, cal_vals, width, label=f"Calibrated Threshold ({calibrated_metrics['threshold']})", color="#50e3c2")

    plt.ylabel("Metric Score", fontsize=12)
    plt.title("Test Set Performance: Default vs. Validation-Calibrated Threshold", fontsize=13, weight="bold", pad=12)
    plt.xticks(x, metric_names, fontsize=11)
    plt.ylim([0.8, 1.02])
    plt.grid(axis="y", linestyle=":", alpha=0.6)
    plt.legend(loc="lower right", fontsize=10)

    for i in range(len(metric_names)):
        plt.text(x[i] - width / 2, def_vals[i] + 0.005, f"{def_vals[i]:.3f}", ha="center", fontsize=9, weight="bold")
        plt.text(x[i] + width / 2, cal_vals[i] + 0.005, f"{cal_vals[i]:.3f}", ha="center", fontsize=9, weight="bold")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def extract_misclassifications(
    df_test: pd.DataFrame,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_probs: np.ndarray,
    max_examples: int = 5,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extracts representative False Positives and False Negatives for error analysis.
    """
    fps = []
    fns = []

    for idx, (true_val, pred_val, prob) in enumerate(zip(y_true, y_pred, y_probs)):
        row = df_test.iloc[idx]
        text_preview = row["text"][:120] + ("..." if len(row["text"]) > 120 else "")
        category = row.get("category", "unknown")
        severity = row.get("severity", "unknown")

        entry = {
            "index": int(idx),
            "text_preview": text_preview,
            "category": str(category),
            "severity": str(severity),
            "predicted_prob_malicious": round(float(prob), 4),
            "text_length": len(row["text"]),
        }

        if true_val == 0 and pred_val == 1:
            fps.append(entry)
        elif true_val == 1 and pred_val == 0:
            fns.append(entry)

    return {
        "false_positives": fps[:max_examples],
        "false_negatives": fns[:max_examples],
        "total_false_positives": len(fps),
        "total_false_negatives": len(fns),
    }


def evaluate(
    model_path: str = "ml/artifacts/prompt_injection_logreg.joblib",
    metadata_path: str = "ml/artifacts/model_metadata.json",
    data_dir: str = "ml/data",
    reports_dir: str = "ml/reports",
    config: str = "core",
) -> Dict[str, Any]:
    """
    Main evaluation workflow on held-out test data.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}. Train model first via ml/train.py.")

    os.makedirs(reports_dir, exist_ok=True)

    print(f"[*] Loading trained pipeline from: {model_path}")
    pipeline = joblib.load(model_path)

    # Load validation-calibrated threshold from metadata if available
    calibrated_th = 0.70
    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
            calibrated_th = meta.get("threshold_calibration", {}).get("best_f1_threshold", 0.70)
    print(f"[*] Validation-calibrated decision threshold: {calibrated_th}")

    print(f"[*] Loading held-out test data ({config} configuration)...")
    _, _, test_df = get_preprocessed_splits(config=config, data_dir=data_dir, drop_duplicates=True)
    X_test, y_test = test_df["text"], test_df["label"].to_numpy()
    test_size = len(X_test)
    num_benign = int((y_test == 0).sum())
    num_malicious = int((y_test == 1).sum())

    print(f"[*] Held-out test set: {test_size:,} examples | Benign: {num_benign:,} | Malicious: {num_malicious:,}")

    # Latency measurement
    print("[*] Measuring inference latency reproducibly...")
    latency_stats = measure_inference_latency(pipeline, X_test.tolist(), num_runs=5, sample_size=100)
    print(f"[+] Full batch latency (942 samples): {latency_stats['full_batch_latency_seconds']:.4f}s ({latency_stats['batch_latency_per_sample_ms']:.3f} ms/sample)")
    print(f"[+] Single-sample inference latency: Mean = {latency_stats['single_request_latency_mean_ms']:.3f} ms | P95 = {latency_stats['single_request_latency_p95_ms']:.3f} ms")

    # Predict probabilities
    y_probs = pipeline.predict_proba(X_test)[:, 1]
    roc_auc = float(roc_auc_score(y_test, y_probs))

    # Evaluate at default threshold (0.50)
    default_metrics = compute_metrics_at_threshold(y_test, y_probs, threshold=0.50)
    calibrated_metrics = compute_metrics_at_threshold(y_test, y_probs, threshold=calibrated_th)

    y_pred_default = (y_probs >= 0.50).astype(int)
    cm_default = confusion_matrix(y_test, y_pred_default, labels=[0, 1])

    # Print Evaluation Reports
    print("\n" + "=" * 70)
    print(" HELD-OUT TEST EVALUATION - DEFAULT THRESHOLD (0.50)")
    print("=" * 70)
    print(f" Accuracy:                 {default_metrics['accuracy']:.4f}")
    print(f" Precision:                {default_metrics['precision']:.4f}")
    print(f" Recall:                   {default_metrics['recall']:.4f}")
    print(f" F1-Score:                 {default_metrics['f1_score']:.4f}")
    print(f" ROC-AUC:                  {roc_auc:.4f}")
    print(f" False Positive Rate (FPR): {default_metrics['false_positive_rate']:.4f}")
    print(f" False Negative Rate (FNR): {default_metrics['false_negative_rate']:.4f}")
    print(f" Confusion Matrix:         TN={default_metrics['confusion_matrix']['tn']}, FP={default_metrics['confusion_matrix']['fp']}, FN={default_metrics['confusion_matrix']['fn']}, TP={default_metrics['confusion_matrix']['tp']}")
    print("\nDetailed Classification Report (Default 0.50):")
    print(classification_report(y_test, y_pred_default, target_names=["Benign (0)", "Malicious (1)"], digits=4))

    print("=" * 70)
    print(f" HELD-OUT TEST EVALUATION - VALIDATION-CALIBRATED THRESHOLD ({calibrated_th})")
    print("=" * 70)
    print(f" Accuracy:                 {calibrated_metrics['accuracy']:.4f}")
    print(f" Precision:                {calibrated_metrics['precision']:.4f}")
    print(f" Recall:                   {calibrated_metrics['recall']:.4f}")
    print(f" F1-Score:                 {calibrated_metrics['f1_score']:.4f}")
    print(f" False Positive Rate (FPR): {calibrated_metrics['false_positive_rate']:.4f}")
    print(f" False Negative Rate (FNR): {calibrated_metrics['false_negative_rate']:.4f}")
    print(f" Confusion Matrix:         TN={calibrated_metrics['confusion_matrix']['tn']}, FP={calibrated_metrics['confusion_matrix']['fp']}, FN={calibrated_metrics['confusion_matrix']['fn']}, TP={calibrated_metrics['confusion_matrix']['tp']}")

    # Misclassification sampling
    misclass = extract_misclassifications(test_df, y_test, y_pred_default, y_probs, max_examples=5)

    print("\n--- Sample False Positives (Benign misclassified as Malicious) ---")
    for ex in misclass["false_positives"]:
        print(f" [{ex['category']}] Prob: {ex['predicted_prob_malicious']:.3f} | Len: {ex['text_length']} chars | Text: \"{ex['text_preview']}\"")

    print("\n--- Sample False Negatives (Malicious misclassified as Benign) ---")
    for ex in misclass["false_negatives"]:
        print(f" [{ex['category']} - Sev: {ex['severity']}] Prob: {ex['predicted_prob_malicious']:.3f} | Len: {ex['text_length']} chars | Text: \"{ex['text_preview']}\"")

    # Generate and save Visualizations
    cm_path = os.path.join(reports_dir, "confusion_matrix.png")
    plot_confusion_matrix(cm_default, cm_path, title=f"Test Confusion Matrix (Threshold = 0.50, N={test_size})")
    print(f"\n[+] Saved confusion matrix heatmap to: {cm_path}")

    roc_path = os.path.join(reports_dir, "roc_curve.png")
    plot_roc_curve(y_test, y_probs, roc_auc, roc_path)
    print(f"[+] Saved ROC curve to: {roc_path}")

    metrics_chart_path = os.path.join(reports_dir, "metrics_summary.png")
    plot_metrics_summary(default_metrics, calibrated_metrics, metrics_chart_path)
    print(f"[+] Saved metrics summary comparison chart to: {metrics_chart_path}")

    # Save complete JSON summary
    summary = {
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataset_config": config,
        "test_samples": test_size,
        "class_distribution": {
            "benign_0": num_benign,
            "malicious_1": num_malicious,
        },
        "roc_auc": round(roc_auc, 4),
        "latency_stats": latency_stats,
        "default_threshold_metrics": default_metrics,
        "calibrated_threshold_metrics": calibrated_metrics,
        "misclassifications_summary": {
            "total_false_positives": misclass["total_false_positives"],
            "total_false_negatives": misclass["total_false_negatives"],
            "sample_false_positives": misclass["false_positives"],
            "sample_false_negatives": misclass["false_negatives"],
        },
    }

    summary_json_path = os.path.join(reports_dir, "test_evaluation_summary.json")
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"[+] Saved complete evaluation JSON report to: {summary_json_path}")

    return summary


def main():
    parser = argparse.ArgumentParser(description="Evaluate SentinelAI Baseline Model on Held-Out Test Set")
    parser.add_argument("--model-path", type=str, default="ml/artifacts/prompt_injection_logreg.joblib")
    parser.add_argument("--metadata-path", type=str, default="ml/artifacts/model_metadata.json")
    parser.add_argument("--data-dir", type=str, default="ml/data")
    parser.add_argument("--reports-dir", type=str, default="ml/reports")
    parser.add_argument("--config", type=str, default="core", choices=["core", "full"])
    args = parser.parse_args()

    evaluate(
        model_path=args.model_path,
        metadata_path=args.metadata_path,
        data_dir=args.data_dir,
        reports_dir=args.reports_dir,
        config=args.config,
    )


if __name__ == "__main__":
    main()
