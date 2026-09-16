"""
CyberShield Data Platform - Events Route
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from services.api import crud
from services.api.database import get_db
from services.api.schemas import PaginatedEventsResponse, SecurityEventDetailSchema

router = APIRouter(tags=["Events"])


@router.get("/events", response_model=PaginatedEventsResponse, summary="List Cybersecurity Events")
def list_events(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    severity: Optional[str] = Query(None, description="Filter by severity (low, medium, high, critical)"),
    event_type: Optional[str] = Query(None, description="Filter by event_type"),
    source_ip: Optional[str] = Query(None, description="Filter by source IP address"),
    protocol: Optional[str] = Query(None, description="Filter by protocol (TCP, UDP, etc.)"),
    event_date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """Retrieve paginated cybersecurity events with optional filtering."""
    result = crud.get_events(
        db=db,
        page=page,
        page_size=page_size,
        severity=severity,
        event_type=event_type,
        source_ip=source_ip,
        protocol=protocol,
        event_date=event_date,
    )
    return result


@router.get("/events/{event_id}", response_model=SecurityEventDetailSchema, summary="Get Single Event Detail")
def get_event_detail(event_id: str, db: Session = Depends(get_db)):
    """Retrieve detail of a single security event including associated ML results."""
    event = crud.get_event_by_id(db=db, event_id=event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Security event with ID '{event_id}' not found.",
        )
    return event
