"""
AgroPulse AI - Alerts & Risk Assessment Router
GET /alerts/{farmer_id}
"""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Query
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.schemas.alert import AlertListResponse, AlertResponse, RiskAssessmentRequest, RiskAssessmentResponse
from app.services.sagemaker_service import sagemaker_service

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def _build_alerts(state: str = "", rainfall_mm: float = 800.0) -> list[AlertResponse]:
    """Build dynamic alerts based on state and rainfall — no hardcoded single set."""
    alerts = []

    # Drought alert — triggered when rainfall < 60% of state normal
    state_normals = {
        "rajasthan": 531, "gujarat": 832, "haryana": 617, "punjab": 649,
        "maharashtra": 1177, "karnataka": 1139, "andhra pradesh": 934,
        "telangana": 934, "madhya pradesh": 1017, "uttar pradesh": 991,
        "kerala": 3055, "west bengal": 1582, "assam": 2818, "odisha": 1489,
        "bihar": 1326, "jharkhand": 1422, "chhattisgarh": 1292,
        "tamil nadu": 998, "himachal pradesh": 1469, "uttarakhand": 1530,
    }
    normal = state_normals.get(state.lower(), 900.0)

    rain_ratio = rainfall_mm / normal

    if rain_ratio < 0.6:
        alerts.append(AlertResponse(
            id=str(uuid.uuid4()),
            alert_type="weather",
            severity="high",
            title="Drought Risk — Below Normal Rainfall",
            message=f"Your area received {rainfall_mm:.0f}mm against normal {normal:.0f}mm "
                    f"({rain_ratio*100:.0f}% of normal). High drought risk for standing crops. "
                    f"Consider drip irrigation and mulching immediately.",
            risk_score=round(1 - rain_ratio, 2),
            is_read=False,
            created_at=datetime.now(timezone.utc),
            metadata={"rainfall_mm": rainfall_mm, "normal_mm": normal, "ratio_pct": round(rain_ratio*100, 1)},
        ))
    elif rain_ratio > 1.3:
        alerts.append(AlertResponse(
            id=str(uuid.uuid4()),
            alert_type="weather",
            severity="high",
            title="Flood Risk — Excess Rainfall",
            message=f"Rainfall is {rain_ratio*100:.0f}% of normal ({rainfall_mm:.0f}mm vs {normal:.0f}mm). "
                    f"Ensure field drainage channels are clear. Risk of waterlogging and root rot.",
            risk_score=round(min(0.95, (rain_ratio - 1) / 2), 2),
            is_read=False,
            created_at=datetime.now(timezone.utc),
            metadata={"rainfall_mm": rainfall_mm, "normal_mm": normal, "ratio_pct": round(rain_ratio*100, 1)},
        ))
    elif rain_ratio < 0.8:
        alerts.append(AlertResponse(
            id=str(uuid.uuid4()),
            alert_type="weather",
            severity="medium",
            title="Below Normal Rainfall — Monitor Crops",
            message=f"Rainfall is {rain_ratio*100:.0f}% of normal. Monitor soil moisture closely "
                    f"and irrigate if needed. Rabi sowing may be delayed.",
            risk_score=round(1 - rain_ratio, 2),
            is_read=False,
            created_at=datetime.now(timezone.utc),
            metadata={"rainfall_mm": rainfall_mm, "normal_mm": normal},
        ))

    # Market alert — always relevant
    alerts.append(AlertResponse(
        id=str(uuid.uuid4()),
        alert_type="market",
        severity="low",
        title="Commodity Price Alert",
        message="Wheat & paddy MSP revised upward by 5.4% for 2024-25. "
                "Register on e-NAM portal (enam.gov.in) for better mandi prices.",
        risk_score=0.20,
        is_read=True,
        created_at=datetime.now(timezone.utc),
        metadata={"source": "CACP MSP notification", "commodity": "wheat,paddy"},
    ))

    # Pest alert — seasonal
    current_month = datetime.now().month
    if 6 <= current_month <= 10:   # Kharif season
        alerts.append(AlertResponse(
            id=str(uuid.uuid4()),
            alert_type="pest",
            severity="medium",
            title="Kharif Pest Advisory",
            message="High humidity increases Fall Armyworm and Brown Plant Hopper risk in maize and paddy. "
                    "Inspect crops weekly. Contact your local KVK for bio-pesticide options.",
            risk_score=0.45,
            is_read=False,
            created_at=datetime.now(timezone.utc),
            metadata={"pests": ["fall_armyworm", "brown_plant_hopper"], "season": "kharif"},
        ))
    elif current_month >= 11 or current_month <= 3:  # Rabi season (Nov-Mar)
        alerts.append(AlertResponse(
            id=str(uuid.uuid4()),
            alert_type="pest",
            severity="low",
            title="Rabi Crop Advisory",
            message="Watch for aphids and yellow rust in wheat. Early morning scouting recommended. "
                    "Apply fungicide if rust coverage exceeds 5% of leaf area.",
            risk_score=0.25,
            is_read=True,
            created_at=datetime.now(timezone.utc),
            metadata={"pests": ["aphids", "yellow_rust"], "season": "rabi"},
        ))

    return alerts


@router.get(
    "/{farmer_id}",
    response_model=AlertListResponse,
    summary="Get Farmer Alerts",
    description="Returns active risk alerts — weather, pest, and market — based on location and rainfall.",
)
async def get_alerts(
    request: Request,
    farmer_id: str,
    state: str = Query(default="", description="Farmer's state for localised alerts"),
    rainfall_mm: float = Query(default=800.0, description="Annual rainfall at farm (mm)"),
):
    alerts = _build_alerts(state=state, rainfall_mm=rainfall_mm)
    return AlertListResponse(
        farmer_id=farmer_id,
        total_alerts=len(alerts),
        unread_count=sum(1 for a in alerts if not a.is_read),
        alerts=alerts,
    )


@router.post(
    "/assess-risk",
    response_model=RiskAssessmentResponse,
    summary="Comprehensive Risk Assessment",
)
@limiter.limit("10/minute")
async def assess_risk(request: Request, payload: RiskAssessmentRequest):
    return await sagemaker_service.assess_risk(payload)
