"""
AgroPulse AI - Yield Prediction Schemas
"""
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class WeatherForecast(BaseModel):
    temperature_celsius: float = Field(..., ge=5, le=50)
    rainfall_mm: float = Field(..., ge=0, le=500)
    humidity_percent: float = Field(..., ge=0, le=100)
    sunshine_hours: Optional[float] = Field(None, ge=0, le=24)


class YieldPredictionRequest(BaseModel):
    crop: str = Field(..., description="Crop name e.g. 'rice', 'wheat', 'cotton'")
    area_hectares: float = Field(..., gt=0, le=1000, description="Farm area in hectares")
    soil_nitrogen: float = Field(..., ge=0, le=200)
    soil_ph: float = Field(..., ge=3.0, le=10.0)
    weather_forecast: WeatherForecast
    irrigation: bool = Field(True, description="Is irrigation available?")
    fertilizer_type: Optional[str] = Field(None, description="e.g. 'organic', 'chemical', 'mixed'")
    farmer_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "crop": "rice",
                "area_hectares": 2.5,
                "soil_nitrogen": 85,
                "soil_ph": 6.2,
                "weather_forecast": {
                    "temperature_celsius": 28,
                    "rainfall_mm": 120,
                    "humidity_percent": 75,
                    "sunshine_hours": 7.5,
                },
                "irrigation": True,
                "fertilizer_type": "chemical",
            }
        }


class YieldPredictionResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    crop: str
    predicted_yield_kg_per_hectare: float
    total_yield_kg: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    key_factors: List[dict]
    prediction_id: str
    model_version: str
    generated_at: str
