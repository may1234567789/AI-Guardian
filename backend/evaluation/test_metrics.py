from __future__ import annotations

from backend.evaluation.metrics import calculate_detection_metrics, calculate_enforcement_metrics


def _row(
    expected_malicious: bool,
    predicted: bool,
    *,
    expected_auth: str = "ALLOW",
    expected_execution: bool = True,
    executed: bool = True,
    sensitive: bool = False,
    exposed: bool = False,
    score: float | None = None,
) -> dict:
    return {
        "expected_malicious": expected_malicious,
        "predicted_detection": predicted,
        "detection_score": score,
        "score_type": "decision_function" if score is not None else None,
        "expected_authorization_outcome": expected_auth,
        "expected_tool_execution": expected_execution,
        "tool_executed": executed,
        "execution_applicable": True,
        "error_status": None,
        "sensitive_output_expected": sensitive,
        "sensitive_data_exposed": exposed,
    }


def test_detection_metrics_use_malicious_as_positive_and_only_model_scores_for_auc() -> None:
    rows = [
        _row(True, True, score=1.0),
        _row(False, False, score=-1.0),
        _row(False, True, score=0.2),
        _row(True, False, score=-0.2),
    ]
    metrics = calculate_detection_metrics(rows)
    assert metrics["confusion_matrix"] == {"tn": 1, "fp": 1, "fn": 1, "tp": 1}
    assert metrics["false_positive_rate"] == 0.5
    assert metrics["false_negative_rate"] == 0.5
    assert metrics["roc_auc"] == 0.75
    assert metrics["score_type"] == "decision_function"


def test_policy_denial_and_sensitive_output_denominators_are_independent() -> None:
    rows = [
        _row(False, False, expected_auth="DENY", expected_execution=False, executed=False),
        _row(True, True, expected_auth="ALLOW", expected_execution=False, executed=False),
        _row(False, False, sensitive=True, exposed=False),
        _row(False, False, sensitive=True, exposed=True),
    ]
    metrics = calculate_enforcement_metrics(rows)
    assert metrics["unauthorized_action_prevention"] == {"prevented": 1, "denominator": 1}
    assert metrics["legitimate_task_completion"] == {"completed": 2, "denominator": 2}
    assert metrics["sensitive_data_leakage_prevention"] == {
        "prevented_or_redacted": 1,
        "denominator": 2,
    }
    assert metrics["attack_detection_counts"] == {"detected": 1, "denominator": 1}


def test_detection_metrics_do_not_invent_auc_for_binary_rule_scores() -> None:
    metrics = calculate_detection_metrics([
        _row(True, True, score=None),
        _row(False, False, score=None),
    ])
    assert metrics["roc_auc"] is None
    assert metrics["average_precision"] is None
