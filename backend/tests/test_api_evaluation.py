from __future__ import annotations

import json

from backend.api import evaluation
from backend.main import app


def test_evaluation_summary_has_an_empty_state_when_no_run_exists(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(evaluation, "SUMMARY_PATH", tmp_path / "missing.json")
    response = evaluation.get_evaluation_summary()
    assert response["available"] is False
    assert "Run the documented" in response["message"]


def test_evaluation_summary_returns_saved_measured_data(tmp_path, monkeypatch) -> None:
    path = tmp_path / "experiment_summary.json"
    expected = {"available": True, "scenario_count": 130, "experiments": {"E4": {}}}
    path.write_text(json.dumps(expected), encoding="utf-8")
    monkeypatch.setattr(evaluation, "SUMMARY_PATH", path)
    assert evaluation.get_evaluation_summary() == expected


def test_evaluation_summary_api_serves_the_saved_run() -> None:
    from fastapi.testclient import TestClient

    response = TestClient(app).get("/evaluation/summary")
    assert response.status_code == 200
    expected_available = evaluation.SUMMARY_PATH.is_file()
    assert response.json()["available"] is expected_available
    if expected_available:
        assert response.json()["scenario_count"] >= 100
