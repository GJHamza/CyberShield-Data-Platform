"""
CyberShield Data Platform - Statistics Routes
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from services.api import crud
from services.api.database import get_db
from services.api.schemas import DistributionResponse, OverviewStatistics

router = APIRouter(prefix="/statistics", tags=["Statistics"])


@router.get("/overview", response_model=OverviewStatistics, summary="Get Overview Security Statistics")
def get_overview(db: Session = Depends(get_db)):
    """Calculate aggregated security events & ML metrics from PostgreSQL."""
    return crud.get_overview_statistics(db)


@router.get("/severity", response_model=DistributionResponse, summary="Get Severity Distribution")
def get_severity_dist(db: Session = Depends(get_db)):
    """Calculate distribution of events grouped by severity."""
    return crud.get_severity_distribution(db)


@router.get("/event-types", response_model=DistributionResponse, summary="Get Event Types Distribution")
def get_event_types_dist(db: Session = Depends(get_db)):
    """Calculate distribution of events grouped by event_type."""
    return crud.get_event_types_distribution(db)


@router.get("/risk-levels", response_model=DistributionResponse, summary="Get Risk Levels Distribution")
def get_risk_levels_dist(db: Session = Depends(get_db)):
    """Calculate distribution of events grouped by ML risk_level."""
    return crud.get_risk_levels_distribution(db)
