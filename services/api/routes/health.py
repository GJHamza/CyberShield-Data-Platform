"""
CyberShield Data Platform - Health Check Route
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from services.api.database import get_db
from services.api.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="API Health Check")
def health_check(db: Session = Depends(get_db)):
    """
    Check API health and active PostgreSQL database connectivity.
    Returns HTTP 200 if connected, HTTP 503 if database connection fails.
    """
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connectivity check failed: {str(e)}",
        )

    return HealthResponse(
        status="healthy",
        service="cybershield-api",
        database=db_status,
        timestamp=datetime.now(timezone.utc),
    )
