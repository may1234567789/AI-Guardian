from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.schemas.request_models import DocumentScanRequest, OutputScanRequest, PromptScanRequest
from backend.schemas.response_models import DocumentScanResponse, PromptScanResponse, ScanOutputResponse
from backend.services.event_service import EventService
from backend.services.security_service import SecurityService

router = APIRouter(prefix="", tags=["security"])


@router.post("/scan", response_model=PromptScanResponse, status_code=status.HTTP_200_OK)
def scan_prompt_endpoint(payload: PromptScanRequest, db: Session = Depends(get_db)):
    service = SecurityService()
    request_id = service.generate_request_id()
    result = service.scan_prompt(payload.prompt)
    result["request_id"] = request_id

    event_service = EventService(db)
    event = event_service.create_event(
        request_id=request_id,
        event_type="prompt_scan",
        pseudonymous_user_id=payload.user_context or "mock-user",
        user_role=None,
        action="scan_prompt",
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        decision=result["decision"],
        reason="; ".join(result["reasons"]),
        policy_id="prompt_policy",
        request_summary=f"scan prompt from source={payload.source or 'unknown'}",
    )
    result["event_id"] = event.id
    return result


@router.post("/scan-output", response_model=ScanOutputResponse, status_code=status.HTTP_200_OK)
def scan_output_endpoint(payload: OutputScanRequest):
    service = SecurityService()
    result = service.scan_output_text(payload.output_text)
    return result


@router.post("/scan-document", response_model=DocumentScanResponse, status_code=status.HTTP_200_OK)
def scan_document_endpoint(payload: DocumentScanRequest):
    service = SecurityService()
    result = service.scan_document(payload.document_text)
    return result
