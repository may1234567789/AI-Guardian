from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = Path(__file__).with_name("results")
CHART_DIR = ROOT / "ml" / "reports" / "day8"
CONFIGURATIONS = ("E1", "E2", "E3", "E4")


def _bar_chart(
    summary: dict[str, Any],
    filename: str,
    title: str,
    metrics: list[tuple[str, str, str, float | None]],
    *,
    percent: bool = True,
) -> None:
    labels = [label for _, label, _, _ in metrics]
    fig, axis = plt.subplots(figsize=(9, 4.8))
    x = np.arange(len(CONFIGURATIONS))
    width = 0.8 / len(metrics)
    colors = ("#4a90e2", "#42b883", "#f0a44b", "#d56aa0", "#8b77d1")
    for metric_index, (key, label, section, scale) in enumerate(metrics):
        values = []
        for configuration in CONFIGURATIONS:
            value = summary["experiments"][configuration][section][key]
            values.append(np.nan if value is None else float(value) * (scale or 1))
        bars = axis.bar(
            x + (metric_index - (len(metrics) - 1) / 2) * width,
            values,
            width,
            label=label,
            color=colors[metric_index % len(colors)],
        )
        for bar, value in zip(bars, values):
            if np.isfinite(value):
                axis.annotate(
                    f"{value:.0f}%" if percent else f"{value:.2f}",
                    (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )
    axis.set_xticks(x, CONFIGURATIONS)
    axis.set_ylim(0, 108 if percent else None)
    axis.set_ylabel("Rate (%)" if percent else "Milliseconds")
    axis.set_title(title)
    axis.grid(axis="y", alpha=0.2)
    axis.legend(loc="best", frameon=False)
    fig.tight_layout()
    fig.savefig(CHART_DIR / filename, dpi=160, bbox_inches="tight")
    plt.close(fig)


def generate_charts() -> list[Path]:
    summary = json.loads((RESULTS_DIR / "experiment_summary.json").read_text(encoding="utf-8"))
    results = json.loads((RESULTS_DIR / "scenario_results.json").read_text(encoding="utf-8"))
    CHART_DIR.mkdir(parents=True, exist_ok=True)

    _bar_chart(
        summary,
        "detection_metrics.png",
        "Prompt-injection detection comparison",
        [
            ("accuracy", "Accuracy", "detection", 100),
            ("precision", "Precision", "detection", 100),
            ("recall", "Recall / attack detection", "detection", 100),
            ("f1", "F1", "detection", 100),
        ],
    )
    _bar_chart(
        summary,
        "unauthorized_action_prevention.png",
        "Unauthorized-action prevention",
        [("unauthorized_action_prevention_rate", "Prevention rate", "enforcement", 100)],
    )
    _bar_chart(
        summary,
        "legitimate_task_completion.png",
        "Legitimate task completion",
        [("legitimate_task_completion_rate", "Completion rate", "enforcement", 100)],
    )
    _bar_chart(
        summary,
        "sensitive_data_prevention.png",
        "Sensitive-output prevention",
        [("sensitive_data_leakage_prevention_rate", "Prevention or redaction", "enforcement", 100)],
    )
    _bar_chart(
        summary,
        "false_positive_false_negative.png",
        "Detection error rates",
        [
            ("false_positive_rate", "False-positive rate", "detection", 100),
            ("false_negative_rate", "False-negative rate", "detection", 100),
        ],
    )
    _bar_chart(
        summary,
        "latency_comparison.png",
        "Per-scenario latency (end-to-end)",
        [
            ("average_ms", "Mean", "latency", 1),
            ("median_ms", "Median", "latency", 1),
            ("p95_ms", "P95", "latency", 1),
        ],
        percent=False,
    )

    fig, axes = plt.subplots(2, 2, figsize=(9, 7.5))
    axes_flat = axes.ravel()
    for axis, configuration in zip(axes_flat, CONFIGURATIONS):
        rows = [row for row in results["scenario_results"] if row["configuration"] == configuration]
        tn = sum(not row["expected_malicious"] and not row.get("predicted_detection") for row in rows)
        fp = sum(not row["expected_malicious"] and row.get("predicted_detection") is True for row in rows)
        fn = sum(row["expected_malicious"] and row.get("predicted_detection") is False for row in rows)
        tp = sum(row["expected_malicious"] and row.get("predicted_detection") is True for row in rows)
        matrix = np.asarray([[tn, fp], [fn, tp]])
        image = axis.imshow(matrix, cmap="Blues", vmin=0)
        axis.set_title(configuration)
        axis.set_xticks([0, 1], ["Benign", "Malicious"])
        axis.set_yticks([0, 1], ["Benign", "Malicious"])
        axis.set_xlabel("Predicted")
        axis.set_ylabel("Expected")
        for (row_index, column_index), value in np.ndenumerate(matrix):
            axis.text(column_index, row_index, str(value), ha="center", va="center", color="black", fontsize=12)
    fig.colorbar(image, ax=axes_flat.tolist(), shrink=0.8, label="Scenario count")
    fig.suptitle("Detection confusion matrices (malicious is positive class)")
    fig.subplots_adjust(left=0.09, right=0.88, bottom=0.1, top=0.88, wspace=0.32, hspace=0.35)
    path = CHART_DIR / "confusion_matrices.png"
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)

    robustness = results.get("robustness_results", [])
    if robustness:
        labels = [row["case_id"].replace("_", " ") for row in robustness]
        detected = [row["predicted_detection"] is True for row in robustness]
        fig, axis = plt.subplots(figsize=(10, 4.8))
        colors = ["#d56aa0" if row["expected_malicious_assumption"] else "#42b883" for row in robustness]
        axis.barh(labels, [int(value) for value in detected], color=colors)
        axis.set_xlim(0, 1.15)
        axis.set_xticks([0, 1], ["Not detected", "Detected"])
        axis.set_title("Robustness suite: observed ML predictions")
        axis.set_xlabel("Prediction (color indicates assumed label)")
        axis.grid(axis="x", alpha=0.2)
        fig.tight_layout()
        fig.savefig(CHART_DIR / "robustness_predictions.png", dpi=160, bbox_inches="tight")
        plt.close(fig)

    generated = sorted(CHART_DIR.glob("*.png"))
    print(f"Generated {len(generated)} charts in {CHART_DIR}")
    return generated


if __name__ == "__main__":
    generate_charts()
