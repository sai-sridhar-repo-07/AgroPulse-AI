"""
AgroPulse AI - Price Forecast Router
POST /predict/price
"""
from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.schemas.price import PriceForecastRequest, PriceForecastResponse
from app.services.price_service import price_service

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/price",
    response_model=PriceForecastResponse,
    summary="Commodity Price Forecast",
    description="""
    Forecasts mandi commodity prices for the next 7-30 days.

    Data sources:
    - AGMARKNET historical mandi prices
    - Seasonal trend analysis
    - Regional demand-supply signals

    **Model:** Facebook Prophet time-series forecasting
    """,
)
@limiter.limit("20/minute")
async def forecast_price(
    request: Request,
    payload: PriceForecastRequest,
):
    """Forecast commodity prices for a specified period"""
    return await price_service.forecast_price(payload)
