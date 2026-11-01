from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PromptScanResponse(BaseModel):
    request_id: str
    decision: str
    risk_score: float
    risk_level: str
    prompt_analysis: Dict[str, Any]
    data_leak_analysis: Dict[str, Any]
    reasons: List[str]
    event_id: Optional[int] = None


class ActionEvaluationResponse(BaseModel):
    request_id: str
    decision: str
    risk_score: float
    risk_level: str
    policy_decision: Dict[str, Any]
    detection_findings: Dict[str, Any]
    explanation: str
    event_id: Optional[int] = None


class ScanOutputResponse(BaseModel):
    request_id: str
    decision: str
    risk_score: float
    risk_level: str
    findings: List[Dict[str, Any]]
    redacted_text: str
    reasons: List[str]


class DocumentScanResponse(BaseModel):
    request_id: str
    decision: str
    risk_score: float
    risk_level: str
    suspicious_findings: List[Dict[str, Any]]
    sensitive_findings: List[Dict[str, Any]]
    reasons: List[str]


class HealthResponse(BaseModel):
    status: str
    database: str
    security_engine: str
    ml_model: str
    app_version: str


class EventRecordResponse(BaseModel):
    id: int
    request_id: str
    timestamp: str
    event_type: str
    pseudonymous_user_id: str
    user_role: Optional[str]
    action: Optional[str]
    risk_score: float
    risk_level: str
    decision: str
    reason: str
    policy_id: Optional[str]
    request_summary: Optional[str]


class StatsResponse(BaseModel):
    total_events: int
    allowed_requests: int
    blocked_requests: int
    review_requests: int
    high_risk_requests: int
    critical_risk_requests: int
    prompt_injection_detections: int
    sensitive_data_detections: int
    decision_distribution: Dict[str, int]
