"""
AgroPulse AI - Crop Recommendation Router
POST /predict/crop
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.schemas.crop import CropRecommendationRequest, CropRecommendationResponse
from app.services.sagemaker_service import sagemaker_service
from app.database import get_db
from app.middleware.auth import get_current_user

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/crop",
    response_model=CropRecommendationResponse,
    summary="Crop Recommendation",
    description="""
    Returns top 3 crop recommendations based on soil NPK values,
    weather conditions, and location-specific data.

    **Model:** XGBoost classifier trained on 2200+ soil-crop combinations

    **Features used:**
    - Soil Nitrogen, Phosphorus, Potassium, pH
    - Temperature, Humidity, Rainfall
    - Geographic location
    """,
)
@limiter.limit("30/minute")
async def predict_crop(
    request: Request,
    payload: CropRecommendationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Predict optimal crops for given soil and weather conditions"""
    result = await sagemaker_service.predict_crop(payload)
    return result
