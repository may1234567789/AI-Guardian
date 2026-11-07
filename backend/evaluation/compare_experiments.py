from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from backend.evaluation.metrics import (
    calculate_detection_metrics,
    calculate_enforcement_metrics,
    calculate_latency_metrics,
)


RESULTS_DIR = Path(__file__).with_name("results")
CONFIGURATIONS = ("E1", "E2", "E3", "E4")


def build_summary(results_payload: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    scenarios = results_payload["scenario_results"]
    expected_ids = {row["scenario_id"] for row in scenarios if row["configuration"] == "E1"}
    for configuration in CONFIGURATIONS:
        rows = [row for row in scenarios if row["configuration"] == configuration]
        if {row["scenario_id"] for row in rows} != expected_ids:
            raise ValueError(f"{configuration} does not use exactly the same scenario suite as E1.")

    per_experiment = {}
    for configuration in CONFIGURATIONS:
        rows = [row for row in scenarios if row["configuration"] == configuration]
        per_experiment[configuration] = {
            "name": results_payload["configurations"][configuration],
            "detection": calculate_detection_metrics(rows),
            "enforcement": calculate_enforcement_metrics(rows),
            "latency": calculate_latency_metrics(rows),
            "tool_errors": sum(row["error_status"] is not None for row in rows),
            "scenarios_with_output_scan": sum(row["output_scanned"] for row in rows),
            "sensitive_outputs_exposed": sum(
                row["sensitive_output_expected"] and row["sensitive_data_exposed"]
                for row in rows
            ),
        }

    all_scenarios = [row for row in scenarios if row["configuration"] == "E1"]
    category_counts: dict[str, int] = {}
    for row in all_scenarios:
        category_counts[row["category"]] = category_counts.get(row["category"], 0) + 1

    return {
        "available": True,
        "run_id": results_payload["run_id"],
        "scenario_count": len(expected_ids),
        "configuration_count": len(CONFIGURATIONS),
        "evaluated_scenario_runs": len(scenarios),
        "scenario_suite_counts_by_category": category_counts,
        "dataset_leakage_audit": metadata["dataset_leakage_audit"],
        "experiment_duration_seconds": metadata["experiment_duration_seconds"],
        "total_duration_seconds": metadata["total_duration_seconds"],
        "experiments": per_experiment,
    }


def _csv_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for configuration in CONFIGURATIONS:
        item = summary["experiments"][configuration]
        detection = item["detection"]
        enforcement = item["enforcement"]
        latency = item["latency"]
        rows.append({
            "configuration": configuration,
            "configuration_name": item["name"],
            "scenario_count": detection["scenario_count"],
            "attack_detection_rate": enforcement["attack_detection_rate"],
            "unauthorized_action_prevention_rate": enforcement["unauthorized_action_prevention_rate"],
            "legitimate_task_completion_rate": enforcement["legitimate_task_completion_rate"],
            "sensitive_data_leakage_prevention_rate": enforcement["sensitive_data_leakage_prevention_rate"],
            "accuracy": detection["accuracy"],
            "precision": detection["precision"],
            "recall": detection["recall"],
            "f1": detection["f1"],
            "false_positive_rate": detection["false_positive_rate"],
            "false_negative_rate": detection["false_negative_rate"],
            "roc_auc": detection["roc_auc"],
            "average_precision": detection["average_precision"],
            "average_latency_ms": latency["average_ms"],
            "median_latency_ms": latency["median_ms"],
            "p95_latency_ms": latency["p95_ms"],
            "max_latency_ms": latency["max_ms"],
            "model_inference_average_ms": latency["model_inference"]["average_ms"],
            "tool_execution_accuracy": enforcement["tool_execution_accuracy"],
            "tool_errors": item["tool_errors"],
        })
    return rows


def main() -> None:
    results_dir = RESULTS_DIR
    results_payload = json.loads((results_dir / "scenario_results.json").read_text(encoding="utf-8"))
    metadata = json.loads((results_dir / "run_metadata.json").read_text(encoding="utf-8"))
    summary = build_summary(results_payload, metadata)
    summary_json = json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    (results_dir / "experiment_summary.json").write_text(summary_json, encoding="utf-8")
    (results_dir / "runs" / summary["run_id"] / "experiment_summary.json").write_text(
        summary_json,
        encoding="utf-8",
    )
    fieldnames = list(_csv_rows(summary)[0])
    csv_path = results_dir / "experiment_summary.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(_csv_rows(summary))
    (results_dir / "runs" / summary["run_id"] / "experiment_summary.csv").write_bytes(
        csv_path.read_bytes()
    )

    columns = (
        ("attack_detection_rate", "Attack detection"),
        ("unauthorized_action_prevention_rate", "Unauthorized prevention"),
        ("legitimate_task_completion_rate", "Legitimate completion"),
        ("sensitive_data_leakage_prevention_rate", "Sensitive-data prevention"),
        ("false_positive_rate", "False-positive rate"),
        ("average_latency_ms", "Average latency (ms)"),
    )
    print("Metric                              " + "  ".join(CONFIGURATIONS))
    for key, label in columns:
        values = []
        for configuration in CONFIGURATIONS:
            item = summary["experiments"][configuration]
            if key == "false_positive_rate":
                value = item["detection"]["false_positive_rate"]
            elif key == "average_latency_ms":
                value = item["latency"]["average_ms"]
            else:
                value = item["enforcement"][key]
            values.append("n/a" if value is None else f"{value:.4f}" if value <= 1 else f"{value:.2f}")
        print(f"{label:34} " + "  ".join(values))
    print(f"Wrote {results_dir / 'experiment_summary.json'}")
    print(f"Wrote {results_dir / 'experiment_summary.csv'}")


if __name__ == "__main__":
    main()
