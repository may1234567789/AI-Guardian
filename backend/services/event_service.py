from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.database.database import SessionLocal
from backend.database.models import SecurityEvent


class EventService:
    def __init__(self, db: Optional[Session] = None):
        self.db = db or SessionLocal()

    def create_event(
        self,
        *,
        request_id: str,
        event_type: str,
        pseudonymous_user_id: str,
        user_role: str | None,
        action: str | None,
        risk_score: float,
        risk_level: str,
        decision: str,
        reason: str,
        policy_id: str | None = None,
        request_summary: str | None = None,
    ) -> SecurityEvent:
        event = SecurityEvent(
            request_id=request_id,
            timestamp=datetime.utcnow(),
            event_type=event_type,
            pseudonymous_user_id=pseudonymous_user_id,
            user_role=user_role,
            action=action,
            risk_score=float(risk_score),
            risk_level=risk_level,
            decision=decision,
            reason=reason,
            policy_id=policy_id,
            request_summary=request_summary,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_event_by_request_id(self, request_id: str) -> SecurityEvent | None:
        return self.db.query(SecurityEvent).filter(SecurityEvent.request_id == request_id).first()

    def list_events(self, *, decision: str | None = None, event_type: str | None = None, limit: int = 50, offset: int = 0) -> List[SecurityEvent]:
        query = self.db.query(SecurityEvent)
        if decision:
            query = query.filter(SecurityEvent.decision == decision)
        if event_type:
            query = query.filter(SecurityEvent.event_type == event_type)
        return query.order_by(SecurityEvent.id.desc()).offset(offset).limit(limit).all()

    def get_stats(self) -> Dict[str, Any]:
        events = self.db.query(SecurityEvent).all()
        total = len(events)

        allowed = sum(1 for e in events if e.decision == "ALLOW")
        blocked = sum(1 for e in events if e.decision == "BLOCK")
        review = sum(1 for e in events if e.decision == "REVIEW")
        high_risk = sum(1 for e in events if e.risk_level == "HIGH")
        critical_risk = sum(1 for e in events if e.risk_level == "CRITICAL")

        prompt_injection = sum(1 for e in events if "Prompt injection" in (e.reason or ""))
        sensitive_data = sum(1 for e in events if "Sensitive" in (e.reason or "") or "sensitive" in (e.reason or ""))

        distribution: Dict[str, int] = {}
        for event in events:
            distribution[event.decision] = distribution.get(event.decision, 0) + 1

        return {
            "total_events": total,
            "allowed_requests": allowed,
            "blocked_requests": blocked,
            "review_requests": review,
            "high_risk_requests": high_risk,
            "critical_risk_requests": critical_risk,
            "prompt_injection_detections": prompt_injection,
            "sensitive_data_detections": sensitive_data,
            "decision_distribution": distribution,
        }
