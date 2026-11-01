from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.services.event_service import EventService

router = APIRouter(prefix="", tags=["stats"])


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    service = EventService(db)
    stats = service.get_stats()
    return {
        "total_events": stats.get("total_events", 0),
        "allowed_requests": stats.get("allowed_requests", 0),
        "blocked_requests": stats.get("blocked_requests", 0),
        "review_requests": stats.get("review_requests", 0),
        "high_risk_requests": stats.get("high_risk_requests", 0),
        "critical_risk_requests": stats.get("critical_risk_requests", 0),
        "prompt_injection_detections": stats.get("prompt_injection_detections", 0),
        "sensitive_data_detections": stats.get("sensitive_data_detections", 0),
        "decision_distribution": stats.get("decision_distribution", {}),
    }
