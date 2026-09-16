"""
CyberShield Data Platform - Alerts Route
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from services.api import crud
from services.api.database import get_db
from services.api.schemas import PaginatedAlertsResponse

router = APIRouter(tags=["Alerts & Anomalies"])


@router.get("/alerts", response_model=PaginatedAlertsResponse, summary="List Security Alerts & Anomalies")
def list_alerts(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level (LOW, MEDIUM, HIGH, CRITICAL)"),
    is_anomaly: Optional[bool] = Query(None, description="Filter by anomaly status (true/false)"),
    min_risk_score: Optional[float] = Query(None, ge=0.0, le=100.0, description="Minimum risk score threshold"),
    db: Session = Depends(get_db),
):
    """Retrieve paginated security alerts filtered by risk level, anomaly status, or risk score threshold."""
    result = crud.get_alerts(
        db=db,
        page=page,
        page_size=page_size,
        risk_level=risk_level,
        is_anomaly=is_anomaly,
        min_risk_score=min_risk_score,
    )
    return result
