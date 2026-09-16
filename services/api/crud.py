"""
CyberShield Data Platform - CRUD Operations
SQLAlchemy database queries for events, ML alerts, and statistics.
"""

from math import ceil
from sqlalchemy.orm import Session
from sqlalchemy import func

from services.api.models import SecurityEvent, SecurityEventML


def get_events(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    severity: str = None,
    event_type: str = None,
    source_ip: str = None,
    protocol: str = None,
    event_date: str = None,
):
    """Query security_events with optional filters and pagination."""
    query = db.query(SecurityEvent)

    if severity:
        query = query.filter(SecurityEvent.severity.ilike(severity.strip()))
    if event_type:
        query = query.filter(SecurityEvent.event_type.ilike(event_type.strip()))
    if source_ip:
        query = query.filter(SecurityEvent.source_ip == source_ip.strip())
    if protocol:
        query = query.filter(SecurityEvent.protocol.ilike(protocol.strip()))
    if event_date:
        query = query.filter(func.date(SecurityEvent.timestamp) == event_date.strip())

    total = query.count()
    total_pages = ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size

    items = query.order_by(SecurityEvent.timestamp.desc()).offset(offset).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "items": items,
    }


def get_event_by_id(db: Session, event_id: str):
    """Query a single security event by event_id, joining ML results."""
    return db.query(SecurityEvent).filter(SecurityEvent.event_id == event_id).first()


def get_alerts(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    risk_level: str = None,
    is_anomaly: bool = None,
    min_risk_score: float = None,
):
    """Query ML alerts joined with security_events."""
    query = (
        db.query(
            SecurityEvent.event_id,
            SecurityEvent.event_type,
            SecurityEvent.severity,
            SecurityEvent.source_ip,
            SecurityEvent.destination_ip,
            SecurityEvent.timestamp,
            SecurityEventML.risk_score,
            SecurityEventML.risk_level,
            SecurityEventML.anomaly_score,
            SecurityEventML.is_anomaly,
            SecurityEventML.model_version,
        )
        .join(SecurityEventML, SecurityEvent.event_id == SecurityEventML.event_id)
    )

    if risk_level:
        query = query.filter(SecurityEventML.risk_level.ilike(risk_level.strip()))
    if is_anomaly is not None:
        query = query.filter(SecurityEventML.is_anomaly == is_anomaly)
    if min_risk_score is not None:
        query = query.filter(SecurityEventML.risk_score >= min_risk_score)

    total = query.count()
    total_pages = ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size

    items = query.order_by(SecurityEventML.risk_score.desc(), SecurityEvent.timestamp.desc()).offset(offset).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "items": items,
    }


def get_overview_statistics(db: Session):
    """Calculate aggregated security & ML statistics directly from PostgreSQL."""
    total_events = db.query(func.count(SecurityEvent.id)).scalar() or 0
    total_anomalies = db.query(func.count(SecurityEventML.id)).filter(SecurityEventML.is_anomaly == True).scalar() or 0
    
    anomaly_rate = round((total_anomalies / total_events * 100.0), 2) if total_events > 0 else 0.0

    critical_events = db.query(func.count(SecurityEventML.id)).filter(SecurityEventML.risk_level == "CRITICAL").scalar() or 0
    high_events = db.query(func.count(SecurityEventML.id)).filter(SecurityEventML.risk_level == "HIGH").scalar() or 0
    medium_events = db.query(func.count(SecurityEventML.id)).filter(SecurityEventML.risk_level == "MEDIUM").scalar() or 0
    low_events = db.query(func.count(SecurityEventML.id)).filter(SecurityEventML.risk_level == "LOW").scalar() or 0

    stats_risk = db.query(
        func.avg(SecurityEventML.risk_score),
        func.min(SecurityEventML.risk_score),
        func.max(SecurityEventML.risk_score),
    ).first()

    avg_risk = round(float(stats_risk[0]), 2) if stats_risk and stats_risk[0] is not None else 0.0
    min_risk = round(float(stats_risk[1]), 2) if stats_risk and stats_risk[1] is not None else 0.0
    max_risk = round(float(stats_risk[2]), 2) if stats_risk and stats_risk[2] is not None else 0.0

    return {
        "total_events": total_events,
        "total_anomalies": total_anomalies,
        "anomaly_rate": anomaly_rate,
        "critical_events": critical_events,
        "high_events": high_events,
        "medium_events": medium_events,
        "low_events": low_events,
        "average_risk_score": avg_risk,
        "min_risk_score": min_risk,
        "max_risk_score": max_risk,
    }


def get_severity_distribution(db: Session):
    """Calculate distribution of events grouped by severity."""
    results = (
        db.query(SecurityEvent.severity, func.count(SecurityEvent.id))
        .group_by(SecurityEvent.severity)
        .all()
    )
    items = [{"name": str(r[0] or "unknown"), "count": r[1]} for r in results]
    return {"metric": "severity", "items": items}


def get_event_types_distribution(db: Session):
    """Calculate distribution of events grouped by event_type."""
    results = (
        db.query(SecurityEvent.event_type, func.count(SecurityEvent.id))
        .group_by(SecurityEvent.event_type)
        .all()
    )
    items = [{"name": str(r[0] or "unknown"), "count": r[1]} for r in results]
    return {"metric": "event_type", "items": items}


def get_risk_levels_distribution(db: Session):
    """Calculate distribution of events grouped by ML risk_level."""
    results = (
        db.query(SecurityEventML.risk_level, func.count(SecurityEventML.id))
        .group_by(SecurityEventML.risk_level)
        .all()
    )
    items = [{"name": str(r[0] or "unknown"), "count": r[1]} for r in results]
    return {"metric": "risk_level", "items": items}
