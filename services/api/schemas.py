"""
CyberShield Data Platform - Pydantic Schemas
Defines request/response payload structures for FastAPI endpoints.
"""

from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: str
    service: str
    database: str
    timestamp: datetime


class SecurityEventMLSchema(BaseModel):
    id: int
    event_id: str
    risk_score: float
    risk_level: str
    anomaly_score: float
    is_anomaly: bool
    model_version: str
    processed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SecurityEventSchema(BaseModel):
    id: int
    event_id: str
    event_type: Optional[str] = None
    severity: Optional[str] = None
    timestamp: datetime
    event_date: Optional[date] = None
    event_hour: Optional[int] = None
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    protocol: Optional[str] = None
    source_port: Optional[int] = None
    destination_port: Optional[int] = None
    processed_at: Optional[datetime] = None
    loaded_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SecurityEventDetailSchema(SecurityEventSchema):
    ml_result: Optional[SecurityEventMLSchema] = None


class PaginatedEventsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[SecurityEventSchema]


class AlertSchema(BaseModel):
    event_id: str
    event_type: Optional[str] = None
    severity: Optional[str] = None
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    timestamp: datetime
    risk_score: float
    risk_level: str
    anomaly_score: float
    is_anomaly: bool
    model_version: str

    model_config = ConfigDict(from_attributes=True)


class PaginatedAlertsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[AlertSchema]


class OverviewStatistics(BaseModel):
    total_events: int
    total_anomalies: int
    anomaly_rate: float
    critical_events: int
    high_events: int
    medium_events: int
    low_events: int
    average_risk_score: float
    min_risk_score: float
    max_risk_score: float


class DistributionItem(BaseModel):
    name: str
    count: int


class DistributionResponse(BaseModel):
    metric: str
    items: List[DistributionItem]
