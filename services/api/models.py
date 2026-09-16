"""
CyberShield Data Platform - SQLAlchemy ORM Models
Maps PostgreSQL security_events and security_event_ml tables.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship

from services.api.database import Base


class SecurityEvent(Base):
    """SQLAlchemy model for security_events table."""
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(50), unique=True, nullable=False, index=True)
    event_type = Column(String(100), index=True)
    severity = Column(String(20), index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    event_date = Column(Date, index=True)
    event_hour = Column(Integer)
    source_ip = Column(String)
    destination_ip = Column(String)
    protocol = Column(String(20))
    source_port = Column(Integer)
    destination_port = Column(Integer)
    processed_at = Column(DateTime(timezone=True))
    loaded_at = Column(DateTime(timezone=True))

    # Relationship to ML results
    ml_result = relationship("SecurityEventML", back_populates="event", uselist=False)


class SecurityEventML(Base):
    """SQLAlchemy model for security_event_ml table."""
    __tablename__ = "security_event_ml"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(50), ForeignKey("security_events.event_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False, index=True)
    anomaly_score = Column(Float, nullable=False)
    is_anomaly = Column(Boolean, nullable=False, index=True)
    model_version = Column(String(50), default="v1.0.0")
    processed_at = Column(DateTime(timezone=True))

    # Relationship back to security event
    event = relationship("SecurityEvent", back_populates="ml_result")
