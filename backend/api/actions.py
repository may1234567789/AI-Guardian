from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.schemas.request_models import ActionCheckRequest
from backend.schemas.response_models import ActionEvaluationResponse
from backend.services.event_service import EventService
from backend.services.security_service import SecurityService

router = APIRouter(prefix="", tags=["actions"])


@router.post("/check-action", response_model=ActionEvaluationResponse, status_code=status.HTTP_200_OK)
def evaluate_action_endpoint(payload: ActionCheckRequest, db: Session = Depends(get_db)):
    if not payload.user_context or not payload.user_context.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing mock user identity reference.")
    if not payload.user_role or not payload.user_role.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User role is required for authorization evaluation.")

    service = SecurityService()
    result = service.evaluate_action(
        prompt=payload.prompt,
        proposed_action=payload.proposed_action,
        role=payload.user_role,
        resource_context=payload.resource_context,
        user_context=payload.user_context,
        confirm_delete=payload.confirm_delete,
    )

    request_id = result["request_id"]
    event_service = EventService(db)
    event = event_service.create_event(
        request_id=request_id,
        event_type="action_check",
        pseudonymous_user_id=payload.user_context or "mock-user",
        user_role=payload.user_role,
        action=payload.proposed_action,
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        decision=result["decision"],
        reason=result["explanation"],
        policy_id="policy_engine",
        request_summary=f"action={payload.proposed_action}",
    )
    result["event_id"] = event.id
    return result
