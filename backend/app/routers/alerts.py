"""
AgroPulse AI - Alerts & Risk Assessment Router
GET /alerts/{farmer_id}
"""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.schemas.alert import AlertListResponse, AlertResponse, RiskAssessmentRequest, RiskAssessmentResponse
from app.services.sagemaker_service import sagemaker_service
from app.database import get_db

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get(
    "/{farmer_id}",
    response_model=AlertListResponse,
    summary="Get Farmer Alerts",
    description="Returns all active risk alerts for a farmer, including weather, pest, and market alerts.",
)
async def get_alerts(
    request: Request,
    farmer_id: str = Path(..., description="Farmer UUID"),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve active alerts for a specific farmer"""
    # In production: query from RDS/DynamoDB based on farmer_id
    # Here we return sample alerts with realistic data
    sample_alerts = [
        AlertResponse(
            id=str(uuid.uuid4()),
            alert_type="weather",
            severity="medium",
            title="Heavy Rainfall Expected",
            message="Moderate to heavy rainfall (45-65mm) expected in your district in the next 72 hours. Protect standing crops and ensure proper drainage.",
            risk_score=0.58,
            is_read=False,
            created_at=datetime.now(timezone.utc),
            metadata={"rainfall_expected_mm": 55, "duration_hours": 72},
        ),
        AlertResponse(
            id=str(uuid.uuid4()),
            alert_type="market",
            severity="low",
            title="Wheat Price Declining",
            message="Wheat prices are projected to decline by 3-5% over the next 14 days. Consider selling soon if you have surplus stock.",
            risk_score=0.32,
            is_read=False,
            created_at=datetime.now(timezone.utc),
            metadata={"commodity": "wheat", "projected_change_pct": -4.2},
        ),
    ]

    return AlertListResponse(
        farmer_id=farmer_id,
        total_alerts=len(sample_alerts),
        unread_count=sum(1 for a in sample_alerts if not a.is_read),
        alerts=sample_alerts,
    )


@router.post(
    "/assess-risk",
    response_model=RiskAssessmentResponse,
    summary="Comprehensive Risk Assessment",
)
@limiter.limit("10/minute")
async def assess_risk(
    request: Request,
    payload: RiskAssessmentRequest,
):
    """Run AI-powered risk assessment for a farmer's location and crop"""
    return await sagemaker_service.assess_risk(payload)
