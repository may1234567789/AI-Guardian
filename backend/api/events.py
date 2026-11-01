from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import SecurityEvent
from backend.services.event_service import EventService

router = APIRouter(prefix="", tags=["events"])


@router.get("/events")
def list_events(
    decision: str | None = None,
    event_type: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    service = EventService(db)
    events = service.list_events(decision=decision, event_type=event_type, limit=limit, offset=offset)
    return {
        "count": len(events),
        "limit": limit,
        "offset": offset,
        "items": [event.to_dict() for event in events],
    }


@router.get("/events/{request_id}")
def get_event(request_id: str, db: Session = Depends(get_db)):
    service = EventService(db)
    event = service.get_event_by_request_id(request_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
    return event.to_dict()
