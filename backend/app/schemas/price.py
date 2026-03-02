"""
AgroPulse AI - Price Forecast Schemas
"""
from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field


class PriceForecastRequest(BaseModel):
    commodity: str = Field(..., description="Commodity name e.g. 'Wheat', 'Rice', 'Cotton'")
    state: str = Field(..., description="Indian state")
    district: Optional[str] = None
    forecast_days: int = Field(7, ge=1, le=30, description="Days to forecast (1-30)")
    farmer_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "commodity": "Wheat",
                "state": "Punjab",
                "district": "Ludhiana",
                "forecast_days": 14,
            }
        }


class PriceForecastPoint(BaseModel):
    date: date
    predicted_price: float
    lower_bound: float
    upper_bound: float
    trend: str  # "rising", "falling", "stable"


class PriceForecastResponse(BaseModel):
    commodity: str
    state: str
    current_price: float
    unit: str = "INR/Quintal"
    forecast: List[PriceForecastPoint]
    price_trend: str
    market_signal: str  # "BUY", "SELL", "HOLD"
    prediction_id: str
    generated_at: str
