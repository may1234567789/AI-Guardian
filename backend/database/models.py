from __future__ import annotations

from sqlalchemy import Boolean, Column, Float, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(64), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    event_type = Column(String(64), nullable=False)
    pseudonymous_user_id = Column(String(64), nullable=False, default="mock-user")
    user_role = Column(String(32), nullable=True)
    action = Column(String(128), nullable=True)
    risk_score = Column(Float, nullable=False, default=0.0)
    risk_level = Column(String(16), nullable=False, default="LOW")
    decision = Column(String(16), nullable=False, default="REVIEW")
    reason = Column(Text, nullable=False, default="")
    policy_id = Column(String(64), nullable=True)
    request_summary = Column(Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "event_type": self.event_type,
            "pseudonymous_user_id": self.pseudonymous_user_id,
            "user_role": self.user_role,
            "action": self.action,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "decision": self.decision,
            "reason": self.reason,
            "policy_id": self.policy_id,
            "request_summary": self.request_summary,
        }
