"""
AgroPulse AI - Yield Prediction Router
POST /predict/yield
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.schemas.yield_schema import YieldPredictionRequest, YieldPredictionResponse
from app.services.sagemaker_service import sagemaker_service
from app.database import get_db

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/yield",
    response_model=YieldPredictionResponse,
    summary="Crop Yield Prediction",
    description="""
    Predicts expected crop yield in kg/hectare based on:
    - Crop type and farm area
    - Soil quality (nitrogen, pH)
    - Weather forecast (temperature, rainfall, humidity)
    - Irrigation availability

    **Model:** Gradient Boosting Regressor with weather time-series features
    """,
)
@limiter.limit("30/minute")
async def predict_yield(
    request: Request,
    payload: YieldPredictionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Predict crop yield for given conditions"""
    return await sagemaker_service.predict_yield(payload)
