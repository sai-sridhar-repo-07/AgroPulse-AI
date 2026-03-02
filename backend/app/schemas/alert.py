"""
AgroPulse AI - Alert Schemas
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AlertResponse(BaseModel):
    id: str
    alert_type: str
    severity: str
    title: str
    message: str
    risk_score: float
    is_read: bool
    created_at: datetime
    metadata: Optional[dict] = None


class AlertListResponse(BaseModel):
    farmer_id: str
    total_alerts: int
    unread_count: int
    alerts: List[AlertResponse]


class RiskAssessmentRequest(BaseModel):
    farmer_id: str
    district: str
    state: str
    crop: Optional[str] = None


class RiskAssessmentResponse(BaseModel):
    overall_risk_score: float = Field(..., ge=0, le=1)
    risk_level: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    risk_factors: List[dict]
    recommendations: List[str]
    generated_at: str
