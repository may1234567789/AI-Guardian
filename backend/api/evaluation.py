from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter


router = APIRouter(prefix="/evaluation", tags=["evaluation"])
SUMMARY_PATH = Path(__file__).resolve().parents[1] / "evaluation" / "results" / "experiment_summary.json"


@router.get("/summary")
def get_evaluation_summary() -> dict[str, Any]:
    if not SUMMARY_PATH.is_file():
        return {
            "available": False,
            "message": "No Day 8 evaluation results are available. Run the documented evaluation commands first.",
        }
    with SUMMARY_PATH.open("r", encoding="utf-8") as handle:
        summary = json.load(handle)
    if not isinstance(summary, dict) or summary.get("available") is not True:
        raise ValueError("The saved Day 8 evaluation summary has an invalid format.")
    return summary
